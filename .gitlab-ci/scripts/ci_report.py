#! /usr/bin/python3
import csv
import json
from collections import defaultdict
from os import environ
from pathlib import Path
from typing import List, Union
from urllib import request

HEADERS = {'JOB-TOKEN': environ['CI_JOB_TOKEN']}
CMD_TEMPLATE = 'https://gitlab.com/api/v4/projects/{}/pipelines/{}/{}?scope[]=failed'


def main():
    """Get failed jobs and dump to csv
    
    Gets pipeline info from environment and calls get_failed_jobs() then
    dumps the returned jobs to a csv file with name in format:
        "job_report_${CI_COMMIT_TIMESTAMP}.csv"
    """
    bridge = {
        'downstream_pipeline': {
            'id': environ['CI_PIPELINE_ID'],
            'project_id': environ['CI_PROJECT_ID'],
            'web_url': environ['CI_PIPELINE_URL']
        }
    }
    failed_jobs = get_failed_jobs([bridge])
    time_stamp = environ['CI_JOB_STARTED_AT'].split('T')[0]
    dump(failed_jobs, f'job_report_{time_stamp}.csv')


def get_failed_jobs(bridges: List[dict]) -> List[dict]:
    """Uses gitlab API to gather and return list of failed jobs
    
    Recursively calls itself, passing in gathered failed bridge jobs and
    jobs, to collect failed jobs from child pipelines.
    """
    failed_jobs = defaultdict(list)
    for bridge in bridges:
        pipeline = bridge['downstream_pipeline']
        pipeline_id = pipeline['id']
        project_id = pipeline['project_id']
        web_url = Path(pipeline['web_url']).relative_to(
            'https://gitlab.com/opencpi/')
        project_name = web_url.parts[0]
        if project_name != 'opencpi':
            project_name = web_url.parts[1]
        job_cmd = CMD_TEMPLATE.format(project_id, pipeline_id, 'jobs')
        bridge_cmd = CMD_TEMPLATE.format(project_id, pipeline_id, 'bridges')
        job_request = request.Request(job_cmd, headers=HEADERS)
        job_responses = urlopen(job_request)
        bridge_request = request.Request(bridge_cmd, headers=HEADERS)
        bridge_responses = urlopen(bridge_request)
        failed_jobs[project_name] += job_responses
        failed_jobs.update(get_failed_jobs(bridge_responses))

    return failed_jobs


def urlopen(url: Union[str, request.Request]) -> List[dict]:
    """Opens a url or Request object and returns reponses.

    Call request.urlopen() to open url. Handles pagination by calling
    self recursively.
    """
    responses = []
    with request.urlopen(url) as f:
        response = f.read()
        responses += json.loads(response)
        links = f.info()['Link'].split(',') # Get pagination info
        links = [link.split(';') for link in links]
        for link in links:
            if link[1].strip() == 'rel="next"':
            # If a link contains a "next" page, follow it
                responses += urlopen(link[0])
                break

    return responses


def dump(failed_jobs: List[dict], file_name: str):
    """Dumps failed jobs out to a csv file"""
    with open(file_name, 'w', newline='') as csvfile:
        writer = csv.writer(csvfile, delimiter=',')
        writer.writerow([
            'PROJECT',
            'NAME', 
            'WEB URL', 
            'FAILURE REASON', 
            'DURATION (seconds)',
            'RUNNER'
        ])
        for project_name,jobs in sorted(failed_jobs.items()):
            print(project_name)
            writer.writerow([project_name])
            for job in sorted(jobs, key=lambda job: job['name']):
                print(f'\t{job["name"]}')
                writer.writerow([
                    '',
                    job['name'], 
                    job['web_url'], 
                    job['failure_reason'], 
                    job['duration'], 
                    job['runner']['description'],
                ])
        

if __name__ == '__main__':
    main()
