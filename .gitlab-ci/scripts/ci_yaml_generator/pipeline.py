#!/usr/bin/env python3

import yaml

class Pipeline():
    
    def __init__(self, jobs, stages=None, include=None):
        self.jobs = jobs
        self.stages = stages
        self.include = include

    def to_dict(self):
        pipeline_dict = {}

        if self.stages:
            pipeline_dict['stages'] = self.stages

        if self.include:
            pipeline_dict['include'] = self.include

        for job in self.jobs:
            pipeline_dict[job.name] = job.to_dict()

        return pipeline_dict
    
    def dump(self, path, pipeline_dict=None):
        if not pipeline_dict:
            pipeline_dict = self.to_dict()

        with open(path, 'w+') as outfile:
            yaml.safe_dump(pipeline_dict, outfile, width=1000, default_flow_style=False)