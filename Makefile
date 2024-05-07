VENV_CMD := . venv/bin/activate &&
CONTAINER_ENGINE = docker
IMAGE_TEST=external_resources_io_test

.PHONY: .build-image
.build-image:
	$(CONTAINER_ENGINE) build -t $(IMAGE_TEST) -f hack/Dockerfile .

.PHONY: release
release: .build-image
	$(CONTAINER_ENGINE) run -e TWINE_PASSWORD --rm $(IMAGE_TEST) /bin/bash hack/release.sh

.PHONY: test
test: .build-image
	$(CONTAINER_ENGINE) run --rm -ti $(IMAGE_TEST) /bin/bash hack/test.sh

.PHONY: dev-venv
	python3.11 -m venv venv
	@$(VENV_CMD) pip install --upgrade pip
	@$(VENV_CMD) pip install -r requirements.txt
	@$(VENV_CMD) pip install -r requirements_dev.txt
	@$(VENV_CMD) pip install -r requirements_test.txt
