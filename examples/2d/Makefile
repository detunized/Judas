.PHONY: default
default:
	@echo Run "make gdb"

2d: 2d.cpp
	g++ -g -O0 -w -o 2d 2d.cpp

gdbinit:
	echo "python exec(open('../../judas.py').read())" > gdbinit

.PHONY: gdb
gdb: 2d gdbinit
	gdb --nx -ex "set height 0" --command=gdbinit -ex "set confirm off" -ex "run" ./2d

.PHONY: clean
clean:
	rm -rf 2d 2d.dSYM gdbinit
