import sys;
sys.path.append(JUDAS_INSTALL_PATH)
from judas import *


class GdbType(Type):
    def name(self):
        return str(self.type)

    def unqualified(self):
        return GdbType(self.type.unqualified())


class GdbValue(Value):
    def __init__(self, value, text = None):
        super(GdbValue, self).__init__(value)
        self.text = text

    def type(self):
        return GdbType(self.value.type)

    def name(self):
        return self.text

    def dereference(self):
        return GdbValue(self.value.dereference())

    def __getitem__(self, key):
        child = self.value[key]
        return GdbValue(child) if child else None

    def __int__(self):
        return int(self.value)

    def __long__(self):
        return long(self.value)

    def __float__(self):
        return float(self.value)


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
        local_symbols = {}
        for index, block in enumerate(reversed(blocks)):
            for i in block:
                local_symbols[i.name] = i

        return [GdbValue(i.value(gdb.selected_frame()), i.name) for i in local_symbols.values()]

    def evaluate_expression(self, expression):
        try:
            return GdbValue(gdb.parse_and_eval(expression), expression)
        except gdb.error:
            pass

        return None


__jds__ = GdbDebugServer()
