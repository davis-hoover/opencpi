from pathlib import Path

class Project():
    

    def __init__(self, path):

        if isinstance(path, str):
            path = Path(path)

        self.name = path.stem
        self.path = path
        self.libraries = self.discover_libraries()


    @classmethod
    def discover_projects(cls, projects_path):
        path = Path(projects_path)
        projects = []

        if path.is_absolute():
            path = project.relative_to(Path.cwd())

        for project_path in path.glob('*'):
            project_path = Path(project_path)

            if project_path.is_symlink():
                project_path = project_path.resolve()

            project_path = project_path.relative_to(Path.cwd())
            project = cls(project_path)
            projects.append(project)

        return projects
    

    def discover_libraries(self):
        self.libraries = set()
        components_path = Path(self.path, 'components')
        hdl_path = Path(self.path, 'hdl')
        library_names = ['primitives', 'devices', 'cards', 'adapters', 'platforms', 'assemblies']

        for library_path in hdl_path.glob('*'):
            if Path(library_path, 'Makefile').is_file():
                if library_path.stem in library_names:
                    self.libraries.add(library_path)

        if Path(components_path, 'specs').is_dir():
            self.libraries.add(components_path)
        else:
            for library_path in components_path.glob('*'):
                if Path(library_path, 'specs').is_dir():
                    self.libraries.add(library_path)

        return list(self.libraries)


    @staticmethod
    def get_project(projects, project_name):
        for project in projects:
            if project.name == project_name:
                return project


    def get_library(self, library_name):
        for library in self.libraries:
            if library.stem == library_name:
                return library