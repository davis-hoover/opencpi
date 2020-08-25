#!/usr/bin/env python3

import yaml
from collections import namedtuple
from .ci_platform import get_rcc_platforms


def to_dict(jobs):
    """Converts Job namedtuple(s) to a dictionary

    Args:
        jobs: A single Job namedtuple or list of Job namedtuples to
              convert into a dictionary

    Returns:
        jobs_dict: A dictionary conversion of Job namedtuples
    """
    if not isinstance(jobs, list):
        jobs = [jobs]

    jobs_dict = {}
    for job in jobs:
        job_dict = {}
        for key,value in job._asdict().items():
            if key != 'name' and value is not None:
                job_dict[key] = value
        jobs_dict[job.name] = job_dict
    
    return jobs_dict


def dump(jobs_dict, path):
    """Outputs a dictionary to a yaml file

    Args:
        jobs_dict:  Dictionary to output to a yaml file
        path:       Path of output file
    """
    if not isinstance(jobs_dict, dict):
        jobs_dict = to_dict(jobs_dict)

    parents = [parent for parent in path.parents]
    for parent in parents[::-1]:
        parent.mkdir(exist_ok=True)

    yaml.SafeDumper.ignore_aliases = lambda *args : True

    with open(path, 'w+') as yml:
        yaml.safe_dump(jobs_dict, yml, width=1000, default_flow_style=False)


def Job(name, stage=None, script=None, before_script=None, after_script=None, 
        artifacts=None, tags=None, resource_group=None, rules=None, 
        variables=None, image=None, overrides=None):
    """Constructs a Job namedtuple

        namedtuples do not support default values in python versions
        prior to 3.7, so this helper function is used until the
        version of python opencpi uses is updated.

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
        image:          Docker image for job to run in
        overrides:      Dictionary to override standard values of above args

    Returns:
        Job namedtuple
    """
    args = locals()

    Job = namedtuple('job', 'name stage script before_script' 
                            ' after_script artifacts tags'
                            ' resource_group rules variables image')

    job_args = {}
    # If overrides were provided, collect them before constructing Job
    for key,value in args.items():
        if key in overrides:
            job_args[key] = overrides[key]
        elif key != 'overrides':
            job_args[key] = value

    return Job(**job_args)


def make_jobs(stages, platform, projects, platforms=None, host_platform=None, 
              overrides=None):
    """Creates Job namedtuple(s) for project/platform combinations

    Calls either make_hdl_jobs() or make_rcc_jobs() based on model
    of platform.

    Args:
        stages:         List of pipeline stages
        platform:       Platform to make jobs for
        projects:       List of projects to make jobs for
        host_platform:  Host platform to create jobs for
        overrides:      Dictionary to override standard job values

    Returns:
        Job namedtuples

    Raises:
        ValueError: if platform model is neither 'rcc' or 'hdl'
    """
    if platform.model == 'hdl':
        return make_hdl_jobs(stages, platform, projects, platforms, 
                             host_platform, overrides)
    elif platform.model == 'rcc':
        return make_rcc_jobs(stages, platform, projects, host_platform, 
                             overrides)
    else:
        raise ValueError('Unknown model: {}'.format(platform.model))


def make_rcc_jobs(stages, platform, projects, host_platform=None, 
                  overrides=None):
    """Creates Job namedtuple(s) for project/platform combinations of
        model 'rcc'

    Determines arguments to pass to make_job().

    Args:
        stages:         List of pipeline stages
        platform:       Platform to make jobs for
        projects:       List of projects to make jobs for
        host_platform:  Host platform to create jobs for
        overrides:      Dictionary to override standard job values

    Returns:
        Job namedtuples
    """
    jobs = []

    for stage in ['prereqs', 'build-rcc', 'build-host', 'test']:
        if stage == 'build-rcc' and platform.is_host:
            continue
        if stage == 'build-host' and not platform.is_host:
            continue

        if stage == 'test' and not platform.is_host:
            for project in projects:
                for library in project.libraries:
                    if library.is_testable:
                        job = make_job(stage, stages, platform, 
                                       project=project, library=library,
                                       host_platform=host_platform,
                                       overrides=overrides)
                        jobs.append(job)
        else:
            job = make_job(stage, stages, platform, 
                           host_platform=host_platform, overrides=overrides)
            jobs.append(job)

        if stage == 'prereqs' and platform.is_host:
            name = make_name('packages', platform)
            job = make_job(stage, stages, platform, name=name, 
                           overrides=overrides)
            jobs.append(job)

    return jobs


def make_hdl_jobs(stages, platform, projects, platforms, host_platform=None,
                  overrides=None):
    """Creates Job namedtuple(s) for project/platform combinations of
        model 'hdl'

    Determines arguments to pass to make_job().

    Args:
        stages:         List of pipeline stages
        platform:       Platform to make jobs for
        projects:       List of projects to make jobs for
        platforms:      List of platforms needed for making jobs
                        requiring an associated rcc platform
        host_platform:  Host platform to create jobs for
        overrides:      Dictionary to override standard job values

    Returns:
        Job namedtuples
    """
    jobs = []
    rcc_platforms = get_rcc_platforms(platforms)

    for project in projects:
        for library in project.libraries:

            if library.is_buildable:
                stage = stage_from_library(library)
                job = make_job(stage, stages, platform, project=project,
                               host_platform=host_platform, library=library,
                               overrides=overrides)
                jobs.append(job)

            if library.is_testable:
                name = make_name('build-tests', platform,project=project, 
                                 host_platform=host_platform, library=library)
                build_test_job = make_job('build-assemblies', stages, platform, 
                                          name=name, project=project, 
                                          host_platform=host_platform, 
                                          library=library, overrides=overrides)
                jobs.append(build_test_job)

                if platform.is_sim:
                    run_test_job = make_job('test', stages, platform, 
                                            project=project, library=library,
                                            host_platform=host_platform,
                                            overrides=overrides)
                    jobs.append(run_test_job)
                

    for rcc_platform in rcc_platforms:
        job = make_job('build-sdcards', stages, platform, 
                       host_platform=host_platform, 
                       linked_platform=rcc_platform, overrides=overrides)
        jobs.append(job)
    
    return jobs


def make_job(stage, stages, platform, 
             project=None, name=None, host_platform=None, library=None, 
             linked_platform=None, overrides=None):
    """Creates Job namedtuple(s) for project/platform combinations

    Calls before_script(), after_script(), script(), and if
    necessary, make_name() to get arguments for construction of a 
    Job namedtuple.

    Args:
        stage:          Stage of pipeline for job to execute in
        stages:         List of pipeline stages
        platform:       Platform to make jobs for
        projects:       List of projects to make jobs for
        platforms:      List of platforms needed for making jobs
                        requiring an associated rcc platform
        host_platform:  Host platform to create jobs for
        overrides:      Dictionary to override standard job values

    Returns:
        Job namedtuples
    """
    if not name:
        name = make_name(stage, platform, project, host_platform, 
                         linked_platform, library)

    if platform.is_host and name.startswith('packages'): 
        tags = ['docker']
        image = platform.image
        before_script = None
        after_script = None
        script = make_scripts_cmd(stage, platform, name)
    else:
        before_script = make_before_script(stage, stages, platform,
                                           host_platform=host_platform, 
                                           linked_platform=linked_platform)
        script = make_script(stage, platform, project=project, library=library, 
                            linked_platform=linked_platform, name=name)
        after_script = make_after_script()
        image = None

        if platform.is_host:
            if name.startswith('packages'): 
                tags = ['docker']
                image = platform.image
                after_script = None
                script = make_scripts_cmd(stage, platform, name)
            else:
                tags = [platform.name, 'shell', 'opencpi']
        elif platform.is_sim or (stage == 'test' and platform.model == 'hdl'):
            tags = [host_platform.name, platform.name, 'shell', 'opencpi']
        else:
            tags = [host_platform.name, 'shell', 'opencpi']

    rules = make_rules(platform, host_platform, linked_platform)

    job = Job(name, stage, script, tags=tags, before_script=before_script,
              after_script=after_script, rules=rules, image=image,
              overrides=overrides)

    return job


def make_name(stage, platform, project=None, host_platform=None, 
              linked_platform=None, library=None):
    """Creates a name for a Job namedtuple

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
                       linked_platform=None):
    """Creates list of commands to run in job's before_script step

        Constructs commands for downloading AWS artifacts, creating
        timestamp, and sourcing opencpi.

    Args:
        stage:           Stage of pipeline for job to execute in.
                         Used to exclude artifacts in same and later
                         stages
        platform:        Platform to download artifacts for
        host_platform:   Host_platform to download artifacts for
        linked_platform: Associated platform to downloaded artifacts for

    Returns:
        list of command strings
    """
    pipeline_id = '"$CI_PIPELINE_ID"'
    
    stage_idx = stages.index(stage)

    # Download artifacts for platform, host_platform, and linked_platform
    includes = ['"*{}.tar.gz"'.format(platform.name) 
                    for platform in [platform, host_platform, linked_platform] 
                    if platform]

    # Don't download artifacts in current or later stages
    excludes = ['"{}:*"'.format(stage) for stage in stages[stage_idx:]]

    download_cmd = ' '.join(['.gitlab-ci/scripts/ci_artifacts.py download',
                             pipeline_id,
                             '-i', ' '.join(includes),
                             '-e', ' '.join(excludes)])

    sleep_cmd = 'sleep 2'
    timestamp_cmd = 'touch .timestamp'
    source_cmd = 'source cdk/opencpi-setup.sh -e'

    if stage == 'prereqs':
        return [timestamp_cmd]
    if stage == 'build-host':
        return [download_cmd, sleep_cmd, timestamp_cmd]
    else:
        return [download_cmd, sleep_cmd, timestamp_cmd, source_cmd]


def make_after_script():
    """Creates list of commands to run in job's after_script step

        Constructs command for uploading opencpi tree to AWS if job
        failed, and cleans entire project directory as final cmd.

    Returns:
        list of command strings
    """
    pipeline_id = '"$CI_PIPELINE_ID"'
    job_name = '"$CI_JOB_NAME"'
    upload_cmd = ' '.join(['if [ ! -f ".success" ];', 
                           'then .gitlab-ci/scripts/ci_artifacts.py upload',
                           pipeline_id, job_name,
                           '-t "failed-job"; fi'])
    clean_cmd = 'rm -rf *'

    return [upload_cmd, clean_cmd]


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
    """
    if stage == 'test':
        return 'scripts/test-opencpi.sh --no-hdl'

    if stage == 'prereqs':
        if name.startswith('prereqs'):
            return 'scripts/install-prerequisites.sh {}'.format(platform.name)
        else:
            return 'scripts/install-packages.sh {}'.format(platform.name)

    if stage in ['build-host', 'build-rcc']:
        return 'scripts/build-opencpi.sh {}'.format(platform.name) 


def make_ocpiadmin_cmd(verb, platform, linked_platform=None):
    """Makes ocpiadmin command

    Args:
        verb:            String to pass to ocpiadmin
        platform:        Platform of job to pass to ocpiadmin
        linked_platform: Associated platform to pass to ocpiadmin

    Returns:
        ocpiadmin command string
    """
    if verb not in ['install', 'deploy']:
        raise Exception('Uknown verb: {}'.format(verb))

    if linked_platform:
        return 'ocpiadmin {} platform {} {}'.format(verb, 
                                                    linked_platform.name,
                                                    platform.name)

    return 'ocpiadmin {} platform {}'.format(verb, platform.name) 


def make_ocpidev_cmd(verb, platform, path, noun=None):
    """Makes ocpidev command

    Args:
        verb:     String to pass to ocpidev
        platform: Platform of job to pass to ocpidev
        path:     Path to pass with '-d' option to ocpidev
        noun:     Noun to pass to ocpidev

    Returns:
        ocpidev command string
    """
    if verb not in ['build', 'run']:
        raise Exception('Uknown verb: {}'.format(verb))
    
    if not noun:
        noun = ''
    elif noun not in ['tests', 'test', 'hdl platforms']:
        raise Exception('Uknown noun: {}'.format(noun))

    if verb == 'run':
        options = '-d {} --only-platform {} --mode prep_run_verify'.format(
            path, platform.name)
    else:
        options = '-d {} --hdl-platform {}'.format(path, platform.name)

    return 'ocpidev {} {} {}'.format(verb, noun, options)


def make_rules(platform, host_platform, linked_platform=None):
    """Makes rules to control when a job is executed in a pipeline

    Calls make_host_rules() if platform is a host_platform, or calls
    make_cross_rules() if platform is not a host_platform

    Args:
        platform:        Platform of job to make rules for
        host_platform:   Host_platform of job if platform to make rules
                         for if not a host_paltform
        linked_platform: Associated platform of job to make rules for

    Returns:
        dictionary of rule strings
    """
    if platform.is_host:
        return make_host_rules(platform)
    elif linked_platform:
        return make_linked_rules(platform, host_platform, linked_platform)

    return make_cross_rules(platform, host_platform)


def make_host_rules(platform):
    """Makes rules to control when a job is executed in a pipeline for
        host_platforms

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
            (r'$CI_COMMIT_MESSAGE =~ /\[ *ci *( \S*)*( +|:)({})(( |:)\S*)*\]/i'
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


def make_cross_rules(platform, host_platform):
    """Makes rules to control when a job is executed in a pipeline for
        platforms that are not host_platforms

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
             r' && $CI_PLATFORMS =~ /(^| |:)({})( |:|$)/i'
             r' && $CI_PIPELINE_SOURCE == "schedule"'
             r' ').format(host_platform.name, platform.name)
        },
        {'if': 
            (r'$CI_PLATFORMS =~ /(^| )({})( |$)/i'
             r' && $CI_PLATFORMS =~ /(^| |:)({})( |:|$)/i'
             r' && $CI_PIPELINE_SOURCE == "web"'
             r' ').format(host_platform.name, platform.name)
        },
        {'if': 
            (r'$CI_MR_PLATFORMS =~ /(^| )({})( |$)/i'
             r' && $CI_MR_PLATFORMS =~ /(^| |:)({})( |:|$)/i'
             r' && $CI_PIPELINE_SOURCE == "merge_request_event"'
             r' ').format(host_platform.name, platform.name)
        },
        {'if': 
            (r'$CI_COMMIT_MESSAGE =~ /\[ *ci *( \S*)*( +|:)({})(( |:)\S*)*\]/i'
             r' && $CI_COMMIT_MESSAGE =~ /\[ *ci *( \S*)*( +|:)({})(( |:)\S*)*\]/i'
             r' && $CI_PIPELINE_SOURCE == "push"'
             r' ').format(host_platform.name, platform.name)
        },
        {'if':
            (r'$CI_PLATFORMS =~ /(^| )({})( |$)/i'
             r' && $CI_PLATFORMS =~ /(^| |:)({})( |:|$)/i'
             r' && $CI_COMMIT_MESSAGE !~ /\[ *ci.*\]/i'
             r' && $CI_PIPELINE_SOURCE == "push"'
             r' ').format(host_platform.name, platform.name)
        }
    ]

def make_linked_rules(platform, host_platform, linked_platform):
    """Makes rules to control when a job is executed in a pipeline for
        jobs that have an associated platform

    Args:
        platform:        Platform of job to make rules for
        host_platform:   Host_platform of job to make rules for
        linked_platform: Associated platform of job to make rules for

    Returns:
        dictionary of rule strings
    """

    platform_link = ':'.join([platform.name, linked_platform.name])
    link_platform = ':'.join([linked_platform.name, platform.name])

    # Rules are the same as above with addition of a check for an
    # associated platform
    return [
        {'if': 
            (r'$CI_PLATFORMS =~ /(^| )({})( |$)/i'
             r' && $CI_PLATFORMS =~ /(^| )({}|{})( |$)/i'
             r' && $CI_PIPELINE_SOURCE == "schedule"'
             r' ').format(host_platform.name, platform_link, link_platform)
        },
        {'if': 
            (r'$CI_PLATFORMS =~ /(^| )({})( |$)/i'
             r' && $CI_PLATFORMS =~ /(^| )({}|{})( |$)/i'
             r' && $CI_PIPELINE_SOURCE == "web"'
             r' ').format(host_platform.name, platform_link, link_platform)
        },
        {'if': 
            (r'$CI_MR_PLATFORMS =~ /(^| )({})( |$)/i'
             r' && $CI_MR_PLATFORMS =~ /(^| )({}|{})( |$)/i'
             r' && $CI_PIPELINE_SOURCE == "merge_request_event"'
             r' ').format(host_platform.name, platform_link, link_platform)
        },
        {'if': 
            (r'$CI_COMMIT_MESSAGE =~ /\[ *ci *\S*( +|:)({})(( |:)\S*)*\]/i'
             r' && $CI_COMMIT_MESSAGE =~ /\[ *ci *( \S*)*( +|:)({}|{})(( |:)\S*)*\]/i'
             r' && $CI_PIPELINE_SOURCE == "push"'
             r' ').format(host_platform.name, platform_link, link_platform)
        },
        {'if':
            (r'$CI_PLATFORMS =~ /(^| )({})( |$)/i'
             r' && $CI_PLATFORMS =~ /(^| )({}|{})( |$)/i'
             r' && $CI_COMMIT_MESSAGE !~ /\[ *ci.*\]/i'
             r' && $CI_PIPELINE_SOURCE == "push"'
             r' ').format(host_platform.name, platform_link, link_platform)
        }
    ]


def stage_from_library(library):
    """Gets the stage of job based on its library

    Args:
        library: Library of job

    Returns:
        stage string of job
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

    raise Exception('Unable to get stage from library {}'.format(library.name))