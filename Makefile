.PHONY: release

CONTAINER_ENGINE = docker
IMAGE_TEST=external_resources_io_test

.build-image:
	$(CONTAINER_ENGINE) build -t $(IMAGE_TEST) -f hack/Dockerfile .

release: .build-image
	$(CONTAINER_ENGINE) run -e TWINE_PASSWORD --rm $(IMAGE_TEST) /bin/bash hack/release.sh

test: .build-image
	$(CONTAINER_ENGINE) run --rm -ti $(IMAGE_TEST) /bin/bash hack/test.sh
