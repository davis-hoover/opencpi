#!/usr/bin/env python3

from . import ci_job, ci_gitlab


def trigger_project(project, pipeline, stage='trigger-projects', 
                    overrides=None):
    """ Creates a trigger job to launch a pipeline for a project

    Creates a trigger to launch a pipeline in a remote gitlab project.
    Calls get_downstream_branch to find matching downstream branch name 
    to trigger.

    Args:
        project:        Project to trigger
        pipeline:       Pipeline to make job for
        stage:          Stage for job to run in        
        generate_job:   The job that generates the yaml to be used by
                        the trigger
        overrides:      Dictionary of overrides for the job

    Returns:
        Job
    """
    name = project.name
    project_trigger = project.url.replace('.git', '').replace(
        'https://gitlab.com/', '')
    project_id = project.id

    # Set trigger
    trigger = {}
    trigger['project'] = project_trigger
    trigger['branch'] = ci_gitlab.get_downstream_branch(project_id, 
                                                        pipeline.ci_env)
    if pipeline.ci_env.pipeline_source != 'schedule':
        # Pipeline is scheduled, don't have pipeline depend on triggered
        # pipelines. That way later stages may progress when prior fail
        trigger['strategy'] = 'depend'

    # Set variables
    variables = {}
    variables['CI_DIRECTIVE'] = pipeline.directive.str
    if pipeline.group_name == 'opencpi':
        variables['CI_OCPI_REF'] = pipeline.ci_env.commit_ref_name
    elif pipeline.group_name == 'osp':
        variables['CI_OSP_REF'] = pipeline.ci_env.commit_ref_name
        try:
            variables['CI_OCPI_REF'] = pipeline.ci_env.ocpi_ref
        except:
            pass
    try:
        variables['CI_ROOT_ID'] = pipeline.ci_env.root_id
    except:
        variables['CI_ROOT_ID'] = pipeline.ci_env.pipeline_id
    try:
        variables['CI_UPSTREAM_ID'] = pipeline.ci_env.root_id
    except:
        variables['CI_UPSTREAM_ID'] = pipeline.ci_env.pipeline_id

    job = ci_job.Job(name, stage=stage, trigger=trigger, overrides=overrides,
                     variables=variables)

    return job


def trigger_platform(host_platform, cross_platform, pipeline, 
                     generate_job=None):
    """Creates a trigger job to launch a pipeline for a platform

    Creates a trigger for a child pipeline if platform is local or calls
    trigger_project() if platform is remote. Calls make_name() to get 
    name for Job. 

    Args:
        host_platform:  Host platform of child pipeline to be triggered
        cross_platform: Platform to be built/tested in child pipeline
        pipeline:       Pipeline to make job for        
        generate_job:   The job that generates the yaml to be used by
                        the trigger

    Returns:
        Job
    """
    stage = 'trigger-platforms'
    overrides = pipeline.get_platform_overrides(cross_platform)

    if cross_platform.project.path or pipeline.group_name == 'comp':
    # Platform is local; make job to trigger child pipeline
        if not generate_job:
            raise Exception(
                'A generate job must be passed for triggering child pipelines')

        name = ci_job.make_name(cross_platform, host_platform=host_platform)

        # Set include
        artifacts = generate_job.artifacts['paths']
        include = []
        for artifact in artifacts:
            include.append({
                'artifact': str(artifact),
                'job': generate_job.name
            })

        # Set trigger
        trigger = {}
        trigger['include'] = include
        if pipeline.ci_env.pipeline_source != 'schedule':
            # Pipeline is scheduled, don't have pipeline depend on triggered
            # pipelines. That way later stages may progress when prior fail
            trigger['strategy'] = 'depend'

        job = ci_job.Job(name, stage=stage, trigger=trigger, 
                         overrides=overrides)
    else:
    # Platform is remote; make job to trigger downstream pipeline
        job = trigger_project(cross_platform.project, pipeline, 
                              stage=stage, overrides=overrides)

    return job