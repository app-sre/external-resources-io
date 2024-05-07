.PHONY: release

CONTAINER_ENGINE ?= $(shell which podman >/dev/null 2>&1 && echo podman || echo docker)
IMAGE=registry.access.redhat.com/ubi9/python-311:latest
BASEPATH=/opt/app-root/src

release:
	$(CONTAINER_ENGINE) run -v $(shell pwd):$(BASEPATH) --rm $(IMAGE) $(BASEPATH)/hack/release.sh
