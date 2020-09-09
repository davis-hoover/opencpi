#!/usr/bin/env python3

import os
import yaml
from collections import namedtuple
from pathlib import Path


_Job = namedtuple('job', 'name stage script before_script after_script' 
                         ' artifacts tags resource_group rules'
                         ' variables dependencies image trigger')


def Job(name, stage=None, script=None, before_script=None, after_script=None, 
        artifacts=None, tags=None, resource_group=None, rules=None, 
        variables=None, dependencies=None, image=None, trigger=None, 
        overrides=None):
    """Constructs a Job

        Will use values in overrides to replace values of other args in
        construction of Job.

    Args:
        name:           Name of job in pipeline
        stage:          Stage of pipeline for job to execute in
        script:         List of commands to be executed in pipeline 
                        'script' step
        before_script:  List of commands to be executed in pipeline 
                        'before_script' step
        after_script:   List of scripts to be executed in pipeline
                        'after_script' step
        artifacts:      List of artifacts to be handled by gitlab 
                        (NOT AWS)
        tags:           List of tags for matching job to runner
        resource_group: Label for allowing only one job with same label
                        to run at a time within pipeline
        rules:          Dictionary of rules that define the conditions
                        that allow a job to execute in a pipeline
        variables:      Dictionary of variables to set when job runs in
                        pipeline
        dependencies:   List of job names a job should download gitlab
                        artifacts from (NOT AWS)
        image:          Docker image for job to run in
        trigger:        The child pipeline to trigger
        overrides:      Dictionary to override standard values of above 
                        args

    Returns:
        Job: namedtuple containing data necessary to create a job in a
             pipeline
    """
    args = locals()
    job_args = {}

    # Check if current job is specified in overrides
    if overrides and name in overrides:
        overrides = overrides[name]

    # Skip this job
    if overrides == 'skip':
        return None

    # Collect overrides
    for key,value in args.items():
        if overrides and key in overrides:
            job_args[key] = overrides[key]
        elif key != 'overrides':
            job_args[key] = value

    return _Job(**job_args)


def to_dict(job):
    """Converts Job(s) to a dictionary

    Args:
        job: A Job to convert into a dictionary

    Returns:
        jobs_dict: A dictionary conversion of a Job
    """
    job_dict = {}
    for key,value in job._asdict().items():
        if key != 'name' and value is not None:
            job_dict[key] = value
    
    return job_dict


def make_jobs(stages, platform, projects, linked_platforms=None, 
              host_platform=None, overrides=None):
    """Creates Job(s) for project/platform combinations

    Calls either make_hdl_jobs() or make_rcc_jobs() based on model
    of platform.

    Args:
        stages:           List of pipeline stages
        platform:         Platform to make jobs for
        projects:         List of projects to make jobs for
        linked_platforms: List of platforms for jobs that require an 
                          associated platform
        host_platform:    Host platform to create jobs for
        overrides:        Dictionary to override standard job values

    Returns:
        Jobs: collection containing data necessary to create jobs in a
              pipeline

    Raises:
        ValueError: if platform model is neither 'rcc' nor 'hdl'
    """
    if platform.model == 'hdl': 
        return make_hdl_jobs(stages, platform, projects, linked_platforms, 
                             host_platform, overrides)
    elif platform.model == 'rcc':
        return make_rcc_jobs(stages, platform, projects, host_platform, 
                             overrides)
    else:
        raise ValueError('Unknown model: {}'.format(platform.model))


def make_rcc_jobs(stages, platform, projects, host_platform=None, 
                  overrides=None):
    """Creates Job(s) for project/platform combinations of model 'rcc'

    Determines arguments to pass to make_job().

    Args:
        stages:        List of pipeline stages
        platform:      Platform to make jobs for
        projects:      List of projects to make jobs for
        host_platform: Host platform to create jobs for
        overrides:     Dictionary to override standard job values

    Returns:
        Jobs: collection containing data necessary to create jobs in a
              pipeline
    """
    jobs = []

    for stage in ['prereqs', 'build-rcc', 'build', 'test']:
        if stage == 'build-rcc' and platform.is_host:
            continue
        if stage == 'build' and not platform.is_host:
            continue

        if stage == 'test' and not platform.is_host:
            for project in projects:
                for library in project.libraries:
                    if library.is_testable:
                        job = make_job(stage, stages, platform, 
                                       project=project, library=library,
                                       host_platform=host_platform,
                                       overrides=overrides)
                        if job:
                            jobs.append(job)
        else:
            job = make_job(stage, stages, platform, 
                           host_platform=host_platform, overrides=overrides)
            if job:
                jobs.append(job)

        if stage == 'prereqs' and platform.is_host:
            name = make_name('packages', platform)
            job = make_job(stage, stages, platform, name=name,
                           overrides=overrides)
            if job:
                jobs.append(job)

    return jobs


def make_hdl_jobs(stages, platform, projects, linked_platforms, 
                  host_platform=None, overrides=None):
    """Creates Job(s) for project/platform combinations of model 'hdl'

    Determines arguments to pass to make_job().

    Args:
        stages:           List of pipeline stages
        platform:         Platform to make jobs for
        projects:         List of projects to make jobs for
        linked_platforms: List of platforms for jobs that require an 
                          associated platform
        host_platform:    Host platform to create jobs for
        overrides:        Dictionary to override standard job values

    Jobs: collection containing data necessary to create jobs in a
          pipeline
    """
    jobs = []

    for project in projects:
        for library in project.libraries:

            if library.is_buildable:
                stage = stage_from_library(library)
                job = make_job(stage, stages, platform, project=project,
                               host_platform=host_platform, library=library,
                               overrides=overrides)
                if job:
                    jobs.append(job)

            if library.is_testable:
                name = make_name('build-tests', platform,project=project, 
                                 host_platform=host_platform, library=library)
                build_test_job = make_job('build-assemblies', stages, platform, 
                                          name=name, project=project, 
                                          host_platform=host_platform, 
                                          library=library, overrides=overrides)
                if build_test_job:
                    jobs.append(build_test_job)

                if platform.is_sim:
                    run_test_job = make_job('test', stages, platform, 
                                            project=project, library=library,
                                            host_platform=host_platform,
                                            overrides=overrides)
                    if run_test_job:
                        jobs.append(run_test_job)

                if not platform.ip or not platform.port:
                    continue    

                for linked_platform in linked_platforms:
                    run_test_job = make_job('test', stages, platform, 
                                            project=project, 
                                            library=library,
                                            host_platform=host_platform,
                                            linked_platform=linked_platform,
                                            overrides=overrides,
                                            do_ocpiremote=True)      
                    if run_test_job:
                        jobs.append(run_test_job)

    for linked_platform in linked_platforms:
        job = make_job('build-sdcards', stages, platform, 
                       host_platform=host_platform, 
                       linked_platform=linked_platform, overrides=overrides)
        if job:
            jobs.append(job)

    return jobs


def make_trigger(host_platform, cross_platform, include, overrides=None):
    #TODO: python docs
    stage = 'trigger-children'
    name = make_name(stage, cross_platform, host_platform)
    rules = make_rules(cross_platform, host_platform)
    trigger = {
        'include': include, 
        'strategy': 'depend'
    }
    job = Job(name, stage=stage, trigger=trigger, rules=rules, 
              overrides=overrides)
    
    return job


def make_job(stage, stages, platform, project=None, name=None, 
             host_platform=None, library=None, linked_platform=None, 
             overrides=None, do_ocpiremote=False):
    """Creates Job(s) for project/platform combinations

    Calls before_script(), after_script(), script(), and if
    necessary, make_name() to get arguments for construction of a Job.

    Args:
        stage:           Stage of pipeline for job to execute in
        stages:          List of pipeline stages
        platform:        Platform to make jobs for
        project:         Project to make jobs for
        name:            Name of job
        host_platform:   Host platform to create jobs for
        library:         Library to make job for
        linked_platform: List of platforms needed for making jobs
                         requiring an associated rcc platform
        
        overrides:     Dictionary to override standard job values
        do_ocpiremote: Whether jobs should run ocpiremote commands

    Returns:
        Job: contains data necessary to create a job in a pipeline
    """
    if not name:
        name = make_name(stage, platform, project, host_platform, 
                         linked_platform, library)

    rules = make_rules(platform, host_platform)
    #TODO: Uncomment below
    # before_script = make_before_script(stage, stages, platform,
    #                                    host_platform=host_platform, 
    #                                    linked_platform=linked_platform,
    #                                    do_ocpiremote=do_ocpiremote)
    # script = make_script(stage, platform, project=project, library=library, 
    #                      linked_platform=linked_platform, name=name)
    # after_script = make_after_script(platform, do_ocpiremote=do_ocpiremote)
    before_script = []
    after_script = []
    script = "echo 'Hello, world'"
    #TODO: Remove above
    dependencies = []

    if platform.is_host:
        tags = [platform.name, 'shell', 'opencpi']
    elif platform.is_sim or (stage == 'test' and platform.model == 'hdl'):
        tags = [host_platform.name, platform.name, 'shell', 'opencpi']
    else:
        tags = [host_platform.name, 'shell', 'opencpi']

    if do_ocpiremote:
        resource_group = platform.name
    else:
        resource_group = None

    #TODO: Remove below
    image = 'centos:7'
    tags = ['docker']

    job = Job(name, stage, script, tags=tags, before_script=before_script,
              after_script=after_script, rules=rules, overrides=overrides,
              resource_group=resource_group, dependencies=dependencies)

    return job


def make_name(stage, platform, project=None, host_platform=None, 
              linked_platform=None, library=None):
    """Creates a name for a job

    Args:
        stage:           Stage of pipeline for job to execute in
        platform:        Platform of job
        project:         Project of job
        host_platform:   Host_platform of job
        linked_platform: Associated platform for jobs requiring both an
                         'hdl' and an 'rcc' platform
        library:         Library for jobs that build/test for a specific
                         library

    Returns:
        name of job string
    """
    attributes = [host_platform, project, library, linked_platform, platform]
    name_attributes = [stage] + [attribute.name for attribute in attributes 
                                 if attribute]
    
    return ':'.join(name_attributes)
    

def make_before_script(stage, stages, platform, host_platform=None, 
                       linked_platform=None, do_ocpiremote=False):
    """Creates list of commands to run in job's before_script step

        Constructs commands for downloading AWS artifacts, creating
        timestamp, and sourcing opencpi.

    Args:
        stage:           Stage of pipeline for job to execute in.
                         Used to exclude artifacts in same and later
                         stages
        stages:          List of all pipeline stages
        platform:        Platform to download artifacts for
        host_platform:   Host_platform to download artifacts for
        linked_platform: Associated platform to downloaded artifacts for
        do_ocpiremote:   Whether jobs should run ocpiremote commands

    Returns:
        list of command strings
    """

    timestamp_cmd = 'touch .timestamp'

    if stage == 'prereqs':
        return [timestamp_cmd]

    # If running in a pipeline, set pipeline_id var to ID of pipeline.
    # Otherwise, set to string "$CI_PIPELINE_ID"
    pipeline_id = os.getenv("CI_PIPELINE_ID")
    if not pipeline_id:
        pipeline_id = '"$CI_PIPELINE_ID"'

    # Download artifacts for platform, host_platform, and linked_platform
    includes = ['"*{}.tar.gz"'.format(platform.name) 
                    for platform in [platform, host_platform, linked_platform] 
                    if platform]
    # Don't download artifacts in current or later stages
    stage_idx = stages.index(stage)
    excludes = ['"{}:*"'.format(stage) for stage in stages[stage_idx:]]
    download_cmd = ' '.join(['.gitlab-ci/scripts/ci_artifacts.py download',
                             pipeline_id,
                             '-i', ' '.join(includes),
                             '-e', ' '.join(excludes)])
    sleep_cmd = 'sleep 2'

    if stage == 'build':
        return [download_cmd, sleep_cmd, timestamp_cmd]
    
    source_cmd = 'source cdk/opencpi-setup.sh -e'
    cmds = [download_cmd, sleep_cmd, timestamp_cmd, source_cmd]

    if do_ocpiremote:
        cmds += [
            make_ocpiremote_cmd('deploy', platform, 
                                linked_platform=linked_platform),
            'sleep 5',
            make_ocpiremote_cmd('load', platform,
                                linked_platform=linked_platform),
            make_ocpiremote_cmd('start', platform,
                                linked_platform=linked_platform),
            'export OCPI_SERVER_ADDRESSES={}:{}'.format(platform.ip,
                                                        platform.port)
        ]

    return cmds


def make_after_script(platform, do_ocpiremote=False):
    """Creates list of commands to run in job's after_script step

        Constructs command for uploading opencpi tree to AWS if job
        failed, and cleans entire project directory as final cmd.

    Args:
        platform:      Platform of job
        do_ocpiremote: Whether jobs should run ocpiremote commands

    Returns:
        list of command strings
    """
    # If running in a pipeline, set pipeline_id var to ID of pipeline.
    # Otherwise, set to string "$CI_PIPELINE_ID"
    pipeline_id = os.getenv("CI_PIPELINE_ID")
    if not pipeline_id:
        pipeline_id = '"$CI_PIPELINE_ID"'

    job_name = '"$CI_JOB_NAME"'
    upload_cmd = ' '.join(['if [ ! -f ".success" ];', 
                           'then .gitlab-ci/scripts/ci_artifacts.py upload',
                           pipeline_id, job_name,
                           '-t "failed-job"; fi'])
    clean_cmd = 'rm -rf *'

    cmds = [upload_cmd]
    
    if do_ocpiremote:
        cmds.append(make_ocpiremote_cmd('unload', platform))

    cmds.append(clean_cmd)

    return cmds


def make_script(stage, platform, project=None, linked_platform=None,
                library=None, name=None):
    """Creates list of commands to run in job's script step

        Constructs commands for downloading AWS artifacts, creating
        timestamp, and sourcing opencpi.

    Args:
        stage:           Stage of pipeline for job to execute in
        platform:        Platform of job
        project:         Project of job
        linked_platform: Associated platform for jobs requiring both an
                         'hdl' and an 'rcc' platform
        library:         Library for jobs that build/test for a specific
                         library
        name:            Name of job in pipeline

    Returns:
        list of command strings
    """
    # If running in a pipeline, set pipeline_id var to ID of pipeline.
    # Otherwise, set to string "$CI_PIPELINE_ID"
    pipeline_id = os.getenv("CI_PIPELINE_ID")
    if not pipeline_id:
        pipeline_id = '"$CI_PIPELINE_ID"'

    job_name = '"$CI_JOB_NAME"'
    upload_cmd = ' '.join(['.gitlab-ci/scripts/ci_artifacts.py upload',
                           pipeline_id, job_name,
                           '-s .timestamp -t "successful-job"'])
    success_cmd = 'touch .success'

    if stage == 'test':
        if platform.is_host:
            cmd = make_scripts_cmd(stage, platform)
        else:
            cmd = make_ocpidev_cmd('run', platform, library.path, 
                                   noun='tests')
    elif platform.model == 'hdl':
        if stage == 'build-platforms':
            cmd = make_ocpidev_cmd('build', platform, project.path, 
                                   'hdl platforms')
        elif stage == 'build-assemblies' and library.name != 'assemblies':
            cmd = make_ocpidev_cmd('build', platform, library.path, 
                                   noun='test')
        elif stage == 'build-sdcards':
            cmd = make_ocpiadmin_cmd('deploy', platform, linked_platform)
        else:
            cmd = make_ocpidev_cmd('build', platform, library.path)
    else:
        cmd = make_scripts_cmd(stage, platform, name=name)

    return [cmd, upload_cmd, success_cmd]


def make_scripts_cmd(stage, platform, name=None):
    """Makes command that executes script in opencpi/scripts/

    Args:
        stage:    Stage of pipeline for job to execute in
        platform: Platform of job
        name:     Name of job in pipeline

    Returns:
        command string

    Raises:
        ValueError: if unrecognized stage provided
    """
    if stage == 'test':
        return 'scripts/test-opencpi.sh --no-hdl'

    if stage == 'prereqs':
        if name and name.startswith('prereqs'):
            return 'scripts/install-prerequisites.sh {}'.format(platform.name)
        else:
            return 'scripts/install-packages.sh {}'.format(platform.name)

    if stage in ['build', 'build-rcc']:
        return 'scripts/build-opencpi.sh {}'.format(platform.name) 

    if stage == 'generate-children':
        return '.gitlab-ci/scripts/ci_yaml_generator.py'

    raise ValueError('Uknown stage: {}'.format(stage))


def make_ocpiadmin_cmd(verb, platform, linked_platform=None):
    """Makes ocpiadmin command

    Args:
        verb:            String to pass to ocpiadmin
        platform:        Platform of job to pass to ocpiadmin
        linked_platform: Associated platform to pass to ocpiadmin

    Returns:
        ocpiadmin command string

    Raises:
        ValueError: if unrecognized verb provided
    """
    if verb == 'install':
        return ' '.join([
            'ocpiadmin install platform',
            platform.name
        ])

    if verb == 'deploy':
        return ' '.join([
            'ocpiadmin deploy platform',
            linked_platform.name,
            platform.name,
        ])

    raise ValueError('Unknown verb: {}'.format(verb))


def make_ocpidev_cmd(verb, platform, path, noun=''):
    """Makes ocpidev command

    Args:
        verb:     String to pass to ocpidev
        platform: Platform of job to pass to ocpidev
        path:     Path to pass with '-d' option to ocpidev
        noun:     Noun to pass to ocpidev

    Returns:
        ocpidev command string

    Raises:
        ValueError: if unrecognized verb or noun provided
    """
    
    if noun and noun not in ['tests', 'test', 'hdl platforms']:
        raise ValueError('Unknown noun: {}'.format(noun))

    if verb == 'build':
        return ' '.join([
            'ocpidev build',
            noun,
            '-d {}'.format(path),
            '--hdl-platform {}'.format(platform.name)
        ])

    if verb == 'run':
        return ' '.join([
            'ocpidev run',
            noun,
            '-d {}'.format(path),
            '--only-platform {}'.format(platform.name),
            '--mode prep_run_verify'
        ])

    raise ValueError('Unknown verb: {}'.format(verb))


def make_ocpiremote_cmd(verb, platform, linked_platform=None):
    """Makes ocpiremote command

    Args:
        verb:            String to pass to ocpiremote
        platform:        Platform of job to pass to ocpiremote
        linked_platform: Associated platform to pass to ocpiremote

    Returns:
        ocpiadmin command string

    Raises:
        ValueError: if unrecognized verb provided
    """

    if verb == 'deploy':
        return ' '.join([
            'ocpiremote deploy', 
            '-i {}'.format(platform.ip),
            '-w {}'.format(platform.name),
            '-s {}'.format(linked_platform.name)
        ])

    if verb == 'load':
        return ' '.join([
            'ocpiremote load', 
            '-i {}'.format(platform.ip),
            '-r {}'.format(platform.port), 
            '-w {}'.format(platform.name),
            '-s {}'.format(linked_platform.name)
        ])

    if verb in ['start', 'unload']:
        return ' '.join([
            'ocpiremote {}'.format(verb), 
            '-i {}'.format(platform.ip),
        ])

    raise ValueError('Unknown verb: {}'.format(verb))


def make_rules(platform, host_platform=None):
    """Makes rules to control when a job is executed in a pipeline

    Calls make_host_rules() if platform is a host_platform, or calls
    make_cross_rules() if platform is not a host_platform

    Args:
        platform:        Platform of job to make rules for
        host_platform:   Host_platform of job if platform to make rules
                         for if not a host_platform
        linked_platform: Associated platform of job to make rules for

    Returns:
        dictionary of rule strings
    """
    if os.getenv('CI_PIPELINE_ID'):
        return None

    if host_platform:
        return make_trigger_rules(platform, host_platform)
        
    return make_job_rules(platform)


def make_job_rules(platform):
    """Makes rules to control when a job is executed in a pipeline

    Args:
        platform: Platform of job to make rules for

    Returns:
        dictionary of rule strings
    """

    # PyYAML is finicky about keeping quotes in the output yaml.
    # Simplest way I can get it to surround output in quotes is by
    # adding an extra space at the end.
    return [
        {'if': 
            # If platform in CI_PLATFORMS env var and pipeline source
            # is a scheduled pipeline
            (r'$CI_PLATFORMS =~ /(^| )({})( |$)/i'
             r' && $CI_PIPELINE_SOURCE == "schedule"'
             r' ').format(platform.name)
        },
        {'if':
            # If platform in CI_PLATFORMS env var and pipeline source
            # is gitlab web UI 
            (r'$CI_PLATFORMS =~ /(^| )({})( |$)/i'
             r' && $CI_PIPELINE_SOURCE == "web"'
             r' ').format(platform.name)
        },
        {'if':
            # If platform in CI_MR_PLATFORMS env var and pipeline source
            # is a merge request
            (r'$CI_MR_PLATFORMS =~ /(^| )({})( |$)/i'
             r' && $CI_PIPELINE_SOURCE == "merge_request_event"'
             r' ').format( platform.name)
        },
        {'if':
            # If platform in CI_COMMIT_MESSAGE env var and pipeline source
            # is a push 
            (r'$CI_COMMIT_MESSAGE =~ /\[ *ci *( \S*)* +({})( \S*)*\]/i'
             r' && $CI_PIPELINE_SOURCE == "push"'
             r' ').format(platform.name)
        },
        {'if':
            # If platform in CI_PLATFORMS env var, '[ci *]' directive
            # not in CI_COMMIT_MESSAGE env var, and pipeline source
            # is a push 
            (r'$CI_PLATFORMS =~ /(^| )({})( |$)/i'
             r' && $CI_COMMIT_MESSAGE !~ /\[ *ci.*\]/i'
             r' && $CI_PIPELINE_SOURCE == "push"'
             r' ').format(platform.name)
        }
    ]


def make_trigger_rules(platform, host_platform):
    """Makes rules to control when a trigger is executed in a pipeline

    Args:
        platform:       Platform of job to make rules for
        host_platform:  Host_platform of job to make rules for

    Returns:
        dictionary of rule strings
    """

    # Rules are the same as above with addition of a check for host_platform
    # matching same condition as platform
    return [
        {'if': 
            (r'$CI_PLATFORMS =~ /(^| )({})( |$)/i'
             r' && $CI_PLATFORMS =~ /(^| |:|,)({})( |:|,|$)/i'
             r' && $CI_PIPELINE_SOURCE == "schedule"'
             r' ').format(host_platform.name, platform.name)
        },
        {'if': 
            (r'$CI_PLATFORMS =~ /(^| )({})( |$)/i'
             r' && $CI_PLATFORMS =~ /(^| |:|,)({})( |:|,|$)/i'
             r' && $CI_PIPELINE_SOURCE == "web"'
             r' ').format(host_platform.name, platform.name)
        },
        {'if': 
            (r'$CI_MR_PLATFORMS =~ /(^| )({})( |$)/i'
             r' && $CI_MR_PLATFORMS =~ /(^| |:|,)({})( |:|,|$)/i'
             r' && $CI_PIPELINE_SOURCE == "merge_request_event"'
             r' ').format(host_platform.name, platform.name)
        },
        {'if': 
            (r'$CI_COMMIT_MESSAGE =~ /\[ *ci *( \S*)* +({})( \S*)*\]/i'
             r' && $CI_COMMIT_MESSAGE =~ /\[ *ci *( \S*)*( +|:|,)({})(( |:|,)\S*)*\]/i'
             r' && $CI_PIPELINE_SOURCE == "push"'
             r' ').format(host_platform.name, platform.name)
        },
        {'if':
            (r'$CI_PLATFORMS =~ /(^| )({})( |$)/i'
             r' && $CI_PLATFORMS =~ /(^| |:|,)({})( |:|,|$)/i'
             r' && $CI_COMMIT_MESSAGE !~ /\[ *ci.*\]/i'
             r' && $CI_PIPELINE_SOURCE == "push"'
             r' ').format(host_platform.name, platform.name)
        }
    ]


def stage_from_library(library):
    """Gets the stage of job based on its library

    Args:
        library: Library of job

    Returns:
        stage string of job

    Raises:
        ValueError: if unrecognized library passed
    """

    if library.name in ['platforms', 'assemblies']:
        return 'build-{}'.format(library.name)
    
    if (library.name in ['components', 'adapters', 'cards', 'devices']
            or library.path.parent.stem == 'components'):
        return 'build-libraries'

    if library.name == 'primitives':
        if library.project_name == 'core':
            return 'build-primitives-core'
        else:
            return 'build-primitives'

    raise ValueError('Unable to get stage from library {}'.format(library.name))