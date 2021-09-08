#!/usr/bin/env python3

from json import load
from pathlib import Path
from urllib.request import urlopen
from . import ci_asset

class Project():

    def __init__(self, name, path=None, url=None, project_id=None, assets=None, 
                 group=None):
        self.name = name
        self.path = path
        self.url = url
        self.id = project_id
        self.group = group
        self.platforms = []
        self.assets = assets or ci_asset.discover_assets(
            self.path, self, 
            whitelist=['primitives', 'cards', 'devices', 'adapters', 
                       'assemblies', 'components', 'platforms'])


def discover_projects(projects_paths=None, group_ids=None, whitelist=None,
                      blacklist=None):
    """Search opencpi for projects

    Calls discover_libraries() to search for project libraries.

    Args:
    projects_path: Path or list of Paths to opencpi projects
    group_ids:     Gitlab ID or list of Gitlab IDs of project group
    whitelist:     List of projects to include
    blacklist:     List of projects not to include

    Returns:
        projects: List of opencpi projects
    """
    if not projects_paths and not group_ids:
        raise ValueError("projects_path and/or group_id must be provided")

    projects = []
    local_projects = []
    remote_projects = []

    if projects_paths:
        if not isinstance(projects_paths, list):
            projects_paths = [projects_paths]
        for projects_path in projects_paths:
            local_projects += discover_local_projects(
                projects_path, whitelist=whitelist, blacklist=blacklist)
    projects += local_projects
    if group_ids:
        if not isinstance(group_ids, list):
            group_ids = [group_ids]
        for group_id in group_ids:
            remote_projects += discover_remote_projects(
                group_id, whitelist=whitelist, blacklist=blacklist)

    for remote_project in remote_projects:
        if remote_project.name not in [local_project.name 
                                       for local_project 
                                       in local_projects]:
            projects.append(remote_project)
        else:
            for local_project in local_projects:
                if remote_project.name == local_project.name:
                    local_project.url = remote_project.url

    return projects


def discover_local_projects(projects_path, whitelist=None, blacklist=None):
    """Discovers local projects

    Args:
    projects_path: Path to opencpi projects
    whitelist:     List of projects to include
    blacklist:     List of projects not to include

    Returns:
        projects: List of opencpi projects
    """
    projects = []
    for project_path in projects_path.glob('*'):
        project_name = project_path.name

        if (Path(project_path, "Project.xml").is_file() 
                or Path(project_path, "Project.mk").is_file()):
            if blacklist and project_name in blacklist:
                continue
            if whitelist and project_name not in whitelist:
                continue
            group = project_path.parent.stem
            group = 'opencpi' if group == 'projects' else group
            group = 'osp' if group == 'osps' else group
            project = Project(name=project_name, path=project_path, 
                            group=group)
            projects.append(project)
        else:
            projects += discover_local_projects(project_path, 
                                                blacklist=blacklist)

    return projects


def discover_remote_projects(group_id, group_name='opencpi', whitelist=None,
                             blacklist=None):
    """Discovers remote projects

    Uses curl command to call gitlab api to collect project group data.

    Args:
        group_id:   Gitlab ID of project group
        group_name: Name of project group
        whitelist:  List of projects to include
        blacklist:  List of projects not to include     

    Returns:
        List of Project namedtuples
    """
    projects = []
    group_id = str(group_id)
    base_url = 'https://gitlab.com/api/v4/groups'
    projects_url = '/'.join([base_url,group_id,'projects'])
    subgroups_url = '/'.join([base_url,group_id,'subgroups'])

    # Get project data
    with urlopen(projects_url) as response:
        project_dicts = load(response)
    for project_dict in project_dicts:
        project_name = project_dict['path']
        project_id = str(project_dict['id'])
        if blacklist:
            if project_name in blacklist or project_id in blacklist:
                continue
        if whitelist:
            if project_name not in whitelist and project_id not in whitelist:
                continue
        project_url = project_dict['http_url_to_repo']
        project = Project(project_name, url=project_url, 
                            project_id=project_id, group=group_name)
        projects.append(project)
    
    # Get subgroup data and recurse to get project data
    with urlopen(subgroups_url) as response:
        subgroups = load(response)
    for subgroup_dict in subgroups:
        subgroup_name = subgroup_dict['path']
        subgroup_id = subgroup_dict['id']
        recursive_projects = discover_remote_projects(
            group_id=subgroup_id, group_name=subgroup_name,
            whitelist=whitelist, blacklist=blacklist)
        projects += recursive_projects

    return projects
