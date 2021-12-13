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
            if val is not None:
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
        base_image_tag: str, dump_path: Path, config: dict, 
        image_tags: List[str]=None):
        """Initializes a Pipelinebuilder"""
        self.pipeline_id = pipeline_id
        self.image_tags = image_tags
        self.base_image_tag = base_image_tag
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

    def _build_trigger(self, stage, host: str=None, platform: str=None,
        base_platform: str=None, project: str=None) -> dict:
        """Constructs and returns a job's trigger as a dictionary"""
        trigger = {}
        if project:
        # Trigger is for an external project
            trigger['project'] = 'opencpi/' + project
            trigger['strategy'] = 'depend'
        else:
        # Trigger is for a child pipeline
            if stage == 'assemblies-platform':
                need_stage = 'generate-platform'
            else:
                need_stage = 'generate-base-platform'
            job = self._build_name(host, base_platform, platform, 
                need_stage)
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

    def _build_image_name(self, repo: str, tag: str) -> str:
        """Constructs a name for a docker image"""
        image_name = '{}/{}:{}'.format(self.container_registry, repo, tag)

        return image_name

    def _build_docker_cmd(self, cmd: str, image: str, stage: str, 
        ocpi_cmd: str=None, source: str=None, dest: str=None, 
        dockerfile: str=None, volumes: List[str]=None, tag: str=None,
        devices: List[str]=None, caps: List[str]=None) -> str:
        """Returns a docker command based on the passed cmd and stage"""
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
            if not ocpi_cmd:
                err_msg = '"docker {}" requires a command to run'.format(cmd)
                raise Exception(err_msg)
            if stage in ['generate-platform', 'generate-base-platform']:
            # Pass CI_ and OCPI_ env vars to cmd
                pattern = '"^CI_|^OCPI_"'
            else:
            # Pass OCPI_ env vars to cmd
                pattern = '^OCPI_'
            env_cmd = 'env | grep -E {} |'.format(pattern)
            docker_cmd = ' '.join([
                env_cmd,
                'docker {}'.format(cmd),
                '--net=host',
                '--env-file=/dev/stdin --name=${CI_JOB_ID}',
                '-v ' + '-v '.join(volumes) if volumes else '',
                '--device ' + '--device '.join(devices) if devices else '',
                '--cap-add ' + '--cap-add '.join(caps) if caps else '',
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
        elif cmd == 'tag':
            if not tag:
                raise Exception('docker cmd "tag" requires a tag')
            docker_cmd = 'docker tag {} {}'.format(image, tag)
        else:
            docker_cmd = None

        return docker_cmd

    @staticmethod
    def _build_ecr_repo_cmd(repo: str):
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

    @staticmethod
    def _build_socket_interface_cmd(runners: dict):
        """Create a cmd to set the OCPI_SOCKET_INFERACE env var
        
        A dictionary of runner IDs to socket interface must be provided
        """
        interface_cmd = 'declare -A interfaces && interfaces=('
        for runner_id,runner_configs in runners.items():
            interface_cmd += ' ["{}"]="{}"'.format(
                runner_id, runner_configs['socket_interface'])
        interface_cmd += ')'
        interface_cmd = ' && '.join([
            interface_cmd,
            'export OCPI_SOCKET_INTERFACE="${interfaces[$CI_RUNNER_ID]}"',
            'echo $OCPI_SOCKET_INTERFACE'
        ])

        return interface_cmd


class PlatformPipelineBuilder(PipelineBuilder):
    def __init__(self, pipeline_id: str, container_registry: str, 
        base_image_tag: str, hosts: List[str], platforms: List[str], 
        projects: List[str], dump_path: Path, config: dict, 
        image_tags: List[str]=None):
        """Initializes a PlatformPipelineBuilder"""
        super().__init__(pipeline_id, container_registry, base_image_tag, 
            dump_path, config, image_tags)
        self.stages = [
            'packages', 
            'prereqs', 
            'build', 
            'test',
            'osp',
            'install-base-platform',
            'install-platform',
            'generate-base-platform',
            'generate-platform',
            'comp',
            'assemblies-base-platform',
            'assemblies-platform',
        ]
        self.hosts = hosts
        self.platforms = platforms
        self.projects = projects

    def _build_jobs(self) -> List[Job]:
        """Create jobs for host platforms"""
        jobs = []
        for stage in self.stages:
        # Build job for each stage
            if stage in ['osp', 'comp']:
            # Build bridge job for each project
                projects = self.projects[stage]
                for project in projects:
                    job = self._build_job(stage, None, project=project)
                    jobs.append(job)
                continue
            for host in self.hosts:
            # Build job for each host
                if stage in ['packages', 'prereqs', 'build', 'test']:
                # Build job for host platform
                    job = self._build_job(stage, host)
                    jobs.append(job)
                elif stage in ['install-base-platform']:
                # Build job for installing a platform that other platforms
                # will depend on
                    for base_platform,platforms in self.platforms.items():
                        if not platforms:
                        # No associated platforms; continue
                            continue
                        job = self._build_job(stage, host, 
                            platform=base_platform)
                        jobs.append(job)
                else:
                    for base_platform,platforms in self.platforms.items():
                        if platforms:
                        # Build jobs for a base platform for each associated
                        # platform that depends on it
                            for platform in platforms:
                                job = self._build_job(stage, host, 
                                    platform=platform, 
                                    base_platform=base_platform)
                                jobs.append(job)
                        elif stage in ['install-platform', 'generate-platform', 
                                       'assemblies-platform']:
                        # Build jobs for a platform that does not have any
                        # associated platforms depending on it
                            job = self._build_job(stage, host, 
                                platform=base_platform)
                            jobs.append(job)

        return jobs

    def _build_job(self, stage: str, host: str, platform: str=None, 
        base_platform: str=None, project: str=None) -> Job:
        """Build a bridge or script job"""
        if stage in ['assemblies-base-platform', 'assemblies-platform', 'osp', 
                     'comp']:
        # Build bridge job
            if stage in ['osp', 'comp']:
                name = self._build_name(project.split('.')[-1], stage)
            else:
                name = self._build_name(host, base_platform, platform, stage)
            variables = self._build_variables(stage, host, platform)
            trigger = self._build_trigger(stage, host=host, platform=platform, 
                base_platform=base_platform, project=project)
            needs = self._build_needs(stage, host, platform=platform, 
                base_platform=base_platform)
            job = BridgeJob(name, stage, trigger, variables=variables, 
                            needs=needs)
        else:
        # Build script job
            name = self._build_name(host, base_platform, platform, stage)
            variables = self._build_variables(stage, host, platform=platform,
                base_platform=base_platform)
            script = self._build_script(stage, host, platform=platform, 
                base_platform=base_platform)
            after_script = self._build_after_script(stage, host, 
                platform=platform, base_platform=base_platform)
            before_script = self._build_before_script(stage, host,
                platform=platform, base_platform=base_platform)
            retry = self._build_retry()
            artifacts = self._build_artifacts(stage)
            needs = self._build_needs(stage, host, platform=platform, 
                base_platform=base_platform)
            tags = self._build_tags(stage)
            job = ScriptJob(name, stage, script, tags=tags, retry=retry,
                            variables=variables, before_script=before_script,
                            after_script=after_script, artifacts=artifacts,
                            needs=needs)

        return job

    def _build_script(self, stage: str, host: str, platform: str=None,
        base_platform: str=None) -> str:
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
            if stage in ['install-platform', 'install-base-platform']:
                volumes = ['/opt/Xilinx:/opt/Xilinx']
            else:
                volumes = None
            base_image = self._build_base_image_name(host, stage, 
                platform=platform, base_platform=base_platform)
            ocpi_cmd = self._build_ocpi_cmd(stage, platform=platform, 
                base_platform=base_platform)
            docker_run_cmd = self._build_docker_cmd('run', base_image, stage,
                ocpi_cmd=ocpi_cmd, volumes=volumes)
            script = [docker_run_cmd]
        if stage in ['prereqs', 'build', 'install-base-platform', 
                     'install-platform']:
        # Create 'docker commit' and 'docker push' cmds
            image = self._build_image_name(host, stage, platform=platform,
                base_platform=base_platform)
            repo = self._build_repo_name(host, stage, platform=platform, 
                base_platform=base_platform)
            docker_commit_cmd = self._build_docker_cmd('commit', image, stage)
            ecr_repo_cmd = PipelineBuilder._build_ecr_repo_cmd(repo)
            docker_push_cmd = self._build_docker_cmd('push', image, stage)
            script += [docker_commit_cmd, ecr_repo_cmd, docker_push_cmd]
        # Add additional tag to image
            for tag in self.image_tags:
                tag = self._build_image_name(host, stage, platform=platform, 
                    base_platform=base_platform, tag=tag)
                docker_tag_cmd = self._build_docker_cmd('tag', image, stage,
                    tag=tag)
                docker_push_cmd = self._build_docker_cmd('push', tag, stage)
                script += [docker_tag_cmd, docker_push_cmd]
        elif stage in ['generate-platform', 'generate-base-platform']:
        # Create 'docker cp' cmd to copy generate yml file to host machine
        # So that it can be uploaded as a GitLab artifact
            source = '{}:/{}/{}'.format(
                '$CI_JOB_ID', 'opencpi', self.dump_path)
            docker_cp_cmd = self._build_docker_cmd(
                'cp', base_image, stage, source=source)
            script.append(docker_cp_cmd)
        if stage in ['build', 'install-platform', 'install-base-platform']:
        # Add additional tag to image
            for tag in self.image_tags:
                tag = self._build_image_name(host, stage, platform=platform, 
                    base_platform=base_platform, tag=tag)
                docker_tag_cmd = self._build_docker_cmd('tag', image, stage,
                    tag=tag)
                docker_push_cmd = self._build_docker_cmd('push', tag, stage)
                script += [docker_tag_cmd, docker_push_cmd]

        return script

    def _build_before_script(self, stage: str, host: str, platform: str=None,
        base_platform: str=None) -> str:
        """Build a job's before_script"""
        if stage == 'packages':
            return None
        # If there was a prior stage, pull its image
        image = self._build_base_image_name(host, stage, platform=platform,
            base_platform=base_platform)
        docker_pull_cmd = 'docker pull {}'.format(image)
        script = [docker_pull_cmd]

        return script

    def _build_after_script(self, stage: str, host: str, platform: str=None,
        base_platform: str=None) -> str:
        """Build a job's after_script"""
        script = []
        if stage != 'packages':
            # Remove container
            docker_rm_cmd = self._build_docker_cmd('rm', None, stage)
            script = [docker_rm_cmd]
            # Remove pulled image
            base_image = self._build_base_image_name(host, stage, 
                platform=platform, base_platform=base_platform)
            docker_rmi_cmd = self._build_docker_cmd('rmi', base_image, stage)
            script.append(docker_rmi_cmd)
        if stage not in ['test', 'generate-platform', 
                         'generate-base-platform']:
        # Remove created image
            image = self._build_image_name(host, stage, platform=platform,
                base_platform=base_platform)
            docker_rmi_cmd = self._build_docker_cmd('rmi', image, stage)
            script.append(docker_rmi_cmd)

        return script

    def _build_variables(self, stage: str, host: str, platform: str=None, 
        base_platform: str=None, **kwargs: dict) -> dict:
        """Constructs and returns a job's variables as a dictionary
        
        Any key/value pair provided as **kwargs will be added to the
        dictionary
        """
        variables = {}
        if stage not in ['packages', 'osp', 'comp']:
        # Only clone repo in 'packages' stage
            variables['GIT_STRATEGY'] = 'none'
        if stage in ['generate-platform', 'generate-base-platform', 
                       'osp', 'comp']:
        # Gather variables for generating child pipeline or triggering project
            for key,val in environ.items():
                if key.startswith('CI_OCPI_') or key.startswith('OCPI_'):
                # Gather OCPI_ and CI_OCPI_ env vars to pass
                    variables[key] = val
            variables['CI_OCPI_ROOT_PIPELINE_ID'] = self.pipeline_id
            if stage in ['generate-platform', 'generate-base-platform']:
            # Add variables needed to generate yaml for child pipeline
                variables['CI_OCPI_HOST'] = host
                container_repo = self._build_base_repo_name(host, stage, 
                    platform=platform, base_platform=base_platform)
                variables['CI_OCPI_CONTAINER_REPO'] = container_repo
                if stage == 'generate-platform':
                    variables['CI_OCPI_PLATFORM'] = platform
                    if base_platform:
                        variables['CI_OCPI_OTHER_PLATFORM'] = base_platform
                else:
                    variables['CI_OCPI_PLATFORM'] = base_platform
                    variables['CI_OCPI_OTHER_PLATFORM'] = platform
            elif stage == 'osp':
            # Don't override platforms if triggering an osp
                variables.pop('CI_OCPI_PLATFORMS')
        else:
        # Get variables from config
            if stage == 'install-platform':
                platform_name = platform
            elif stage == 'install-base-platform':
                platform_name = base_platform
            else:
                platform_name = host
            try:
                kwargs.update(self.config[platform_name]['variables'])
            except KeyError:
                pass
            variables.update(super()._build_variables(**kwargs))
            
        return variables

    def _build_needs(self, stage: str, host: str, platform: str=None,
        base_platform: str=None) -> List[str]:
        """Constructs and returns a job's needs as a list of strings"""
        if stage in ['osp', 'comp']:
            return None
        needs = []
        if stage == 'packages':
            return needs
        if stage in ['assemblies-platform', 'assemblies-base-platform']:
            if stage == 'assemblies-platform':
                need_stage = 'generate-platform'
            else:
                need_stage = 'generate-base-platform'
            need = self._build_name(host, base_platform, platform, need_stage)
        elif stage in ['install-platform', 'install-base-platform']:
            need_stage = 'install-base-platform' if base_platform else 'test'
            need = self._build_name(host, base_platform, need_stage)
        elif stage in ['generate-base-platform', 'generate-platform']:
            need_stage = 'install-platform'
            need = self._build_name(host, base_platform, platform, need_stage)
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
        if stage in ['generate-platform', 'generate-base-platform']:
            artifacts = {
                'paths': [
                    str(self.dump_path)
                ],
                'expire_in': '1 week'
            }
        else:
            return None

        return artifacts

    def _build_ocpi_cmd(self, stage: str, platform: str=None, 
        base_platform: str=None) -> str:
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
        elif stage in ['install-base-platform', 'install-platform']:
            if not platform:
                raise Exception('platform required to build ocpi cmd')
            ocpi_cmd = 'ocpiadmin install platform {}'.format(platform)
            if base_platform:
                ocpi_cmd += ' && (ocpiadmin deploy platform {} {}'.format(
                    platform, base_platform)
                ocpi_cmd += ' || ocpiadmin deploy platform {} {})'.format(
                    base_platform, platform)
        elif stage in ['generate-base-platform', 'generate-platform']:
            ocpi_cmd = '.gitlab-ci/scripts/ci_generate_pipeline.py assembly'
        elif stage == 'test':
            ocpi_cmd = 'scripts/test-opencpi.sh --no-hdl'
        else:
            ocpi_cmd = None

        return ocpi_cmd

    def _build_repo_name(self, host: str, stage: str, platform: str=None,
        base_platform: str=None) -> str:
        """Constructs a repo name for a docker image"""
        if stage == 'build':
            repo = self._build_name(host)
        elif stage in ['packages', 'prereqs']:
            repo = self._build_name(host, stage, delimiter='.')
        elif stage in ['install-platform', 'install-base-platform']:
            repo = self._build_name(host, base_platform, platform)
        else:
            repo = None

        return repo

    def _build_base_repo_name(self, host: str, stage: str, platform: str,
        base_platform: str=None) -> str:
        """Returns the base repo for a job based on the job's stage"""
        if stage == 'test':
            base_repo = self._build_name(host)
        elif stage in ['prereqs', 'build']:
            base_stage_index = self.stages.index(stage) - 1
            base_stage = self.stages[base_stage_index]
            base_repo = self._build_name(host, base_stage, delimiter='.')
        elif stage in ['install-platform', 'install-base-platform']:
            base_repo = self._build_name(host, base_platform)
        elif stage in ['generate-platform', 'generate-base-platform']:
            base_repo = self._build_name(host, base_platform, platform)
        else:
            base_repo =  None

        return base_repo

    def _build_image_name(self, host: str, stage: str, platform: str=None,
        base_platform: str=None, tag=None) -> str:
        """Constructs a name for a docker image base on job's stage"""
        tag = self.pipeline_id if tag == None else tag
        repo = self._build_repo_name(host, stage, platform=platform, 
            base_platform=base_platform)
        image_name = super()._build_image_name(repo, tag)

        return image_name

    def _build_base_image_name(self, host: str, stage: str, platform: str=None,
        base_platform: str=None, tag=None) -> str:
        """Constructs a name for a docker base image based on job's stage"""
        tag = self.base_image_tag if tag == None else tag
        repo = self._build_base_repo_name(host, stage, platform=platform,
            base_platform=base_platform)
        image_name = super()._build_image_name(repo, tag)

        return image_name


class OspPipelineBuilder(PlatformPipelineBuilder):
    def __init__(self, pipeline_id: str, container_registry: str, 
        base_image_tag: str, hosts: List[str], platforms: List[str], 
        projects: List[str], project: str, dump_path: Path, config: dict, 
        image_tags: List[str]=None):
        """Initialize an OspPipelineBuilder"""
        super().__init__(pipeline_id, container_registry,
            base_image_tag, hosts, platforms, projects, dump_path, config,
            image_tags)
        self.stages = [
            'install-base-platform',
            'install-platform',
            'comp',
            'generate-base-platform',
            'generate-platform',
            'assemblies-base-platform',
            'assemblies-platform'
        ]
        self.project = project

    def _build_script(self, stage: str, host: str, platform: str=None,
        base_platform: str=None) -> str:
        """Build a script for a job"""
        script = []
        if stage in ['install-platform', 'install-base-platform']:
            base_image = self._build_base_image_name(host, stage, 
                platform=platform, base_platform=base_platform)
            ocpi_cmd = self._build_ocpi_cmd(stage, platform, base_platform)
            volumes = ['/opt/Xilinx:/opt/Xilinx']
            docker_create_cmd = self._build_docker_cmd('create', base_image, 
                stage, ocpi_cmd=ocpi_cmd, volumes=volumes)
            source = '.'
            dest = '$CI_JOB_ID:/opencpi/projects/osps/{}'.format(self.project)
            docker_cp_cmd = self._build_docker_cmd('cp', None, stage, 
                source=source, dest=dest)
            docker_start_cmd = self._build_docker_cmd('start', None, stage)
            script += [docker_create_cmd, docker_cp_cmd, docker_start_cmd]
            # Create 'docker commit' and 'docker push' cmds
            image = self._build_image_name(host, stage, platform=platform,
                base_platform=base_platform)
            repo = self._build_repo_name(host, stage, platform=platform, 
                base_platform=base_platform)
            docker_commit_cmd = self._build_docker_cmd('commit', image, stage)
            ecr_repo_cmd = PipelineBuilder._build_ecr_repo_cmd(repo)
            docker_push_cmd = self._build_docker_cmd('push', image, stage)
            script += [docker_commit_cmd, ecr_repo_cmd, docker_push_cmd]
            # Add additional tag to image
            for tag in self.image_tags:
                tag = self._build_image_name(host, stage, platform=platform, 
                    base_platform=base_platform, tag=tag)
                docker_tag_cmd = self._build_docker_cmd('tag', image, stage,
                    tag=tag)
                docker_push_cmd = self._build_docker_cmd('push', tag, stage)
                script += [docker_tag_cmd, docker_push_cmd]
        else:
            script += super()._build_script(stage, host, platform=platform, 
                base_platform=base_platform)

        return script

    def _build_needs(self, stage: str, host: str, platform: str=None,
        base_platform: str=None) -> List[str]:
        """Constructs and returns a job's needs as a list of strings"""
        if stage == 'install-base-platform':
            needs = []
        elif stage == 'install-platform' and base_platform:
            need = self._build_name(host, base_platform, 
                'install-base-platform')
            needs = [need]
        else:
            needs = super()._build_needs(stage, host, platform=platform,
                base_platform=base_platform)

        return needs

    def _build_ocpi_cmd(self, stage: str, platform: str=None, 
        base_platform: str=None) -> str:
        """Returns an ocpi command based on the job's stage"""
        ocpi_cmd = super()._build_ocpi_cmd(stage, platform=platform,
            base_platform=base_platform)
        if (stage == 'install-base-platform' 
            or (stage == 'install-platform' and base_platform is None)):
        # First stage in pipeline; need to register project
            ocpi_cmd = " && ".join([
                'ocpidev register project -d projects/osps/{}'.format(
                    self.project),
                ocpi_cmd
            ])

        return ocpi_cmd

    def _build_variables(self, stage: str, host: str, platform: str = None, 
        base_platform: str = None, **kwargs: dict) -> dict:
        """Constructs and returns a job's variables as a dictionary
        
        Any key/value pair provided as **kwargs will be added to the
        dictionary
        """
        variables = super()._build_variables(stage, host, platform=platform, 
            base_platform=base_platform, **kwargs)
        if (stage == 'install-base-platform' 
            or (stage == 'install-platform' and base_platform is None)):
        # Need to add project to image, so remove 'GIT_STRATEGY' = none
            variables.pop('GIT_STRATEGY')

        return variables


class AssemblyPipelineBuilder(PipelineBuilder):
    def __init__(self, pipeline_id, container_registry, container_repo,
        base_image_tag, host, platform, model, other_platform, assembly_dirs, 
        test_dirs, dump_path, config=None, runners=list(), do_hwil=False):
        """Initializes an AssemblyPipelineBuilder"""
        super().__init__(pipeline_id, container_registry, base_image_tag,
            dump_path, config)
        self.container_repo = container_repo
        self.assembly_dirs = assembly_dirs
        self.test_dirs = test_dirs
        self.host = host
        self.platform = platform
        self.model = model
        self.other_platform = other_platform
        self.do_hwil = do_hwil
        self.user = self.password = 'root'
        self.ip = self.port = None
        self.runners = runners
        if config:
            for key in ['ip', 'port', 'user', 'password']:
                if key in config:
                    self.__dict__[key] = config[key]
        self.stages = [
            'build-assemblies', 
            'build-unit_tests', 
            'run-unit_tests'
        ]

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
                if not self.do_hwil:
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
        name = self._build_name(asset_name, stage)
        tags = self._build_tags(stage)
        script = self._build_script(stage, asset)
        needs = self._build_needs(stage, asset_name)
        before_script = self._build_before_script(stage)
        after_script = self._build_after_script(stage)
        artifacts = self._build_artifacts(stage, asset)
        variables = self._build_variables(stage)
        resource_group = self._build_resource_group(stage)
        job = ScriptJob(name, stage, script, tags=tags, needs=needs, 
                        before_script=before_script, after_script=after_script, 
                        artifacts=artifacts, variables=variables,
                        resource_group=resource_group)

        return job

    def _build_script(self, stage: str, asset: str=None) -> List[str]:
        """Build a job's script"""
        ocpi_cmd = self._build_ocpi_cmd(stage, asset)
        base_image = self._build_base_image_name(stage)
        volumes = ['/opt/Xilinx:/opt/Xilinx']
        if stage == 'run-unit_tests':
        # Create "docker create" cmd, copy artifacts to container, and create
        # "docker start" cmd
            script = []
            devices = None
            caps = None
            if self.ip:
            # Device is remote; set appropriate env vars
                socket_interface_cmd = self._build_socket_interface_cmd(
                    self.runners)
                addresses_cmd = 'export OCPI_SERVER_ADDRESSES={}:{}'.format(
                    self.ip, self.port)
                script += [socket_interface_cmd, addresses_cmd]
            elif self.do_hwil:
            # Device is local to runner; allow container access to /dev/mem
                devices = ['/dev/mem']
                caps = ['SYS_RAWIO']
            docker_create_cmd = self._build_docker_cmd('create', base_image, 
                stage, ocpi_cmd=ocpi_cmd, volumes=volumes, devices=devices, 
                caps=caps)
            dest = '$CI_JOB_ID:/opencpi/{}'.format(str(Path(asset).parent))
            source = Path(asset).name
            docker_cp_cmd = self._build_docker_cmd('cp', None, stage, 
                source=source, dest=dest)
            docker_start_cmd = self._build_docker_cmd('start', None, stage)
            script += [docker_create_cmd, docker_cp_cmd, docker_start_cmd]
        else:
        # Run opencpi command on container
            docker_run_cmd = self._build_docker_cmd('run', base_image, stage,
                ocpi_cmd=ocpi_cmd, volumes=volumes)
            script = [docker_run_cmd]
        if stage == 'build-unit_tests':
        # Copyfiles from container to upload as artifacts
            source = '$CI_JOB_ID:/opencpi/{}'.format(asset)
            docker_cp_cmd = self._build_docker_cmd('cp', None, stage, 
                source=source)
            script.append(docker_cp_cmd)
        
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

        return script

    def _build_tags(self, stage: str) -> List[str]:
        """Constructs and returns a job's tags as a list of strings"""
        tags = ['opencpi', 'shell']
        if stage == 'run-unit_tests' and self.do_hwil:
            if self.model == 'hdl':
                tags.append(self.platform)
            elif self.model == 'rcc':
                tags.append(self.other_platform)
        else:
            tags.append('aws')

        return tags

    def _build_needs(self, stage: str, asset: str) -> List[str]:
        """Constructs and returns a job's needs as a list of strings"""
        needs = []
        if stage in ['build-assemblies', 'build-unit_tests']:
            return needs
        if stage == 'run-unit_tests':
            need = self._build_name(asset, 'build-unit_tests')
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
        if self.config and 'variables' in self.config:
            kwargs.update(self.config['variables'])
        variables = super()._build_variables(**kwargs)
        variables['GIT_STRATEGY'] = 'none'

        return variables

    def _build_resource_group(self, stage) -> str:
        """Builds a reource group for a job"""
        if stage == 'run-unit_tests':
            if self.model == 'hdl':
                resource_group = self.platform
            else:
                resource_group = self.other_platform
        else:
            resource_group = None

        return resource_group

    def _build_ocpi_cmd(self, stage: str, asset: str) -> str:
        """Returns an ocpi command based on the job's stage"""
        if stage in ['build-assemblies', 'build-unit_tests']:
            ocpi_cmd = 'ocpidev build -d {} --{}-platform {}'.format(
                asset, self.model, self.platform)
        elif stage == 'run-unit_tests':
            ocpi_cmds = []
            ocpidev_run_cmd = ' '.join([
                'ocpidev run -d',
                asset,
                '--only-platform',
                self.platform,
                '--mode prep_run_verify'
            ])
            if self.ip:
                ocpiremote_load_cmd = self._build_ocpiremote_cmd('load')
                ocpiremote_start_cmd = self._build_ocpiremote_cmd('start')
                ocpiremote_unload_cmd = self._build_ocpiremote_cmd('unload')
                ocpi_cmds = [
                    ocpiremote_unload_cmd + ' || true',
                    ocpiremote_load_cmd, 
                    ocpiremote_start_cmd,
                    ocpidev_run_cmd, 
                    ocpiremote_unload_cmd
                ]
                ocpi_cmd = ' && '.join(ocpi_cmds)
            else:
                ocpi_cmd = ocpidev_run_cmd
        else:
            ocpi_cmd = None

        return ocpi_cmd

    def _build_ocpiremote_cmd(self, cmd: str):
        if cmd == 'load':
            if self.model == 'hdl':
                hdl_platform = self.platform
                rcc_platform = self.other_platform
            else:
                hdl_platform = self.other_platform
                rcc_platform = self.platform
            ocpiremote_cmd = ' '.join([
                'ocpiremote load',
                '--hdl-platform={}'.format(hdl_platform),
                '--rcc-platform={}'.format(rcc_platform),
                '-i {}'.format(self.ip),
                '-r {}'.format(self.port),
                '-u {}'.format(self.user),
                '-p {}'.format(self.password)
            ])
        elif cmd in ['start', 'stop', 'unload']:
            ocpiremote_cmd = ' '.join([
                'ocpiremote {}'.format(cmd),
                '-i {}'.format(self.ip),
                '-u {}'.format(self.user),
                '-p {}'.format(self.password)
            ])

        return ocpiremote_cmd

    def _build_base_image_name(self, stage: str, tag: str=None) -> str:
        """Constructs a name for a docker base image based on job's stage"""
        image_name = super()._build_image_name(self.container_repo,
            self.pipeline_id)

        return image_name
