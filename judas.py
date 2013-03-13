import re
import sys
import json
import errno
import select
import threading
import traceback
import SocketServer
import multiprocessing


class DebugServer(object):
    def parser_for_type(type):
        return self.parsers.get(str(type.unqualified()))

    def parse_value(self, value, name):
        try:
            parser = self.parsers.get(str(value.type.unqualified()))
            if parser:
                return {
                    "n": name,
                    "t": str(value.type),
                    "p": parser(value)
                }
        except Exception as e:
            # There's a lot of exceptions thrown around when variables aren't
            # initialized or have garbage.
            # TODO: Try no to swallow all the exceptions, just the relevant ones.
            print e

        return None

    def evaluate_expression(self, expression):
        raise NotImplementedError()

    def parse_expression(self, expression):
        value = self.evaluate_expression(expression)
        return self.parse_value(value, expression) if value else None

    def serialize(self, local_variables, member_variables, watches):
        return json.dumps({"locals": local_variables, "members": member_variables, "watches": watches})

    def local_symbols(self):
        raise NotImplementedError()

    def member_symbols(self):
        raise NotImplementedError()

    def store_locals(self):
        try:
            # Try to parse every variable, store what works.
            local_variables = {}
            for (name, value) in self.local_symbols().iteritems():
                parsed = self.parse_value(value, name)
                if parsed:
                    local_variables[name] = parsed

            # Do the same for the member variables.
            member_variables = {}
            for (name, value) in self.member_symbols().iteritems():
                parsed = self.parse_value(value, name)
                if parsed:
                    member_variables[name] = parsed

            # Add watches to the variables.
            watches = {}
            for i in self.watches:
                parsed = self.parse_expression(i)
                if parsed:
                    watches[i] = parsed

            self.send_to_server(self.serialize(local_variables, member_variables, watches))
        except Exception as e:
            traceback.print_exc()
            print e

    def add_watch(self, expression):
        self.watches.add(expression)

    class ThreadedTCPRequestHandler(SocketServer.BaseRequestHandler):
        def read_file(self, filename):
            with open(filename, "r") as file:
                return file.read()

        def send(self, data, format):
            self.request.sendall("HTTP/1.1 200 OK\n"
                                 "Content-Type: %s; charset=UTF-8\n"
                                 "Content-Length: %d\n"
                                 "\n"
                                 "%s"
                                 % (format, len(data), data))

        def handle(self):
            data = self.request.recv(4096)
            match = re.match("GET (.*?) HTTP/1\.1", data)
            if match:
                url = match.group(1)
                if url == "/":
                    self.send(self.read_file("client.html"), "text/html")
                elif url == "/lv":
                    self.send(self.server.content_to_serve(), "application/json")
                else:
                    self.request.sendall("HTTP/1.1 404 Not Found\n")

    class ThreadedTCPServer(SocketServer.ThreadingMixIn, SocketServer.TCPServer):
        # Monkey patch select.select to ignore signals and retry
        original_select = select.select

        def signal_resistant_select(*args, **kwargs):
            while True:
                try:
                    return DebugServer.ThreadedTCPServer.original_select(*args, **kwargs)
                except select.error as e:
                    if e[0] != errno.EINTR:
                        raise

        select.select = signal_resistant_select

        def __init__(self, server_address, RequestHandlerClass, json_debug_server):
            self.json_debug_server = json_debug_server
            self.allow_reuse_address = True
            SocketServer.TCPServer.__init__(self, server_address, RequestHandlerClass)

        def content_to_serve(self):
            return self.json_debug_server.content_to_serve

    def send_to_server(self, content):
        self.parent_end.send(content)

    def start_server(self, our_end, parent_end):
        # Close parent's end of the pipe, otherwise we don't get notified when the parent dies
        parent_end.close()

        # Create the server thread
        server = DebugServer.ThreadedTCPServer(("localhost", 4000), DebugServer.ThreadedTCPRequestHandler, self)
        server_thread = threading.Thread(target = server.serve_forever)
        server_thread.daemon = True
        server_thread.start()

        # Wait for data from the parent
        while True:
            try:
                self.content_to_serve = our_end.recv()
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

    def command_add_watch(self, argument):
        if len(argument) > 0:
            self.add_watch(argument)
            self.store_locals()

    def command_list_watches(self, argument):
        for index, watch in enumerate(sorted(self.watches)):
            print "#%d:" % index, watch

    def command_remove_watch(self, argument):
        if len(argument) > 0:
            original_size = len(self.watches)

            if argument[0] == "#":
                try:
                    index = int(argument[1:])
                    if index < original_size:
                        self.watches.remove(sorted(self.watches)[index])
                    else:
                        print "Index '#%d' is too big" % index
                except ValueError as e:
                    print "Invalid index '%s'" % argument
            elif argument == "*":
                self.watches.clear()
            elif argument in self.watches:
                self.watches.remove(argument)
            else:
                print "Map watch '%s' doesn't exist" % argument

            if len(self.watches) != original_size:
                self.store_locals()

    #
    # Initialization
    #

    def load_parsers(self):
        # Decorator used in parser declaration
        #
        # @parsed_type("ns::Type")
        # def parse_type_ns_Type(value):
        #     return float(value["member"])

        def parsed_type(name):
            def parsed_type_decorator(function):
                function.parsed_type = name
                return function
            return parsed_type_decorator

        parsers = {"parsed_type": parsed_type}
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

        self.parsers = parsers

    def add_commands(self):
        self.add_command("jds-add-watch", self.command_add_watch)
        self.add_command("jds-list-watches", self.command_list_watches)
        self.add_command("jds-remove-watch", self.command_remove_watch)

    def add_command(self, name, handler):
        raise NotImplementedError()

    def install_stop_hook(self, hook):
        raise NotImplementedError()

    def __init__(self):
        self.content_to_serve = self.serialize({}, {}, {})
        self.parent_end, child_end = multiprocessing.Pipe()
        self.watches = set()
        self.parsers = {}

        # Create a server
        server_process = multiprocessing.Process(target = self.start_server, args = (child_end, self.parent_end))
        server_process.daemon = True
        server_process.start()

        # Close child's end of the pipe, otherwise the child doesn't receive an error when the parent dies
        child_end.close()

        self.load_parsers()
        self.add_commands()
        self.install_stop_hook(self.store_locals)

        print "Supported types:"
        for i in self.parsers:
            print " -", i

class GdbDebugServer(DebugServer):
    class Command(gdb.Command):
        def __init__(self, name, handler):
            super(self.__class__, self).__init__(name, gdb.COMMAND_DATA)
            self.handler = handler

        def invoke(self, argument, from_tty):
            self.handler(argument)

    def add_command(self, name, handler):
        self.Command(name, handler)

    def install_stop_hook(self, hook):
        gdb.events.stop.connect(lambda event: hook())

    def local_symbols(self):
        # Collect blocks up to the function level.
        blocks = []
        block = gdb.selected_frame().block()
        while not (block == None or block.is_static or block.is_global):
            blocks.append(block)
            block = block.superblock

        # Go though all the blocks from the most outer to the most inner one and
        # collect all local variable names.
        symbols = {}
        for index, block in enumerate(reversed(blocks)):
            for i in block:
                symbols[i.name] = i

        # Evaluate: convert symbols to values.
        # For GDB 7.5 it should be: symbol.value(gdb.selected_frame())
        # For now use version that works on both 7.4 and 7.5+
        return {name: gdb.selected_frame().read_var(symbol.name) for (name, symbol) in symbols.iteritems()}

    def member_symbols(self):
        members = []
        try:
            members = gdb.parse_and_eval("this").dereference().type.fields()
        except gdb.error:
            # Not in a class context
            pass

        return {i.name: gdb.parse_and_eval("(*this).%s" % i.name) for i in members if not i.is_base_class}

    def evaluate_expression(self, expression):
        try:
            return gdb.parse_and_eval(expression)
        except gdb.error:
            pass

        return None

__jds__ = GdbDebugServer()
