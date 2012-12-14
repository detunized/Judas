import re
import json
import errno
import select
import threading
import SocketServer
import multiprocessing

def parse_type_LatLon(value):
    return [float(value["lat"]), float(value["lon"])]

def parse_type_Polyline(value):
    points = value["points"]["_M_impl"]
    start = points["_M_start"]
    size = int(points["_M_finish"] - start)
    return [coord for i in range(size) for coord in parse_type_LatLon(start[i])]

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

def serialize(local_variables, watches):
    return json.dumps({"locals": local_variables, "watches": watches})

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
    local_variables = {}
    for name, symbol in local_symbols.iteritems():
        parsed = parse_expression(name, symbol.type)
        if parsed:
            local_variables[name] = parsed

    # Add watches to the variables.
    watches = {}
    for i in g_watches:
        parsed = parse_expression(i)
        if parsed:
            watches[i] = parsed

    send_to_server(serialize(local_variables, watches))

def add_watch(expression):
    global g_watches
    g_watches.add(expression)

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
                self.request.sendall(g_content_to_serve)

class ThreadedTCPServer(SocketServer.ThreadingMixIn, SocketServer.TCPServer):
    # Monkey patch select.select to ignore signals and retry
    original_select = select.select

    def signal_resistant_select(*args, **kwargs):
        while True:
            try:
                return ThreadedTCPServer.original_select(*args, **kwargs)
            except select.error as e:
                if e[0] != errno.EINTR:
                    raise

    select.select = signal_resistant_select

    def __init__(self, server_address, RequestHandlerClass):
        self.allow_reuse_address = True
        SocketServer.TCPServer.__init__(self, server_address, RequestHandlerClass)

def send_to_server(content):
    g_parent_end.send(content)

def start_server(our_end, parent_end):
    global g_content_to_serve

    # Close parent's end of the pipe, otherwise we don't get notified when the parent dies
    parent_end.close()

    # Create the server thread
    server = ThreadedTCPServer(("localhost", 4000), ThreadedTCPRequestHandler)
    server_thread = threading.Thread(target = server.serve_forever)
    server_thread.daemon = True
    server_thread.start()

    # Wait for data from the parent
    while True:
        try:
            g_content_to_serve = our_end.recv()
        except IOError as e:
            if e.errno != errno.EINTR:
                raise
        except EOFError as e:
            # This should happen when the parent's terminated and the pipe got closed
            server.shutdown()
            server_thread.join
            return

#
# Entry point
#

def main():
    # Create a server
    server_process = multiprocessing.Process(target = start_server, args = (g_child_end, g_parent_end))
    server_process.daemon = True
    server_process.start()

    # Close child's end of the pipe, otherwise the child doesn't receive an error when the parent dies
    g_child_end.close()

    # Install GDB hook
    gdb.events.stop.connect(store_locals)

# Some globals
g_content_to_serve = serialize({}, {})
g_parent_end, g_child_end = multiprocessing.Pipe()
g_watches = set()

if __name__ == "__main__":
    main()
