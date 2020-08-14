#!/usr/bin/env python3

class Job():

    def __init__(self, name, stage, script=None, 
                 before_script=None, after_script=None, 
                 artifacts=None, tags=None,
                 resource_group=None, trigger=None,
                 rules=None):
        self.stage = stage
        self.name = name
        self.script = script
        self.before_script = before_script
        self.after_script = after_script
        self.artifacts = artifacts
        self.tags = tags
        self.resource_group = resource_group
        self.trigger = trigger
        self.rules = rules

    def to_dict(self):
        job_dict = {}

        for key,value in self.__dict__.items():
            if key != 'name' and value is not None:
                job_dict[key] = value
        
        return job_dict