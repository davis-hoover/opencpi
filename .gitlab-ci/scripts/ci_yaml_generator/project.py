#!/usr/bin/env python3

from pathlib import Path
# from sys import exit

class Project():
    __slots__ = "name", "libraries", "path", "is_osp"

    def __init__(self, name, path, is_osp, libraries=None):
        self.name = name
        self.path = path
        self.is_osp = is_osp
        self.libraries = libraries

    @classmethod
    def discover_projects(cls, projects_path, discover_libraries=True, platform_filter=None):
        if isinstance(projects_path, str):
            projects_path = Path(projects_path)
    
        if not isinstance(projects_path, Path):
            raise TypeError('projects_path must be a str or pathlib Path')

        projects = []

        # if projects_path.is_absolute():
        #     projects_path = projects_path.relative_to(Path.cwd())

        for project_path in projects_path.glob('*'):
            project_name = project_path.stem
            project = cls(name=project_name, path=project_path, is_osp=False)

            if discover_libraries:
                project.libraries = project.discover_libraries()

            projects.append(project)

        return projects

    def discover_libraries(self):
        libraries = []
        components_path = Path(self.path, 'components')
        hdl_path = Path(self.path, 'hdl')
        library_names = ['primitives', 'devices', 'cards', 'adapters', 'platforms', 'assemblies']

        for library_path in hdl_path.glob('*'):
            if Path(library_path, 'Makefile').is_file():
                if library_path.stem in library_names:
                    library_name = library_path.stem
                    library = Library(library_name, library_path, self.name)
                    libraries.append(library)

        if Path(components_path, 'specs').is_dir():
            library_name = components_path.stem
            library = Library(library_name, components_path, self.name, is_testable=True)
            libraries.append(library)
        else:
            for library_path in components_path.glob('*'):
                if Path(library_path, 'specs').is_dir():
                    library_name = library_path.stem
                    library = Library(library_name, library_path, self.name, is_testable=True)
                    libraries.append(library)

        return libraries


class Library():

    def __init__(self, name, path, project, is_buildable=True, is_testable=False):
        self.name = name
        self.path = path
        self.project = project
        self.is_buildable = is_buildable
        self.is_testable = is_testable