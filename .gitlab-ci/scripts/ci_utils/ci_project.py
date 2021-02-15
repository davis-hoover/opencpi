#!/usr/bin/env python3

from json import load
from pathlib import Path
from urllib.request import urlopen
from . import ci_asset

class Project():

    def __init__(self, name, path=None, url=None, project_id=None, assets=None, 
                 is_builtin=True):
        self.name = name
        self.path = path
        self.url = url
        self.id = project_id
        self.is_builtin = is_builtin
        self.assets = assets or ci_asset.discover_assets(
            self.path, whitelist=['primitives', 'cards', 'devices', 'adapters', 
                                  'assemblies', 'components', 'platforms'])


def discover_projects(projects_paths=None, group_ids=None, blacklist=None):
    """Search opencpi for projects

    Calls discover_libraries() to search for project libraries.

    Args:
    projects_path: Path or list of Paths to opencpi projects
    group_ids:     Gitlab ID or list of Gitlab IDs of project group
    blacklist:     List of projects not to include

    Returns:
        projects: List of opencpi projects
    """
    if not projects_paths and not group_ids:
        raise ValueError("projects_path and/or group_id must be provided")

    projects = []

    if projects_paths:
        if not isinstance(projects_paths, list):
            projects_paths = [projects_paths]

        for projects_path in projects_paths:
            projects += discover_local_projects(projects_path, 
                                                blacklist=blacklist)

    if group_ids:
        if not isinstance(group_ids, list):
            group_ids = [group_ids]

        for group_id in group_ids:
            projects += discover_remote_projects(group_id, blacklist=blacklist)

    return projects


def discover_local_projects(projects_path, blacklist=None):
    """Discovers local projects

    Args:
    projects_path: Path to opencpi projects
    blacklist:     List of projects not to include

    Returns:
        projects: List of opencpi projects
    """
    projects = []
    for project_path in projects_path.glob('*'):
        project_name = str(project_path).split('.')[-1].split('/')[-1]

        if blacklist and project_name in blacklist:
            continue

        makefile_path = Path(project_path, 'Makefile')
        if makefile_path.is_file():
            is_builtin = project_path.parent.stem != 'ext'
            project = Project(name=project_name, path=project_path, 
                              is_builtin=is_builtin)
            projects.append(project)
        else:
            projects += discover_local_projects(project_path, 
                                                blacklist=blacklist)

    return projects


def discover_remote_projects(group_id, blacklist=None):
    """Discovers remote projects

    Uses curl command to call gitlab api to collect OSP group data.

    Args:
        group_id:  Gitlab ID of project group
        blacklist: List of projects not to include     

    Returns:
        List of Project namedtuples
    """
    projects = []
    url = 'https://gitlab.com/api/v4/groups/{}/projects'.format(group_id)

    with urlopen(url) as response:
        projects_dict = load(response)

        for project in projects_dict:
            if blacklist and str(project["id"]) in blacklist:
                continue

            project_id = str(project['id'])
            project_url = project['http_url_to_repo']
            project_name = project['name']
            project = Project(project_name, url=project_url, 
                              project_id=project_id, is_builtin=False)
            projects.append(project)

    return projects