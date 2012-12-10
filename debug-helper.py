from __future__ import with_statement

import re
import json
import errno
import select
import threading
import SocketServer

# TODO: Hide these properly and lock!
__variables = {}
__watches = set()

def set_variables(local_variables = {}, watches = {}):
    global __variables
    __variables = {"locals": local_variables, "watches": watches}

def get_variables():
    return __variables

def parse_type_LatLon(value):
    return [float(value["lat"]), float(value["lon"])]

def parse_type_Polyline(value):
    points = value["points"]["_M_impl"]
    start = points["_M_start"]
    size = int(points["_M_finish"] - start)
    return [coord for i in range(size) for coord in parse_type_LatLon(start[i])]

def add_watch(expression):
    global __watches
    __watches.add(expression)

def parser_for_type(type):
    return globals().get("parse_type_" + str(type.unqualified()))

def parse_expression(expression, type = None):
    try:
        value = None

        if not type:
            value = gdb.parse_and_eval(expression)
            type = value.type

        if type:
            parser = parser_for_type(type)
            if parser:
                return {
                    "n": expression,
                    "t": str(type.unqualified()),
                    "p": parser(value if value else gdb.parse_and_eval(expression))
                }
    except gdb.error:
        pass

    return None

def store_locals(event):
    # Collect blocks up to the function level.
    blocks = []
    block = gdb.selected_frame().block()
    while not (block == None or block.is_static or block.is_global):
        blocks.append(block)
        block = block.superblock

    # Go though all the blocks from the most outer to the most inner one and
    # collect all local variable names.
    local_symbols = {}
    for index, block in enumerate(reversed(blocks)):
        for i in block:
            local_symbols[i.name] = i

    # Try to parse every variable, store what works.
    locals_variables = {}
    for name, symbol in local_symbols.iteritems():
        parsed = parse_expression(name, symbol.type)
        if parsed:
            locals_variables[name] = parsed

    # Add watches to the variables.
    watches = {}
    for i in __watches:
        parsed = parse_expression(i)
        if parsed:
            watches[i] = parsed

    set_variables(locals_variables, watches)

#
# Entry point
#

set_variables()

add_watch("g_p")
# add_watch("p1")
# add_watch("main")
# add_watch("?")
# add_watch(".")
# add_watch("abc")

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
                self.request.sendall(json.dumps(get_variables()))

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
