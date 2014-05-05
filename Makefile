# This is needed to prevent bytecode to be genrated.
# It breakes folder sharing between the LXC container and the host.
export PYTHONDONTWRITEBYTECODE=1

.PHONY: test
test:
	@$(MAKE) -C examples/geo build
	@cd test && py.test -qs

.PHONY: examples
examples:
	@for i in 2d geo raw; do \
		$(MAKE) -C examples/$$i build; \
	done
