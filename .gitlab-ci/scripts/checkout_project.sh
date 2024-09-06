#!/bin/bash

project="${UPSTREAM_PROJECT}"
ref="${UPSTREAM_REF}"
namespace="${UPSTREAM_NAMESPACE}"
if [ -n "${project}" ] ; then 
    group=$(basename "${namespace}")s
    projectpath=${CI_PROJECT_DIR}/projects/${group}/${project}
    git -C ${projectpath} fetch origin ${ref}
    git -C ${projectpath} checkout ${ref}
fi