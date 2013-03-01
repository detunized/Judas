import os
import re
import sys
import json
import time
import httplib
import pexpect
import collections

class Debugger(object):
    debugger_prompt = "\(gdb\) "

    def __init__(self, verbose = False):
        self.debugger = pexpect.spawn("make gdb", cwd = "../example")
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
    connection = httplib.HTTPConnection("localhost:4000")
    connection.request("GET", "/lv")
    response = connection.getresponse()
    data = None
    if response.status == 200:
        data = json.loads(response.read())
    connection.close()
    return data

def test_all():
    with open("../example/example.cpp") as f:
        lines = f.readlines()

    assertions = {}
    for index, line in enumerate(lines, start = 1):
        matches = re.match(r"^\s*CHECK//\s*(.*?)\s*$", line)
        if matches:
            assertions[index] = matches.group(1)

    # TODO: This is potentially O(N^2)
    breakpoints = collections.defaultdict(list)
    for i in assertions.keys():
        break_on = i
        while break_on - 1 in assertions:
            break_on -= 1
        breakpoints[break_on].append(i)

    d = Debugger(verbose = False)

    debugger_breakpoints = {}
    for i in breakpoints.keys():
        d.send("b %d" % i)
        d.debugger.expect("Breakpoint (\d+) at")
        debugger_breakpoints[int(d.debugger.match.group(1))] = i
        d.wait()

    d.step("jds-list-watches")
    d.send("run")

    while True:
        stop_reason = d.wait(["Breakpoint (\d+), ", "\[Inferior 1 \(process \d+\) exited normally\]"])
        match = d.debugger.match
        d.wait()
        if stop_reason == 0:
            v = get_variables()
            line = int(match.group(1))
            if line in debugger_breakpoints:
                for i in breakpoints[debugger_breakpoints[line]]:
                    print "Asserting", assertions[i]
                    assert eval(assertions[i])
            d.send("continue")
        elif stop_reason == 1:
            break

    d.quit()