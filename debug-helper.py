import re
import json
import errno
import select
import threading
import SocketServer
import multiprocessing

def parser_for_type(type):
    return g_parsers.get(str(type.unqualified()))

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
                self.request.sendall(read_file("client.html"))
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
# Commands
#

class AddMapWatchCommand(gdb.Command):
    def __init__(self):
        super (AddMapWatchCommand, self).__init__("add-map-watch", gdb.COMMAND_DATA)

    def invoke(self, argument, from_tty):
        if len(argument) > 0:
            add_watch(argument)
            store_locals(None)

class ListMapWatchesCommand(gdb.Command):
    def __init__(self):
        super (ListMapWatchesCommand, self).__init__("list-map-watches", gdb.COMMAND_DATA)

    def invoke(self, argument, from_tty):
        for index, watch in enumerate(sorted(g_watches)):
            print "#%d:" % index, watch

class RemoveMapWatchCommand(gdb.Command):
    def __init__(self):
        super (RemoveMapWatchCommand, self).__init__("remove-map-watch", gdb.COMMAND_DATA)

    def invoke(self, argument, from_tty):
        if len(argument) > 0:
            original_size = len(g_watches)

            if argument[0] == "#":
                try:
                    index = int(argument[1:])
                    if index < original_size:
                        g_watches.remove(sorted(g_watches)[index])
                    else:
                        print "Index '#%d' is too big" % index
                except ValueError as e:
                    print "Invalid index '%s'" % argument
            elif argument == "*":
                g_watches.clear()
            elif argument in g_watches:
                g_watches.remove(argument)
            else:
                print "Map watch '%s' doesn't exist" % argument

            if len(g_watches) != original_size:
                store_locals(None)

#
# Entry point
#

def load_parsers():
    global g_parsers

    parsers = {}
    execfile("parsers.py", parsers)

    parsers = {
        parsers[i].parsed_type: parsers[i]
            for i in parsers
            if "parsed_type" in dir(parsers[i])
    }

    # Add reference and pointer equivalents
    for i in parsers.keys():
        # References
        parsers["%s &" % i] = parsers[i]
        parsers["const %s &" % i] = parsers[i]

        # Pointers
        dereference_and_parse = lambda value: parsers[i](value.dereference())
        parsers["%s *" % i] = dereference_and_parse
        parsers["const %s *" % i] = dereference_and_parse

    g_parsers = parsers

def main():
    # Create a server
    server_process = multiprocessing.Process(target = start_server, args = (g_child_end, g_parent_end))
    server_process.daemon = True
    server_process.start()

    # Close child's end of the pipe, otherwise the child doesn't receive an error when the parent dies
    g_child_end.close()

    # Install GDB hook
    gdb.events.stop.connect(store_locals)

    load_parsers()

    print "Supported types:"
    for i in g_parsers:
        print " -", i

    # Add commands
    AddMapWatchCommand()
    ListMapWatchesCommand()
    RemoveMapWatchCommand()

# Some globals
g_content_to_serve = serialize({}, {})
g_parent_end, g_child_end = multiprocessing.Pipe()
g_watches = set()
g_parsers = {}

if __name__ == "__main__":
    main()
