.PHONY: base
.PHONY: framework
.PHONY: rcc_platform
.PHONY: hdl_target
.PHONY: hdl_platform
.PHONY: hdl_rcc_platform
.PHONY: deploy

REG = $(CI_OCPI_CONTAINER_REGISTRY)
CACHE_BASE = $(REG)/cache.base
CACHE_PACKAGES = $(REG)/cache.packages
CACHE_PREREQS = $(REG)/cache.prereqs
CACHE_BUILD = $(REG)/cache.build
CACHE_FRAMEWORK = $(REG)/cache.framework
CACHE_INSTALL = $(REG)/cache.install
FRAMEWORK_IMAGE = $(REG)/$(HOST)
RCC_PLATFORM_IMAGE = $(FRAMEWORK_IMAGE)/$(RCC_PLATFORM)
HDL_TARGET_IMAGE = $(FRAMEWORK_IMAGE)/$(HDL_TARGET)
HDL_PLATFORM_IMAGE = $(FRAMEWORK_IMAGE)/$(HDL_PLATFORM)
HDL_RCC_PLATFORM_IMAGE = $(FRAMEWORK_IMAGE)/$(HDL_PLATFORM)/${RCC_PLATFORM}
COMMIT_TAG = $(CI_PIPELINE_ID)
DEPLOY_REPO = $(HOST)$(if $(HDL_PLATFORM),/$(HDL_PLATFORM))$(if $(RCC_PLATFORM),/$(RCC_PLATFORM))
DEPLOY_SOURCE_IMAGE = $(REG)/$(DEPLOY_REPO)
DEPLOY_IMAGE = $(CI_REGISTRY)/$(DEPLOY_REPO)
CONTAINER_OPENCPI_DIR = /home/user/opencpi
CONTAINER_ARTIFACTS_DIR = $(CONTAINER_OPENCPI_DIR)/.gitlab-ci/artifacts

define create-repository =
aws ecr create-repository --repository-name $(1) >/dev/null 2>&1 || true
aws ecr put-lifecycle-policy --repository-name $(1) --lifecycle-policy-text="$$(cat policy.json)" \
	>/dev/null 2>&1 || true
endef

base:
	podman build - --progress=plain \
		--tag base \
		--layers \
		--cache-to $(CACHE_BASE) \
		--cache-from $(CACHE_BASE) \
		< container/${HOST}.containerfile

packages: base
	podman build .. -f container/Containerfile --progress=plain --target packages \
		--ignorefile=container/packages.containerignore \
		--tag packages \
		--layers \
		--cache-to $(CACHE_PACKAGES) \
		--cache-from $(CACHE_PACKAGES)

prereqs: packages
	podman build .. -f container/Containerfile --progress=plain --target prereqs \
		--ignorefile=container/prereqs.containerignore \
		--tag prereqs \
		--layers \
		--cache-to $(CACHE_PREREQS) \
		--cache-from $(CACHE_PREREQS)

build: prereqs
	podman build .. -f container/Containerfile --progress=plain --target build \
		--ignorefile=container/build.containerignore \
		--tag build \
		--layers \
		--cache-to $(CACHE_BUILD) \
		--cache-from $(CACHE_BUILD)

framework: build
	mkdir -p /tmp/artifacts
	podman build .. -f container/Containerfile --progress=plain --target framework \
		--ignorefile=container/framework.containerignore \
		--env OCPI_XILINX_VIVADO_VERSION \
		--build-arg OCPI_HOST=${HOST} \
		--build-arg OCPI_OSP="${OSP}" \
		--build-arg OCPI_COMP="${COMP}" \
		--tag ${FRAMEWORK_IMAGE}:${COMMIT_TAG} \
		--layers \
		--cache-to $(CACHE_FRAMEWORK) \
		--cache-from $(CACHE_FRAMEWORK) \
		-v /tmp/artifacts:${CONTAINER_ARTIFACTS_DIR}:rw
	$(call create-repository, ${HOST})
	podman push ${FRAMEWORK_IMAGE}:${COMMIT_TAG}
	podman run --rm -v /tmp/artifacts:${CONTAINER_ARTIFACTS_DIR} \
		--env CI_PIPELINE_ID \
		--env HOST \
		--env RCC_PLATFORM \
		--env HDL_PLATFORM \
		${FRAMEWORK_IMAGE}:${COMMIT_TAG} \
		/bin/bash -c "source $(CONTAINER_OPENCPI_DIR)/cdk/opencpi-setup.sh -r \
		&& $(CONTAINER_OPENCPI_DIR)/.gitlab-ci/scripts/generate.py ${CONTAINER_ARTIFACTS_DIR}/test.yml"

rcc_platform:
	mkdir -p /tmp/artifacts
	podman build .. -f container/Containerfile --progress=plain --target install \
		--build-arg SOURCE_IMAGE=${FRAMEWORK_IMAGE}:${COMMIT_TAG} \
		--build-arg OCPI_TARGET=${RCC_PLATFORM} \
		--build-arg OCPI_TARGET_TYPE=platform \
		--tag ${RCC_PLATFORM_IMAGE}:${COMMIT_TAG} \
		--cache-to $(CACHE_INSTALL) \
		--cache-from $(CACHE_INSTALL) \
		-v /tmp/artifacts:${CONTAINER_ARTIFACTS_DIR}:rw \
		-v /tools:/tools
	$(call create-repository, ${HOST}/${RCC_PLATFORM})
	podman push ${RCC_PLATFORM_IMAGE}:${COMMIT_TAG}

hdl_target:
	mkdir -p /tmp/artifacts
	podman build .. -f container/Containerfile --progress=plain --target install \
		--build-arg SOURCE_IMAGE=${FRAMEWORK_IMAGE}:${COMMIT_TAG} \
		--build-arg OCPI_TARGET=${HDL_TARGET} \
		--build-arg OCPI_TARGET_TYPE=hdl-target \
		--tag ${HDL_TARGET_IMAGE}:${COMMIT_TAG} \
		--cache-to $(CACHE_INSTALL) \
		--cache-from $(CACHE_INSTALL) \
		-v /tmp/artifacts:${CONTAINER_ARTIFACTS_DIR}:rw \
		-v /tools:/tools
	$(call create-repository, ${HOST}/${HDL_TARGET})
	podman push ${HDL_TARGET_IMAGE}:${COMMIT_TAG}

hdl_platform:
	mkdir -p /tmp/artifacts
	podman build .. -f container/Containerfile --progress=plain --target install \
		--build-arg SOURCE_IMAGE=${HDL_TARGET_IMAGE}:${COMMIT_TAG} \
		--build-arg OCPI_TARGET=${HDL_PLATFORM} \
		--build-arg OCPI_TARGET_TYPE=platform \
		--tag ${HDL_PLATFORM_IMAGE}:${COMMIT_TAG} \
		--cache-to $(CACHE_INSTALL) \
		--cache-from $(CACHE_INSTALL) \
		-v /tmp/artifacts:${CONTAINER_ARTIFACTS_DIR}:rw \
		-v /tools:/tools
	$(call create-repository, ${HOST}/${HDL_PLATFORM})
	podman push ${HDL_PLATFORM_IMAGE}:${COMMIT_TAG}

hdl_rcc_platform:
	podman build .. -f container/Containerfile --progress=plain --target hdl_rcc_platform \
		--build-arg RCC_SOURCE_IMAGE=${RCC_PLATFORM_IMAGE}:${COMMIT_TAG} \
		--build-arg HDL_SOURCE_IMAGE=${HDL_PLATFORM_IMAGE}:${COMMIT_TAG} \
		--build-arg OCPI_RCC_PLATFORM=${RCC_PLATFORM} \
		--build-arg OCPI_HDL_PLATFORM=${HDL_PLATFORM} \
		--tag ${HDL_RCC_PLATFORM_IMAGE}:${COMMIT_TAG} \
		--cache-to $(CACHE_INSTALL) \
		--cache-from $(CACHE_INSTALL)
	$(call create-repository, ${HOST}/${HDL_PLATFORM}/${RCC_PLATFORM})
	podman push ${HDL_RCC_PLATFORM_IMAGE}:${COMMIT_TAG}

deploy:
	podman build .. -f container/Containerfile --progress=plain --target deploy --squash-all \
		--build-arg SOURCE_IMAGE=${DEPLOY_SOURCE_IMAGE}:${COMMIT_TAG} \
		--tag ${DEPLOY_IMAGE}:${DEPLOY_TAG}
	podman push ${DEPLOY_IMAGE}:${DEPLOY_TAG}
