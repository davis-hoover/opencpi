ARG IMAGE
FROM $IMAGE

RUN groupadd -g 1000 user && useradd -ms /bin/bash -u 1000 -g 1000 user && mkdir /home/user/opencpi && chown user /home/user/opencpi
WORKDIR /home/user/opencpi
COPY --chown=user:user . $WORKDIR
ARG RCC_PLATFORM
ARG HDL_PLATFORM
RUN source ./cdk/opencpi-setup.sh -r \
    && ocpidoc --help || true \
    && if [[ -n "$RCC_PLATFORM" && -n "$HDL_PLATFORM" ]] ; \
       then ocpiadmin deploy platform ${RCC_PLATFORM} ${HDL_PLATFORM} ; fi
ENTRYPOINT /bin/bash
