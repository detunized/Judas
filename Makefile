# This is needed to prevent bytecode to be genrated.
# It breakes folder sharing between the LXC container and the host.
export PYTHONDONTWRITEBYTECODE=1

.PHONY: test
test:
	make --directory examples/geo build
	cd test && py.test -qs

.PHONY: examples
examples:
	make --directory examples/2d build
	make --directory examples/geo build
	make --directory examples/raw build
