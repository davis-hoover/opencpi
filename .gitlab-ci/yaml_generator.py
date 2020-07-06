#!/usr/bin/env python3

import yaml
import os
import sys

hw_platform = sys.argv[2]
host_platform = sys.argv[1]
CI_PROJECT_DIR = os.environ.get('CI_PROJECT_DIR')

yml = {}

yml['stages'] = [
    'prereq',
    'build',
    'build-primitives-core',
    'build-primitives',
    'build-workers',
    'build-platforms',
    'build-assemblies',
    'test'
]
  
yml['default'] = {
    'tags': [
        'opencpi',
        '{}'.format(host_platform),
        'shell'
    ],
    'before_script': [
        'for f in artifacts*.tar; do if [ -f "$f" ]; then tar -xf "$f"; fi; done',
        'sleep 2',
        'date "+%Y-%m-%d %H:%M:%S" > timestamp.txt',
        'sleep 2',
    ],
    'after_script': [
        'if [ ! -f {}/.success ]; then {}/.gitlab-ci/upload-failed-job.sh exit 1 fi'.format(CI_PROJECT_DIR, CI_PROJECT_DIR),
        'rm -f {}/.success'.format(CI_PROJECT_DIR),
        'find -not -type d -newerct "$(< timestamp.txt)" > artifacts-$CI_JOB_STAGE-$CI_JOB_ID.txt',
        'tar -T artifacts-$CI_JOB_STAGE-$CI_JOB_ID.txt -cf artifacts-$CI_JOB_STAGE-$CI_JOB_ID.tar',
        'for f in artifacts*.tar; do if [ "$f" != "artifacts-$CI_JOB_STAGE-$CI_JOB_ID.tar" ]; then rm -rf "$f"; fi; done',
    ]
}

yml['install-prereqs'] = {
    'stage': 'prereq',
    'script': [
        'yum -y distro-sync',
        './scripts/install-packages.sh',
        'touch {}/.success"'.format(CI_PROJECT_DIR)
    ]
}

yml['build-opencpi'] = {
    'stage': 'build',
    'script': [
        './scripts/install-prerequisites.sh',
        'touch {}/.success"'.format(CI_PROJECT_DIR)
    ]
}

cwd = os.path.dirname(sys.argv[0])
source_cmd = 'source cdk/opencpi-setup.sh -r'
build_hdl = 'ocpidev build -d {} --hdl-platform {}'
build_plat = 'ocpidev build hdl platforms -d {} --hdl-platform {}'
os.chdir(os.path.join(cwd,'..'))
projects_dir = os.path.abspath('projects')
projects = [os.path.join(projects_dir,d) 
            for d in os.listdir(projects_dir) 
            if os.path.isdir(os.path.join(projects_dir, d))
                and d != 'tutorial']

for project in projects:
    hdl_dir = os.path.join(project, 'hdl') if os.path.isdir(os.path.join(project, 'hdl')) else None
    comp_dir = os.path.join(project, 'components') if os.path.isdir(os.path.join(project, 'components')) else None
    workers = []

    if os.path.basename(project) == 'assets' and comp_dir:
        workers += [os.path.join(comp_dir, d) 
                    for d in os.listdir(comp_dir)
                    if os.path.isdir(os.path.join(comp_dir, d))]
    elif comp_dir:
        workers.append(comp_dir)

    if hdl_dir:
        workers = [os.path.join(hdl_dir, d) for d in os.listdir(hdl_dir)]

    for worker in workers:
        if not os.path.isdir(worker):
            continue

        script = build_hdl.format(worker, hw_platform)

        if os.path.basename(worker) == 'assemblies':
            stage = 'build-assemblies'
        elif os.path.basename(worker) == 'primitives':
            if os.path.basename(project) == 'core':
                stage = 'build-primitives-core'
            else:
                stage = 'build-primitives'
        elif os.path.basename(worker) == 'platforms':
            stage = 'build-platforms'
            script = build_plat.format(worker, hw_platform)
        else:
            stage = 'build-workers'

        yml['build-{}-{}'.format(os.path.basename(project), os.path.basename(worker))] = {
            'stage': stage,
            'script': [
                source_cmd,
                script
            ]
        }



with open(os.path.join(cwd, '{}-{}.yml'.format(host_platform, hw_platform)), 'w') as f:
    yml= yaml.dump(yml, f, width=1000, default_flow_style=False)

# with open(".gitlab-ci/templates.yml", 'r') as stream:
#     print(yaml.safe_load(stream))