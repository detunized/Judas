import os
import re
import ast
import sys
import json
import time
import httplib
import pexpect
import collections

class Debugger(object):
    debugger_prompt = "\(gdb\) "

    def __init__(self, verbose = False):
        self.debugger = pexpect.spawn("make gdb", cwd = "../examples/geo")
        if verbose:
            self.debugger.logfile_read = sys.stdout
        self.wait()

    def wait(self, what = debugger_prompt):
        return self.debugger.expect(what)

    def send(self, command):
        self.debugger.send(command + "\r")

    def step(self, command):
        self.send(command)
        self.wait()

    def quit(self):
        self.send("quit")
        self.wait(pexpect.EOF)

def get_variables():
    connection = httplib.HTTPConnection("localhost:4000") # TODO: Make this configurable
    connection.request("GET", "/lv")
    response = connection.getresponse()
    data = None
    if response.status == 200:
        data = json.loads(response.read())
    connection.close()
    return data

def print_assertion_parts(assertion, v):
    def evaluate(node, v):
        return eval(compile(ast.Expression(node), "<string>", "eval"))

    expression = ast.parse(assertion, "<string>", "eval").body
    if isinstance(expression, ast.Compare):
        print "  - left side:", evaluate(expression.left, v)
        for subexpression in expression.comparators:
            print "  - right side:", evaluate(subexpression, v)


def test_all():
    with open("../examples/geo/geo.cpp") as f:
        lines = f.readlines()

    # Collect all debugger commands
    commands = []
    for index, line in enumerate(lines, start = 1):
        matches = re.match(r"^\s*DEBUGGER//\s*(.*?)\s*$", line)
        if matches:
            commands.append(matches.group(1))

    # Collect all assertions
    assertions = {}
    for index, line in enumerate(lines, start = 1):
        matches = re.match(r"^\s*CHECK//\s*(.*?)\s*$", line)
        if matches:
            assertions[index] = matches.group(1)

    # Collapse breakpoints on consecutive lines into one
    # TODO: This is potentially O(N^2)
    breakpoints = collections.defaultdict(list)
    for i in assertions.keys():
        break_on = i
        while break_on - 1 in assertions:
            break_on -= 1
        breakpoints[break_on].append(i)

    # Start the debugger
    d = Debugger(verbose = False)

    # Execute all commands
    for i in commands:
        print "Executing:", i
        d.step(i)

    # Set all break points
    debugger_breakpoints = {}
    for i in breakpoints.keys():
        d.send("b %d" % i)
        d.debugger.expect("Breakpoint (\d+) at")
        debugger_breakpoints[int(d.debugger.match.group(1))] = i
        d.wait()

    # Go
    d.send("run")

    # Wait for breakpoints to get hit and assert on expressions associated with them
    while True:
        stop_reason = d.wait(["Breakpoint (\d+), ", "\[Inferior 1 \(process \d+\) exited normally\]"])
        match = d.debugger.match
        d.wait()
        if stop_reason == 0:
            v = get_variables()
            line = int(match.group(1))
            if line in debugger_breakpoints:
                for i in breakpoints[debugger_breakpoints[line]]:
                    print "Asserting:", assertions[i], "at", debugger_breakpoints[line]
                    try:
                        assert eval(assertions[i])
                    except AssertionError as e:
                        print_assertion_parts(assertions[i], v)
                        raise
            d.send("continue")
        elif stop_reason == 1:
            break

    d.quit()
