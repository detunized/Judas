default:
	@echo Run "make gdb" or "make lldb"

example: example.cpp
	g++ -g -O0 -w -o example example.cpp

gdbinit:
	echo "python JUDAS_INSTALL_PATH = \"$(shell pwd)/../\"; execfile(JUDAS_INSTALL_PATH + \"judas-gdb.py\")" > gdbinit

.lldbinit:
	echo "script JUDAS_INSTALL_PATH = \"$(shell pwd)/../\"; execfile(JUDAS_INSTALL_PATH + \"judas-lldb.py\")" > .lldbinit

.PHONY: gdb
gdb: example gdbinit
	gdb --nx --init-command=gdbinit -ex "set confirm off" -ex "b 89" -ex "run" ./example

.PHONY: lldb
lldb: example .lldbinit
	lldb ./example

.PHONY: clean
clean:
	rm -rf example example.dSYM gdbinit .lldbinit
