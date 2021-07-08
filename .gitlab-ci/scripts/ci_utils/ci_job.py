#!/usr/bin/env python3

import os
import yaml
from collections import namedtuple
from json import load
from pathlib import Path
from urllib.request import urlopen
from . import ci_gitlab

        
_Job = namedtuple('job', 'name stage script before_script after_script'
                         ' artifacts tags resource_group'
                         ' variables dependencies image trigger')


def Job(name, stage=None, script=None, before_script=None, 
        after_script=None, artifacts=None, tags=None, resource_group=None, 
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
        variables:      Dictionary of variables to set when job runs in
                        pipeline
        dependencies:   List of job names a job should download gitlab
                        artifacts from (NOT AWS)
        image:          Docker image for job to run in
        trigger:        Child pipeline to trigger
        overrides:      Dictionary of overrides for the job

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
        if overrides and key in overrides and key != 'variables':
            job_args[key] = overrides[key]
        elif key != 'overrides':
            job_args[key] = value

    if overrides and 'variables' in overrides:
        if 'variables' in job_args and job_args['variables']:
            for key,val in overrides['variables'].items():
                job_args['variables'][key] = val
        else:
            job_args['variables'] = overrides['variables']

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


def make_jobs(stages, platform, projects, pipeline, host_platform=None):
    """Creates Job(s) for project/platform combinations

    Calls either make_hdl_jobs() or make_rcc_jobs() based on model
    of platform.

    Args:
        stages:        List of pipeline stages
        platform:      Platform to make jobs for
        projects:      List of projects to make jobs for
        pipeline:      Pipeline to create jobs for
        host_platform: Host platform to create jobs for

    Returns:ocpiremote
        Jobs: collection containing data necessary to create jobs in a
              pipeline

    Raises:
        ValueError: if platform model is neither 'rcc' nor 'hdl'
    """
    if platform.model == 'hdl':
        return make_hdl_jobs(stages, platform, projects, pipeline, 
                             host_platform=host_platform)
    elif platform.model == 'rcc':
        return make_rcc_jobs(stages, platform, projects, pipeline,
                             host_platform=host_platform)
    else:
        raise ValueError('Unknown model: {}'.format(platform.model))


def make_rcc_jobs(stages, platform, projects, pipeline, host_platform=None):
    """Creates Job(s) for project/platform combinations of model 'rcc'

    Determines arguments to pass to make_job().

    Args:
        stages:        List of pipeline stages
        platform:      Platform to make jobs for
        projects:      List of projects to make jobs for
        pipeline:      Pipeline to create jobs for
        host_platform: Host platform to create jobs for

    Returns:
        Jobs: collection containing data necessary to create jobs in a
              pipeline
    """
    jobs = []

    for stage in stages:
        if stage in ['generate-children', 'trigger-platforms', 
                     'trigger-projects', 'deploy']:
            continue
        
        if stage in ['build-assets', 'build-assets-comp', 'build-assemblies']:
            for project in projects:
                for asset in project.assets:
                    if stage == 'build-assemblies':
                        if asset.is_testable:
                            name = make_name(platform, project=project, 
                                            stage='build-tests',
                                            host_platform=host_platform, 
                                            asset=asset)
                            build_test_job = make_job(
                                pipeline, stage, stages, platform, name=name, 
                                project=project, host_platform=host_platform,
                                asset=asset)
                            if build_test_job:
                                jobs.append(build_test_job)
                    elif stage in ['build-assets', 'build-assets-comp']:
                        if asset.path.parent.stem != 'components':
                            continue
                        job = make_job(pipeline, stage, stages, platform, 
                                       project=project, 
                                       host_platform=host_platform, 
                                       asset=asset)
                        if job:
                            jobs.append(job)
        else:
            job = make_job(pipeline, stage, stages, platform,
                           host_platform=host_platform)
            if job:
                jobs.append(job)

        if stage == 'prereqs' and not pipeline.is_downstream:
            name = make_name(platform, stage='packages')
            job = make_job(pipeline, stage, stages, platform, name=name)
            if job:
                jobs.append(job)

    return jobs


def make_hdl_jobs(stages, platform, projects, pipeline, host_platform=None):
    """Creates Job(s) for project/platform combinations of model 'hdl'

    Determines arguments to pass to make_job().

    Args:
        stages:        List of pipeline stages
        platform:      Platform to make jobs for
        projects:      List of projects to make jobs for
        pipeline:      Pipeline to create jobs for
        host_platform: Host platform to create jobs for

    Jobs: collection containing data necessary to create jobs in a
          pipeline
    """
    jobs = []
    
    for project in projects:
        if project.name == platform.project.name:
            assets = project.assets + platform.assets
        else:
            assets = project.assets

        for asset in assets:
            if asset.is_buildable:
                stage = get_asset_stage(asset, project)
                if stage not in stages:
                    continue

                job = make_job(pipeline, stage, stages, platform, 
                               project=project, host_platform=host_platform, 
                               asset=asset)
                if job:
                    jobs.append(job)

            if asset.is_testable:
                name = make_name(platform, project=project, 
                                 stage='build-tests',
                                 host_platform=host_platform, asset=asset)
                build_test_job = make_job(pipeline, 'build-assemblies', stages, 
                                          platform, name=name, project=project,
                                          asset=asset, 
                                          host_platform=host_platform)
                if build_test_job:
                    jobs.append(build_test_job)

                if platform.is_sim:
                    run_test_job = make_job(pipeline, 'test', stages, platform,
                                            project=project, asset=asset,
                                            host_platform=host_platform)
                    if run_test_job:
                        jobs.append(run_test_job)

                if not platform.ip or not platform.port:
                    continue

                for linked_platform in platform.linked_platforms:
                    run_test_job = make_job(pipeline, 'test', stages, platform,
                                            project=project, asset=asset,
                                            host_platform=host_platform,
                                            linked_platform=linked_platform,
                                            do_ocpiremote=True)
                    if run_test_job:
                        jobs.append(run_test_job)

    for linked_platform in platform.linked_platforms:
        job = make_job(pipeline, 'build-sdcards', stages, platform,
                       host_platform=host_platform,
                       linked_platform=linked_platform)
        if job:
            jobs.append(job)

    return jobs


def make_generate(host_platform, cross_platform, pipeline):
    """Creates a job to generate a yaml fie for a child pipeline

    Calls make_name() and make_before_script() to get attributes to pass
    for construction of Job.

    Args:
        host_platform:  Host platform of child pipeline to be triggered
        cross_platform: Platform to be built/tested in child pipeline
        pipeline:       Pipeline to make job for

    Returns:
        Job
    """
    script = ['.gitlab-ci/scripts/ci_yaml_generator.py']
    artifacts = {'paths': [str(pipeline.path)]}
    tags = ['docker']
    image = 'centos:7'
    stage = 'generate-children'
    name = make_name(cross_platform, stage=stage, host_platform=host_platform)
    before_script = [        
        'yum install epel-release -y',
        'yum install python36-PyYAML -y',
        'yum install git -y'
    ]
    before_script += make_before_script(pipeline, stage, [], cross_platform)
    variables = {}
    variables['CI_DIRECTIVE'] = pipeline.directive.str
    variables['CI_PLATFORM'] = cross_platform.name
    variables['CI_HOST_PLATFORM'] = host_platform.name

    try:
        variables['CI_ROOT_ID'] = pipeline.ci_env.root_id
    except:
        variables['CI_ROOT_ID'] = pipeline.ci_env.pipeline_id
    
    try:
        variables['CI_UPSTREAM_ID'] = pipeline.ci_env.upstream_id
    except:
        pass
    try:
        variables['CI_OCPI_REF'] = pipeline.ci_env.ocpi_ref
    except:
        pass
    try:
        variables['CI_OSP_REF'] = pipeline.ci_env.osp_ref
    except:
        pass
    
    if pipeline.ci_env.project_name != 'opencpi':
        variables['GIT_STRATEGY'] = 'none'
    
    overrides = pipeline.get_platform_overrides(cross_platform)
    job = Job(name, stage=stage, script=script, tags=tags, 
              image=image, variables=variables, before_script=before_script, 
              artifacts=artifacts, overrides=overrides)

    return job


def make_job(pipeline, stage, stages, platform, project=None, name=None,
             host_platform=None, asset=None, linked_platform=None,
             overrides=None, config=None, do_ocpiremote=False):
    """Creates Job for project/platform combinations

    Calls before_script(), after_script(), script(), and if
    necessary, make_name() to get arguments for construction of a Job.

    Args:
        pipeline:        Pipeline to create jobs for
        stage:           Stage of pipeline for job to execute in
        stages:          List of pipeline stages
        platform:        Platform to make jobs for
        project:         Project to make jobs for
        name:            Name of job
        host_platform:   Host platform to create jobs for
        asset:           Asset to make job for
        linked_platform: List of platforms needed for making jobs
                         requiring an associated rcc platform
        overrides:       Dictionary to override standard job values
        config:          Dictionary of configs
        do_ocpiremote:   Whether jobs should run ocpiremote commands

    Returns:
        Job: contains data necessary to create a job in a pipeline
    """
    if not name:
        name = make_name(platform, stage=stage, project=project,
                         host_platform=host_platform,
                         linked_platform=linked_platform, asset=asset)

    before_script = make_before_script(pipeline, stage, stages, platform,
                                       host_platform=host_platform,
                                       linked_platform=linked_platform,
                                       do_ocpiremote=do_ocpiremote)
    script = make_script(stage, platform, project=project, asset=asset,
                         linked_platform=linked_platform, name=name)
    after_script = make_after_script(pipeline, platform, 
                                     do_ocpiremote=do_ocpiremote)
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

    if pipeline.project_name != 'opencpi':
        variables = {'GIT_STRATEGY': 'none'}
    else:
        variables = None

    overrides = pipeline.get_platform_overrides(platform)
    job = Job(name, stage, script, tags=tags, before_script=before_script, 
              after_script=after_script, resource_group=resource_group, 
              dependencies=dependencies, variables=variables, 
              overrides=overrides)

    return job


def make_name(platform, stage=None, project=None, host_platform=None,
              linked_platform=None, asset=None):
    """Creates a name for a job

    Args:
        platform:        Platform of job
        stage:           Stage of pipeline for job to execute in
        project:         Project of job
        host_platform:   Host_platform of job
        linked_platform: Associated platform for jobs requiring both an
                         'hdl' and an 'rcc' platform
        asset:         asset for jobs that build/test for a specific
                         asset

    Returns:
        name of job string
    """
    elems = [host_platform, project, asset, linked_platform, platform]
    name_elems = [stage] if stage else []
    name_elems += [elem.name for elem in elems if elem]

    return ':'.join(name_elems)


def make_before_script(pipeline, stage, stages, platform, host_platform=None,
                       linked_platform=None, do_ocpiremote=False):
    """Creates list of commands to run in job's before_script step

        Constructs commands for downloading AWS artifacts, creating
        timestamp, and sourcing opencpi.

    Args:
        pipeline:        Pipeline to make job for
        stage:           Stage of pipeline for job to execute in.
                         Used to exclude artifacts in same and later
                         stages
        stages:          List of all pipeline stages
        platform:        Platform to download artifacts for
        host_platform:   Host_platform to download artifacts for
        linked_platform: Associated platform to download artifacts 
                         for
        do_ocpiremote:   Whether job should run ocpiremote commands

    Returns:
        list of command strings
    """
    cmds = []

    pipeline_id = os.getenv("CI_UPSTREAM_ID")
    clean_cmd = 'rm -rf * .* 2>/dev/null || true'
    
    if pipeline_id:
    # In triggered pipeline
        ocpi_ref = pipeline.ci_env.ocpi_ref
        do_clone = True
        do_register = True
        cmds.append(clean_cmd)
    else:
    # In non-triggered pipeline
        pipeline_id = os.getenv("CI_ROOT_ID")

        if not pipeline_id:
            pipeline_id = os.getenv("CI_PIPELINE_ID")

        if pipeline.project_name == 'opencpi':
        # In opencpi project
            do_clone = False
            do_register = False
        else:
        # In downstream project
            ocpi_ref = ci_gitlab.get_upstream_branch()
            do_clone = True
            cmds.append(clean_cmd)

            if platform.is_host:
                do_register = False
            else:
                do_register = True

    if do_clone:
        # Clone opencpi repo
        cmd = ' '.join(['git clone --depth 1 --single-branch --branch',
                        ocpi_ref,
                        '"https://gitlab.com/opencpi/opencpi.git"', 
                        'opencpi'])
        cmds.append(cmd)

        if (platform.project.group == 'osp' 
            and (pipeline.group_name != 'comp' 
                 or stage != 'generate-children')):
            # If the platform is an osp, clone the osp's repo
                
            path = '/'.join(['opencpi', 'projects', 'osps',
                            platform.project.name])
            path = '"{}"'.format(path)

            if pipeline.project_name == platform.project.name:
            # Platform belongs to this project, so clone this project
                url = pipeline.ci_env.repository_url
                osp_ref = pipeline.ci_env.commit_ref_name
            else:
            # Platform is remote, so clone its project
                url = platform.project.url
                try:
                    osp_ref = pipeline.ci_env.osp_ref
                except:
                    osp_ref = 'develop'

            cmd = ' '.join(['git clone --depth 1 --single-branch --branch', 
                            osp_ref, url, path])
            cmds.append(cmd)

        if pipeline.group_name == 'comp':
        # If pipeline is in a comp project also clone its repo
            path = '/'.join(['opencpi', 'projects', pipeline.group_name,
                            pipeline.project_name])
            path = '"{}"'.format(path)
            cmd = ' '.join(['git clone --depth 1 --single-branch --branch', 
                            pipeline.ci_env.commit_ref_name, 
                            pipeline.ci_env.repository_url,
                            path])

            cmds.append(cmd)
        
        cmds.append('cd opencpi')

    timestamp_cmd = 'touch .timestamp'
    cmds.append(timestamp_cmd)
    
    if stage in ['prereqs', 'generate-children']:
        return cmds

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
    cmds += [download_cmd, sleep_cmd, timestamp_cmd]
    
    if stage == 'build':
        return cmds

    source_cmd = 'source cdk/opencpi-setup.sh -e'
    cmds.append(source_cmd)

    if do_register:
        if platform.project.group == 'osp':
        # Platform is an osp, register its project
            path = '/'.join(['projects', 'osps', 
                             platform.project.name])
            path = '"{}"'.format(path)
            register_cmd = make_ocpidev_cmd(
                'register', path=path, noun='project')
            cmds.append(register_cmd)

        if pipeline.group_name == 'comp':
        # Pipeline is in comp project, register comp project
            path = '/'.join(['projects', pipeline.group_name, 
                             pipeline.project_name])
            path = '"{}"'.format(path)
            register_cmd = make_ocpidev_cmd(
                'register', path=path, noun='project')
            cmds.append(register_cmd)
    
    if do_ocpiremote:
        # Set up hash to look up interface for runner from within job
        runners = pipeline.config['ci']['runners']
        interfaces_cmd = ' && '.join(['declare -A interfaces',
                                      'interfaces=('])
        for runner_id,runner_configs in runners.items():
            interfaces_cmd += ' ["{}"]="{}"'.format(
                runner_id, runner_configs['socket_interface'])
        interfaces_cmd += ')'
        
        if platform.do_deploy:
            cmds +=[
                make_ocpiremote_cmd('deploy', platform,
                                    linked_platform=linked_platform),
                'sleep 60'
            ]

        cmds += [
            make_ocpiremote_cmd('load', platform,
                                linked_platform=linked_platform),
            make_ocpiremote_cmd('start', platform,
                                linked_platform=linked_platform),
            # temporarily disable log retrieval here until the
            # log command can be executed in the background.
            # make_ocpiremote_cmd('log', platform,
            #                     linked_platform=linked_platform),
            interfaces_cmd,
            'export OCPI_SOCKET_INTERFACE="${interfaces[$CI_RUNNER_ID]}"',
            'echo "${OCPI_SOCKET_INTERFACE}"',
            'export OCPI_SERVER_ADDRESSES={}:{}'.format(platform.ip,
                                                        platform.port)
        ]

    return cmds


def make_after_script(pipeline, platform, do_ocpiremote=False):
    """Creates list of commands to run in job's after_script step

        Constructs command for uploading opencpi tree to AWS if job
        failed, and cleans entire project directory as final cmd.

    Args:
        pipeline:      Pipeline to make job for
        platform:      Platform of job
        do_ocpiremote: Whether jobs should run ocpiremote commands

    Returns:
        list of command strings
    """
    cmds = []
    script_path = '.gitlab-ci/scripts/ci_artifacts.py'
    success_path = Path('.success')

    pipeline_id = os.getenv("CI_UPSTREAM_ID")
    if not pipeline_id:
        pipeline_id = os.getenv("CI_ROOT_ID")
    if not pipeline_id:
        pipeline_id = os.getenv("CI_PIPELINE_ID")

    cmds.append('date')

    if pipeline.is_downstream:
        cmds.append('cd opencpi')

    job_name = '"$CI_JOB_NAME"'
    upload_cmd = ' '.join(['if [ ! -f "{}" ];'.format(success_path),
                           'then {} upload'.format(script_path),
                           pipeline_id, job_name,
                           '-t "failed-job"; fi'])
    cmds.append(upload_cmd)

    if do_ocpiremote:
        cmds.append('source cdk/opencpi-setup.sh -e')
        cmds.append(make_ocpiremote_cmd('stop', platform) + " || true")
        # temporarily retrieve log here
        cmds.append(make_ocpiremote_cmd('log', platform))
        cmds.append(make_ocpiremote_cmd('unload', platform))

    clean_cmd = 'rm -rf * .* 2>/dev/null || true'
    cmds.append(clean_cmd)

    return cmds


def make_script(stage, platform, project=None, linked_platform=None,
                asset=None, name=None):
    """Creates list of commands to run in job's script step

        Constructs commands for downloading AWS artifacts, creating
        timestamp, and sourcing opencpi.

    Args:
        stage:           Stage of pipeline for job to execute in
        platform:        Platform of job
        project:         Project of job
        linked_platform: Associated platform for jobs requiring both an
                         'hdl' and an 'rcc' platform
        asset:           asset for jobs that build/test for a specific
                         asset
        name:            Name of job in pipeline

    Returns:
        list of command strings
    """
    pipeline_id = os.getenv("CI_UPSTREAM_ID")
    if not pipeline_id:
        pipeline_id = os.getenv("CI_ROOT_ID")
    if not pipeline_id:
        pipeline_id = os.getenv("CI_PIPELINE_ID")

    job_name = '"$CI_JOB_NAME"'
    upload_cmd = ' '.join(['.gitlab-ci/scripts/ci_artifacts.py upload',
                           pipeline_id, job_name,
                           '-s .timestamp -t "successful-job"'])
    success_cmd = 'touch .success'
    cmds = []

    if stage == 'test':
        if platform.is_host:
            cmd = make_scripts_cmd(stage, platform)
        else:
            cmd = make_ocpidev_cmd('run', platform, asset.path,
                                   noun='tests')
    elif stage == 'build-assemblies' and asset.name != 'assemblies':
        cmd = make_ocpidev_cmd('build', platform, asset.path, noun='test')
    elif stage in ['build-assets', 'build-assets-comp']:
        cmd = make_ocpidev_cmd('build', platform, asset.path)
    elif platform.model == 'hdl':
        if stage == 'build-platforms':
            cmd = make_ocpidev_cmd('build', platform, project.path,
                                   'hdl platforms')
        elif stage == 'build-sdcards':
            cmd = ('cdk/scripts/export-platform-to-framework.sh' 
                   ' -v hdl {} {}/lib'.format(platform.name, platform.path))
            cmds.append(cmd)
            cmd = make_ocpiadmin_cmd('deploy', platform, linked_platform)
        else:
            cmd = make_ocpidev_cmd('build', platform, asset.path)
    else:
        cmd = make_scripts_cmd(stage, platform, name=name)

    cmds += [cmd, upload_cmd, success_cmd]

    return cmds


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

    if stage in ['prereqs', 'prereqs-rcc']:
        if name and name.startswith('packages'):
            return 'scripts/install-packages.sh {}'.format(platform.name)
        else:
            return 'scripts/install-prerequisites.sh {}'.format(platform.name)

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


def make_ocpidev_cmd(verb, platform=None, path=None, noun=''):
    """Makes ocpidev command

    Args:
        verb:     String to pass to ocpidev
        platform: Platform of job to pass to ocpidev
        path:     Path to noun
        noun:     Noun to pass to ocpidev

    Returns:
        ocpidev command string

    Raises:
        ValueError: if unrecognized verb or noun provided
    """
    if noun and noun not in ['tests', 'test', 'hdl platforms', 'project']:
        raise ValueError('Unknown noun: {}'.format(noun))

    if verb == 'build':
        return ' '.join([
            'ocpidev build',
            noun,
            '-d {}'.format(path),
            '--{}-platform {}'.format(platform.model, platform.name)
        ])

    if verb == 'run':
        return ' '.join([
            'ocpidev run',
            noun,
            '-d {}'.format(path),
            '--only-platform {}'.format(platform.name),
            '--mode prep_run_verify'
        ])

    if verb == 'register':
        return ' '.join([
            'ocpidev register',
            noun,
            '"{}"'.format(path)
        ])

    raise ValueError('Unknown verb: {}'.format(verb))


def make_ocpiremote_cmd(verb, platform, linked_platform=None):
    """Makes ocpiremote command

    Args:
        verb:            String to pass to ocpiremote
        platform:        Platform of job to pass to ocpiremote
        linked_platform: Associated platform to pass to ocpiremote

    Returns:
        ocpiremote command string

    Raises:
        ValueError: if unrecognized verb provided
    """
    if verb == 'deploy':
        cmd = ' '.join([
            'ocpiremote deploy',
            '-i {}'.format(platform.ip),
            '-w {}'.format(platform.name),
            '-s {}'.format(linked_platform.name)
        ])

    if verb == 'load':
        cmd = ' '.join([
            'ocpiremote load',
            '-i {}'.format(platform.ip),
            '-r {}'.format(platform.port),
            '-w {}'.format(platform.name),
            '-s {}'.format(linked_platform.name)
        ])

    if verb in ['start', 'unload', 'stop', 'log']:
        cmd = ' '.join([
            'ocpiremote {}'.format(verb),
            '-i {}'.format(platform.ip),
        ])

        if verb == 'start':
            cmd += (' -b')
            cmd += ' -l 10'

    if platform.password:
        cmd += (' -p {}'.format(platform.password))

    if platform.user:
        cmd += (' -u {}'.format(platform.user))

    if verb not in ['deploy', 'load', 'start', 'unload', 'stop', 'log']:
        raise ValueError('Unknown verb: {}'.format(verb))
 
    return cmd


def get_asset_stage(asset, project):
    """Gets the stage of job based on its Asset and Project

    Args:
        asset:   Asset of job
        project: Project of job

    Returns:
        stage string of job

    Raises:
        ValueError: if unrecognized asset passed
    """
    asset_name = asset.name.split(':')[-1]

    if asset_name in ['platforms', 'assemblies']:
        return 'build-{}'.format(asset_name)

    if (asset_name in ['components', 'adapters', 'cards', 'devices']
            or asset.path.parent.stem == 'components'):
        if project.group == 'opencpi':
            return 'build-assets'
        elif project.group == 'osp':
            return 'build-assets-{}'.format(project.name)
        elif project.group == 'comp':
            return 'build-assets-comp'
        
    if asset_name == 'primitives':
        if project.name == 'core':
            return 'build-primitives-core'
        else:
            return 'build-primitives'

    raise ValueError('Unable to get stage from asset: ', asset.name)
