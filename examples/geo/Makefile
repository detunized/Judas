default:
	@echo Run "make gdb"

geo: geo.cpp
	g++ -g -O0 -w -o geo geo.cpp

gdbinit:
	echo "python exec(open('../../judas.py').read())" > gdbinit

.PHONY: gdb
gdb: geo gdbinit
	gdb --nx -ex "set height 0" --command=gdbinit -ex "set confirm off" -ex "b 175" -ex "run" ./geo

.PHONY: clean
clean:
	rm -rf geo geo.dSYM gdbinit
