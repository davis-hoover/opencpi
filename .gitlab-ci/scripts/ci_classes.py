#!/usr/bin/env python3

from abc import ABC, abstractmethod
from typing import List
from pathlib import Path
import re
import yaml


class Job():
    """Models a pipeline job"""
    def __init__(self, name: str, stage: str, **kwargs):
        """Initialized the Job object"""
        self.name = name
        self.stage = stage
        for key,val in kwargs.items():
            if val:
                setattr(self, key, val)

    def to_dict(self):
        """Converts and returns Job to a dictionary"""
        job_dict = {}
        for key,value in self.__dict__.items():
            if key != 'name' and value is not None:
                job_dict[key] = value

        return job_dict

    def __str__(self) -> str:
        """String representation of a Job"""
        string = '{}:'.format(self.name)
        for key,val in self.__dict__.items():
            if key != 'name':
                string += '\n\t\t{}: {}'.format(key, val)

        return string


class ScriptJob(Job):
    """Models a pipeline job that requires a script"""
    def __init__(self, name: str, stage: str, script: List[str], **kwargs):
        """Initalizes a ScriptJob"""
        self.script = script
        super().__init__(name, stage, **kwargs)


class BridgeJob(Job):
    """Models a pipeline job that requires a trigger"""
    def __init__(self, name: str, stage: str, trigger: dict, **kwargs):
        """Initializes a BridgeJob"""
        self.trigger = trigger
        super().__init__(name, stage, **kwargs)


class Pipeline():
    """Models a pipeline"""
    def __init__(self, workflow: dict, stages: List[str], jobs: List[Job]):
        """Initializes a Pipeline object"""
        self.workflow = workflow
        self.stages = stages
        self.jobs = jobs

    def to_dict(self):
        """Converts and returns Pipeline to a dictionary"""
        pipeline_dict = {
            'stages': self.stages,
            'workflow': self.workflow,
        }
        for job in self.jobs:
            pipeline_dict[job.name] = job.to_dict()

        return pipeline_dict

    def dump(self, mode: str='w+'):
        """Write Pipeline to a yaml file"""
        pipeline_dict = self.to_dict()
        path = Path('.gitlab-ci.yml')

        parents = [parent for parent in path.parents]
        for parent in parents[::-1]:
            parent.mkdir(exist_ok=True)

        yaml.SafeDumper.ignore_aliases = lambda *args : True
        with open(path, mode) as yml:
            yaml.safe_dump(
                pipeline_dict, yml, width=1000, default_flow_style=False)

    def __str__(self):
        """String representation of a Pipeline"""
        if self.workflow is not None:
            string = 'workflow:'
            for key,val in self.workflow.items():
                string += '\n\t{}: {}'.format(key, val)
        if self.stages is not None:
            string += '\nstages:'
            for stage in self.stages:
                string += '\n\t{}'.format(stage)
        if self.jobs is not None:
            string += '\njobs:'
            for job in self.jobs:
                string += '\n\t{}'.format(job)

        return string


class PipelineBuilder(ABC):
    """Abstract class for building a pipeline
    
    Sublcasses must implement the following methods:
        _build_jobs()
    """
    def __init__(self, pipeline_id, container_registry, config):
        """Initializes a Pipelinebuilder"""
        self.pipeline_id = pipeline_id
        self.config = config
        self.container_registry = container_registry

    @abstractmethod
    def _build_jobs(self) -> List[Job]:
        """Abstract method to be implemented by subclasses

        Handles logic for constructing and returning jobs
        """
        pass
    
    def build(self) -> List[Job]:
        """Construct and returns a Pipeline"""
        jobs = self._build_jobs()
        workflow = {'rules': [{'when': 'always'}]}
        pipeline = Pipeline(workflow, self.stages, jobs)

        return pipeline

    def _build_name(self, *args) -> str:
        """Constructs and returns a job's name as a string
        
        Anything provided as *args will be appended to the name in order 
        in which they are provided
        """
        name = '/'.join([arg for arg in args if arg])

        return name

    def _build_tags(self, *args) -> List[str]:
        """Constructs and returns a job's tags as a list of strings
        
        Anything provided as *args will be appended to the list of tags
        """
        tags = ['opencpi', 'shell']
        for arg in args:
            if arg:
                tags.append(arg)

        return tags

    def _build_variables(self, **kwargs) -> dict:
        """Constructs and returns a job's variables as a dictionary
        
        Any key/value pair provided as **kwargs will be added to the
        dictionary
        """
        variables = {}
        for key,val in kwargs.items():
            if val:
                variables[key] = val

        return variables

    def _build_trigger(self, project: str=None, host: str=None, 
        platform: str=None) -> dict:
        """Constructs and returns a job's trigger as a dictionary"""
        trigger = {}
        if project:
        # Trigger is for an external project
            if '/' not in project:
            # If the project does not contain a group, try to get group
            # from middle of project name. Ex: ocpi.comp.sdr group == comp,
            # so full project == comp/ocpi.comp.sdr
                try:
                    group = re.search(r'.*\.(.*)\..*', project).group(1)
                    project = '{}/{}'.format(group, project)
                except AttributeError:
                    pass
            trigger['project'] = project
        else:
        # Trigger is for a child pipeline
            job = '/'.join(['generate', host, platform])
            trigger['include'] = [{
                'artifact': '.gitlab-ci.yml',
                'job': job
            }]
            trigger['strategy'] = 'depend'

        return trigger

    def _build_needs(self, stage: str, name: str) -> List[str]:
        """Constructs and returns a job's needs as a list of strings

        Replaces the occurence of the job's stage in the job's name with
        the stage of the job it needs
        """
        needs = []
        if stage in ['packages']:
            return needs
        need_stage = self.stages[self.stages.index(stage) - 1]
        need = name.replace(stage, need_stage)
        needs.append(need)

        return needs

    def _build_retry(self) -> dict:
        """
        Constructs and returns a dictionary for a job's retry setting
        """
        retry = {'max': 1}

        return retry

    def _build_artifacts(self, stage: str) -> str:
        if stage == 'generate':
            artifacts = {
                'paths': [
                    '.gitlab-ci.yml'
                ]
            }
        else:
            return None

        return artifacts

    def _build_image_name(self, host: str, tag: str, *args) -> str:
        """
        Constructs a name for a docker image

        Anything in "args" gets appended to the name before the tag
        """
        repo_name = self._build_repo_name(host, *args)
        image_name = '{}/{}:{}'.format(self.container_registry, repo_name, tag)

        return image_name

    def _build_repo_name(self, host: str, *args) -> str:
        """
        Constructs a name for a docker image

        Anything in "args" gets appended to the name
        """
        repo_name = '/'.join([host, *args])

        return repo_name


class HostPipelineBuilder(PipelineBuilder):
    def __init__(self, pipeline_id: str, container_registry: str, 
            hosts: List[str], platforms: List[str], projects: List[str], 
            config: dict):
        """Initializes a HostPipelineBuilder"""
        super().__init__(pipeline_id, container_registry, config)
        self.stages = ['packages', 'prereqs', 'build', 'test', 'generate', 
                       'trigger']
        self.hosts = hosts
        self.platforms = platforms
        self.projects = projects

    def _build_jobs(self) -> List[Job]:
        """Create jobs for host platforms"""
        jobs = []
        for host in self.hosts:
        # Build job for each host
            for stage in self.stages:
                if stage in ['trigger', 'generate']:
                    for platform in self.platforms:
                    # Build trigger job for each platform
                        if not platform:
                            continue
                        job = self._build_job(stage, host, platform=platform)
                        jobs.append(job)
                    if stage == 'trigger':
                        for project in self.projects:
                        # Build trigger job for each project
                            if not project:
                                continue
                            job = self._build_job(stage, host, project=project)
                            jobs.append(job)
                else:
                # Build non-trigger job
                    job = self._build_job(stage, host)
                    jobs.append(job)

        return jobs

    def _build_job(self, stage: str, host: str, platform: str=None, 
            project: str=None) -> Job:
        """Build a bridge or script job"""
        name = self._build_name(host, platform, project, stage)
        if stage == 'trigger':
        # Build bridge job
            variables = self._build_variables(stage, host, platform)
            trigger = self._build_trigger(project=project, host=host, 
                platform=platform)
            job = BridgeJob(name, stage, trigger, variables=variables)
        else:
        # Build script job
            variables = self._build_variables(stage, host, platform)
            tags = self._build_tags('aws')
            script = self._build_script(stage, host)
            after_script = self._build_after_script(stage, host)
            before_script = self._build_before_script(stage, host)
            retry = self._build_retry()
            artifacts = self._build_artifacts(stage)
            needs = self._build_needs(stage, name)
            job = ScriptJob(name, stage, script, tags=tags, retry=retry,
                            variables=variables, before_script=before_script,
                            after_script=after_script, artifacts=artifacts,
                            needs=needs)

        return job

    def _build_script(self, stage: str, host: str) -> str:
        """Build's a job's script"""
        if stage == 'test':
        # Make a "docker run" command and return script
            image_stage = self.stages[self.stages.index(stage) - 1]
            image = self._build_image_name(host, self.pipeline_id, image_stage)
            docker_cmd = 'docker run {} "{}"'.format(
                image, './scripts/test-opencpi.sh')
            script = [docker_cmd]

            return script

        # Make cmd to create repo and put lifecycle policy if necessary
        repo = self._build_repo_name(host, stage)
        with open('.gitlab-ci/scripts/policy.json') as f:
            lifecycle_policy = f.read().replace('\n','').replace('  ', '')
            lifecycle_policy = lifecycle_policy.replace('"', '\\"')
        create_repo_cmd = ' '.join([
            'aws ecr create-repository', 
            '--repository-name {}'.format(repo),
            '--image-scanning-configuration scanOnPush=true',
            '--region us-east-2', 
            '&& aws ecr put-lifecycle-policy', 
            '--repository-name {}'.format(repo), 
            '--lifecycle-policy-text="{}"'.format(lifecycle_policy),
            '|| true'
        ])
        image = self._build_image_name(host, self.pipeline_id, stage)
        docker_push_cmd = 'docker push {}'.format(image)

        if stage == 'packages':
        # Use existing dockerfile and return script
            dockerfile = str(Path('.gitlab-ci', 'dockerfiles', 
                '{}.dockerfile'.format(host)))
            ocpi_cmd = './scripts/install-packages.sh'
            docker_cmd = ' '.join([
                'docker build . -t {} -f {}'.format(image, dockerfile),
                '--build-arg SCRIPT="{}"'.format(ocpi_cmd)
            ])

            return [docker_cmd, create_repo_cmd, docker_push_cmd]

        # Create dockerfile string to pipe to "docker build"
        if stage == 'prereqs':
            ocpi_cmd = './scripts/install-prerequisites.sh'
        elif stage == 'build':
            ocpi_cmd = './scripts/build-opencpi.sh'
        elif stage == 'test':
            ocpi_cmd = './scripts/test-opencpi.sh --no-hdl'
        elif stage == 'generate':
            ocpi_cmd = './.gitlab-ci/scripts/ci_generate_pipeline.py cross'
        else:
            raise Exception('Uknown stage: {}'.format(stage))
        from_image_stage = self.stages[self.stages.index(stage) - 1]
        from_image = self._build_image_name(
            host, self.pipeline_id, from_image_stage)
        dockerfile_cmd = '\\n'.join([
                'printf "FROM {}'.format(from_image),
                'RUN {}"',
            ])
        dockerfile_cmd = dockerfile_cmd.format(ocpi_cmd)
        docker_cmd = "{} | docker build -t {} -".format(dockerfile_cmd, image)

        script = [docker_cmd, create_repo_cmd, docker_push_cmd]

        return script

    def _build_before_script(self, stage: str, host:str) -> str:
        """Build a job's before_script"""
        auth_cmd = ' '.join([
            'aws ecr get-login-password --region us-east-2 | docker login', 
            '--username AWS --password-stdin', 
            self.container_registry
        ])
        script = [auth_cmd]
        # If there was a prior stage, pull its image
        image_stage_index = self.stages.index(stage) - 1
        if self.stages[image_stage_index] == 'test':
        # Don't pull an image from test stage; pull from stage before
            image_stage_index -= 1
        if image_stage_index < 0:
        # Not prior stage
            return script
        image_stage = self.stages[image_stage_index]
        image = self._build_image_name(host, self.pipeline_id, image_stage)
        docker_pull_cmd = 'docker pull {}'.format(image)
        script.append(docker_pull_cmd)

        return script

    def _build_after_script(self, stage: str, host: str) -> str:
        """Build a job's after_script"""
        image = self._build_image_name(host, self.pipeline_id, stage)
        docker_rmi_cmd = 'docker rmi -f {}'.format(image)
        script = [docker_rmi_cmd]

        return script

    def _build_variables(self, stage: str, host: str, platform: str=None, 
            **kwargs) -> dict:
        """Constructs and returns a job's variables as a dictionary
        
        Any key/value pair provided as **kwargs will be added to the
        dictionary
        """
        variables = super()._build_variables(**kwargs)
        if stage not in ['packages', 'trigger']:
            variables['GIT_STRATEGY'] = 'none'
        if stage == 'generate':
            variables['CI_OCPI_HOST'] = host
            variables['CI_OCPI_PLATFORM'] = platform
        if stage == 'trigger':
            variables['CI_OCPI_ROOT_PIPELINE_ID'] = self.pipeline_id
            variables['CI_OCPI_HOST'] = host

        return variables


class CrossPipelineBuilder(PipelineBuilder):
    def __init__(self, pipeline_id, container_registry, host, platform, 
            assembly_dirs, test_dirs, config):
        super().__init__(pipeline_id, container_registry, config)
        self.assembly_dirs = assembly_dirs
        self.test_dirs = test_dirs
        self.host = host
        self.platform = platform
        self.stages = ['install', 'assemblies', 'unit-test']

    def _build_jobs(self) -> List[Job]:
        jobs = []
        for stage in self.stages:
            if stage == 'assemblies':
                for assembly in self.assembly_dirs:
                    job = self._build_job(stage, assembly)
                    jobs.append(job)
            if stage in ['assemblies', 'unit-test']:
                for test in self.test_dirs:
                    job = self._build_job(stage, test)
                    jobs.append(job)
            else:
                job = self._build_job(stage)
                jobs.append(job)

        return jobs

    def _build_job(self, stage: str, asset: str=None):
        asset_name = Path(asset).stem if asset else None
        name = self._build_name(self.host, self.platform, asset_name, stage)
        tags = self._build_tags(self.host, self.platform)
        script = self._build_script(stage, asset)
        needs = self._build_needs(stage, name)
        before_script = self._build_before_script(stage)
        after_script = self._build_after_script(stage)
        job = ScriptJob(name, stage, script, tags=tags, needs=needs, 
            before_script=before_script, after_script=after_script)

        return job

    def _build_script(self, stage: str, asset: str=None) -> List[str]:
        if stage == 'install':
            script = 'ocpiadmin install {}'.format(self.platform)
        elif stage == 'assemblies':
            script = 'ocpidev build -d {}'.format(asset)
        elif stage == 'unit-test':
            script = 'ocpidev run -d {}'.format(asset)
    
        return script

    def _build_before_script(self, stage: str) -> List[str]:
        before_script = ['source cdk/opencpi-setup.sh -r']
        if stage == 'unit-test':
            # TODO: finish these commands. need a config?
            before_script += ['ocpiremote load', 
                              'ocpiremote start']
        
        return before_script

    def _build_after_script(self, stage: str) -> List[str]:
        after_script = ['source cdk/opencpi-setup.sh -r']
        if stage == 'unit-test':
            after_script += ['ocpiremote stop',
                             'ocpiremote log']
        
        return after_script