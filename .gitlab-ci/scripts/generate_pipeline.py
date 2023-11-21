#! usr/bin/python3

import argparse
import json
import os
import re
import subprocess
from sys import argv
import yaml
from typing import List, Optional, Union, Dict, Any
from pathlib import Path
from collections import namedtuple


Project = namedtuple('Project', ['name', 'path', 'libraries'])
Library = namedtuple('Library', ['name', 'path', 'project'])
Platform = namedtuple('Platform', ['name', 'target', 'model', 'project_name', 'tests', 'other_platforms'])
Target = namedtuple('Target', ['name', 'project_name'])
Asset = namedtuple('Asset', ['name', 'path', 'library'])
ExternalProject = namedtuple('ExternalProject', ['name', 'url', 'branch'])

class Stages:
    """Collection of CI/CD job stages"""
    register_projects = 'register-projects'
    generate_targets = 'generate-targets'
    trigger_targets = 'trigger-targets'
    trigger_platforms = 'trigger-platforms'
    generate_tests = 'generate-tests'
    trigger_tests = 'trigger-tests'
    build_primitives = 'build-primitives'
    build_hdl_workers = 'build-hdl-workers'
    install_platforms = 'install-platforms'
    build_rcc_workers = 'build-rcc-workers'
    build_assemblies = 'build-assemblies'
    build_tests = 'build-tests'
    build_applications = 'build-applications'
    run_tests = 'run-tests'
    run_applications = 'run-applications'
    deploy = 'deploy'
    child_stages = [generate_targets, trigger_targets, trigger_platforms, deploy, 
                    generate_tests, trigger_tests]
    target_stages = [build_primitives, build_hdl_workers]
    platform_stages = [install_platforms, build_rcc_workers, build_assemblies]
    test_stages = [build_tests, run_tests]
    app_stages = [build_applications, run_applications]
    generate_stages = [generate_targets, generate_tests]
    trigger_stages = [trigger_targets, trigger_platforms, trigger_tests]
    run_stages = [run_tests, run_applications]


class Job:
    """Representation of a CI/CD Job"""
    __slots__ = ('name', 'stage', 'image', 'script', 'before_script', 'needs', 'artifacts', 
                 'parallel', 'variables', 'services', 'when', 'retry', 'tags', 'after_script')

    def __init__(self, name: str, stage: str, image: str, script: List[str], 
                 before_script: List[str], after_script: List[str], 
                 needs: Optional[List[str]]=None, artifacts: Optional[List[dict]]=None, 
                 parallel: Optional[dict]=None, variables: Optional[dict]=None, 
                 services: Optional[Union[str, List[str]]]=None, when: Optional[str]=None, 
                 tags: Optional[List[str]]=None):
        self.name = name
        self.stage = stage
        self.image = image
        self.script = script
        self.retry = 2
        if before_script is not None:
            self.before_script = before_script
        if needs is not None:
            self.needs = needs
        if artifacts is not None:
            self.artifacts = artifacts
        if parallel is not None:
            self.parallel = parallel
        if variables is not None:
            self.variables = variables
        if services is not None:
            self.services = services
        if when is not None:
            self.when = when
        if tags is not None:
            self.tags = tags
        if after_script is not None:
            self.after_script = after_script

    def to_dict(self):
        """Convert a Job into a dictionary representation."""
        job_dict = {slot: getattr(self, slot) for slot in self.__slots__ if hasattr(self, slot)}
        return job_dict
    

class Bridge(Job):
    """Representation of a CI/CD Bridge Job"""
    __slots__ = ('name', 'stage', 'trigger', 'needs', 'parallel', 'when')

    def __init__(self, name:str, stage: str, trigger: dict, needs: Optional[List[str]]=None,
                 parallel: Optional[dict]=None, when: str=None):
        self.name = name
        self.stage = stage
        self.trigger = trigger
        if needs is not None:
            self.needs = needs
        if parallel is not None:
            self.parallel = parallel
        if when is not None:
            self.when = when 


class Pipeline:
    """Representation of a CI/CD Pipeline"""
    __slots__ = ('stages', 'jobs')
    
    def __init__(self, stages, jobs):
        self.stages = stages
        self.jobs = jobs

    def to_dict(self):
        """Convert a Pipeline into a dictionary representation."""
        pipeline_dict = {'stages': self.stages}
        for job in self.jobs:
            job_dict = job.to_dict()
            pipeline_dict[job_dict.pop('name')] = job_dict
        pipeline_dict['workflow'] = {'rules': [{'when': 'always'}]}
        return pipeline_dict

    def dump(self, dump_path: Path):
        """Dump a Pipeline to a yaml file.
        
        Args:
            dump_path: Path of yaml file to dump Pipeline to.
        """
        pipeline_dict = self.to_dict()
        yaml.Dumper.ignore_aliases = lambda *args : True
        with dump_path.open('w+') as yml:
            yaml.dump(pipeline_dict, yml, width=1000, default_flow_style=False)
        print(f'Dumped to: {dump_path}')


class JobBuilder:
    """Responsible for building CI/CD Jobs."""
    def __init__(self, artifact_dir_path: Path):
        self.artifacts_dir_path = artifact_dir_path

    def build(self, stage: str, image: str, target: Optional[Union[Target, Platform]]=None, 
              library: Path=None, assets: Optional[Union[Asset, List[Asset]]]=None, 
              external_project: Optional[ExternalProject]=None, 
              other_platform: Optional[Platform]=None) -> Job:
        """Build a Job.
        
        If assets arg is provided as a list, the built job will contain 
        a parallel matrix entry to run the jobs for each Asset. 
        Otherwise, if assets is a singular Asset, the job is built only 
        for the specified asset, and if no asset is specified, the job
        is built only for the specified Target/Platform. If library arg 
        is provided, the library will be used in a Job's name, to 
        determine the Job's needs, and to determine the Path containing 
        the assets (if provided).

        Args:
            stage: Stage of the Job.
            image: The docker image used to run the job within.
            target: The Target or Platform the Job is for.
            library: Optional. Library of Assets(s) the Job is for.
            assets: Optional. Asset or list of Assets to create a 
                parallel matrix for.
            external_project: Optional. ExternalProject the job is for.
        Returns:
            A Job based on the provided args.
        """
        name = self.build_name(stage, target, other_platform, library, assets, external_project)
        needs = self.build_needs(stage, target, library=library, assets=assets)
        when = self.build_when(stage)
        if stage in Stages.trigger_stages:
            trigger = self.build_trigger(stage, target)
            return Bridge(name, stage, trigger, needs=needs, when=when)
        before_script = self.build_before_script(stage)
        script = self.build_script(stage, target=target, asset=assets,
                                   external_project=external_project,
                                   other_platform=other_platform)
        after_script = self.build_after_script(stage)
        if isinstance(assets, list):
            artifacts = None
            parallel = self.build_parallel(assets)
        else:
            artifacts = self.build_artifacts(stage, asset=assets)
            parallel = None
        tags = self.build_tags(stage, target=target, other_platform=other_platform)
        variables = self.build_variables(stage, target=target, library=library)
        services = self.build_services(stage)
        return Job(name, stage, image, script, before_script, needs=needs, 
                   artifacts=artifacts, parallel=parallel, variables=variables,
                   services=services, when=when, tags=tags, after_script=after_script)

    def build_name(self, stage: str, *args):
        """Build the name of the Job.

        Name is created by concatenating the provided args, joined by a 
        '|'. The stage is required to avoid name collisions with jobs 
        from other stages.
        
        Args:
            stage: Stage of the Job.
            args: List of strings or elements with a 'name' attribute to
                  append to the name.
        Returns:
            A string based on the provided args.
        """
        name = stage
        for arg in args:
            if hasattr(arg, 'name'):
                name += f'|{arg.name}'
            elif isinstance(arg, str):
                name += f'|{arg}'
        return name
    
    def build_needs(self, stage: str, target: Optional[Union[Target, Platform]]=None,
                    library: Path=None, assets: Optional[Union[Asset, List[Asset]]]=None
                   ) -> Optional[List[str]]:
        """Builds the needs of the Job.
        
        Returns empty list if Job has no dependencies, meaning the job 
        can execute immediately. Return None if Job depends on all jobs 
        in previous stages to complete.

        Args:
            stage: Stage of the Job.
            target: Optional. The Target or Platform the Job is for.
            library: Optional. Library of Assets(s) the Job is for.
            assets: Optional. Asset or list of Assets to create a 
                parallel matrix for.
        Returns:
            None or a List of strings corresponding to the Job names of
            needed jobs.
        """
        needs = []
        if stage is Stages.build_primitives and library.project.name != 'ocpi.core':
            needs.append(self.build_name(Stages.build_primitives, target, 'ocpi.core.primitives'))
        elif stage is Stages.run_tests:
            needs.append(self.build_name(Stages.build_tests, target, library, assets))
        elif stage is Stages.trigger_platforms:
            if target.model == 'hdl':
                # Hdl platforms must wait for their target to finish
                needs.append(self.build_name(Stages.trigger_targets, target.target, library))
            else:
                # Rcc platforms can build as soon as yaml is generated
                needs.append(self.build_name(Stages.generate_targets))
        # elif stage is Stages.trigger_tests:
        #     needs.append(self.build_name(Stages.generate_tests))
        return needs if needs else None
    
    def build_before_script(self, stage) -> Optional[Union[List[str], str]]:
        """Builds the before_script of the Job.
        
        Returns a string representation of the before_script to
        execute in a Job.

        Args:
            stage: Stage of the Job.
        Returns:
            None, str, or a List of strings corresponding to the Job 
            names of needed jobs.
        """
        if stage in Stages.test_stages + Stages.app_stages + [Stages.generate_tests]:
            script = [
                'cd ${OLDPWD}',
                'source ./cdk/opencpi-setup.sh -r'
            ]
            if stage is Stages.run_tests:
                script.append(f'ocpiremote unload -i $CI_OCPI_DEVICE_IP -u $CI_OCPI_DEVICE_USER'
                               ' -p $CI_OCPI_DEVICE_PWD || true')
            return script
        if stage is Stages.deploy:
            return ('aws ecr get-login-password --region us-east-1'
                    ' | docker login --username AWS --password-stdin $CI_OCPI_CONTAINER_REGISTRY')
        return 'source ./cdk/opencpi-setup.sh -r'
    
    def build_script(self, stage: str, target: Optional[Union[Target, Platform]]=None,
                     asset: Optional[Asset]=None, external_project: Optional[ExternalProject]=None,
                     other_platform: Optional[Platform]=None) -> Union[str, List[str]]:
        """Build the script of the Job.
        
        Args:
            stage: Stage of the Job.
            target: Optional. The Target or Platform the Job is for.
            asset: Optional. Asset to create script for.
            external_project: Optional. ExternalProject the job is for.
            other_platform: Associated platform for ocpiremote cmds.
        Returns:
            A string or List of strings for the Job to execute.
        """
        if stage is Stages.install_platforms:
            script = []
            if target.name.lower().startswith('xilinx'):
            # Clone repos necessary to install Xilinx platforms
                script += [
                    'mkdir ~/git && export OCPI_XILINX_GIT_REPOSITORY=~/git && cd ~/git',
                    'git clone https://github.com/Xilinx/linux-xlnx.git',
                    'git clone https://github.com/Xilinx/u-boot-xlnx.git',
                    'cd $CI_PROJECT_DIR'
                ]
            script.append(f'ocpiadmin install platform {target.name} --minimal --artifacts-only')
        elif stage is Stages.build_primitives:
            script = [
                'echo "building ${DIR}"',
                f'ocpidev build -d "${{DIR}}" --hdl-target {target.name}'
            ]
        elif stage in Stages.target_stages:
            script = [
                'echo "building ${DIR}/${ASSET}"',
                f'ocpidev build -d "${{DIR}}/${{ASSET}}" --hdl-target {target.name} --artifacts-only'
            ]
        elif stage in Stages.platform_stages:
            script = [
                'echo "building ${DIR}/${ASSET}"',
                f'ocpidev build -d "${{DIR}}/${{ASSET}}" --{target.model}-platform {target.name} --artifacts-only'
            ]
        elif stage in Stages.generate_stages:
            script = 'python3 .gitlab-ci/scripts/generate_pipeline.py'
            if stage is Stages.generate_targets:
                script += ' targets'
            else:
                script += ' tests'
        elif stage in Stages.run_tests:
            script = [f'cp -Tr {self.artifacts_dir_path.joinpath(asset.name)} {asset.path}']
            run_cmd = f'ocpidev run -d "{asset.path}" --only-platform {target.name} --nothing-error'
            if not target.name.endswith('sim'):
                load_cmd = (f'ocpiremote load --{target.model}-platform={target.name}'
                            f' --{other_platform.model}-platform={other_platform.name}'
                            ' -i $CI_OCPI_DEVICE_IP -r 1000 -u $CI_OCPI_DEVICE_USER'
                            ' -p $CI_OCPI_DEVICE_PWD')
                start_cmd = f'ocpiremote start -i $CI_OCPI_DEVICE_IP -u $CI_OCPI_DEVICE_USER -p $CI_OCPI_DEVICE_PWD -b'
                script += [load_cmd, start_cmd]
            script.append(run_cmd)
        elif stage is Stages.build_tests:
            script = [
                f'ocpidev build -d "{asset.path}" --{target.model}-platform {target.name} --artifacts-only',
                f'cp -Tr {asset.path} {self.artifacts_dir_path.joinpath(asset.name)}'
            ]
        elif stage is Stages.register_projects:
            script = []
            if external_project.name.startswith('ocpi.osp'):
                project_path = Path(os.getenv('CI_PROJECT_DIR', '${CI_PROJECT_DIR}'),
                                    'projects',
                                    'osps',
                                    external_project.name).resolve()
            else:
                project_path = Path(os.getenv('CI_PROJECT_DIR', '${CI_PROJECT_DIR}'),
                                    'projects',
                                    external_project.name).resolve()
            script.append(f'git clone {external_project.url} -b {external_project.branch}'
                          f' "{project_path}"')
            script.append(f'ocpidev register project -d "{project_path}"')
            if external_project.name.startswith('ocpi.comp'):
                script.append(f'ocpidev build project -d "{project_path}"')
        elif stage is Stages.deploy:
            from_tag = os.getenv('CI_OCPI_IMAGE_TAG', '${CI_OCPI_IMAGE_TAG}')
            deploy_tag = os.getenv('CI_OCPI_ROOT_PIPELINE_ID', '${CI_OCPI_ROOT_PIPELINE_ID}')
            host = os.getenv('CI_OCPI_HOST', '${CI_OCPI_HOST}')
            deploy_image = f'${{CI_OCPI_CONTAINER_REGISTRY}}/{host}:{deploy_tag}'
            from_image = f'${{CI_OCPI_CONTAINER_REGISTRY}}/{host}.packages'
            script = [
                'docker build . -f .gitlab-ci/dockerfiles/deploy.dockerfile'
                    f' -t "{deploy_image}"'
                    f' --build-arg IMAGE="{from_image}"'
                    f' --build-arg TAG="{from_tag}"',
                f'docker push "{deploy_image}"'
            ]
        else:
            script = ''
        return script
    
    def build_after_script(self, stage: str):
        if stage is Stages.run_tests:
            return ([
                'cd ${OLDPWD}',
                'source ./cdk/opencpi-setup.sh -r',
                f'ocpiremote unload -i $CI_OCPI_DEVICE_IP -u $CI_OCPI_DEVICE_USER'
                    ' -p $CI_OCPI_DEVICE_PWD'
            ])
        return None
    
    def build_artifacts(self, stage: str, asset: Asset) -> Optional[Dict[str, str]]:
        """Build the artifacts of the Job.

        Args:
            stage: Stage of the Job.
            asset: Optional. Asset to create artifact for.
        Returns:
            None or a dictionary of strings representing file paths for 
            artifacts.
        """
        if stage in Stages.generate_stages:
            artifacts = {'paths': [str(self.artifacts_dir_path)]}
        elif stage is Stages.build_tests:
            artifacts = {'paths': [str(self.artifacts_dir_path.joinpath(asset.name))]}
        else:
            artifacts = None
        return artifacts
    
    def build_trigger(self, stage: str, target: Union[Target, Platform]) -> Dict[str, Any]:
        """Builds a child pipeline trigger for a Job.
        
        Args:
            stage: The stage of the Job to build a trigger for.
            target: The target of the Job to build a trigger for.
        Returns:
            A dictionary representation of a trigger.
        """
        if stage in Stages.trigger_stages:
            if stage is Stages.trigger_platforms:
                name = f'platform-{target.name}'
                job = Stages.generate_targets
            elif stage is Stages.trigger_targets:
                name = f'target-{target.name}'
                job = Stages.generate_targets
            else:
                name = f'test-{target.name}'
                job = Stages.generate_tests
            artifact = self.artifacts_dir_path.joinpath(name).with_suffix('.yml')
            # include must be relative to the project dir
            artifact = artifact.relative_to(os.environ['CI_PROJECT_DIR'])
            trigger = {
                'strategy': 'depend',
                'include': [{
                    'artifact': str(artifact), 
                    'job': job
                }],
                'forward': {
                    'yaml_variables': True,
                    'pipeline_variables': True
                }
            }
        else:
            trigger = None
        return trigger

    def build_parallel(self, assets: List[Asset]) -> Dict[str, List[Dict[str, str]]]:
        """Build a parallel matrix for a Job.
        
        Runs the same job for each asset as a parallel matrix job.

        Args:
            assets: The assets to create the parallel matrix job for.
        Returns:
            A dictionary representing the parallel matrix.
        """
        matrix= [{'ASSET': [str(asset.path.name) for asset in assets]}]
        return {'matrix': matrix}
    
    def build_variables(self, stage, target: Union[Target, Platform]=None, library: Library=None
                        ) -> Dict[str, str]:
        """Builds variables for a Job.

        Args:
            stage: The stage of the Job.
            target: Optional. The target of the Job to create variables
                for.
            library: Optional. The library of the Job to create
                variables for.
        Returns:
            A dictionary of variables for the Job.
        """
        variables = {}
        if library is not None:
            variables["DIR"] = str(library.path)
        if stage is Stages.deploy:
            variables['DOCKER_HOST'] = 'tcp://docker:2376'
            variables['DOCKER_TLS_CERTDIR'] = '/certs'
            variables['DOCKER_TLS_VERIFY'] = 1
            variables['DOCKER_CERT_PATH'] = "/certs/client"
        if stage is Stages.run_tests and not target.name.endswith('sim'):
            variables['OCPI_SERVER_ADDRESSES'] = '$CI_OCPI_DEVICE_IP:1000'
        if not variables:
            return None
        return variables
    
    def build_services(self, stage) -> List[str]:
        """Build services for the Job.
        
        Args:
            stage: The stage of the Job to build services for.
        Returns:
            A list of strings representing services.
        """
        if stage is Stages.deploy:
            return ['docker:24.0.5-dind']
        return None
    
    def build_when(self, stage) -> Optional[str]:
        """Build the when for the Job to determine when a Job runs.
        
        Args:
            stage: The stage of the Job to build when for.
        Returns:
            None or a string that dictates when a Job can run.
        """
        if stage in [Stages.deploy, Stages.generate_tests] + Stages.trigger_stages:
            return 'always'
        return None
    
    def build_tags(self, stage: str, target: Optional[Union[Target, Platform]]=None, other_platform: Optional[Platform]=None) -> List[str]:
        """Build the tags for the Job.
        
        Dictates what runner(s) are allowed to run the job.
        
        Args:
            stage: The stage of the Job to build when for.
            target: The target or platform to build the tags for.
        Returns:
            A list of strings representing tags.
        """
        tags = ['opencpi']
        if stage in Stages.run_stages and not target.name.endswith('sim'):
        # Local HWIL jobs
            tags.append('docker')
            if target.model == 'hdl':
                tags.append(target.name)
            else:
                tags.append(other_platform.name)
        else:
            tags += ['aws', 'eks']
        return tags


class PipelineBuilder:
    """Responsible for building CI/CD Pipelines."""
    def __init__(self, job_builder: JobBuilder, **kwargs):
           self.job_builder = job_builder
           self.base_image: str = kwargs.get('base_image', '')
           self.deploy_image: str = kwargs.get('deploy_image', '')
           self.deployer_image: str = kwargs.get('deployer_image', '')
           self.platforms: List[Platform] = kwargs.get('platforms', [])
           self.targets: List[Target] = kwargs.get('targets', [])
           self.projects: List[Project] = kwargs.get('projects', [])
           self.rcc_workers: List[Asset] = kwargs.get('rcc_workers', [])
           self.hdl_workers: List[Asset] = kwargs.get('hdl_workers', [])
           self.primitives: List[Library] = kwargs.get('primitives', [])
           self.tests: List[Asset] = kwargs.get('tests', [])
           self.assemblies: List[Asset] = kwargs.get('assemblies', [])
           self.applications: List[Asset] = kwargs.get('applications', [])
           self.external_projects: List[Project] = kwargs.get('external_projects', [])
           self.do_hwil: bool = kwargs.get('do_hwil', False)
           self.hwil_whitelist: dict = kwargs.get('hwil_whitelist', {})

    def build(self, stages: List[str], target: Target=None) -> Pipeline:
        """Builds a Pipeline.
        
        Args:
            stages: List of stages for the Pipeline.
            target: Optional. The target the pipeline is for.
        Returns:
            A Pipeline.
        """
        jobs = []
        for stage in stages:
            # Determine image to run job in
            if stage in Stages.test_stages + [Stages.generate_tests, Stages.run_applications]:
                image = self.deploy_image
            elif stage is Stages.deploy:
                image = self.deployer_image
            else:
                image = self.base_image
            # Get jobs
            if stage in [Stages.trigger_platforms, Stages.trigger_tests]:
                for platform in self.platforms:
                    jobs.append(self.job_builder.build(stage, image, target=platform))
            elif stage is Stages.trigger_targets:
                for target in self.targets:
                    jobs.append(self.job_builder.build(stage, image, target=target))
            elif stage in Stages.generate_stages:
                jobs.append(self.job_builder.build(stage, image))
            elif stage is Stages.install_platforms:
                jobs.append(self.job_builder.build(stage, image, target=target))
            elif stage is Stages.build_primitives:
                for primitives in self.primitives:
                    jobs.append(self.job_builder.build(stage, image, target=target, 
                                                       library=primitives))
            elif stage is Stages.register_projects:
                for project in self.external_projects:
                    jobs.append(self.job_builder.build(stage, image, external_project=project))
            elif stage is Stages.deploy:
                jobs.append(self.job_builder.build(stage, image))
            elif stage is Stages.run_tests and not target.name.endswith('sim') and not target.other_platforms:
                continue
            else:
                for project in self.projects:
                    for library in project.libraries:
                        assets = self.assets_by_stage(stage, target=target, library=library)
                        if not assets:
                            continue
                        if stage is Stages.run_tests:
                            if target.name.endswith('sim'):
                                for asset in assets:
                                    jobs.append(self.job_builder.build(stage, image, target=target, 
                                        assets=asset, library=library))
                            else:
                                for other_platform in target.other_platforms:
                                    for asset in assets:
                                        jobs.append(self.job_builder.build(
                                            stage, image, target=target, assets=asset, 
                                            library=library, other_platform=other_platform))
                        elif stage in Stages.test_stages:
                            for asset in assets:
                                jobs.append(self.job_builder.build(
                                    stage, image, target=target, assets=asset, library=library))
                        else:
                            jobs.append(self.job_builder.build(
                                stage, image, target=target, assets=assets, library=library))
        return Pipeline(stages, jobs)
    
    def assets_by_stage(self, stage, target: Union[Target, Platform], library: Library=None
                        ) -> List[str]:
        """"Returns a list of OpenCPI assets based on stage and target.
        
        Args:
            stage: The stage that determines the assets to return.
            target: The target that determines the assets to return.
            library: Optional. The library to filter assets by.
        Returns:
            A list of OpenCPI assets.
        """
        if stage is Stages.build_primitives:
            assets = self.primitives
        elif stage is Stages.build_hdl_workers:
            assets = self.hdl_workers
        elif stage is Stages.build_rcc_workers:
            if target.model != 'rcc':
                assets = []
            else:
                assets = self.rcc_workers
        elif stage in [Stages.build_tests, Stages.run_tests]:
            if stage is Stages.run_tests and not (target.name.endswith('sim') or self.do_hwil):
            # Only run tests if simulator or do_hwil is set true
                assets = []
            else:
                assets = target.tests
        elif stage is Stages.build_assemblies:
            if target.model != 'hdl':
                assets = []
            else:
                assets = self.assemblies
        elif stage in [Stages.build_applications, Stages.run_applications]:
            assets = self.applications
        else:
            assets = []
        if library is not None:
            if library.project.name.startswith('ocpi.osp'):
                if library.project.name != target.project_name:
                # Only build osp project assets for the osp platform
                    assets = []
            assets = [asset for asset in assets if asset.library is library]
        return assets


def get_args(pipeline_type) -> Dict[str, str]:
    """Gets arguments to pass to the PipelineBuilder.

    Arguments may include necessary environment variables, OpenCPI assets
    to include in the Pipeline, container images to use and/or create.
    
    Args:
        pipeline_type: The type of pipeline to be built.
    Returns:
        Dictionary of arguments.
    """
    container_registry = '${CI_OCPI_CONTAINER_REGISTRY}'
    host = os.getenv('CI_OCPI_HOST', '${CI_OCPI_HOST}')
    image_tag = os.getenv('CI_OCPI_IMAGE_TAG', '${CI_OCPI_IMAGE_TAG}')
    args = {}
    args['base_image'] = f'{container_registry}/{host}.packages:{image_tag}'
    args['deployer_image'] = os.getenv(
        'CI_OCPI_DEPLOYER_IMAGE',
        'registry.gitlab.com/gitlab-org/cloud-deploy/aws-base:latest'
    )
    image_tag = os.getenv('CI_OCPI_ROOT_PIPELINE_ID', '${CI_OCPI_ROOT_PIPELINE_ID}')
    args['deploy_image'] = f'{container_registry}/{host}:{image_tag}'
    args['do_hwil'] = os.getenv('CI_OCPI_HWIL', False)
    if args['do_hwil']:
        with open(".gitlab-ci/yaml/hwil-whitelist.yml", "r") as yml:
            args['hwil_whitelist'] = yaml.safe_load(yml)
    else:
        args['hwil_whitelist'] = {}
    if pipeline_type == 'projects':
        args['external_projects'] = get_external_projects()
        return args
    platforms = get_platforms(args['hwil_whitelist'])
    projects = get_projects()
    args['platforms'] = platforms
    args['projects'] = projects
    args['targets'] = get_targets(platforms)
    if pipeline_type == 'targets':
        args['rcc_workers'], args['hdl_workers'] = get_workers(projects)
        args['primitives'] = get_primitives(projects)
        args['assemblies'] = get_assemblies(projects)
    if pipeline_type == 'tests':
        for platform in platforms:
            tests = platform.tests
            tests += get_tests(projects, platform)
    return args


def get_platforms(hwil_whitelist: dict={}) -> List[Platform]:
    """Gets the OpenCPI Platforms to run the Pipeline for.
    
    Uses ocpidev to find available platforms. Filters platforms based on
    those defined in CI_OCPI_PLATFORMS environment variable directive.

    Returns:
        List of Platforms.
    """
    platforms = json.loads(subprocess.run(['ocpidev', 'show', 'platforms', '--json'], 
                                          stdout=subprocess.PIPE).stdout)
    platforms_dict = {**platforms['rcc'], **platforms['hdl']}
    platforms_directive = re.split(r'\s', os.environ['CI_OCPI_PLATFORMS'])
    platforms_directive_dict = {}
    for platform in platforms_directive:
    # Parse platforms directive
        if ':' in platform:
            platform_name, other_platforms = platform.split(':')
        else:
            platform_name = platform
            other_platforms = ''
        platform_name = platform_name.strip(',')
        if platform_name not in platforms_directive_dict:
        # Initialize platform in directive dict
            platforms_directive_dict[platform_name] = set()
        for other_platform_name in other_platforms.split(','):
        # Associate platforms in directive dict
            if other_platform_name not in platforms_directive_dict:
                platforms_directive_dict[other_platform_name] = set()
            if (platform_name not in hwil_whitelist 
                or other_platform_name not in hwil_whitelist[platform_name]):
            # Do not associate platforms not in whitelist
                continue
            platforms_directive_dict[platform_name].add(other_platform_name)
            platforms_directive_dict[other_platform_name].add(platform_name)
    platforms = []
    for name, platform in platforms_dict.items():
    # Initialize platform named_tuples
        if name not in platforms_directive_dict:
        # Ignore platforms not specified in platforms directive
            continue
        project_name = '.'.join(platform['package_id'].split('.')[:-1])
        target = Target(platform['target'], project_name)
        platform = Platform(name, target, platform['model'], project_name, [], [])
        platforms.append(platform)
    for platform in platforms:
    # Associate platform named_tuples
        platform.other_platforms.extend(
            [other_platform for other_platform in platforms 
             if other_platform.name in platforms_directive_dict[platform.name]]
        )
    print('Platform Directive:')
    for platform in platforms:
        print(f'{platform.name}:')
        for other_platform in platform.other_platforms:
            print(f'\t{other_platform.name}')
    return platforms


def get_targets(platforms: List[Platform]) -> List[Target]:
    """Gets the OpenCPI Targets to run the Pipeline for.
    
    Args:
        platforms: List of Platforms to include the targets of.
    Returns:
        List of Targets.
    """
    targets = set()
    for platform in platforms:
        if platform.model == 'hdl':
            targets.add(platform.target)
    return targets


def get_projects() -> List[Project]:
    """Gets the OpenCPI Projects to run the Pipeline for.
    
    Uses ocpidev to find available projects.

    Returns:
        List of Projects.
    """
    projects = []
    projects_dict = json.loads(subprocess.run(['ocpidev', 'show', 'projects', '--json'],
                                               stdout=subprocess.PIPE).stdout)['projects']
    for project_name, project_dict in projects_dict.items():
        try:
        # ocpidev beautifully errors when a project doesn't contain any
        # component libraries instead of returning an empty dict.
            libraries_dict = json.loads(subprocess.run([
                'ocpidev', 'show', 'libraries', '--json', '-d', project_dict['real_path']],
                stdout=subprocess.PIPE).stdout)
        except:
            libraries_dict = {}
        project_path = Path(project_dict['real_path'].strip())
        libraries = []
        project = Project(project_name, project_path, libraries)
        libraries += [Library(name, Path(library['directory'].strip()), project) 
                      for name, library in libraries_dict.items()]
        assemblies_path = project.path.joinpath('hdl', 'assemblies')
        if assemblies_path.exists():
            name = f'{project.name}.assemblies'
            libraries.append(Library(name, assemblies_path, project))
        projects.append(project)
    return projects


def get_external_projects() -> List[ExternalProject]:
    """Gets a list of ExternalProjects to include in the Pipeline.
    
    ExternalProjects typically include the gitlab.io project, COMP
    projects, and/or OSP projects.

    Returns:
        List of ExternalProjects.
    """
    group = 'opencpi'
    url = f'"https://gitlab.com/{group}/{{}}/{{}}.git"'
    projects = []
    projects_directive = os.getenv('CI_OCPI_PROJECTS', '')
    print(f'External Project Directive: {projects_directive}')
    osp_directive = re.findall(r'ocpi\.osp\.[^\s,]+', projects_directive)
    source_project = os.getenv('CI_OCPI_SOURCE_PROJECT_NAME', '')
    source_ref = os.getenv('CI_OCPI_SOURCE_REF_NAME')
    for osp in osp_directive:
        branch = source_ref if osp == source_project else 'develop'
        projects += [ExternalProject(osp, url.format('osp', osp), branch)]
    comp_directive = re.findall(r'ocpi\.comp\.[^\s,]+', projects_directive)
    for comp in comp_directive:
        branch = source_ref if comp == source_project else 'develop'
        projects += [ExternalProject(comp, url.format('comp', comp), branch)]
    print(f'External Projects:')
    for project in projects:
        print(f'\t{project.name}\t{project.url}\t{project.branch}')
    return projects


def get_tests(projects: List[Project], platform: Platform) -> List[Asset]:
    """Gets a list of test Assets to include in the Pipeline.
    
    Uses ocpidev to find available Tests. Filters Tests by Platform.

    Args:
        platform: The Platform to find Tests for.
    Returns:
        List of test Assets.
    """
    tests = []
    for project in projects:
        for library in project.libraries:
            if library.name.split('.')[-1] == 'assemblies':
                continue
            cmd = ['ocpidev', 'show', 'tests', '--json', '-v', '-d', library.path,
                   f'--{platform.model}-platform', platform.name]
            tests_dict = json.loads(subprocess.run(cmd, stdout=subprocess.PIPE).stdout)
            for test in tests_dict.values():
                test_path = Path(test['path'])
                tests.append(Asset(test_path.name, test_path, library))
    return tests


def get_workers(projects: List[Project]) -> List[Asset]:
    """Gets a list of worker Assets to include in the Pipeline.

    Does not use ocpidev.

    Args:
        projects: Projects to find workers inside of.
    Returns:
        List of worker Assets.
    """
    rcc_workers = []
    hdl_workers = []
    for project in projects:
        for library in project.libraries:
            if library.name.split('.')[-1] == 'assemblies':
                continue
            for hdl_path in library.path.glob('*.hdl'):
                hdl_workers.append(Asset(hdl_path.name, hdl_path, library))
            for rcc_path in library.path.glob('*.rcc'):
                rcc_workers.append(Asset(hdl_path.name, rcc_path, library))
    return rcc_workers, hdl_workers


def get_primitives(projects: List[Project]) -> List[Asset]:
    """Gets a list of primitive Assets to include in the Pipeline.

    Does not use ocpidev.

    Args:
        projects: Projects to find primitives inside of.
    Returns:
        List of primitive Assets.
    """
    primitives = []
    for project in projects:
        path = project.path.joinpath('hdl', 'primitives')
        if path.exists():
            primitives.append(Library(f'{project.name}.primitives', path, project))
    return primitives


def get_assemblies(projects: List[Project]) -> List[Asset]:
    """Gets a list of assembly Assets to include in the Pipeline.

    Does not use ocpidev.

    Args:
        projects: Projects to find assemblies inside of.
    Returns:
        List of primitive Assets.
    """
    assemblies = []
    for project in projects:
        for library in project.libraries:
            if library.name.split('.')[-1] != 'assemblies':
                continue
            for assembly_path in library.path.glob('*'):
                if assembly_path.joinpath(assembly_path.name).with_suffix('.xml').exists():
                    assemblies.append(Asset(assembly_path.name, assembly_path, library))
    return assemblies


def main(pipeline_type, **kwargs):
    """Main function.
    
    Instantiates JobBuilder and PipelineBuilder with passed in kwargs,
    calls the PipelineBuilder's build() method to build a Pipeline,
    and calls the Pipeline's dump() method to dump the Pipeline to a
    yaml file.

    Args:
        pipeline_type: The type of Pipeline to build.
        kwargs: Args to pass into the instantiation of the
            PipelineBuilder.
    """
    ci_project_dir = os.environ.get('CI_PROJECT_DIR', '$CI_PROJECT_DIR')
    artifact_dir_path = Path(ci_project_dir).joinpath('.gitlab-ci', 'artifacts').resolve()
    job_builder = JobBuilder(artifact_dir_path=artifact_dir_path)
    pipeline_builder = PipelineBuilder(job_builder, **kwargs)
    artifact_dir_path.mkdir(exist_ok=True)
    if pipeline_type == 'projects':
    # Generate yaml to pull and register external projects
        pipeline = pipeline_builder.build([Stages.register_projects])
        dump_path = artifact_dir_path.joinpath('projects.yml')
        pipeline.dump(dump_path=dump_path)
    elif pipeline_type == 'children':
    # Generate child pipeline yaml to generate and trigger grandchild 
    # pipelines for building and testing all targets/platforms
        pipeline = pipeline_builder.build(Stages.child_stages)
        dump_path = artifact_dir_path.joinpath('children.yml')
        pipeline.dump(dump_path=dump_path)
    elif pipeline_type == 'targets':
    # Generate yaml for building assets for individual targets/platforms
        for target in kwargs.get('targets', []):
            pipeline = pipeline_builder.build(Stages.target_stages, target=target)
            dump_path = artifact_dir_path.joinpath(f'target-{target.name}.yml')
            pipeline.dump(dump_path=dump_path)
        for platform in kwargs.get('platforms', []):
            pipeline = pipeline_builder.build(Stages.platform_stages, target=platform)
            dump_path = artifact_dir_path.joinpath(f'platform-{platform.name}.yml')
            pipeline.dump(dump_path=dump_path)
    elif pipeline_type == 'tests':
    # Generate yaml for building and running tests for individual 
    # platforms
        for platform in kwargs.get('platforms', []):
            pipeline = pipeline_builder.build(Stages.test_stages, target=platform)
            dump_path = artifact_dir_path.joinpath(f'test-{platform.name}.yml')
            pipeline.dump(dump_path=dump_path)


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('type', choices=['children', 'targets', 'projects', 'tests'])
    pipeline_type = parser.parse_args(argv[1:]).type
    import time
    start = time.time()
    args = get_args(pipeline_type=pipeline_type)
    main(pipeline_type, **args)
    end = time.time()
    print(end - start)
