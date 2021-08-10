#!/usr/bin/env python3

import yaml
from collections import namedtuple
from os import getenv
from pathlib import Path
from sys import argv
from . import ci_job, ci_platform, ci_gitlab, ci_trigger

class Pipeline():

    def __init__(self, path, ci_env, directive, project_name=None, 
                 group_name=None, is_downstream=False, config=None):
        self.path = path
        self.ci_env = ci_env
        self.directive = directive
        if project_name:
            self.project_name = project_name
        else:
            self.project_name = self.ci_env.project_name.lower().split('.')[-1]
        if group_name:
            self.group_name = group_name
        else:
            self.group_name = Path(self.ci_env.project_namespace).stem
        if is_downstream:
            self.is_downstream = is_downstream
        else:
            self.is_downstream = self.ci_env.project_name != 'opencpi'
        self.config = config

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
        # Not triggered by host pipeline, so set host pipeline stages
            stages = ['prereqs', 'build', 'test', 'generate-children',
                      'trigger-platforms', 'trigger-projects', 'deploy']
            host_platform = None
        else:
        # Triggered by host pipeline, so set child pipeline stages and get
        # host and cross platforms
            host_platform = ci_platform.get_platform(self.ci_env.host_platform, 
                                                     platforms)
            platform = ci_platform.get_platform(self.ci_env.platform, 
                                                host_platform.cross_platforms)
            # if self.group_name == 'comp':
            # # In comp project pipeline
            #     if platform.model == 'rcc':
            #         stages = ['build-assets-comp', 'build-assemblies']
            #     else:
            #         stages = ['build-primitives', 'build-assets-comp', 
            #                   'build-assemblies', 'build-sdcards', 'test']
            if platform.model == 'rcc':
            # platform is rcc
                stages = ['prereqs-rcc', 'build-rcc', 'build-assemblies']
            else:
            # platform is hdl
                stages = ['build-primitives-core', 'build-primitives',
                          'build-assets', 'build-platforms', 
                          'build-assemblies', 'build-sdcards', 'test']
                if platform.project.group != 'opencpi':
                # not built-in platform, so add stage to create assets after
                # built-in assets
                    project_stage = 'build-assets-{}'.format(
                        platform.project.name)
                    stages.insert(3, project_stage)

            platforms = [platform]

        # If a comp project, remove all projects except that project
        # if self.group_name == 'comp':
        #     projects = [project for project in projects 
        #                 if project.name == self.project_name]

        jobs = []
        for platform in platforms:
            # If triggered by upstream pipeline, do not generate jobs
            # to build host platforms. Assume this was done in the
            # upstream pipeline
            # if self.ci_env.pipeline_source != 'pipeline':
            jobs += ci_job.make_jobs(stages, platform, projects, self,
                                        host_platform=host_platform)

            for cross_platform in platform.cross_platforms:
                # If platform is local or project is in COMP group, 
                # make job to generate child yaml file
                # if cross_platform.project.path or self.group_name == 'comp':
                #     # If platform does not belong to same group as pipeline
                #     # and pipeline is not in the 'comp' group, don't make jobs
                #     if self.group_name != 'comp':
                #             continue

                    generate_job = ci_job.make_generate(
                        platform, cross_platform, self)
                    jobs.append(generate_job)

                    # Make trigger job for child pipeline
                    trigger = ci_trigger.trigger_platform(
                        platform, cross_platform, self, 
                        generate_job=generate_job)
                    jobs.append(trigger)

                # elif self.ci_env.project_name == 'opencpi':
                #     # Make trigger job for downstream pipeline
                #     trigger = ci_trigger.trigger_platform(
                #         platform, cross_platform, self)
                #     jobs.append(trigger)

            # Create triggers for COMP projects
            # if platform.is_host:
            #     # Don't make trigger if pipeline launched by upstream pipeline
            #     if self.ci_env.pipeline_source == 'pipeline':
            #         continue
            #     # Don't make trigger if pipeline not in opencpi or osp project
            #     if self.project_name != 'opencpi' and self.group_name != 'osp':
            #             continue
            #     for project in projects:
            #         if project.group == 'comp':
            #             trigger = ci_trigger.trigger_project(project, self)
            #             jobs.append(trigger)
        
        self._stages = stages
        self._jobs = jobs

        return self


    def get_platform_overrides(self, platform):
        """Gets job overrides for a platform from a dictionary of platforms

        Overrides will replace default job values (tags, script, etc.).

        Args:
            platform: Platform to get overrides for

        Returns:
            A dictionary of job overrides for a specified platform
        """
        try:
            return self.config[platform.name]['overrides']
        except:
            return {}