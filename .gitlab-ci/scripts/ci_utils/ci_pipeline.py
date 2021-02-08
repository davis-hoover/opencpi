#!/usr/bin/env python3

import yaml
from collections import namedtuple
from os import getenv
from pathlib import Path
from sys import argv
from . import ci_job, ci_platform

class Pipeline():

    def __init__(self, path, ci_env, directive):
        self.path = path
        self.ci_env = ci_env
        self.directive = directive

    def to_dict(self):
        """ Converts a Pipeline namedtuple to a dictionary

            Dictionary is created with the intention for it to be dumped
            to a yaml file.

        Returns:
            Dictionary representation of a Pipeline namedtuple
        """
        pipeline_dict = {
            'stages': self._stages,
            }

        for job in self._jobs:
            pipeline_dict[job.name] = ci_job.to_dict(job)

        pipeline_dict['workflow'] = {
            'rules': [{
                'when': 'always'
            }]
        }

        return pipeline_dict

    def dump(self, path, mode='w+'):
        """ Write Pipeline or dictionary to a yaml file

            If parent directiories of path do not already exist,
            they will be created.

        Args:
            path: Path of yaml to dump to
            mode: mode to pass to open() cmd
        """
        pipeline_dict = self.to_dict()

        if not isinstance(path, Path):
            path = Path(path)

        parents = [parent for parent in path.parents]
        for parent in parents[::-1]:
            parent.mkdir(exist_ok=True)

        yaml.SafeDumper.ignore_aliases = lambda *args : True
        with open(path, mode) as yml:
            yaml.safe_dump(pipeline_dict, yml, width=1000, 
                default_flow_style=False)

    def generate(self, projects, platforms, config=None):
        """Generates a pipeline for opencpi projects and platforms

        Calls get_overrides() to get the job overrides for a platform
        or specific job. If source of pipeline is 'parent_pipeline', 
        makes pipeline for passed Platforms; otherwise makes pipeline
        for cross_platforms in each passed Platform. 
        Calls ci_job.make_job() to make jobs for appropriate platforms.
        Calls ci_job.make_trigger() and ci_job.make_generate() to
        generate trigger jobs and generator jobs for each cross_platform
        in appropriate Platforms.

        Args: 
            projects:  List of Projects to generate pipeline for
            platforms: List of Platforms to generate pipeline for
            config:    Dictionary with platform names as keys and
                       dictonaries as values. Dictionary in the values 
                       must include a dictionary with 'overrides' as key 
                       and job overrides as values
        """

        if self.ci_env.pipeline_source != 'parent_pipeline':
            stages = ['prereqs', 'build', 'test', 'generate-children',
                      'trigger-children', 'deploy']
            host_platform = None
        else:
            host_platform = ci_platform.get_platform(self.ci_env.host_platform, 
                                                     platforms)
            platform = ci_platform.get_platform(self.ci_env.platform, 
                                                host_platform.cross_platforms)
            if platform.model == 'rcc':
                stages = ['prereqs-rcc', 'build-rcc', 'build-assemblies', 
                          'test']
            else:
                stages = ['build-primitives-core', 'build-primitives',
                          'build-assets', 'build-platforms', 
                          'build-assemblies', 'build-sdcards', 'test']
                if not platform.project.is_builtin:
                    project_stage = 'build-assets-{}'.format(
                        platform.project.name)
                    stages.insert(3, project_stage)

            platforms = [platform]

        jobs = []
         
        for platform in platforms:
            overrides = get_overrides(platform, config)
            is_downstream = self.ci_env.project_name != 'opencpi'

            # If triggered by upstream pipeline, do not generate jobs
            # to build host platforms. Assume this was done in the
            # upstream pipeline
            if self.ci_env.pipeline_source != 'pipeline':
                jobs += ci_job.make_jobs(stages, platform, projects,
                                        config=config,
                                        overrides=overrides, 
                                        host_platform=host_platform,
                                        is_downstream=is_downstream)

            for cross_platform in platform.cross_platforms:
                # If platform is local, make job to generate child yaml file
                if cross_platform.project.path:
                    # If platform is a built-in opencpi platform, but the
                    # project is not opencpi, don't make jobs
                    if self.ci_env.project_name != 'opencpi':
                        if cross_platform.project.is_builtin:
                            continue

                    generate_job = ci_job.make_generate(
                        platform, cross_platform, self, overrides=overrides)
                    jobs.append(generate_job)

                    # Make trigger job for child pipeline
                    trigger = ci_job.make_trigger(
                        platform, cross_platform, self, 
                        generate_job=generate_job, overrides=overrides)
                    jobs.append(trigger)

                elif self.ci_env.project_name == 'opencpi':
                    trigger = ci_job.make_trigger(
                        platform, cross_platform, self, 
                        overrides=overrides)
                    jobs.append(trigger)
        
        self._stages = stages
        self._jobs = jobs

        return self


def get_overrides(platform, config):
    """Gets job overrides for a platform from a dictionary of platforms

    Overrides will replace default job values (tags, script, etc.).

    Args:
        platform: Platform to get overrides for
        config:   Dictionary with platform names as keys and
                  dictonaries as values. Dictionary in the values must
                  include a dictionary with 'overrides' as key and
                  job overrides as values

    Returns:
        A dictionary of job overrides for a specified platform
    """
    try:
        return config[platform.name]['overrides']
    except:
        return {}