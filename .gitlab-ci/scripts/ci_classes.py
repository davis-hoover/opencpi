#!/usr/bin/env python3

from abc import ABC, abstractmethod
from os import environ
from pathlib import Path
from typing import List
import re
import sys
import yaml


class Job():
    """Models a pipeline job"""
    def __init__(self, name: str, stage: str, **kwargs: dict):
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
    def __init__(self, name: str, stage: str, script: List[str], 
        **kwargs: dict):
        """Initalizes a ScriptJob"""
        self.script = script
        super().__init__(name, stage, **kwargs)


class BridgeJob(Job):
    """Models a pipeline job that requires a trigger"""
    def __init__(self, name: str, stage: str, trigger: dict, **kwargs: dict):
        """Initializes a BridgeJob"""
        self.trigger = trigger
        super().__init__(name, stage, **kwargs)


class Pipeline():
    """Models a pipeline"""
    def __init__(self, workflow: dict, stages: List[str], jobs: List[Job], 
        dump_path: Path):
        """Initializes a Pipeline object"""
        self.workflow = workflow
        self.stages = stages
        self.jobs = jobs
        self.dump_path = dump_path

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
        parents = [parent for parent in self.dump_path.parents]
        for parent in parents[::-1]:
            parent.mkdir(exist_ok=True)
        yaml.SafeDumper.ignore_aliases = lambda *args : True
        with open(self.dump_path, mode) as yml:
            yaml.safe_dump(pipeline_dict, yml, width=1000, 
                           default_flow_style=False)

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
    def __init__(self, pipeline_id: str, container_registry: str, 
        dump_path: Path, config: dict):
        """Initializes a Pipelinebuilder"""
        self.pipeline_id = pipeline_id
        self.config = config
        self.dump_path = dump_path
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
        pipeline = Pipeline(workflow, self.stages, jobs, self.dump_path)

        return pipeline

    def _build_name(self, *args: list, delimiter='/') -> str:
        """Constructs and returns a job's name as a string
        
        Anything provided as *args will be appended to the name in order 
        in which they are provided
        """
        name = delimiter.join([arg for arg in args if arg])

        return name

    def _build_variables(self, **kwargs: dict) -> dict:
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
            job = self._build_name(host, platform, 'generate')
            trigger['include'] = [{
                'artifact': str(self.dump_path),
                'job': job
            }]
            trigger['strategy'] = 'depend'

        return trigger

    def _build_retry(self) -> dict:
        """
        Constructs and returns a dictionary for a job's retry setting
        """
        retry = {'max': 1}

        return retry

    def _build_image_name(self, repo: str) -> str:
        """Constructs a name for a docker image"""
        image_name = '{}/{}:{}'.format(self.container_registry, repo, 
            self.pipeline_id)

        return image_name

    def _build_docker_cmd(self, cmd: str, image: str, stage: str, 
        ocpi_cmd: str=None, source: str=None, dest: str=None, 
        dockerfile: str=None, volumes: List[str]=None) -> str:
        """Returns a docker command based on the passed cmd and stage"""
        if volumes is not None:
            volumes = '-v {}'.format(' -v '.join(volume for volume in volumes))
        else:
            volumes = ''
        if cmd in ['pull', 'push']:
            docker_cmd = 'docker {} {}'.format(cmd, image)
        elif cmd == 'cp':
            if not source:
                raise Exception('docker cmd "cp" requires a source')
            if not dest:
            # "- | tar -x" seems to be a necessary workaround for "docker cp"
            # as it doesn't seem to like relative symlinks. Not sure why the
            # workaround works
                docker_cmd = 'docker cp {} - | tar -x'.format(source)
            else:
                docker_cmd = 'docker cp {} {}'.format(source, dest)
        elif cmd == 'commit':
            docker_cmd = 'docker commit $CI_JOB_ID {}'.format(image)
        elif cmd in ['run', 'create']:
        # Pass OCPI_ env vars to command
        # Generate job also needs CI_ env vars
            if not ocpi_cmd:
                err_msg = '"docker {}" requires a command to run'.format(cmd)
                raise Exception(err_msg)
            pattern = '"^CI_|^OCPI_"' if stage == 'generate' else '^OCPI_'
            env_cmd = 'env | grep -E {} |'.format(pattern)
            docker_cmd = ' '.join([
                env_cmd,
                'docker {}'.format(cmd),
                '--env-file=/dev/stdin --name=${CI_JOB_ID}',
                volumes,
                image,
                '"{}"'.format(ocpi_cmd)
            ])
        elif cmd == 'build':
            if dockerfile is None:
                raise Exception('docker cmd "build" requires a dockerfile')
            if not ocpi_cmd:
                raise Exception('docker cmd "run" requires a command to run')
            docker_cmd = ' '.join([
                'docker build . -t {} -f {}'.format(image, dockerfile),
                '--build-arg SCRIPT="{}"'.format(ocpi_cmd)
            ])
        elif cmd == 'rmi':
            docker_cmd = 'docker rmi {} || true'.format(image)
        elif cmd == 'rm':
            docker_cmd = 'docker rm -f $CI_JOB_ID'
        elif cmd == 'start':
            docker_cmd = 'docker start -a $CI_JOB_ID'
        else:
            docker_cmd = None

        return docker_cmd

    @staticmethod
    def _build_ecr_repo_cmd(repo):
        """Create repo and push lifecycle policy"""
        ecr_repo_cmd = ' '.join([
                'aws ecr create-repository', 
                '--repository-name {}'.format(repo),
                '--image-scanning-configuration scanOnPush=true',
                '--region us-east-2', 
        ])
        policy_file = Path(Path(__file__).parent, 'policy.json')
        if policy_file.exists():
        # Put lifecycle policy
            policy = policy_file.read_text().replace('\n', '')
            policy = policy.replace('  ', '').replace('"', '\\"')
            policy_cmd = ' '.join([
                'aws ecr put-lifecycle-policy', 
                '--repository-name {}'.format(repo), 
                '--lifecycle-policy-text="{}"'.format(policy)
            ])
            ecr_repo_cmd = ' && '.join([ecr_repo_cmd, policy_cmd])
        ecr_repo_cmd = ' || '.join([
                ecr_repo_cmd,
                'true'
        ])

        return ecr_repo_cmd


class HostPipelineBuilder(PipelineBuilder):
    def __init__(self, pipeline_id: str, container_registry: str, 
        hosts: List[str], platforms: List[str], projects: List[str], 
        dump_path: Path, config: dict):
        """Initializes a HostPipelineBuilder"""
        super().__init__(pipeline_id, container_registry, dump_path, config)
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
            needs = self._build_needs(stage, host, platform)
            job = BridgeJob(name, stage, trigger, variables=variables, 
                            needs=needs)
        else:
        # Build script job
            variables = self._build_variables(stage, host, platform)
            script = self._build_script(stage, host)
            after_script = self._build_after_script(stage, host)
            before_script = self._build_before_script(stage, host)
            retry = self._build_retry()
            artifacts = self._build_artifacts(stage)
            needs = self._build_needs(stage, host, platform)
            tags = self._build_tags(stage)
            job = ScriptJob(name, stage, script, tags=tags, retry=retry,
                            variables=variables, before_script=before_script,
                            after_script=after_script, artifacts=artifacts,
                            needs=needs)

        return job

    def _build_script(self, stage: str, host: str) -> str:
        """Build's a job's script"""
        if stage == 'packages':
        # Create 'docker build', create ecr repo, and 'docker push' cmds
            image = self._build_image_name(host, stage)
            dockerfile = str(Path(Path(__file__).parent.parent, 'dockerfiles', 
                '{}.dockerfile'.format(host)).relative_to(Path.cwd()))
            if not Path(dockerfile).exists():
                err_msg = 'No Dockerfile found for platform "{}"'.format(host)
                sys.exit('Error: {}'.format(err_msg)) 
            ocpi_cmd = self._build_ocpi_cmd(stage)
            docker_build_cmd = self._build_docker_cmd('build', image, stage, 
                ocpi_cmd=ocpi_cmd, dockerfile=dockerfile)
            repo = self._build_repo_name(host, stage)
            ecr_repo_cmd = PipelineBuilder._build_ecr_repo_cmd(repo)
            docker_push_cmd = self._build_docker_cmd('push', image, stage)
            script = [docker_build_cmd, ecr_repo_cmd, docker_push_cmd]
        else:
        # Create 'docker run' cmd
            base_image = self._build_base_image_name(host, stage)
            ocpi_cmd = self._build_ocpi_cmd(stage)
            docker_run_cmd = self._build_docker_cmd('run', base_image, stage,
                ocpi_cmd=ocpi_cmd)
            script = [docker_run_cmd]
        if stage in ['prereqs', 'build']:
        # Create 'docker commit' and 'docker push' cmds
            image = self._build_image_name(host, stage)
            repo = self._build_repo_name(host, stage)
            docker_commit_cmd = self._build_docker_cmd('commit', image, stage)
            ecr_repo_cmd = PipelineBuilder._build_ecr_repo_cmd(repo)
            docker_push_cmd = self._build_docker_cmd('push', image, stage)
            script += [docker_commit_cmd, ecr_repo_cmd, docker_push_cmd]
        elif stage == 'generate':
        # Create 'docker cp' cmd to copy generate yml file to host machine
        # So that it can be uploaded as a GitLab artifact
            source = '{}:/{}/{}'.format(
                '$CI_JOB_ID', 'opencpi', self.dump_path)
            docker_cp_cmd = self._build_docker_cmd(
                'cp', base_image, stage, source=source)
            script.append(docker_cp_cmd)

        return script

    def _build_before_script(self, stage: str, host:str) -> str:
        """Build a job's before_script"""
        if stage == 'packages':
            return None
        # If there was a prior stage, pull its image
        image = self._build_base_image_name(host, stage)
        docker_pull_cmd = 'docker pull {}'.format(image)
        script = [docker_pull_cmd]

        return script

    def _build_after_script(self, stage: str, host: str) -> str:
        """Build a job's after_script"""
        script = []
        if stage != 'packages':
            # Remove container
            docker_rm_cmd = self._build_docker_cmd('rm', None, stage)
            script = [docker_rm_cmd]
            # Remove pulled image
            base_image = self._build_base_image_name(host, stage)
            docker_rmi_cmd = self._build_docker_cmd('rmi', base_image, stage)
            script.append(docker_rmi_cmd)
        if stage not in ['test', 'generate']:
        # Remove created image
            image = self._build_image_name(host, stage)
            docker_rmi_cmd = self._build_docker_cmd('rmi', image, stage)
            script.append(docker_rmi_cmd)

        return script

    def _build_variables(self, stage: str, host: str, platform: str=None, 
        **kwargs: dict) -> dict:
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

    def _build_needs(self, stage: str, host: str, platform: str) -> List[str]:
        """Constructs and returns a job's needs as a list of strings"""
        needs = []
        if stage == 'packages':
            return needs
        if stage == 'trigger':
            if platform:
                need = self._build_name(host, platform, 'generate')
            else:
                need = self._build_name(host, 'test')
        else:
            need_stage = self.stages[self.stages.index(stage) - 1]
            need = self._build_name(host, need_stage)
        needs.append(need)

        return needs

    def _build_tags(self, stage: str) -> List[str]:
        """Constructs and returns a job's tags as a list of strings"""
        tags = ['opencpi', 'aws', 'shell']

        return tags

    def _build_artifacts(self, stage: str) -> dict:
        """Constructs and returns a job's artifacts"""
        if stage == 'generate':
            artifacts = {
                'paths': [
                    str(self.dump_path)
                ],
                'expire_in': '1 week'
            }
        else:
            return None

        return artifacts

    def _build_ocpi_cmd(self, stage: str) -> str:
        """Returns an ocpi command based on the job's stage"""
        if stage == 'packages':
            ocpi_cmd = './scripts/install-packages.sh'
        elif stage == 'prereqs':
            ocpi_cmd = './scripts/install-prerequisites.sh'
        elif stage == 'build':
            ocpi_setup = str(Path(
                '/opencpi', 
                'cdk', 
                'opencpi-setup.sh'
            ))
            ocpi_cmd = ' '.join([
                './scripts/build-opencpi.sh',
                '&& echo \'source {} -r\''.format(ocpi_setup),
                '>> ~/.bashrc'
            ])
        elif stage == 'generate':
            ocpi_cmd = '.gitlab-ci/scripts/ci_generate_pipeline.py cross'
        elif stage == 'test':
            ocpi_cmd = 'scripts/test-opencpi.sh --no-hdl'
        else:
            ocpi_cmd = None

        return ocpi_cmd

    def _build_repo_name(self, host: str, stage: str) -> str:
        """Constructs a repo name for a docker image"""
        if stage == 'build':
            repo = self._build_name(host)
        else:
            repo = self._build_name(host, stage, delimiter='.')

        return repo

    def _build_base_repo_name(self, host: str, stage: str) -> str:
        """Returns the base repo for a job based on the job's stage"""
        if stage in ['generate', 'test']:
            base_repo = self._build_name(host)
        elif stage in ['prereqs', 'build']:
            base_stage_index = self.stages.index(stage) - 1
            base_stage = self.stages[base_stage_index]
            base_repo = self._build_name(host, base_stage, delimiter='.')
        else:
            base_repo =  None

        return base_repo

    def _build_image_name(self, host: str, stage: str) -> str:
        """Constructs a name for a docker image base on job's stage"""
        repo = self._build_repo_name(host, stage)
        image_name = super()._build_image_name(repo)

        return image_name

    def _build_base_image_name(self, host: str, stage: str) -> str:
        """Constructs a name for a docker base image based on job's stage"""
        repo = self._build_base_repo_name(host, stage)
        image_name = super()._build_image_name(repo)

        return image_name


class CrossPipelineBuilder(PipelineBuilder):
    def __init__(self, pipeline_id, container_registry, host, platform, 
        model, assembly_dirs, test_dirs, dump_path, config):
        """Initializes a CrossPipelineBuilder"""
        super().__init__(pipeline_id, container_registry, dump_path, config)
        self.assembly_dirs = assembly_dirs
        self.test_dirs = test_dirs
        self.host = host
        self.platform = platform
        self.model = model
        try:
            self.ip = config[platform]['ip']
            self.port = config[platform]['port']
        except KeyError:
            self.ip = None
            self.port = None
        self.stages = ['install', 'build-assemblies', 'build-unit_tests', 
                       'run-unit_tests']

    def _build_jobs(self) -> List[Job]:
        """Create jobs for host platforms"""
        jobs = []
        for stage in self.stages:
            if stage == 'build-assemblies':
                for assembly in self.assembly_dirs:
                    job = self._build_job(stage, assembly)
                    jobs.append(job)
            elif stage == 'build-unit_tests':
                for test in self.test_dirs:
                    job = self._build_job(stage, test)
                    jobs.append(job)
            elif stage == 'run-unit_tests':
                if self.model == 'rcc' or not self.platform.endswith('sim'):
                    continue
                for test in self.test_dirs:
                    job = self._build_job(stage, test)
                    jobs.append(job)
            else:
                job = self._build_job(stage)
                jobs.append(job)

        return jobs

    def _build_job(self, stage: str, asset: str=None):
        """Create a script job"""
        asset_name = Path(asset).stem if asset else None
        name = self._build_name(self.host, self.platform, asset_name, stage)
        tags = self._build_tags(stage, self.platform)
        script = self._build_script(stage, asset)
        needs = self._build_needs(stage, asset_name)
        before_script = self._build_before_script(stage)
        after_script = self._build_after_script(stage)
        artifacts = self._build_artifacts(stage, asset)
        variables = self._build_variables(stage)
        job = ScriptJob(name, stage, script, tags=tags, needs=needs, 
                        before_script=before_script, after_script=after_script, 
                        artifacts=artifacts, variables=variables)

        return job

    def _build_script(self, stage: str, asset: str=None) -> List[str]:
        """Build a job's script"""
        ocpi_cmd = self._build_ocpi_cmd(stage, asset)
        base_image = self._build_base_image_name(stage)
        volumes =['/opt/Xilinx:/opt/Xilinx']
        if stage == 'run-unit_tests':
            docker_create_cmd = self._build_docker_cmd('create', base_image, 
                stage, ocpi_cmd=ocpi_cmd, volumes=volumes)
            dest = '$CI_JOB_ID:/opencpi/{}'.format(str(Path(asset).parent))
            source = Path(asset).name
            docker_cp_cmd = self._build_docker_cmd('cp', None, stage, 
                source=source, dest=dest)
            docker_start_cmd = self._build_docker_cmd('start', None, stage)
            script = [docker_create_cmd, docker_cp_cmd, docker_start_cmd]

            return script
        # Run opencpi command on container
        docker_run_cmd = self._build_docker_cmd('run', base_image, stage,
            ocpi_cmd=ocpi_cmd, volumes=volumes)
        script = [docker_run_cmd]
        if stage == 'build-unit_tests':
        # Copy over files to upload as artifacts
            source = '$CI_JOB_ID:/opencpi/{}'.format(asset)
            docker_cp_cmd = self._build_docker_cmd('cp', None, stage, 
                source=source)
            script.append(docker_cp_cmd)
        elif stage == 'install':
        # Create repo and push image
            image = self._build_image_name(stage)
            repo = self._build_repo_name(stage)
            docker_commit_cmd = self._build_docker_cmd('commit', image, stage)
            ecr_repo_cmd = PipelineBuilder._build_ecr_repo_cmd(repo)
            docker_push_cmd = self._build_docker_cmd('push', image, stage)
            script += [docker_commit_cmd, ecr_repo_cmd, docker_push_cmd]
        
        return script

    def _build_before_script(self, stage: str) -> str:
        """Build a job's before_script"""
        base_image = self._build_base_image_name(stage)
        docker_pull_cmd = self._build_docker_cmd('pull', base_image, stage)
        script = [docker_pull_cmd]

        return script

    def _build_after_script(self, stage: str) -> List[str]:
        """Build a job's after_script"""
        docker_rm_cmd = self._build_docker_cmd('rm', None, stage)
        base_image = self._build_base_image_name(stage)
        docker_rmi_cmd = self._build_docker_cmd('rmi', base_image, stage)
        script = [docker_rm_cmd, docker_rmi_cmd]
        if stage == 'install':
        # Remove created image
            image = self._build_image_name(stage)
            docker_rmi_cmd = self._build_docker_cmd('rmi', image, stage)
            script.append(docker_rmi_cmd)

        return script

    def _build_tags(self, stage: str, platform: str) -> List[str]:
        """Constructs and returns a job's tags as a list of strings"""
        tags = ['opencpi', 'shell']
        if stage == 'run-unit_tests' and self.ip:
            tags.append(platform)
        else:
            tags.append('aws')

        return tags

    def _build_needs(self, stage: str, asset: str) -> List[str]:
        """Constructs and returns a job's needs as a list of strings"""
        needs = []
        if stage == 'install':
            return needs
        if stage in ['build-assemblies', 'build-unit_tests']:
            need = self._build_name(self.host, self.platform, 'install')
            needs.append(need)
        if stage == 'run-unit_tests':
            need = self._build_name(self.host, self.platform, asset, 
                'build-unit_tests')
            needs.append(need)

        return needs

    def _build_artifacts(self, stage: str, asset: str) -> str:
        """Constructs and returns a job's artifacts"""
        if stage == 'build-unit_tests':
            artifacts = {
                'paths': [
                    str(Path(asset).name)
                ],
                'expire_in': '1 week'
            }
        else:
            artifacts = None

        return artifacts

    def _build_variables(self, stage, **kwargs: dict) -> dict:
        """Constructs and returns a job's variables as a dictionary
        
        Any key/value pair provided as **kwargs will be added to the
        dictionary
        """
        variables = super()._build_variables(**kwargs)
        variables['GIT_STRATEGY'] = 'none'

        return variables

    def _build_ocpi_cmd(self, stage: str, asset: str=None) -> str:
        """Returns an ocpi command based on the job's stage"""
        if stage == 'install':
            ocpi_cmd = 'ocpiadmin install platform {}'.format(self.platform)
        elif stage in ['build-assemblies', 'build-unit_tests']:
            if asset is None:
                err_msg = 'Asset must be provided for stage {}'.format(stage)
                raise Exception(err_msg)
            ocpi_cmd = 'ocpidev build -d {} --{}-platform {}'.format(
                asset, self.model, self.platform)
        elif stage == 'run-unit_tests':
            ocpi_cmd = ' '.join([
                'ocpidev run -d',
                asset,
                '--only-platform',
                self.platform,
                '--mode prep_run_verify'
            ])
        else:
            ocpi_cmd = None

        return ocpi_cmd

    def _build_repo_name(self, stage: str) -> str:
        """Constructs a repo name for a docker image"""
        if stage == 'install':
            repo = self._build_name(self.host, self.platform)
        else:
            repo = None

        return repo

    def _build_base_repo_name(self, stage: str) -> str:
        """Returns the base repo for a job based on the job's stage"""
        if stage == 'install':
            base_repo = self._build_name(self.host)
        elif stage in ['build-assemblies', 'build-unit_tests', 'run-unit_tests']:
            base_repo = self._build_name(self.host, self.platform)

        return base_repo

    def _build_image_name(self, stage: str) -> str:
        """Constructs a name for a docker image base on job's stage"""
        repo = self._build_repo_name(stage)
        image_name = super()._build_image_name(repo)

        return image_name

    def _build_base_image_name(self, stage: str) -> str:
        """Constructs a name for a docker base image based on job's stage"""
        repo = self._build_base_repo_name(stage)
        image_name = super()._build_image_name(repo)

        return image_name