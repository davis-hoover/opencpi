import yaml

class Pipeline():
    
    def __init__(self, jobs):
        self.jobs = jobs


    def to_dict(self):
        job_dict = {}

        for job in self.jobs:
            job_dict[job.name] = job.to_dict()

        return job_dict

    
    def dump(self, path, job_dict=None):
        if not job_dict:
            job_dict = self.to_dict()
        
        with open(path, 'w+') as outfile:
            yaml.dump(job_dict, outfile, width=1000, default_flow_style=False)