#!/usr/bin/env python3

import os
import re
import sys
import yaml
from collections import defaultdict
from pathlib import Path
from ci_utils import ci_project, ci_platform, ci_job, ci_pipeline

def main():
    opencpi_path = Path(__file__, '..', '..', '..').resolve()
    os.chdir(str(opencpi_path))
    gitlab_ci_path = Path('.gitlab-ci')
    yaml_parent_path = Path('.gitlab-ci', 'yaml-parent')
    yaml_children_path = Path(gitlab_ci_path, 'yaml-children')
    projects_path = Path('project-registry')
    config_path = Path(gitlab_ci_path, 'scripts', 'config.yml')
    whitelist_path = Path(gitlab_ci_path, 'scripts', 'whitelist.yml')

    with open(str(config_path)) as yml:
        config = yaml.safe_load(yml)

    with open(str(whitelist_path)) as yml:
        whitelist = yaml.safe_load(yml)

    # Discover opencpi projects and platforms
    project_blacklist = ['tutorial']
    projects = ci_project.discover_projects(projects_path, 
                                            blacklist=project_blacklist)
    platforms = ci_platform.discover_platforms(projects, config=config)
    host_platforms = ci_platform.get_host_platforms(platforms)
    cross_platforms = ci_platform.get_cross_platforms(platforms)

    if os.getenv('CI_PIPELINE_ID'):
    # If we are in a running pipeline, create child pipeline yamls
        host_platform = ci_platform.get_platform(sys.argv[1], host_platforms)
        cross_platform = ci_platform.get_platform(sys.argv[2], cross_platforms)

        # Get linked_platforms from platform_directive
        platform_directive = get_platform_directive()
        host_whitelist = whitelist[host_platform.name]
        linked_platforms = ci_platform.get_linked_platforms(
            cross_platform, cross_platforms, platform_directive)
        linked_platforms = [linked_platform 
                            for linked_platform in linked_platforms 
                            if linked_platform.name in host_whitelist]
        
        # Make pipeline and dump to yaml
        print("Generating pipeline for platform {} on host {}".format(
            cross_platform.name, host_platform.name))
        pipeline = ci_pipeline.make_child_pipeline(
            projects, host_platform, cross_platform, 
            linked_platforms=linked_platforms, config=config)
        dump_path = Path(yaml_children_path, '{}-{}.yml'.format(
            host_platform.name, cross_platform.name))
        ci_pipeline.dump(pipeline, dump_path)
    else:
    # If not in running pipeline, create parent pipeline yaml
        print("Updating .gitlab-ci.yml for host platforms:")
        pipeline = ci_pipeline.make_parent_pipeline(
            projects, host_platforms, cross_platforms, yaml_parent_path, 
            yaml_children_path, whitelist=whitelist, config=config)
        dump_path = Path('.gitlab-ci.yml')
        ci_pipeline.dump(pipeline, dump_path)        


def get_platform_directive():
    #TODO python docs
    commit_message = os.getenv('CI_COMMIT_MESSAGE')
    commit_directive = re.search(r'\[ *ci (.*) *\]', commit_message)
    space_pattern = re.compile(r'([^ $]+)')
    colon_pattern = re.compile(r'([^:$]+)')
    comma_pattern = re.compile(r'([^,$]+)')
    platforms = defaultdict(set)

    if os.getenv("CI_PIPELINE_SOURCE") in ['scheduled', 'web']:
        platform_names = os.getenv("CI_PLATFORMS")
    elif os.getenv("CI_PIPELINE_SOURCE") == 'merge_request_event':
        platform_names = os.getenv("CI_MR_PLATFORMS")
    elif os.getenv("CI_PIPELINE_SOURCE") == 'push':
        if commit_directive:
            platform_names = commit_directive.group(1)
        else:
            platform_names = os.getenv("CI_PLATFORMS")
    else:
        return platforms

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


if __name__ == '__main__':
    main()