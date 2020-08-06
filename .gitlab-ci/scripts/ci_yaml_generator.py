#!/usr/bin/env python3

from ci_yaml_generator import Project, Platform, Job, Pipeline
from ci_utils import get_platform_directive, get_ci_env
from pathlib import Path
from argparse import ArgumentParser

def main():
    ci_env = get_ci_env()
    platform_directive = get_platform_directive(ci_env.commit_message)
    projects = Project.discover_projects('project-registry')
    platforms = Platform.discover_platforms(projects, platform_directive=platform_directive)
    parser = make_parser()
    args = parser.parse_args()

    if 'func' in args:
        args.func(ci_env, projects, platforms)
    else:
        parser.print_help()


def make_parser():

    # Create parser
    parser = ArgumentParser()
    subparsers = parser.add_subparsers()

    subparser = subparsers.add_parser(
        name='child', 
        help='Generate yaml files for child pipelines')
    subparser.set_defaults(func=child)

    subparser = subparsers.add_parser(
        name='parent', 
        help='Generate yaml files for parent pipeline')
    subparser.set_defaults(func=parent)

    return parser


def child(ci_env, projects, platforms):
    host_platforms = Platform.get_host_platforms(platforms)
    cross_platforms = Platform.get_cross_platforms(platforms)

    for host_platform in host_platforms:
        jobs = []
        print('Generating yaml for host platform: {}'.format(host_platform.name))
        for platform in cross_platforms:
            if platform.model == 'hdl':
                for project in projects:
                    for library in project.libraries:    
                        stage = Job.get_stage_from_library(library) 
                        job = Job(stage=stage, project=project, platform=platform, library=library, host_platform=host_platform)
                        jobs.append(job)
            else:
                for project in projects:
                    for stage in Job.rcc_stages:    
                        job = Job(stage=stage, project=project, platform=platform, host_platform=host_platform)
                        jobs.append(job)

            pipeline = Pipeline(jobs)
            path = Path('.gitlab-ci', 'generated-yaml', '{}'.format(host_platform.name), '{}.yml'.format(platform.name))
            path.parents[1].mkdir(exist_ok=True)
            path.parent.mkdir(exist_ok=True)
            pipeline.dump(path)


def parent(ci_env, projects, platforms):
    job = Job(stage='generate-yaml')
    jobs = [job]
    
    for host_platform in Platform.get_host_platforms(platforms):
        for platform in Platform.get_cross_platforms(platforms):
            job = Job(stage='trigger', platform=platform, host_platform=host_platform)
            jobs.append(job)
        pipeline = Pipeline(jobs)
        path = Path('.gitlab-ci', 'generated-yaml', 'test.yml')
        path.parents[1].mkdir(exist_ok=True)
        path.parent.mkdir(exist_ok=True)
        pipeline.dump(path)

main()