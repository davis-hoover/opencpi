
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

    # Make job to generate child yaml files
    script = '.gitlab-ci/scripts/ci_yaml_generator.py'
    artifacts = {'paths': [str(yaml_children_path)]}
    tags = ['centos7', 'shell', 'opencpi']
    generate_children_job = ci_job.Job(name='generate-children', 
                                       stage='generate-children', 
                                       script=script, artifacts=artifacts,
                                       tags=tags)
    jobs.append(generate_children_job)

    # Make host platform jobs
    for host_platform in host_platforms:
        if whitelist and host_platform.name not in whitelist:
            continue

        overrides = get_overrides(host_platform, config)
        host_jobs = ci_job.make_jobs(stages, host_platform, projects, 
                                     overrides=overrides)
        jobs += host_jobs

        # Make trigger jobs for each child pipeline
        for cross_platform in cross_platforms:
            if whitelist and cross_platform.name not in whitelist[host_platform.name]:
                continue

            overrides = get_overrides(cross_platform.name, config)
            include = [{
                'artifact': str(Path(
                    yaml_children_path, 
                    '{}-{}.yml'.format(host_platform.name, 
                                       cross_platform.name))),
                'job': generate_children_job.name
            }]
            trigger = ci_job.make_trigger(host_platform, cross_platform, 
                                          include, overrides=overrides)
            jobs.append(trigger)

    include = [str(path) for path in Path(yaml_parent_path).glob('*.yml')]

    return Pipeline(stages, jobs=jobs, include=include)


def make_child_pipeline(projects, host_platform, cross_platform, 
                        linked_platforms, config=None):
    if cross_platform.model == 'rcc':
        stages = ['prereqs', 'build', 'test']
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
