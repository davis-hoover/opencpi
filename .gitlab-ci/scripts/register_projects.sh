#!/bin/bash

OSP=$1
COMP=$2
for project in ${OSP[@]} ; do
    echo registering project "ocpi.osp.${project}"
    ocpidev register -d projects/osps/ocpi.osp.${project}
done
for project in ${COMP[@]} ; do 
    echo registering project "ocpi.comp.${project}"
    ocpidev register -d projects/comps/ocpi.comp.${project}
    ocpidev build -d projects/comps/ocpi.comp.${project}
done