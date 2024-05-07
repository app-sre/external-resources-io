.PHONY: release

CONTAINER_ENGINE = docker
IMAGE_TEST=external_resources_io_test

.build-release-image:
	$(CONTAINER_ENGINE) build -t $(IMAGE_TEST) -f hack/Dockerfile.release .

release: .build-release-image
	$(CONTAINER_ENGINE) run -e TWINE_PASSWORD --rm -ti $(IMAGE_TEST) /bin/bash hack/release.sh
