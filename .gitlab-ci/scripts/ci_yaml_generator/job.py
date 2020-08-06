from pathlib import Path

class Job():
    rcc_stages = ['prereqs', 'build', 'test']
    hdl_stages = ['build-primitives', 'build-libraries', 'build-platforms', 
                  'build-assemblies', 'build-sdcard', 'build-tests', 'test']
    stages_dict = {'primitives': 'build-primitives', 
                   'libraries': 'build-libraries', 
                   'platforms': 'build-platforms', 
                   'assemblies': 'build-assemblies'}

    def __init__(self, stage, name=None, script=None, artifacts=None, 
            platform=None, project=None, host_platform=None, library=None):

        self.platform = platform
        self.project = project
        self.host_platform = host_platform
        self.library = library
        self.stage = stage
        self.name = name
        self.artifacts = artifacts
        self.script = script


    @property
    def name(self):
        return self.__name


    @name.setter
    def name(self, name):
        if name:
            self.__name = name

        attributes = [self.stage]

        if self.library:
            attributes.append(self.library.stem)

        if self.host_platform:
            attributes.append(self.host_platform.name)

        if self.platform:
            attributes.append(self.platform.name)

        name = ':'.join(attributes)
        
        self.__name = name


    @property
    def script(self):
        return self.__script


    @script.setter
    def script(self, script):
        if script:
            self.__script = script
            return
        
        if self.stage == 'trigger':
            path = Path('.gitlab-ci', 'generated-yaml', self.host_platform.name, self.platform.name)
            script = {
                'strategy': 'depend',
                'include': [{
                    'artifacts': str(path),
                    'job': 'generate-yaml'
                }]
            }
            self.__script = script

            return 
            
        elif self.stage == 'generate-yaml':
            self.__script = ' '.join([str(Path('.gitlab-ci', 'scripts', 'yaml-generator.py')), 'child'])
            return
    
        stages = Job.hdl_stages if self.platform.model == 'hdl' else Job.rcc_stages
        stage_idx = stages.index(self.stage)
        download_cmd = '.gitlab-ci/scripts/ci_artifacts.py download -i "*{}.tar.gz" "*{}.tar.gz"'.format(
            self.platform.name, self.host_platform.name)
        sleep_cmd = 'sleep 2'
        timestamp_cmd = 'touch .timestamp'
        source_cmd = 'source cdk/opencpi-setup.sh -e'
        success_cmd = 'touch .success'
        upload_cmd = '.gitlab-ci/scripts/ci_artifacts.py upload -t .timestamp'

        for stage in stages[:stage_idx]:
            download_cmd += ' "*/{}/*"'.format(stage)

        if self.platform.model == 'hdl':
            if self.stage in ['build-primitives', 'build-libraries', 'build-assemblies']:
                build_cmd = 'ocpidev build -d {} --hdl-platform {}'.format(self.library, self.platform.name)
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

        script = [download_cmd, sleep_cmd, timestamp_cmd, source_cmd, build_cmd, success_cmd, upload_cmd]

        self.__script = script


    @property
    def artifacts(self):
        return self.__artifacts


    @artifacts.setter
    def artifacts(self, artifacts):
        if artifacts:
            self.__artifacts = artifacts

        elif self.stage == 'generate-yaml':
            self.__artifacts = {
                'paths': [
                    str(Path('.gitlab-ci', 'generated-yaml'))
                ]
            }

        self.__artifacts = None


    @classmethod
    def get_stage_from_library(cls, library):
        if library in cls.stages_dict:
            return cls.stages_dict[library]
        
        return 'build-libraries'


    def to_dict(self):
        if self.stage == 'trigger':
            job_dict = {
                'stage': self.stage,
                'trigger': self.script
            }
        else:
            job_dict = {
                'stage': self.stage,
                'script': self.script
            }

        if self.artifacts:
            job_dict['artifacts'] = self.artifacts

        return job_dict