.PHONY: default
default:
	@echo Run "make gdb"

raw: raw.cpp
	g++ -g -O0 -w -o raw raw.cpp

gdbinit:
	echo "python exec(open('../../judas.py').read())" > gdbinit

.PHONY: gdb
gdb: raw gdbinit
	gdb --nx -ex "set height 0" --command=gdbinit -ex "set confirm off" -ex "run" ./raw

.PHONY: clean
clean:
	rm -rf raw gdbinit
