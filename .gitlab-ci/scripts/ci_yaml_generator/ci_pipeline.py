#!/usr/bin/env python3

import yaml
from collections import namedtuple
from pathlib import Path
from .ci_job import to_dict as job_to_dict

Pipeline = namedtuple('pipeline', 'jobs, stages, include')


def make_pipeline(jobs, stages=None, include=None):
    return Pipeline(jobs, stages, include)


def to_dict(pipeline):
    pipeline_dict = {}

    if pipeline.stages:
        pipeline_dict['stages'] = pipeline.stages

    if pipeline.include:
        pipeline_dict['include'] = pipeline.include

    for job in pipeline.jobs:
        pipeline_dict[job.name] = job_to_dict(job)

    return pipeline_dict


def dump(pipeline_dict, path):
    if isinstance(pipeline_dict, Pipeline):
        pipeline_dict = to_dict(pipeline_dict)

    parents = [parent for parent in path.parents]
    for parent in parents[::-1]:
        parent.mkdir(exist_ok=True)

    with open(path, 'w+') as outfile:
        yaml.safe_dump(pipeline_dict, outfile, width=1000, default_flow_style=False)