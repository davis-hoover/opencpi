#!/usr/bin/env python3

import sys
import yaml
from collections import namedtuple
from os import chdir, getenv, environ
from pathlib import Path
from ci_utils import Pipeline, Directive, ci_project, ci_platform

def main():
    """Creates and dumps a pipeline to a yaml file.

    Discovers local and remote opencpi projects and platforms and
    uses them to create a pipeline.
    """
    opencpi_path = Path(__file__, '..', '..', '..').resolve()
    cwd_path = Path.cwd()
    chdir(str(opencpi_path))
    ci_scripts_path = Path('.gitlab-ci', 'scripts')
    config_path = Path(ci_scripts_path, 'config.yml')
    whitelist_path = Path(ci_scripts_path, 'whitelist.yml')
    pipeline_path = Path('.gitlab-ci.yml')
    ci_env = get_ci_env()

    # Get config and platform whitelist
    with open(str(config_path)) as yml:
        config = yaml.safe_load(yml)
    with open(str(whitelist_path)) as yml:
        platform_whitelist = yaml.safe_load(yml)

    # Get projects
    project_blacklist = ['tutorial', ci_env.project_id]
    project_group_ids = ['6009537', '9500084']
    projects_path = Path('projects')
    projects = ci_project.discover_projects(projects_paths=projects_path, 
                                            group_ids=project_group_ids,
                                            blacklist=project_blacklist)
    # Get platforms
    platforms = ci_platform.discover_platforms(projects, 
                                               whitelist=platform_whitelist, 
                                               config=config)
    directive = Directive.from_env(ci_env)
    platforms = directive.apply(platforms)

    for platform in platforms:
        print(platform.name)
        for cross_platform in platform.cross_platforms:
            print('\t', cross_platform.name)

    # Make pipeline
    pipeline = Pipeline(pipeline_path, ci_env, directive)
    pipeline.generate(projects, platforms, config=config)

    for job in sorted(pipeline._jobs):
        print(job.name)

    # Write pipeline to yaml file
    chdir(str(cwd_path))
    if ci_env.project_name == 'opencpi':
        dump_path = pipeline_path
    else:
        dump_path = Path('..', pipeline_path)
    pipeline.dump(dump_path)


def get_ci_env():
    """Collects CI environment variables

    Collects environment variables with the 'CI_' prefix. The variables
    are lower-cased and the prefix is removed when stored in the
    collection.

    Ex:
        The environment variables CI_COMMIT_MESSAGE can be accessed as
        ci_env.commit_message

    Returns:
        Namedtuple of CI environment variables
    """
    ci_dict = {key.lower().replace('ci_', ''):value 
               for key,value in environ.items() 
               if key.startswith('CI_')}
    Ci_env = namedtuple('Ci_env', ci_dict.keys())
    ci_env = Ci_env(*ci_dict.values())
    
    if not ci_env:
        sys.exit('Error: CI environment not set')

    for key,value in ci_dict.items():
        print('{}: {}'.format(key, value))

    return ci_env


def set_ci_env():
    """Sets CI environment variables

    Simulates a pipeline environment by setting environment variables.
    This function should not be called except for testing.
    """
    environ['CI_COMMIT_MESSAGE'] = '[ci zed:xilinx13_4]'
    environ['CI_PIPELINE_SOURCE'] = 'push'
    environ['CI_ROOT_ID'] = '1'
    environ['CI_PLATFORM'] = 'plutosdr'
    environ['CI_HOST_PLATFORM'] = 'centos7'
    environ['CI_DEFAULT_HOSTS'] = 'centos7'
    environ['CI_PLATFORMS'] = 'zed'
    environ['CI_PIPELINE_ID'] = '0'
    environ['CI_PROJECT_DIR'] = 'plutosdr'
    environ['CI_PROJECT_NAME'] = 'opencpi'
    environ['CI_COMMIT_REF_NAME'] = 'develop'
    environ['CI_PROJECT_TITLE'] = 'plutosdr'
    environ['CI_PROJECT_ID'] = '15332496'
    environ['CI_UPSTREAM_ID'] = '2'
    environ['CI_UPSTREAM_REF'] = 'develop'
    # environ['CI_UPSTREAM_PLATFORMS'] = 'plutosdr modelsim'
    environ['CI_ROOT_SOURCE'] = 'pipeline'
    environ['CI_ROOT_PLATFORMS'] = 'centos7 plutosdr'


if __name__ == '__main__':
    main()