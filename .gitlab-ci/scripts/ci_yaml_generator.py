#!/usr/bin/env python3

import sys
from collections import defaultdict
from argparse import ArgumentParser
import re
from pathlib import Path
from ci_utils import get_ci_env
from ci_yaml_generator import Project, Platform, Pipeline, Job


def main():
    parser = make_parser()
    args = parser.parse_args()
    
    if 'func' in args:
        args.func(args)
    else:
        parser.print_help()


def make_parser():
    parser = ArgumentParser()
    subparsers = parser.add_subparsers()

    subparser = subparsers.add_parser(
        name='child', 
        help='Generate yaml files for child pipelines. \
              Intended to be used within pipeline.')
    subparser.set_defaults(func=child)
    subparser.add_argument('platform', nargs='*')

    subparser = subparsers.add_parser(
        name='parent', 
        help='Generate yaml files for parent pipeline. \
              Intended to be used manually.')
    subparser.set_defaults(func=parent)

    return parser


def child(args):
    ci_env = get_ci_env()
    platform_directive = get_platform_directive(ci_env)
    project_registry_path = Path(ci_env.project_dir, 'project-registry')
    projects = Project.discover_projects(project_registry_path)

    if platform_directive:
        platform_filter = platform_directive.keys()
    else:
        platform_filter = None

    platforms = Platform.discover_platforms(projects, platform_filter, 
        platform_directive, only_child=args.platform, do_osp_search=False)

    # if platform_directive:
    #     Platform.link_platforms(platforms, platform_directive)

    for platform in platforms:
        print(platform.name, platform.links)

    host_platforms = Platform.get_host_platforms(platforms)
    cross_platforms = Platform.get_cross_platforms(platforms)
    hdl_stages = ['build-primitives-core', 'build-primitives', 'build-libraries',
                  'build-platforms', 'build-assemblies', 'test']
    rcc_stages = ['prereqs', 'build', 'test']

    for host_platform in host_platforms:
        print('Generating yaml for host platform: {}'.format(host_platform.name))
        for platform in cross_platforms:
            stages = hdl_stages if platform.model == 'hdl' else rcc_stages
            jobs = make_child_jobs(stages, projects, platform, host_platform)
            pipeline = Pipeline(jobs, stages)

            path = Path(ci_env.project_dir, '.gitlab-ci', 'yaml-dynamic', 
                '{}'.format(host_platform.name), '{}.yml'.format(platform.name))
            path.parents[1].mkdir(exist_ok=True)
            path.parent.mkdir(exist_ok=True)
            pipeline.dump(path)


def parent(args):
    project_registry_path = Path('project-registry')
    projects = Project.discover_projects(project_registry_path)
    platforms = Platform.discover_platforms(projects)

    host_platforms = Platform.get_host_platforms(platforms)
    cross_platforms = Platform.get_cross_platforms(platforms)
    stages = ['prereqs', 'build', 'test', 'generate-yaml', 'trigger-children']
    yaml_generator_job = make_generate_yaml_job()
    
    include = []
    for host_platform in host_platforms:
        jobs = make_parent_jobs(stages, yaml_generator_job, 
            projects, cross_platforms, host_platform)
        pipeline = Pipeline(jobs)

        path = Path('.gitlab-ci', 'yaml', '{}.yml'.format(host_platform.name))
        include.append(str(path))
        path.parents[1].mkdir(exist_ok=True)
        path.parent.mkdir(exist_ok=True)
        pipeline.dump(path)

    jobs = [yaml_generator_job]
    for platform in cross_platforms:
        if not platform.is_osp:
            continue
        stage = 'trigger-children'
        job = make_bridge_job(stage, platform)
        jobs.append(job)

    pipeline = Pipeline(jobs, stages=stages, include=include)
    path = Path('.gitlab-ci.yml')
    pipeline.dump(path)


def get_platform_directive(ci_env):
    commit_directive = re.search('\[ci (.*)\]', ci_env.commit_message)
    space_pattern = re.compile(r'([^ $]+)')
    colon_pattern = re.compile(r'([^:$]+)')
    comma_pattern = re.compile(r'([^,$]+)')
    platforms = defaultdict(set)

    if commit_directive:
        platform_names = commit_directive.group(1)
    else:
        platform_names = ci_env.platforms

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


def make_parent_jobs(stages, yaml_generator_job, 
                     projects, platforms, host_platform):
    jobs = []

    for stage in stages:
        if stage == 'trigger-children':
            for platform in platforms:
                if platform.is_osp:
                    continue
                job = make_trigger_job(stage, yaml_generator_job, 
                    host_platform, platform)
                jobs.append(job)
        elif stage != 'generate-yaml':
            for platform in platforms:
                name = ':'.join([stage, host_platform.name])
                script = make_script(stage, stages, host_platform)
                tags = [host_platform.name, 'shell', 'opencpi']
                rules = make_parent_rules(host_platform)
                job = Job(name, stage, script, tags=tags, rules=rules)
                jobs.append(job)
    
    return jobs


def make_child_jobs(stages, projects, platform, host_platform):
    jobs = []

    if platform.model == 'hdl':
        for project in projects:
            for library in project.libraries:
                stage = stage_from_library(library)
                name = ':'.join([stage, project.name, library.name, 
                                 host_platform.name, platform.name])
                script = make_script(stage, stages, platform, host_platform, path=library.path)
                tags = [host_platform.name, 'shell', 'opencpi']
                rules = make_parent_rules(platform)
                job = Job(name, stage, script, rules=rules, tags=tags)
                jobs.append(job)

                if library.is_testable:
                    stage = 'test'
                    name = ':'.join([stage, project.name, library.name, 
                                     host_platform.name, platform.name])
                    script = make_script(stage, stages, platform, host_platform, path=library.path)
                    tags = [platform.name, host_platform.name, 'shell', 'opencpi']
                    resource_group = platform.name
                    rules = make_parent_rules(platform)
                    job = Job(name, stage, script, tags=tags, rules=rules, resource_group=resource_group)
                    jobs.append(job)
    elif platform.model == 'rcc':
        for stage in stages:
            if stage == 'test':
                for project in projects:
                    for library in project.libraries:
                        if library.is_testable:
                            name = ':'.join([stage, project.name, library.name, 
                                             host_platform.name, platform.name])
                            script = make_script(stage, stages, platform, host_platform, path=library.path)
                            tags = [host_platform.name, 'shell', 'opencpi']
                            rules = make_parent_rules(platform)
                            job = Job(name, stage, script, tags=tags, rules=rules)
                            jobs.append(job)
            else:
                name = ':'.join([stage, host_platform.name, platform.name])
                script = make_script(stage, stages, platform, host_platform)
                tags = [host_platform.name, 'shell', 'opencpi']
                rules = make_parent_rules(platform)
                job = Job(name, stage, script, tags=tags, rules=rules)
                jobs.append(job)

    return jobs


def make_trigger_job(stage, yaml_generater_job, host_platform, platform):
    name = ':'.join([stage, host_platform.name, platform.name])
    # rules = [{'exists': '.gitlab-ci/yaml-generated/{}-{}.yml'.format(host_platform.name, platform.name)}]
    # rules = make_child_rules(platform, host_platform)
    trigger = {
        'strategy': 'depend',
        'include': [{
            'artifact': '.gitlab-ci/generated_yaml/{}-{}.yml'.format(
                host_platform.name, platform.name),
            'job': yaml_generater_job.name
        }]
    }
    job = Job(name, stage, trigger=trigger, rules=rules)

    return job


def make_bridge_job(stage, platform):
    name = ':'.join([stage, platform.name])
    # rules = make_child_rules(platform, host_platform)
    trigger = {
        'strategy': 'depend',
        'variables': {
            'CI_COMMIT_MESSAGE': '$CI_COMMIT_MESSAGE'
        },
        'project': platform.repo,
        'branch': 'develop' #CHANGE TO TEST REPO
    }
    job = Job(name, stage, trigger=trigger, rules=rules)

    return job


def make_generate_yaml_job():
    stage = 'generate-yaml'
    name = stage
    script = '.gitlab-ci/scripts/ci_generate_yaml.py child'
    artifacts = {'paths': [
        '.gitlab-ci/yaml-generated/'
    ]}
    job = Job(name, stage, script, artifacts=artifacts)
    
    return job


def make_parent_rules(platform):
    return [
        {'if': "\"$CI_HDL_PLATFORM\" =~ /(^| |\:)({})( |$|\:)/i && $CI_PIPELINE_SOURCE == \"schedule\"".format(platform.name)},
        {'if': "\"$CI_HDL_PLATFORM =~ /(^| |\:)({}|all)( |$|\:)/i && $CI_PIPELINE_SOURCE == \"web\"\"".format(platform.name)},
        {'if': "\"$CI_HDL_PLATFORM_MR =~ /(^| |\:)({}|all)( |$|\:)/i && $CI_PIPELINE_SOURCE == \"merge_request_event\"".format(platform.name)},
        {'if': "\"$CI_COMMIT_MESSAGE =~ /\[ *ci *\S* +({}|all)( \S*)*\]/i && $CI_PIPELINE_SOURCE == \"push\"".format(platform.name)},
        {'if': "\"$CI_HDL_PLATFORM =~ /(^| |\:)({}|all)( |$|\:)/i && $CI_COMMIT_MESSAGE !~ /\[ *ci.*\]/i && $CI_PIPELINE_SOURCE == \"push\"".format(platform.name)}
    ]


def make_script(stage, stages, platform, host_platform=None, path=None):
    stage_idx = stages.index(stage)
    download_cmd = '.gitlab-ci/scripts/ci_artifacts.py download -i {}'.format(
        ' '.join(["*{}.tar.gz".format(platform.name) for platform in [platform, host_platform] if platform]))
    sleep_cmd = 'sleep 2'
    timestamp_cmd = 'touch .timestamp'
    source_cmd = 'source cdk/opencpi-setup.sh -e'
    success_cmd = 'touch .success'
    upload_cmd = '.gitlab-ci/scripts/ci_artifacts.py upload -t .timestamp'

    exclude_stages = ' '.join('*/{}/*'.format(stage) for stage in stages[stage_idx:])
    download_cmd = ' '.join([download_cmd, '-e', exclude_stages])

    if platform.model == 'hdl':
        if stage == 'generate-yaml':
            build_cmd = '.gitlab-ci/scripts/generate-yaml.py child'
        elif stage in ['build-primitives-core', 'build-primitives', 'build-libraries']:
            build_cmd = 'ocpidev build -d {} --hdl-platform {}'.format(path, platform.name)
        elif stage == 'build-platforms':
            build_cmd = 'ocpidev build hdl platforms {} --hdl-platform {}'.format(path, platform.name)
        # elif self.stage == 'build-sdcard':
        #     build_cmd = 'ocpiadmin deploy platform {} {}'.format(self.platform.name, self.platform.name)
        elif stage == 'build-assemblies':
            build_cmd = 'ocpidev build test {} --hdl-platform {}'.format(path, platform.name)
        elif stage == 'test':
            build_cmd = 'ocpidev run tests {} --only-platform {}'.format(path, platform.name)
    else:
        if stage == 'prereqs':
            build_cmd = 'scripts/install-prerequisites.sh {}'.format(platform.name)
        elif stage == 'build':
            build_cmd = 'scripts/install-opencpi.sh {}'.format(platform.name)
        elif stage == 'test':
            if platform.is_host:
                build_cmd = 'scripts/test-opencpi.sh'
            else:
                build_cmd = 'ocpidev run tests {} --only-platform {}'.format(path, platform.name)


    return [download_cmd, sleep_cmd, timestamp_cmd, source_cmd, build_cmd, success_cmd, upload_cmd] 


def stage_from_library(library):

    if library.name == 'primitives':
        if library.project == 'core':
            return 'build-primitives-core'
        else:
            return 'build-primitives'

    if library.name in ['platforms', 'assemblies']:
        return 'build-{}'.format(library.name)
    
    if (library.name in ['components', 'adapters', 'cards', 'devices']
            or library.path.parent.stem == 'components'):
        return 'build-libraries'

    raise Exception('Unable to get stage from library {}'.format(library.name))


main()