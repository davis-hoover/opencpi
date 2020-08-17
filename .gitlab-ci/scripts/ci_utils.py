#!/usr/bin/env python3

import os
from collections import namedtuple


def get_ci_env():
    ci_env_dict = {}

    for key,value in os.environ.items():
        if key.startswith('CI_'):
            ci_env_dict[key[3:].lower()] = value

    if ci_env_dict:
        Ci_Env = namedtuple('Env', ci_env_dict.keys())
        ci_env = Ci_Env(*ci_env_dict.values())
    else:
        exit('Error: No CI env vars exist')

    return ci_env


def set_test_env():
    os.environ["CI_PROJECT_DIR"] = os.getcwd()
    os.environ["CI_JOB_STAGE"] = "test_stage"
    os.environ["CI_JOB_NAME"] = "test_job"
    os.environ["CI_COMMIT_MESSAGE"] = "[ci ubuntu18_04 centos7 zed,matchstiq_z1:xilinx13_3,xilinx13_4 \
        zcu104:xilinx13_4, xilinx13_4:zcu104, zcu104:xilinx13_3, plutosdr]"
    os.environ["CI_PIPELINE_ID"] = "test_pipeline"
    os.environ["CI_PLATFORMS"] = 'centos7 xsim xilinx13_3 xilinx13_4'
    os.environ["CI_MR_PLATFORMS"] = 'centos7 xsim modelsim zed:xlinx13_4,xilinx13_3'
    os.environ["CI_PIPELINE_SOURCE"] = "push"