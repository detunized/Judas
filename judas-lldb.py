import sys;
sys.path.append(JUDAS_INSTALL_PATH)
from judas import *


class LldbType(Type):
    def name(self):
        return self.type.name

    def unqualified(self):
        return LldbType(self.type.GetUnqualifiedType())


class LldbValue(Value):
    def type(self):
        return LldbType(self.value.type)

    def name(self):
        return self.value.name

    def dereference(self):
        return LldbValue(self.value.Dereference())

    def __getitem__(self, key):
        child = self.value.GetChildMemberWithName(key)
        return LldbValue(child) if child else None

    def __int__(self):
        return int(self.value.GetValue())

    def __long__(self):
        return long(self.value.GetValue())

    def __float__(self):
        return float(self.value.GetValue())


class LldbDebugServer(DebugServer):
    def __init__(self):
        super(LldbDebugServer, self).__init__()

    def add_command(self, name, handler):
        pass

    def install_stop_hook(self, hook):
        self.stop_hook = hook
        lldb.debugger.HandleCommand("target stop-hook add -o 'script __jds__.stop_hook()'") # TODO: Fix the hack!

    def local_symbols(self):
        return [LldbValue(i) for i in lldb.frame.get_all_variables()]

    def evaluate_expression(self, expression):
        value = lldb.frame.EvaluateExpression(expression)
        return LldbValue(value) if value.IsValid() else None


__jds__ = LldbDebugServer()
