FROM ubuntu:18.04

RUN apt update \
 && apt -y upgrade \
 && apt -y install git iproute2 iputils-ping nfs-common \
 && rm -rf /var/lib/{apt,cache,dkpg,log}

CMD ["/bin/bash"]
