#!/usr/bin/env python3

from collections import defaultdict
from argparse import ArgumentParser
import re
from pathlib import Path
import ci_utils
import subprocess
from ci_yaml_generator import ci_project, ci_platform, ci_pipeline, ci_job


def main():
    parser = make_parser()
    args = parser.parse_args()
    ci_utils.set_test_env()
    if 'func' in args:
        args.func(args)
    else:
        parser.print_help()


def make_parser():
    parser = ArgumentParser()
    subparsers = parser.add_subparsers()

    subparser = subparsers.add_parser(
        name='children', 
        help='Generate yaml files for child pipelines. \
              Intended to be used within pipeline.')
    subparser.set_defaults(func=children)

    subparser = subparsers.add_parser(
        name='parent', 
        help='Generate yaml files for parent pipeline. \
              Intended to be used manually.')
    subparser.set_defaults(func=parent)

    return parser


def children(args):
    ci_utils.set_test_env()
    ci_env = ci_utils.get_ci_env()
    platform_directive = get_platform_directive(ci_env)
    project_path = Path(ci_env.project_dir, 'projects')
    projects = ci_project.discover_projects(project_path)

    if platform_directive:
        platform_filter = platform_directive.keys()
    else:
        platform_filter = None

    platforms = ci_platform.discover_platforms(projects, platform_filter, 
                                               platform_directive, 
                                               do_osps=False)

    host_platforms = ci_platform.get_host_platforms(platforms)
    cross_platforms = ci_platform.get_cross_platforms(platforms)
    hdl_stages = ['build-primitives-core', 'build-primitives', 'build-libraries',
                  'build-platforms', 'build-assemblies', 'build-test', 
                  'build-sdcard', 'test']
    rcc_stages = ['prereqs', 'build', 'test']

    for host_platform in host_platforms:
        print('Generating child yaml for host platform: {}'.format(host_platform.name))
        for platform in cross_platforms:
            print('\t{}'.format(platform.name))
            stages = hdl_stages if platform.model == 'hdl' else rcc_stages
            jobs = ci_job.make_child_jobs(stages, projects, platform, host_platform)
            pipeline = ci_pipeline.make_pipeline(jobs, stages)

            path = Path(ci_env.project_dir, '.gitlab-ci', 'yaml_dynamic', 
                '{}'.format(host_platform.name), '{}.yml'.format(platform.name))
            ci_pipeline.dump(pipeline, path)


def parent(args):
    project_registry_path = Path('project-registry')
    projects = ci_project.discover_projects(project_registry_path)
    platforms = ci_platform.discover_platforms(projects)

    host_platforms = ci_platform.get_host_platforms(platforms)
    cross_platforms = ci_platform.get_cross_platforms(platforms)
    stages = ['prereqs', 'build', 'test', 'generate-yaml', 
              'trigger-children', 'deploy']
    yaml_generator_job = ci_job.make_yaml_generator_job()
    
    for host_platform in host_platforms:
        print('Generating yaml for platform: {}'.format(host_platform.name))
        jobs = ci_job.make_parent_jobs(stages, yaml_generator_job, 
                                       projects, cross_platforms, host_platform)
        pipeline = ci_pipeline.make_pipeline(jobs)

        path = Path('.gitlab-ci', 'yaml', '{}.yml'.format(host_platform.name))
        ci_pipeline.dump(pipeline, path)
        subprocess.call(["git", "add", str(path)])
    
    jobs = [yaml_generator_job]
    # for platform in cross_platforms:
    #     if not platform.is_osp:
    #         continue
    #     stage = 'trigger-children'
    #     job = ci_job.make_bridge_job(stage, platform)
    #     jobs.append(job)

    include = [str(path) for path in Path('.gitlab-ci', 'yaml').glob('*')]
    pipeline = ci_pipeline.Pipeline(jobs, stages=stages, include=include)
    path = Path('.gitlab-ci.yml')
    print('Updating {} include files'.format(str(path)))
    ci_pipeline.dump(pipeline, path)


def get_platform_directive(ci_env):
    commit_directive = re.search('\[ *ci (.*) *\]', ci_env.commit_message)
    space_pattern = re.compile(r'([^ $]+)')
    colon_pattern = re.compile(r'([^:$]+)')
    comma_pattern = re.compile(r'([^,$]+)')
    platforms = defaultdict(set)

    if ci_env.pipeline_source in ['scheduled', 'web']:
        platform_names = ci_env.platforms
    elif ci_env.pipeline_source == 'merge_request_event':
        platform_names = ci_env.mr_platforms
    elif ci_env.pipeline_source == 'push':
        if commit_directive:
            platform_names = commit_directive.group(1)
        else:
            platform_names = ci_env.platforms
    else:
        return []

    print(platform_names)

    spaces = space_pattern.findall(platform_names)
    for space in spaces:
        colons = colon_pattern.findall(space)
        left = colons[0]
        
        if left:
            l_commas = comma_pattern.findall(left)
            
            for l_comma in l_commas:

                if len(colons) == 2:
                    right = colons[1]
                    r_commas = comma_pattern.findall(right)

                    for r_comma in r_commas:
                        platforms[l_comma].add(r_comma)
                        platforms[r_comma].add(l_comma)

                else:
                    platforms[l_comma] = {}
    
    return platforms


main()