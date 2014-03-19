# This is needed to prevent bytecode to be genrated.
# It breakes folder sharing between the LXC container and the host.
export PYTHONDONTWRITEBYTECODE=1

.PHONY: test
test:
	cd examples/geo && make geo
	cd test && py.test -qs
