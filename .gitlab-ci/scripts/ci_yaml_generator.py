#!/usr/bin/env python3

import os
import yaml
from pathlib import Path
from ci_utils import ci_project, ci_platform, ci_job


def main():
    """Creates yaml files for jobs based on projects and platforms

    Discovers opencpi projects and platforms, constructs jobs, and dumps
    them out to yaml files.
    """
    opencpi_path = Path(__file__, '..', '..', '..').resolve()
    os.chdir(str(opencpi_path))
    gitlab_ci_path = Path('.gitlab-ci')
    yaml_path = Path(gitlab_ci_path, 'yaml')
    projects_path = Path('projects')
    config_path = Path(gitlab_ci_path, 'scripts', 'config.yml')
    whitelist_path = Path(gitlab_ci_path, 'scripts', 'whitelist.yml')

    with open(str(config_path)) as yml:
        config = yaml.safe_load(yml)

    with open(str(whitelist_path)) as yml:
        whitelist = yaml.safe_load(yml)

    project_blacklist = ['tutorial']
    projects = ci_project.discover_projects(projects_path, project_blacklist)
    platforms = ci_platform.discover_platforms(projects, config=config)

    stages = ['.pre', 'prereqs', 'build-host', 'build-rcc', 
              'build-primitives-core', 'build-primitives', 'build-libraries', 
              'build-platforms', 'build-assemblies', 'build-sdcards', 'test', 
              'deploy']

    host_platforms = ci_platform.get_host_platforms(platforms)
    cross_platforms = ci_platform.get_cross_platforms(platforms)
    rcc_platforms = ci_platform.get_rcc_platforms(platforms)

    for host_platform in host_platforms:
        if whitelist and host_platform.name not in whitelist:
            continue

        print('Generating yaml for host platform: {}'.format(
              host_platform.name))

        for cross_platform in cross_platforms:
            if whitelist:
                if cross_platform.name not in whitelist[host_platform.name]:
                    continue
                
                linked_platforms = [rcc_platform for rcc_platform 
                                    in rcc_platforms 
                                    if rcc_platform.name 
                                    in whitelist[host_platform.name]]
            else:
                linked_platforms = rcc_platforms
                
            print('\t{}'.format(cross_platform.name))

            overrides = get_overrides(cross_platform, config)
            cross_jobs = ci_job.make_jobs(stages, cross_platform, projects, 
                                          linked_platforms=linked_platforms, 
                                          host_platform=host_platform,
                                          overrides=overrides)
            cross_path = Path(yaml_path, host_platform.name, 
                              '{}.yml'.format(cross_platform.name))
            ci_job.dump(cross_jobs, cross_path)

        overrides = get_overrides(host_platform, config)
        host_jobs = ci_job.make_jobs(stages, host_platform, projects, 
                                     overrides=overrides)
        host_path = Path(yaml_path, '{}.yml'.format(host_platform.name))
        ci_job.dump(host_jobs, host_path)
        
        host_include = [str(path) for path in 
            Path(yaml_path, host_platform.name).glob('*.yml')]
        host_dict = {'include': host_include}
        dump(host_dict, host_path, 'a')

    print('\nUpdating "include" section of .gitlab-ci.yml')
    gitlab_yml_path = Path('.gitlab-ci.yml')
    gitlab_yml_include = [str(path) for path in Path(yaml_path).glob('*.yml')]
    gitlab_yml_dict = {
        'include': gitlab_yml_include,
        'stages': stages
    }
    dump(gitlab_yml_dict, gitlab_yml_path, 'w+')

    print('\nYaml files available at: {}'.format(Path(Path.cwd(), yaml_path)))
    print('*IMPORTANT: If a new platform was added,'
          ' be sure to commit any newly generated yaml files')


def get_overrides(platform, config):
    """Gets job overrides for a platform from a dictionary of platforms

    Overrides will replace default job values (tags, script, etc.).

    Args:
        platform: Platform to get overrides for
        config:   Dictionary with platform names as keys and
                  overrides as values

    Returns:
        A dictionary of job overrides for a specified platform
    """
    try:
        return config[platform.name]['overrides']
    except:
        return {}


def dump(yaml_dict, yaml_path, mode):
    """Dumps a dictionary to a yaml file

    Args:
        yaml_dict:  Dictionary to dump to a yaml file
        yaml_path:  Path of yaml file to dump dictionary to
        mode:       Mode to open file in
    """
    yaml.SafeDumper.ignore_aliases = lambda *args : True

    with open(yaml_path, mode) as yml:
        yaml.safe_dump(yaml_dict, yml, width=1000, default_flow_style=False)


if __name__ == '__main__':
    main()