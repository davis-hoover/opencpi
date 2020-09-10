#!/usr/bin/env python3

import os
import sys
import yaml
from pathlib import Path
from ci_utils import ci_project, ci_platform, ci_job, ci_pipeline

def main():
    #TODO: python docs
    # Set paths and change dir to opencpi root
    opencpi_path = Path(__file__, '..', '..', '..').resolve()
    os.chdir(str(opencpi_path))
    gitlab_ci_path = Path('.gitlab-ci')
    yaml_parent_path = Path('.gitlab-ci', 'yaml-parent')
    yaml_children_path = Path(gitlab_ci_path, 'yaml-children')
    projects_path = Path('project-registry')
    config_path = Path(gitlab_ci_path, 'scripts', 'config.yml')
    whitelist_path = Path(gitlab_ci_path, 'scripts', 'whitelist.yml')

    # Get config and platform whitelist
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

        # Get the cross_platform's linked_platforms
        host_whitelist = whitelist[host_platform.name]
        linked_platforms = ci_platform.get_linked_platforms(
            cross_platform, cross_platforms, whitelist=host_whitelist)

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


if __name__ == '__main__':
    main()