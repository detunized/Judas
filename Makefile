.PHONY: test
test:
	cd example && make example
	cd test && py.test -qs
