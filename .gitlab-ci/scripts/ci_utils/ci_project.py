#!/usr/bin/env python3

import json
from collections import namedtuple
from pathlib import Path
from urllib.request import urlopen

Project = namedtuple('project', 'name, libraries, path, is_osp')
Library = namedtuple('library', ('name path project_name'
                                 ' is_buildable is_testable'))


def discover_projects(projects_path, blacklist=None):
    """Search opencpi for projects

    Calls discover_libraries() to search for project libraries.

    Args:
       projects_path:   Path to opencpi projects
       blacklist:       List of projects not to include

    Returns:
        projects: List of opencpi projects
    """
    projects = []
    for project_path in projects_path.glob('*'):
        project_name = str(project_path).split('.')[-1]

        if blacklist and project_name in blacklist:
            continue

        makefile_path = Path(project_path, 'Makefile')
        if not makefile_path.is_file():
            continue

        makefile_path = Path(project_path, 'Makefile')
        if not makefile_path.is_file():
            continue

        library_blacklist = ['vendors']
        project_libraries = discover_libraries(project_name, project_path,
                                               blacklist=library_blacklist)
        project = Project(name=project_name, libraries=project_libraries,
                          path=project_path, is_osp=False)
        projects.append(project)

    return projects


def discover_libraries(project_name, project_path, blacklist=None):
    """Search for libraries for opencpi project

    Will search for hdl libraries in:
        <project_path>/hdl/
    and for components in:
        <project_path>/components/
    Determines if a directory is a component library by existence of
    directory
        specs
    Determines if a directory is an hdl library by existence of
        Makefile

    Args:
       project_name: Name of project to find libraries for
       project_path: Path of project to search for libraries in
       blacklist:    List of libraries not to include

    Returns:
        libraries: List of project libraries
    """
    libraries = []
    components_path = Path(project_path, 'components')
    hdl_path = Path(project_path, 'hdl')

    for library_path in hdl_path.glob('*'):

        if not Path(library_path, 'Makefile').is_file():
            continue

        library_name = library_path.stem

        if blacklist and library_name in blacklist:
            continue

        library = Library(library_name, library_path, project_name,
                            is_buildable=True, is_testable=False)
        libraries.append(library)

    if Path(components_path, 'specs').is_dir():
        library_name = components_path.stem
        library = Library(name=library_name, path=components_path,
                          project_name=project_name, is_buildable=True,
                          is_testable=True)
        libraries.append(library)
    else:
        for library_path in components_path.glob('*'):

            if not Path(library_path, 'specs').is_dir():
                continue

            library_name = library_path.stem
            library = Library(name=library_name, path=library_path,
                                project_name=project_name, is_buildable=True,
                                is_testable=True)
            libraries.append(library)

    return libraries