#!/usr/bin/env python3

import re
import yaml
import sys
from ci_env import get_ci_env
from pathlib import Path

def main():
    ci_env = get_ci_env()
    projects = Project.discover_projects('project-registry')
    platforms = Platform.discover_platforms(projects)

    for platform in platforms:
        pipeline = Pipeline(platform, projects, ci_env.host_platform)
        pipeline.to_yml()



class Pipeline():

    def __init__(self, platform, projects, host_platform_name):

        if not isinstance(projects, list):
            projects = [projects]

        self.platform = platform
        self.projects = projects
        self.host_platform_name = host_platform_name
        self.jobs = self.gen_jobs()

    
    def gen_jobs(self):
        jobs = []

        for self.project in self.projects:
            if self.platform.model == 'hdl':
                for library_path in self.project.libraries:
                    job = Job(self.platform, self.project, self.host_platform_name, library_path=library_path)
                    jobs.append(job)

                    if 'components' in [library_path.parent.stem, library_path.parents[1].stem]:
                        job = Job(self.platform, self.project, self.host_platform_name, 
                            library_path=library_path, stage='build-tests')
                        jobs.append(job)
            
            else:
                for stage in Job.rcc_stages:
                    job = Job(self.platform, self.project, self.host_platform_name, stage=stage)
                    jobs.append(job)

        return jobs


    def to_yml(self):
        yml = {}

        for job in self.jobs:
            yml[job.name] = {
                'stage': job.stage,
                'script': job.script
            }

        path = Path('.gitlab-ci', 'generated-yaml')
        path.mkdir(exist_ok=True)
        path = Path(path, '{}-{}.yaml'.format(self.host_platform_name, self.platform.name))
        with open(path, 'w+') as f:
            yaml.dump(yml, f, width=1000, default_flow_style=False)



class Job():
    rcc_stages = ['prereqs', 'build', 'test']
    hdl_stages = ['build-primitives', 'build-libraries', 'build-platforms', 
                  'build-assemblies', 'build-sdcard', 'build-tests', 'test']


    def __init__(self, platform, project, host_platform_name, library_path=None, stage=None):
        self.project = project
        self.platform = platform
        self.host_platform_name = host_platform_name

        if library_path or platform.model == 'rcc':
            self.library_path = library_path
        else:
            sys.Exit('Library path must be provided for hdl platform job')

        if stage:
            self.stage = stage
        elif platform.model == 'hdl':
            self.stage = self.gen_stage()
        else:
            sys.Exit('Stage must be provided for rcc platform job')

        self.name = self.gen_name()
        self.script = self.gen_script()


    def gen_name(self):
        if self.platform.model == 'hdl':
            name = '{}:{}:{}:{}:{}'.format(
                self.project.name,  self.stage, self.library_path.stem, 
                self.host_platform_name, self.platform.name)
        else:
            name = '{}:{}'.format(self.host_platform_name, self.platform.name)

        return name


    def gen_stage(self):
        if self.library_path.stem == 'primitives':
            return 'build-primitives'
        elif self.library_path.stem == 'platforms':
            return 'build-platforms'
        elif self.library_path.stem in ['assemblies', 'tests']:
            return 'build-assemblies'
        else:
            return 'build-libraries'


    def gen_script(self):
        stages = Job.hdl_stages if self.platform.model == 'hdl' else Job.rcc_stages
        stage_idx = stages.index(self.stage)
        download_cmd = '.gitlab-ci/ci_artifacts.py download -i "*{}.tar.gz" "*{}.tar.gz"'.format(
            self.platform.name, self.host_platform_name)
        sleep_cmd = 'sleep 2'
        timestamp_cmd = 'touch .timestamp'
        source_cmd = 'source cdk/opencpi-setup.sh -e'
        success_cmd = 'touch .success'
        upload_cmd = '.gitlab-ci/ci_artifacts.py upload -t .timestamp'

        for stage in stages[:stage_idx]:
            download_cmd += ' "*/{}/*"'.format(stage)

        if self.platform.model == 'hdl':
            if self.stage in ['build-primitives', 'build-libraries', 'build-assemblies']:
                build_cmd = 'ocpidev build -d {} --hdl-platform {}'.format(self.library_path, self.platform.name)
            elif self.stage == 'build-platforms':
                build_cmd = 'ocpidev build hdl platforms {} --hdl-platform {}'.format(self.project.path, self.platform.name)
            # elif self.stage == 'build-sdcard':
            #     build_cmd = 'ocpiadmin deploy platform {} {}'.format(self.platform.name, self.platform.name)
            elif self.stage == 'build-tests':
                build_cmd = 'ocpidev build test {} --hdl-platform {}'.format(self.project.path, self.platform.name)
            elif self.stage == 'test':
                build_cmd = 'ocpidev run tests {} --only-platform {}'.format(self.project.path, self.platform.name)
            else:
                sys.exit('Unkown hdl stage: {}'.format(self.stage))
        else:
            if self.stage == 'prereqs':
                build_cmd = 'scripts/install-prerequisites.sh {}'.format(self.platform.name)
            elif self.stage == 'build':
                build_cmd = 'scripts/install-opencpi.sh {}'.format(self.platform.name)
            elif self.stage == 'test':
                build_cmd = 'ocpidev run tests {} --only-platform {}'.format(self.project.path, self.platform.name)
            else:
                sys.exit('Unkown rcc stage: {}'.format(self.stage))

        return [download_cmd, sleep_cmd, timestamp_cmd, source_cmd, build_cmd, success_cmd, upload_cmd]


class Project():
    

    def __init__(self, path):

        if isinstance(path, str):
            path = Path(path)

        self.name = path.stem
        self.path = path
        self.libraries = self.discover_libraries()


    @classmethod
    def discover_projects(cls, projects_path):
        path = Path(projects_path)
        projects = []

        if path.is_absolute():
            path = project.relative_to(Path.cwd())

        for project_path in path.glob('*'):
            project_path = Path(project_path)

            if project_path.is_symlink():
                project_path = project_path.resolve()

            project_path = project_path.relative_to(Path.cwd())
            project = cls(project_path)
            projects.append(project)

        return projects
    

    def discover_libraries(self):
        self.libraries = set()
        components_path = Path(self.path, 'components')
        hdl_path = Path(self.path, 'hdl')
        library_names = ['primitives', 'devices', 'cards', 'adapters', 'platforms', 'assemblies']

        for library_path in hdl_path.glob('*'):
            if Path(library_path, 'Makefile').is_file():
                if library_path.stem in library_names:
                    self.libraries.add(library_path)

        if Path(components_path, 'specs').is_dir():
            self.libraries.add(components_path)
        else:
            for library_path in components_path.glob('*'):
                if Path(library_path, 'specs').is_dir():
                    self.libraries.add(library_path)

        return list(self.libraries)


class Platform():


    def __init__(self, path, links=None):
        self.path = path
        self.name = path.stem
        self.model = path.parents[1].stem

        if not links:
            links = []

        self.links = links

    
    @classmethod
    def discover_platforms(cls, projects):
        platforms = []

        if not isinstance(projects, list):
            projects = [projects]
        
        for project in projects:
            hdl_platforms_path = Path(project.path, 'hdl', 'platforms')
            rcc_platforms_path = Path(project.path, 'rcc', 'platforms')

            for platforms_path in [hdl_platforms_path, rcc_platforms_path]:
                if platforms_path.is_dir():

                    for platform_path in platforms_path.glob('*'):
                        if Path(platform_path, 'Makefile').is_file():
                            platform = cls(platform_path)
                            platforms.append(platform)

        return platforms


    @classmethod
    def get_platform(cls, platforms, platform_name):
        for platform in platforms:
            if platform.name == platform_name:
                return platform

        return None


main()