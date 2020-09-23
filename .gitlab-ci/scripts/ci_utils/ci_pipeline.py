#!/usr/bin/env python3

import yaml
from collections import namedtuple
from os import getenv
from pathlib import Path
from . import ci_job


_Pipeline = namedtuple('pipeline', 'stages, jobs, include, workflow')


def Pipeline(stages, jobs, include=None, workflow=None):
    """ Create a Pipeline namedtuple

    Args:
        stages:  Stages in the pipeline
        jobs:    Jobs for the pipeline to execute
        include: Other yaml files to include in the pipeline

    Returns:
        Pipeline namedtuple
    """
    pipeline = _Pipeline(jobs=jobs, stages=stages, include=include,
                         workflow=workflow)

    return pipeline


def to_dict(pipeline):
    """ Converts a Pipeline namedtuple to a dictionary

        Dictionary is created with the intention for it to be dumped
        to a yaml file.

    Args:
        pipeline: Pipeline namedtuple to convert to a dictionary

    Returns:
        Dictionary representation of a Pipeline namedtuple
    """
    pipeline_dict = {
        'stages': pipeline.stages,
        }

    if pipeline.include:
        pipeline_dict['include'] = pipeline.include

    if pipeline.workflow:
        pipeline_dict['workflow'] = pipeline.workflow

    for job in pipeline.jobs:
        pipeline_dict[job.name] = ci_job.to_dict(job)

    return pipeline_dict


def dump(pipeline, path, mode='w+'):
    """ Write Pipeline or dictionary to a yaml file

        If Pipeline is passed, to_dict() is called to convert it to a
        dictionary. If parent directiories of path do not already exist,
        they will be created.

    Args:
        pipeline: Pipeline namedtuple or dictionary to be dumped to yaml
        path:     Path of yaml to dump to
    """
    if not isinstance(pipeline, dict):
        pipeline = to_dict(pipeline)

    parents = [parent for parent in path.parents]
    for parent in parents[::-1]:
        parent.mkdir(exist_ok=True)

    yaml.SafeDumper.ignore_aliases = lambda *args : True
    with open(path, mode) as yml:
        yaml.safe_dump(pipeline, yml, width=1000, default_flow_style=False)


def make_parent_pipeline(host_platforms, cross_platforms,
                         yaml_parent_path, yaml_children_path, whitelist=None, 
                         config=None):
    """ Construct a parent pipeline

    Args:
        host_platforms:     List of all host Platforms
        cross_platforms:    List of all non-host Platforms
        yaml_parent_path:   Path to files to include in parent pipeline
        yaml_children_path: Path to artifact to CI yaml for jobs
                            triggering child pipelines
        whitelist:          List of names of allowed platforms
        config:             Dictionary of platform overrides

    Returns:
        Pipeline namedtuple
    """
    stages = ['.pre', 'prereqs', 'build', 'test', 'generate-children',
              'trigger-children', 'deploy']
    jobs = []

    # Make host platform jobs
    for host_platform in host_platforms:
        if whitelist:
            if host_platform.name in whitelist:
                host_whitelist = whitelist[host_platform.name]
            else:
                continue

        print("\t", host_platform.name)
        overrides = get_overrides(host_platform, config)
        host_jobs = ci_job.make_jobs(stages, host_platform, 
                                     overrides=overrides)
        jobs += host_jobs

        for cross_platform in cross_platforms:
            if whitelist and cross_platform.name not in host_whitelist:
                continue

            overrides = get_overrides(cross_platform.name, config)
            yaml_child_path = Path(yaml_children_path,
                                   '{}-{}.yml'.format(host_platform.name,
                                                      cross_platform.name))

            # Make job to generate child yaml file
            script = [
                'yum install epel-release -y',
                'yum install python36-PyYAML -y',
                '.gitlab-ci/scripts/ci_yaml_generator.py {} {}'.format(
                    host_platform.name, cross_platform.name),
            ]
            artifacts = {'paths': [str(yaml_child_path)]}
            tags = ['docker']
            image = 'centos:7'
            stage = 'generate-children'
            name = ci_job.make_name(cross_platform, stage=stage,
                                    host_platform=host_platform)
            rules = ci_job.make_rules(cross_platform, host_platform)
            generate_child_job = ci_job.Job(name=name, stage=stage,
                                            script=script, artifacts=artifacts,
                                            tags=tags, image=image,
                                            rules=rules, overrides=overrides)
            jobs.append(generate_child_job)

            # Make trigger job for child pipeline
            include = [{
                'artifact': str(yaml_child_path),
                'job': generate_child_job.name
            }]
            trigger = ci_job.make_trigger(host_platform, cross_platform,
                                          include, overrides=overrides)
            jobs.append(trigger)

    include = [str(path) for path in Path(yaml_parent_path).glob('*.yml')]

    return Pipeline(stages, jobs=jobs, include=include)


def make_child_pipeline(projects, host_platform, cross_platform,
                        linked_platforms, config=None):
    """ Construct a child pipeline

    Args:
        projects:           List of opencpi Projects
        host_platform:      Host Platform of child pipeline
        cross_platform:     Platform to build/test in child pipeline
        yaml_parent_path:   Path to files to include in parent pipeline
        yaml_children_path: Path to artifact to CI yaml for jobs
                            triggering child pipelines
        whitelist:          List of names of allowed platforms
        config:             Dictionary of platform overrides

    Returns:
        Pipeline namedtuple
    """
    if cross_platform.model == 'rcc':
        stages = ['prereqs', 'build-rcc', 'test']
    else:
        stages = ['build-primitives-core', 'build-primitives',
                  'build-libraries', 'build-libraries-osp', 'build-platforms', 
                  'build-assemblies', 'build-sdcards', 'test']

    overrides = get_overrides(cross_platform, config)
    workflow = {'rules': [
        {'if': '$CI_MERGE_REQUEST_ID'},
        {'when': 'always'}
    ]}

    jobs = ci_job.make_jobs(stages, cross_platform, projects,
                            host_platform=host_platform,
                            linked_platforms=linked_platforms,
                            overrides=overrides)

    return Pipeline(stages, jobs, workflow=workflow)


def make_downstream_pipeline(host_platforms, osp, osp_path, yaml_children_path, 
                             whitelist=None, config=None):
    #TODO: docs
    stages = ['generate-children', 'trigger-children']
    jobs = []

    for host_platform in host_platforms:
        if whitelist:
            if host_platform.name in whitelist:
                host_whitelist = whitelist[host_platform.name]
            else:
                continue

        for cross_platform in osp.platforms:
            if whitelist and cross_platform.name not in host_whitelist:
                continue

            overrides = get_overrides(cross_platform, config)

            # Make job to generate child yaml file
            script = [
                'yum install epel-release -y',
                'yum install python36-PyYAML -y',
                '.gitlab-ci/scripts/ci_yaml_generator.py {} {}'.format(
                    host_platform.name, cross_platform.name),
            ]
                
            before_script = [
                'yum install git -y',
                #TODO: change ref to 'develop'
                'if [ -z "$CI_UPSTREAM_ID" ];' \
                    ' then export REF_NAME="1347-osp-yaml-generator"; fi',
                ' '.join(['git clone --depth 1 --single-branch --branch'
                            ' "$REF_NAME"',
                          '"https://gitlab.com/opencpi/opencpi.git"',
                          'opencpi']),
                ' '.join(['git clone --depth 1 --single-branch --branch', 
                          '"$CI_COMMIT_REF_NAME"', 
                          '"$CI_REPOSITORY_URL"', 
                          '"opencpi/projects/osps/${CI_PROJECT_NAME}"']),
                'cd opencpi'
            ]
            artifacts = {'paths': [str(Path('opencpi', yaml_children_path))]}
            tags = ['docker']
            image = 'centos:7'
            stage = 'generate-children'
            name = ci_job.make_name(cross_platform, stage=stage,
                                    host_platform=host_platform)
            rules = ci_job.make_rules(cross_platform, host_platform)
            generate_child_job = ci_job.Job(name=name, stage=stage,
                                            script=script, 
                                            before_script=before_script, 
                                            artifacts=artifacts,
                                            tags=tags, image=image,
                                            rules=rules, overrides=overrides)
            jobs.append(generate_child_job)

            # Make trigger job for child pipeline
            include = [{
                'artifact': str(Path('opencpi', yaml_children_path)),
                'job': generate_child_job.name
            }]
            trigger = ci_job.make_trigger(host_platform, cross_platform,
                                            include, overrides=overrides)
            jobs.append(trigger)

    return Pipeline(stages, jobs)


def get_overrides(platform, config):
    """Gets job overrides for a platform from a dictionary of platforms

    Overrides will replace default job values (tags, script, etc.).

    Args:
        platform: Platform to get overrides for
        config:   Dictionary with platform names as keys and
                  overrides as values

    Returns:
        A dictionary of job overrides for a specified platform
    """
    try:
        return config[platform.name]['overrides']
    except:
        return {}