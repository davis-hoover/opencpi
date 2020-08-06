#!/usr/bin/env python3

import os
import re
from collections import namedtuple, defaultdict

def get_ci_env():
    ci_env_dict = {}

    for key,value in os.environ.items():
        if key.startswith('CI_'):
            ci_env_dict[key[3:].lower()] = value

    Ci_Env = namedtuple('Env', ci_env_dict.keys())
    ci_env = Ci_Env(*ci_env_dict.values())

    return ci_env


def get_platform_directive(commit_message):
    commit_directive = re.search('\[ci (.*)\]', commit_message)
    space_pattern = re.compile(r'([^ $]+)')
    colon_pattern = re.compile(r'([^:$]+)')
    comma_pattern = re.compile(r'([^,$]+)')
    platforms = defaultdict(set)

    if commit_directive:
        platform_names = commit_directive.group(1)
    else:
        platform_names = self.ci_env.hdl_platforms

    spaces = space_pattern.findall(platform_names)
    for space in spaces:
        colons = colon_pattern.findall(space)
        left = colons[0]
        
        if left:
            l_commas = comma_pattern.findall(left)
            
            for l_comma in l_commas:

                if len(colons) == 2:
                    right = colons[1]
                    r_commas = comma_pattern.findall(right)

                    for r_comma in r_commas:
                        platforms[l_comma].add(r_comma)
                        platforms[r_comma].add(l_comma)

                else:
                    platforms[l_comma] = {}

    return platforms


def set_test_env():
    os.environ["CI_PROJECT_DIR"] = os.getcwd()
    os.environ["CI_JOB_STAGE"] = "test_stage"
    os.environ["CI_JOB_ID"] = "test_job"
    os.environ["CI_COMMIT_MESSAGE"] = "[ci centos7 zed,matchstiq_z1:xilinx13_3,xilinx13_4 \
        zcu104:xilinx13_4, xilinx13_4:zcu104, zcu104:xilinx13_3, plutosdr]"
    os.environ["CI_PIPELINE_ID"] = "test_pipeline"
    os.environ["CI_HOST_PLATFORM"] = 'centos7'

set_test_env()