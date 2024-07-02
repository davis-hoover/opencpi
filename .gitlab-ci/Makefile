.PHONY: packages
.PHONY: deploy
.PHONY: all

REG = $(CI_OCPI_CONTAINER_REGISTRY)
DOCKER_BUILDKIT = 1
BASE_IMAGE = $(HOST)/packages
DEFAULT_TAG = $(CI_DEFAULT_BRANCH)
BRANCH_TAG = $(shell echo $${CI_COMMIT_BRANCH:-$${CI_MERGE_REQUEST_SOURCE_BRANCH_NAME}})
COMMIT_TAG = $(CI_COMMIT_SHORT_SHA)
DEPLOY_IMAGE = $(shell echo $${HOST}$${HDL_TARGET:+/}$${HDL_TARGET:-}$${HDL_PLATFORM:+/}$${HDL_PLATFORM:-}$${RCC_PLATFORM:+/}$${RCC_PLATFORM:-})

all: packages deploy

packages:
	docker buildx build .. -f dockerfiles/$(HOST).dockerfile --progress=plain \
		--tag $(REG)/$(BASE_IMAGE):$(BRANCH_TAG) \
		--tag $(REG)/$(BASE_IMAGE):$(COMMIT_TAG) \
		--cache-to type=inline \
		--cache-from type=registry,ref=$(REG)/$(BASE_IMAGE):$(COMMIT_TAG) \
		--cache-from type=registry,ref=$(REG)/$(BASE_IMAGE):$(BRANCH_TAG) \
		--cache-from type=registry,ref=$(REG)/$(BASE_IMAGE):$(DEFAULT_TAG)
	aws ecr create-repository --repository-name ${BASE_IMAGE} || true
	docker push $(REG)/$(BASE_IMAGE):$(BRANCH_TAG)
	docker push $(REG)/$(BASE_IMAGE):$(COMMIT_TAG)
deploy:
	docker buildx build .. -f dockerfiles/deploy.dockerfile --progress=plain \
		--tag $(REG)/$(DEPLOY_IMAGE):$(BRANCH_TAG) \
		--tag $(REG)/$(DEPLOY_IMAGE):$(COMMIT_TAG) \
		--build-arg IMAGE=$(REG)/$(BASE_IMAGE):$(COMMIT_TAG) \
		--build-arg RCC_PLATFORM=$(RCC_PLATFORM) \
		--build-arg HDL_PLATFORM=$(HDL_PLATFORM) \
		--cache-from type=registry,ref=$(REG)/$(BASE_IMAGE):$(COMMIT_TAG) \
		--cache-from type=registry,ref=$(REG)/$(BASE_IMAGE):$(BRANCH_TAG) \
		--cache-from type=registry,ref=$(REG)/$(BASE_IMAGE):$(DEFAULT_TAG)
	aws ecr create-repository --repository-name ${DEPLOY_IMAGE} --image-scanning-configuration scanOnPush=true 2>/dev/null \
		&& aws ecr put-lifecycle-policy --repository-name ${DEPLOY_IMAGE} --lifecycle-policy-text="$(cat scripts/policy.json)" \
		|| true
	docker push $(REG)/$(DEPLOY_IMAGE):$(COMMIT_TAG)
	docker push $(REG)/$(DEPLOY_IMAGE):$(BRANCH_TAG)