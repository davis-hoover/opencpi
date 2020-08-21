#!/usr/bin/env python3

from collections import namedtuple
from pathlib import Path

Project = namedtuple('project', 'name, libraries, path')
Library = namedtuple('library', ('name path project_name'
                                 ' is_buildable is_testable'))


def discover_projects(projects_path, blacklist=None):
    projects = []
    for project_path in projects_path.glob('*'):
        project_name = project_path.stem

        if project_name in blacklist:
            continue

        project_libraries = discover_libraries(project_name, project_path)
        project = Project(name=project_name, libraries=project_libraries, 
                          path=project_path)
        projects.append(project)

    return projects


def discover_libraries(project_name, project_path):
    libraries = []
    components_path = Path(project_path, 'components')
    hdl_path = Path(project_path, 'hdl')
    library_names = ['primitives', 'devices', 'cards', 
                     'adapters', 'platforms', 'assemblies']

    for library_path in hdl_path.glob('*'):

        if not Path(library_path, 'Makefile').is_file():
            continue

        library_name = library_path.stem
        if library_name in library_names:
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