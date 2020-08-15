#!/usr/bin/env python3

import ci_utils
from collections import namedtuple

Job = namedtuple('job', 'name stage script \
                         before_script after_script \
                         artifacts tags resource_group \
                         trigger rules')
        

def to_dict(job):
    job_dict = {}

    for key,value in job._asdict().items():
        if key != 'name' and value is not None:
            job_dict[key] = value
    
    return job_dict


def make_job(name, stage, script=None, 
             before_script=None, after_script=None, 
             artifacts=None, tags=None, 
             resource_group=None, trigger=None, 
             rules=None):
    
    return Job(name=name, stage=stage, script=script,
               before_script=before_script, after_script=after_script,
               artifacts=artifacts, tags=tags, resource_group=resource_group,
               trigger=trigger, rules=rules)


def make_parent_jobs(stages, yaml_generator_job, 
                     projects, platforms, host_platform):
    jobs = []

    for stage in stages:
        if stage == 'trigger-children':
            for platform in platforms:
                if platform.is_osp:
                    continue
                job = make_trigger_job(stage, yaml_generator_job, 
                                       host_platform, platform)
                jobs.append(job)
        elif stage not in ['generate-yaml', 'deploy']:
            for platform in platforms:
                name = ':'.join([stage, host_platform.name])
                before_script = make_before_script(stage, stages, host_platform)
                script = make_script(stage, stages, host_platform)
                after_script = make_after_script()
                tags = [host_platform.name, 'shell', 'opencpi']
                rules = make_parent_rules(host_platform)
                job = make_job(name, stage, script, tags=tags, rules=rules)
                jobs.append(job)
    
    return jobs


def make_child_jobs(stages, projects, platform, host_platform):
    jobs = []

    if platform.model == 'hdl':
        for project in projects:
            for library in project.libraries:
                stage = stage_from_library(library)
                name = ':'.join([stage, project.name, library.name, 
                                 host_platform.name, platform.name])
                job = make_build_job(name, stage, stages, 
                                     platform, host_platform)
                jobs.append(job)

                # if library.is_testable:
                #     for link in platform.links:
                #         stage = 'test'
                #         job = make_test_job(stage, stages, project, library, 
                #                             platform, host_platform, link=link,
                #                             resource_group=platform.name)
                #         jobs.append(job)

    elif platform.model == 'rcc':
        for stage in stages:
            if stage == 'test':
                for project in projects:
                    for library in project.libraries:
                        if library.is_testable:
                            job = make_test_job(stage, stages, project, 
                                                library, platform, 
                                                host_platform)
                            jobs.append(job)
            else:
                name = ':'.join([stage, host_platform.name, platform.name])
                job = make_build_job(name, stage, stages, platform, host_platform)
                jobs.append(job)

    return jobs


def make_build_job(name, stage, stages, platform, host_platform):
    before_script = make_before_script(stage, stages, platform, host_platform)
    script = make_script(stage, stages, platform, host_platform)
    after_script = make_after_script()
    tags = [host_platform.name, 'shell', 'opencpi']

    job = make_job(name, stage, script, tags=tags, 
                    before_script=before_script,
                    after_script=after_script)

    return job


def make_test_job(stage, stages, project, library, platform, host_platform, resource_group=None, link=None):
    if link:
        platform_name = '{}-{}'.format(link, platform.name)
    else:
        platform_name = platform.name

    name = ':'.join([stage, project.name, library.name, 
                     host_platform.name, platform_name])
    before_script = make_before_script(stage, stages, platform, host_platform, link)
    script = make_script(stage, stages, platform, host_platform, library.path)
    after_script = make_after_script()
    tags = [host_platform.name, 'shell', 'opencpi']

    job = make_job(name, stage, script, tags=tags, 
                   resource_group=resource_group,
                   before_script=before_script, 
                   after_script=after_script)

    return job


def make_trigger_job(stage, yaml_generater_job, host_platform, platform):
    name = ':'.join([stage, host_platform.name, platform.name])
    rules = make_trigger_rules(platform, host_platform)
    trigger = {
        'strategy': 'depend',
        'include': [{
            'artifact': '.gitlab-ci/yaml_dynamic/{}-{}.yml'.format(
                host_platform.name, platform.name),
            'job': yaml_generater_job.name
        }]
    }
    job = make_job(name, stage, trigger=trigger, rules=rules)

    return job


def make_bridge_job(stage, platform):
    name = ':'.join([stage, platform.name])
    rules = make_trigger_rules(platform, host_platform)
    trigger = {
        'strategy': 'depend',
        'variables': {
            'CI_COMMIT_MESSAGE': '$CI_COMMIT_MESSAGE'
        },
        'project': platform.repo,
        'branch': 'develop'
    }
    job = make_job(name, stage, trigger=trigger, rules=rules)

    return job


def make_yaml_generator_job():
    stage = 'generate-yaml'
    name = stage
    script = '.gitlab-ci/scripts/ci_generate_yaml.py child'
    artifacts = {'paths': [
        '.gitlab-ci/yaml-generated/'
    ]}
    job = make_job(name, stage, script, artifacts=artifacts)
    
    return job


def make_parent_rules(platform):
    return [
        {'if': ' '.join([
                    '' '$CI_PLATFORMS =~ /(^| |:)({})( |:|$)/i',
                       '&& $CI_PIPELINE_SOURCE == "schedule"'' '
                    ]).format(platform.name)},
        {'if': ' '.join([
                    '' '$CI_PLATFORMS =~ /(^| |:)({})( |:|$)/i',
                       '&& $CI_PIPELINE_SOURCE == "web"'' '
                    ]).format( platform.name)},
        {'if': ' '.join([
                    '' '$CI_MR_PLATFORMS =~ /(^| |:)({})( |:|$)/i',
                       '&& $CI_PIPELINE_SOURCE == "merge_request_event"'' '
                    ]).format( platform.name)},
        {'if': ' '.join([
                    '' '$CI_COMMIT_MESSAGE =~ /\[ *ci *\S* +({})( \S*)*\]/i',
                       '&& $CI_PIPELINE_SOURCE == "push"'' '
                    ]).format(platform.name)},
        {'if': ' '.join([
                    '' '$CI_PLATFORMS =~ /(^| |:)({})( |:|$)/i',
                       '&& $CI_COMMIT_MESSAGE !~ /\[ *ci.*\]/i',
                       '&& $CI_PIPELINE_SOURCE == "push"'' '
                    ]).format(platform.name)}
    ]


def make_trigger_rules(platform, host_platform):

    return [
        {'if': ' '.join([
                    '' '$CI_PLATFORMS =~ /(^| |:)({})( |:|$)/i',
                       '&& $CI_PLATFORMS =~ /(^| |:)({})( |:|$)/i',
                       '&& $CI_PIPELINE_SOURCE == "schedule"'' '
                    ]).format(host_platform.name, platform.name)},
        {'if': ' '.join([
                    '' '$CI_PLATFORMS =~ /(^| |:)({})( |:|$)/i',
                       '&& $CI_PLATFORMS =~ /(^| |:)({})( |:|$)/i',
                       '&& $CI_PIPELINE_SOURCE == "web"'' '
                    ]).format(host_platform.name, platform.name)},
        {'if': ' '.join([
                    '' '$CI_MR_PLATFORMS =~ /(^| |:)({})( |:|$)/i',
                       '&& $CI_MR_PLATFORMS =~ /(^| |:)({})( |:|$)/i',
                       '&& $CI_PIPELINE_SOURCE == "merge_request_event"'' '
                    ]).format(host_platform.name, platform.name)},
        {'if': ' '.join([
                    '' '$CI_COMMIT_MESSAGE =~ /\[ *ci *\S* +({})( \S*)*\]/i',
                       '&& $CI_COMMIT_MESSAGE =~ /\[ *ci *\S* +({})( \S*)*\]/i',
                       '&& $CI_PIPELINE_SOURCE == "push"'' '
                    ]).format(host_platform.name, platform.name)},
        {'if': ' '.join([
                    '' '$CI_PLATFORMS =~ /(^| |:)({})( |:|$)/i',
                       '&& $CI_PLATFORMS =~ /(^| |:)({})( |:|$)/i',
                       '&& $CI_COMMIT_MESSAGE !~ /\[ *ci.*\]/i',
                       '&& $CI_PIPELINE_SOURCE == "push"'' '
                    ]).format(host_platform.name, platform.name)}
    ]


def make_before_script(stage, stages, platform, host_platform=None, link=None):
    if platform.is_host:
        pipeline_id = '"$CI_PIPELINE_ID"'
    else:
        ci_env = ci_utils.get_ci_env()
        pipeline_id = ci_env.pipeline_id
    stage_idx = stages.index(stage)

    download_cmd = '.gitlab-ci/scripts/ci_artifacts.py download {} -i {}'.format(
        pipeline_id,
        ' '.join(["*{}.tar.gz".format(platform.name) for platform in [platform, host_platform] if platform]))

    if link:
        download_cmd += ' *{}.tar.gz*'.format(link)

    download_cmd += ' -e {}'.format(' '.join('*/{}/*'.format(stage) for stage in stages[stage_idx:]))
    sleep_cmd = 'sleep 2'
    timestamp_cmd = 'touch .timestamp'

    return [download_cmd, sleep_cmd, timestamp_cmd]


def make_after_script():
    return [
      'if [ ! -f ".success" ]; then .gitlab-ci/artifacts.py upload -t "failed-job"; fi'
    ]


def make_script(stage, stages, platform, host_platform=None, path=None):
    if platform.is_host:
        pipeline_id = '"$CI_PIPELINE_ID"'
    else:
        ci_env = ci_utils.get_ci_env()
        pipeline_id = ci_env.pipeline_id
    
    source_cmd = 'source cdk/opencpi-setup.sh -e'
    upload_cmd = '.gitlab-ci/scripts/ci_artifacts.py upload {} -s .timestamp -t "successful-job"'.format(
        pipeline_id)
    success_cmd = 'touch .success'

    if platform.model == 'hdl':
        if stage == 'generate-yaml':
            build_cmd = '.gitlab-ci/scripts/generate-yaml.py child'
        elif stage in ['build-primitives-core', 'build-primitives', 'build-libraries']:
            build_cmd = 'ocpidev build -d {} --hdl-platform {}'.format(path, platform.name)
        elif stage == 'build-platforms':
            build_cmd = 'ocpidev build hdl platforms {} --hdl-platform {}'.format(path, platform.name)
        elif stage == 'build-sdcard':
            build_cmd = 'ocpiadmin deploy platform {} {}'.format(platform.name, platform.name)
        elif stage == 'build-assemblies':
            build_cmd = 'ocpidev build test {} --hdl-platform {}'.format(path, platform.name)
        elif stage == 'test':
            build_cmd = 'ocpidev run tests {} --only-platform {}'.format(path, platform.name)
    else:
        if stage == 'prereqs':
            build_cmd = 'scripts/install-prerequisites.sh {}'.format(platform.name)
        elif stage == 'build':
            build_cmd = 'scripts/install-opencpi.sh {}'.format(platform.name)
        elif stage == 'test':
            if platform.is_host:
                build_cmd = 'scripts/test-opencpi.sh --no-hdl'
            else:
                build_cmd = 'ocpidev run tests {} --only-platform {}'.format(path, platform.name)


    return [source_cmd, build_cmd, upload_cmd, success_cmd] 


def stage_from_library(library):

    if library.name == 'primitives':
        if library.project_name == 'core':
            return 'build-primitives-core'
        else:
            return 'build-primitives'

    if library.name in ['platforms', 'assemblies']:
        return 'build-{}'.format(library.name)
    
    if (library.name in ['components', 'adapters', 'cards', 'devices']
            or library.path.parent.stem == 'components'):
        return 'build-libraries'

    raise Exception('Unable to get stage from library {}'.format(library.name))