
import yaml
from collections import namedtuple
from os import getenv
from pathlib import Path
from . import ci_job


_Pipeline = namedtuple('pipeline', 'stages, jobs, include')


def Pipeline(stages, jobs, include=None):
    pipeline = _Pipeline(jobs=jobs, stages=stages, include=include)

    return pipeline


def to_dict(pipeline):
    pipeline_dict = {
        'stages': pipeline.stages,
        }

    if pipeline.include:
        pipeline_dict['include'] = pipeline.include

    for job in pipeline.jobs:
        pipeline_dict[job.name] = ci_job.to_dict(job)

    return pipeline_dict


def dump(pipeline, path):
    if not isinstance(pipeline, dict):
        pipeline = to_dict(pipeline)

    parents = [parent for parent in path.parents]
    for parent in parents[::-1]:
        parent.mkdir(exist_ok=True)

    yaml.SafeDumper.ignore_aliases = lambda *args : True
    with open(path, 'w+') as yml:
        yaml.safe_dump(pipeline, yml, width=1000, default_flow_style=False)


def make_parent_pipeline(projects, host_platforms, cross_platforms, 
                         yaml_parent_path, yaml_children_path, whitelist=None, 
                         config=None):
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
        host_jobs = ci_job.make_jobs(stages, host_platform, projects, 
                                     overrides=overrides)
        jobs += host_jobs

        for cross_platform in cross_platforms:
            if whitelist and cross_platform.name not in host_whitelist:
                continue

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
            name = ci_job.make_name(stage, cross_platform, 
                                    host_platform=host_platform)
            rules = ci_job.make_rules(cross_platform, host_platform)
            generate_child_job = ci_job.Job(name=name, stage=stage, 
                                            script=script, artifacts=artifacts,
                                            tags=tags, rules=rules)
            jobs.append(generate_child_job)

            # Make trigger job for child pipeline
            include = [{
                'artifact': str(yaml_child_path),
                'job': generate_child_job.name
            }]
            overrides = get_overrides(cross_platform.name, config)
            trigger = ci_job.make_trigger(host_platform, cross_platform, 
                                          include, overrides=overrides)
            jobs.append(trigger)

    include = [str(path) for path in Path(yaml_parent_path).glob('*.yml')]

    return Pipeline(stages, jobs=jobs, include=include)


def make_child_pipeline(projects, host_platform, cross_platform, 
                        linked_platforms, config=None):
    if cross_platform.model == 'rcc':
        stages = ['prereqs', 'build-rcc', 'test']
    else:
        stages = ['build-primitives-core', 'build-primitives', 
                  'build-libraries', 'build-platforms', 'build-assemblies', 
                  'build-sdcards', 'test']

    overrides = get_overrides(cross_platform, config)
    jobs = ci_job.make_jobs(stages, cross_platform, projects, 
                            host_platform=host_platform, 
                            linked_platforms=linked_platforms, 
                            overrides=overrides)
    
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
