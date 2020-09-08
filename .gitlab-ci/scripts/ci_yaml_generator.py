#!/usr/bin/env python3

import os
import re
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

    project_blacklist = ['tutorial']
    projects = ci_project.discover_projects(projects_path, 
                                            blacklist=project_blacklist)
    platforms = ci_platform.discover_platforms(projects, config=config)
    host_platforms = ci_platform.get_host_platforms(platforms)
    cross_platforms = ci_platform.get_cross_platforms(platforms)
    platform_directive = get_platform_directive()

    # If we are in a running pipeline, create child pipeline yamls
    if os.getenv('CI_PIPELINE_ID'):
        for host_platform in host_platforms:
            if whitelist and host_platform.name not in whitelist:
                continue

            if host_platform.name not in platform_directive.keys():
                continue

            host_whitelist = whitelist[host_platform.name]
            for cross_platform in cross_platforms:
                if whitelist and cross_platform.name not in host_whitelist:
                    continue

                if cross_platform.name not in platform_directive:
                    continue

                linked_platforms = ci_platform.get_linked_platforms(
                    cross_platform, cross_platforms, platform_directive)
                pipeline = ci_pipeline.make_child_pipeline(
                    projects, host_platform, cross_platform, 
                    linked_platforms=linked_platforms, config=config)
                dump_path = Path(yaml_children_path, '{}-{}.yml'.format(
                    host_platform.name, cross_platform.name))
                ci_pipeline.dump(pipeline, dump_path)
    # If not in running pipeline, create parent pipeline yaml
    else:
        pipeline = ci_pipeline.make_parent_pipeline(
            projects, host_platforms, cross_platforms, yaml_parent_path, 
            yaml_children_path, whitelist=whitelist, config=config)
        dump_path = Path('.gitlab-ci.yml')
        ci_pipeline.dump(pipeline, dump_path)          
    # else:   
    #     for host_platform in host_platforms:
    #         for cross_platform in cross_platforms:
    #             pipeline = ci_pipeline.make_child_pipeline(projects, 
    #                                                        cross_platform, 
    #                                                        host_platform, 
    #                                                        whitelist=whitelist, 
    #                                                        config=config)
    #             yaml_path = Path(yaml_dir_path, 
    #                                 '{}.yml'.format(cross_platform.name))
    #         ci_pipeline.dump(pipeline, yaml_path)
    

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
    

    # print('Generating yaml for host platforms:')
    # for host_platform in host_platforms:
    #     if host_platform.name not in whitelist:
    #         continue

    #     print(host_platform.name)
    #     pipeline = ci_pipeline.make_pipeline(projects, cross_platforms, host_platform, yaml_path)
    #     path = Path(yaml_path, '{}.yml'.format(host_platform.name))
    #     ci_pipeline.dump(pipeline, path, 'w+')

    # ci_pipeline.update('.gitlab-ci.yml', yaml_path)

    # print('\nUpdating "include" section of .gitlab-ci.yml')
    # path = Path('.gitlab-ci.yml')
    # include = [str(path) for path in Path(yaml_path).glob('*.yml')]
    # stages = ['.pre', 'prereqs', 'build', 'test', 'generate-children', 'trigger-children', 'deploy']
    # pipeline = ci_pipeline.Pipeline(stages=stages, include=include}

    # with open(str(gitlab_yml_path), 'w+') as yml:
    #     yaml.safe_dump(gitlab_yml_dict, yml, width=1000, 
    #                    default_flow_style=False)

    # print('\nYaml files available at: {}'.format(Path(Path.cwd(), yaml_path)))
    # print('*IMPORTANT: If a new platform was added,'
    #       ' be sure to commit any newly generated yaml files')


# def main():
#     """Creates yaml files for jobs based on projects and platforms

#     Discovers opencpi projects and platforms, constructs jobs, and dumps
#     them out to yaml files.
#     """
#     opencpi_path = Path(__file__, '..', '..', '..').resolve()
#     os.chdir(str(opencpi_path))
#     gitlab_ci_path = Path('.gitlab-ci')
#     yaml_path = Path(gitlab_ci_path, 'yaml')
#     projects_path = Path('projects')
#     config_path = Path(gitlab_ci_path, 'scripts', 'config.yml')
#     whitelist_path = Path(gitlab_ci_path, 'scripts', 'whitelist.yml')

#     with open(str(config_path)) as yml:
#         config = yaml.safe_load(yml)

#     with open(str(whitelist_path)) as yml:
#         whitelist = yaml.safe_load(yml)

#     project_blacklist = ['tutorial']
#     projects = ci_project.discover_projects(projects_path, project_blacklist)
#     platforms = ci_platform.discover_platforms(projects, config=config)

#     stages = ['.pre', 'prereqs', 'build-host', 'build-rcc', 
#               'build-primitives-core', 'build-primitives', 'build-libraries', 
#               'build-platforms', 'build-assemblies', 'build-sdcards', 'test', 
#               'deploy']

#     host_platforms = ci_platform.get_host_platforms(platforms)
#     cross_platforms = ci_platform.get_cross_platforms(platforms)
#     rcc_platforms = ci_platform.get_rcc_platforms(platforms)

#     for host_platform in host_platforms:
#         if whitelist and host_platform.name not in whitelist:
#             continue

#         print('Generating yaml for host platform: {}'.format(
#               host_platform.name))

#         for cross_platform in cross_platforms:
#             if whitelist:
#                 if cross_platform.name not in whitelist[host_platform.name]:
#                     continue
                
#                 linked_platforms = [rcc_platform for rcc_platform 
#                                     in rcc_platforms 
#                                     if rcc_platform.name 
#                                     in whitelist[host_platform.name]]
#             else:
#                 linked_platforms = rcc_platforms
                
#             print('\t{}'.format(cross_platform.name))

#             overrides = get_overrides(cross_platform, config)
#             cross_jobs = ci_job.make_jobs(stages, cross_platform, projects, 
#                                           linked_platforms=linked_platforms, 
#                                           host_platform=host_platform,
#                                           overrides=overrides)
#             cross_path = Path(yaml_path, host_platform.name, 
#                               '{}.yml'.format(cross_platform.name))
#             ci_job.dump(cross_jobs, cross_path)

#         overrides = get_overrides(host_platform, config)
#         host_jobs = ci_job.make_jobs(stages, host_platform, projects, 
#                                      overrides=overrides)
#         host_path = Path(yaml_path, '{}.yml'.format(host_platform.name))
#         ci_job.dump(host_jobs, host_path)
        
#         host_include = [str(path) for path in 
#             Path(yaml_path, host_platform.name).glob('*.yml')]
#         host_dict = {'include': host_include}
#         dump(host_dict, host_path, 'a')

#     print('\nUpdating "include" section of .gitlab-ci.yml')
#     gitlab_yml_path = Path('.gitlab-ci.yml')
#     gitlab_yml_include = [str(path) for path in Path(yaml_path).glob('*.yml')]
#     gitlab_yml_dict = {
#         'include': gitlab_yml_include,
#         'stages': stages
#     }
#     dump(gitlab_yml_dict, gitlab_yml_path, 'w+')

#     print('\nYaml files available at: {}'.format(Path(Path.cwd(), yaml_path)))
#     print('*IMPORTANT: If a new platform was added,'
#           ' be sure to commit any newly generated yaml files')








if __name__ == '__main__':
    main()