#!/usr/bin/env python3

from . import ci_job

def trigger_platform(host_platform, cross_platform, pipeline, generate_job):
    """Creates a trigger job to launch a pipeline for a platform

    Creates a trigger for a child pipeline. Calls make_name() to get 
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
    trigger['strategy'] = 'depend'

    job = ci_job.Job(name, stage=stage, trigger=trigger, overrides=overrides)

    return job