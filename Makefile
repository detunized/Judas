.PHONY: test
test:
	cd examples/geo && make example
	cd test && py.test -qs
