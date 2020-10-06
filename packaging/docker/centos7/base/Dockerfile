FROM centos:7

RUN yum -y distro-sync \
 && yum -y install git nfs-utils \
 && yum clean all \
 && rm -rf /var/cache/yum

CMD ["/bin/bash"]
