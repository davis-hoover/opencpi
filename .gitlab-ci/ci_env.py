#!/usr/bin/env python3

import os
from collections import namedtuple

def get_ci_env():
    ci_env_dict = {}

    for key,value in os.environ.items():
        if key.startswith('CI_'):
            ci_env_dict[key[3:].lower()] = value

    keys = ['{}'.format(key) for key in ci_env_dict.keys()]
    values = ['{}'.format(value) for value in ci_env_dict.values()]

    Ci_Env = namedtuple('Env', keys)
    ci_env = Ci_Env(*values)

    return ci_env

def set_test_env():
    os.environ["CI_PROJECT_DIR"] = os.getcwd()
    os.environ["CI_JOB_STAGE"] = "test_stage"
    os.environ["CI_JOB_ID"] = "test_job"
    os.environ["CI_COMMIT_MESSAGE"] = "[ci zed,matchstiq_z1:xilinx13_3,xilinx13_4 zcu104:xilinx13_4, xilinx13_4:zcu104, plutosdr]"
    os.environ["CI_PIPELINE_ID"] = "test_pipeline"
    os.environ["CI_HOST_PLATFORM"] = 'centos7'

set_test_env()