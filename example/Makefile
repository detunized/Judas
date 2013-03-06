default:
	@echo Run "make gdb"

example: example.cpp
	g++ -g -O0 -w -o example example.cpp

gdbinit:
	echo "set height 0\npython execfile('../judas.py')" > gdbinit

.PHONY: gdb
gdb: example gdbinit
	gdb --nx -ex "set height 0" --init-command=gdbinit -ex "set confirm off" -ex "b 175" -ex "run" ./example

.PHONY: clean
clean:
	rm -rf example example.dSYM gdbinit
