import judas

class GdbType(judas.Type):
    pass


class GdbValue(judas.Value):
    pass


class GdbJsonDebugServer(judas.JsonDebugServer):
    class Command(gdb.Command):
        def __init__(self, name, handler):
            super(Command, self).__init__(name, gdb.COMMAND_DATA)
            self.handler = handler

        def invoke(self, argument, from_tty):
            self.handler(argument)

    def add_command(self, name, handler):
        Command(name, handler)

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
        local_symbols = {}
        for index, block in enumerate(reversed(blocks)):
            for i in block:
                local_symbols[i.name] = i

        # # Try to parse every variable, store what works.
        # local_variables = {}
        # for name, symbol in local_symbols.iteritems():
        #     parsed = parse_expression(name, symbol.type)
        #     if parsed:
        #         local_variables[name] = parsed

        # # Add watches to the variables.
        # watches = {}
        # for i in self.g_watches:
        #     parsed = parse_expression(i)
        #     if parsed:
        #         watches[i] = parsed

        return local_symbols

    def evaluate_expression(self, expression):
        try:
            return GdbValue(gdb.parse_and_eval(expression))
        except gdb.error:
            pass

        return None


jds = GdbJsonDebugServer()
