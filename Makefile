.PHONY: test
test:
	cd examples/geo && make geo
	cd test && py.test -qs
