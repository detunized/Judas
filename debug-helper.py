from __future__ import with_statement

import re
import json
import errno
import select
import threading
import SocketServer

# TODO: Hide it properly and lock
__local_variables = {}

def set_local_variables(local_variables):
    global __local_variables
    __local_variables = local_variables

def get_local_variables():
    return __local_variables

def parse_type_LatLon(value):
    return [float(value["lat"]), float(value["lon"])]

def parse_type_Polyline(value):
    points = value["points"]
    return [coord for i in range(int(value["count"])) for coord in parse_type_LatLon(points[i])]

def collect_locals(block, depth, variables):
    for i in block:
        name = i.name
        unique_name = "%d_%s" % (depth, name)
        unqualified_type = str(i.type.unqualified())
        parser = "parse_type_%s" % unqualified_type
        if parser in globals():
            variables[unique_name] = {
                "n": name,
                "t": unqualified_type,
                "p": globals()[parser](gdb.parse_and_eval(name))
            }
    return variables

def store_locals(event):
    local_variables = {}

    blocks = []
    block = gdb.selected_frame().block()
    while not (block == None or block.is_static or block.is_global):
        blocks.append(block)
        block = block.superblock

    for index, block in enumerate(reversed(blocks)):
        collect_locals(block, index, local_variables)

    set_local_variables(local_variables)

# Install GDB hook
gdb.events.stop.connect(store_locals)

def read_file(filename):
    with open(filename, "r") as file:
        return file.read()

class ThreadedTCPRequestHandler(SocketServer.BaseRequestHandler):
    def handle(self):
        data = self.request.recv(4096)
        match = re.match("GET (.*?) HTTP/1\.1", data)
        if match:
            url = match.group(1)
            if url == "/":
                self.request.sendall(read_file("/home/dyakimen/nokia/debug-helper/client.html"))
            elif url == "/lv":
                self.request.sendall(json.dumps(get_local_variables()))

class ThreadedTCPServer(SocketServer.ThreadingMixIn, SocketServer.TCPServer):
    def __init__(self, server_address, RequestHandlerClass):
        self.allow_reuse_address = True
        SocketServer.TCPServer.__init__(self, server_address, RequestHandlerClass)

    def serve_forever(self, poll_interval=0.5):
        self._BaseServer__is_shut_down.clear()
        try:
            while not self._BaseServer__shutdown_request:
                # XXX: Consider using another file descriptor or
                # connecting to the socket to wake this up instead of
                # polling. Polling reduces our responsiveness to a
                # shutdown request and wastes cpu at all other times.
                while True:
                    try:
                        #r, w, e = select.select([self], [], [], poll_interval)
                        r, w, e = select.select([self], [], [])
                    except select.error, v:
                        if v[0] != errno.EINTR:
                            raise
                    else:
                        break
                if self in r:
                    self._handle_request_noblock()
        finally:
            self._BaseServer__shutdown_request = False
            self._BaseServer__is_shut_down.set()

# Create a server
server = ThreadedTCPServer(("localhost", 5000), ThreadedTCPRequestHandler)

# Start the server in a thread
server_thread = threading.Thread(target = server.serve_forever)
server_thread.daemon = True
server_thread.start()
