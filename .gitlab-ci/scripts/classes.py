import asyncio
import os
import shutil
from pathlib import Path
from re import match
from typing import List, Optional, Union, Coroutine, Any
import xml.etree.ElementTree as ET

import utils
import report


class Project():
    """Wrapper class for OpenCPI project.

    Attributes:
        path: Path to the Platform.
        is_osp: Whether the Project is an OSP.
    """

    def __init__(self, path: Path) -> None:
        """Project initializer.

        Args:
            path: Path to the project.
        """
        self.path = path
        self.name = self.path.name
        self.is_osp = self.name.startswith('ocpi.osp.')
        self._primitives = None
        self._workers = None
        self._assemblies = None
        self._tests = None
        self._platforms = None
        self._libraries = None
        self._rcc_workers = None
        self._hdl_workers = None
        self._rcc_platforms = None
        self._hdl_platforms = None
        self._project_dependencies = None
        self._xml_path = self.path.joinpath('Project.xml')

    @property
    def project_dependencies(self) -> List[str]:
        if self._project_dependencies is not None:
            return self._project_dependencies
        if self._xml_path.exists():
            tree = ET.parse(self._xml_path)
            root = tree.getroot()
            attrib = {key.lower(): value for key, value in root.attrib.items()}
            self._project_dependencies = attrib.get('projectdependencies', '').split()
        else:
            self._project_dependencies = []
        return self.project_dependencies

    @property
    def rcc_workers(self) -> List['Asset']:
        """Rcc worker Assets discovered in Project."""
        if self._rcc_workers is None:
            self.workers
        return self._rcc_workers

    @property
    def hdl_workers(self) -> List['Asset']:
        """Hdl worker Assets discovered in Project."""
        if self._hdl_workers is None:
            self.workers
        return self._hdl_workers

    @property
    def rcc_platforms(self) -> List['RccPlatform']:
        """RccPlatforms discovered in Project."""
        if self._rcc_platforms is None:
            self.platforms
        return self._rcc_platforms

    @property
    def hdl_platforms(self) -> List['HdlPlatform']:
        """HdlPlatforms discovered in Project."""
        if self._hdl_platforms is None:
            self.platforms
        return self._hdl_platforms

    @property
    def platforms(self) -> List['Platform']:
        """OpenCPI Platforms discovered in the Project."""
        if self._platforms is not None:
            return self._platforms
        rcc_path = self.path.joinpath('rcc', 'platforms')
        hdl_path = self.path.joinpath('hdl', 'platforms')

        def make_platforms(platforms_path, PlatformClass):
            if not platforms_path.exists():
                return
            utils.logger.debug(f'Searching for platforms in {platforms_path} ...')
            for platform_path in platforms_path.glob('*'):
                if platform_path.joinpath(platform_path.name).with_suffix('.mk').exists():
                    utils.logger.debug(f'Discovered platform at {platform_path}')
                    yield PlatformClass(platform_path, self)
                elif platform_path.joinpath(platform_path.name).with_suffix('.xml').exists():
                    utils.logger.debug(f'Discovered platform at {platform_path}')
                    yield PlatformClass(platform_path, self)

        self._rcc_platforms = list(make_platforms(rcc_path, RccPlatform))
        self._hdl_platforms = list(make_platforms(hdl_path, HdlPlatform))
        self._platforms = self._rcc_platforms + self._hdl_platforms
        return self._platforms

    @property
    def libraries(self) -> List['Asset']:
        """OpenCPI libraries discovered in the Project."""
        if self._libraries is not None:
            return self._libraries
        utils.logger.debug(f'Discovering libraries in {self.name} ...')
        libs = []
        hdl_path = self.path.joinpath('hdl')
        for lib in ['adapters', 'cards', 'devices']:
            lib_path = hdl_path.joinpath(lib)
            if lib_path.exists():
                utils.logger.debug(f'Discovered library at {lib_path}')
                libs.append(Asset('library', lib_path))
        comp_path = self.path.joinpath('components')
        if not comp_path.exists():
            return libs
        if comp_path.joinpath('specs').exists():
            # Top-level components library
            utils.logger.debug(f'Discovered library at {comp_path}')
            libs.append(Asset('library', comp_path))
        else:
            # Check for nested components libraries
            for path in comp_path.glob('*'):
                if path.is_dir() and path.joinpath('specs').exists():
                    utils.logger.debug(f'Discovered library at {path}')
                    libs.append(Asset('library', path))
        self._libraries = libs
        return self._libraries

    @property
    def workers(self) -> List['Asset']:
        """OpenCPI workers discovered in the Project."""
        if self._workers is not None:
            return self._workers
        hdl_workers = []
        rcc_workers = []
        for library in self.libraries:
            utils.logger.debug(f'Discovering workers in {library.name} ...')
            for worker_path in library.path.glob('*'):
                if worker_path.suffix == '.rcc':
                    utils.logger.debug(f'Discovered rcc worker at {worker_path}')
                    rcc_workers.append(Asset('worker', worker_path))
                elif worker_path.suffix == '.hdl':
                    utils.logger.debug(f'Discovered hdl worker at {worker_path}')
                    hdl_workers.append(Asset('worker', worker_path))
        self._hdl_workers = hdl_workers
        self._rcc_workers = rcc_workers
        self._workers = self._hdl_workers + self._rcc_workers
        return self._workers

    @property
    def tests(self) -> List['Asset']:
        """OpenCPI tests discovered in the Project."""
        if self._tests is not None:
            return self._tests
        tests = []
        for library in self.libraries:
            utils.logger.debug(f'Discovering assemblies in {library.name} ...')
            for test_path in library.path.glob('*.test'):
                if not (test_path.with_suffix('.hdl').exists()
                        or test_path.with_suffix('.rcc').exists()):
                    continue
                if not test_path.joinpath(f'{test_path.stem}-test.xml').exists():
                    continue
                utils.logger.debug(f'Discovered test at {test_path}')
                tests.append(Test(test_path))
        self._tests = tests
        return self._tests

    @property
    def primitives(self) -> Optional['Asset']:
        """OpenCPI tests discovered in the Project."""
        if self._primitives is not None:
            return self._primitives
        utils.logger.debug(f'Discovering primitives in {self.name} ...')
        prim_path = self.path.joinpath('hdl', 'primitives')
        if prim_path.exists():
            utils.logger.debug(f'Discovered primitives at {prim_path}')
            return Asset(f'primitives', prim_path, name=self.path.name)
        return None

    @property
    def assemblies(self) -> List['Asset']:
        """OpenCPI assemblies discovered in the Project."""
        if self._assemblies is not None:
            return self._assemblies
        utils.logger.debug(f'Discovering assemblies in {self.name} ...')
        assemblies = []
        assemblies_path = self.path.joinpath('hdl', 'assemblies')
        for assembly_path in assemblies_path.glob('*'):
            if assembly_path.joinpath(assembly_path.name).with_suffix('.xml').exists():
                utils.logger.debug(f'Discovered assembly at {assembly_path}')
                assemblies.append(Asset('assembly', assembly_path))
        self._assemblies = assemblies
        return self._assemblies

    def get_platform(self, name: str) -> Optional['Platform']:
        """Get platform by name.

        Args:
            name: Name of Platform to get.

        Returns:
            Platform if found with name; otherwise, None.
        """
        for platform in self.platforms:
            if platform.name == name:
                return platform
        return None

    def get_test(self, path: Path) -> Optional['Test']:
        """Get test by path.

        Args:
            path: Path of Test to get.

        Returns:
            Test if found at path; otherwise, None.
        """
        for test in self.tests:
            if test.path == path:
                return test
        return None


class Platform():
    """Wrapper class for OpenCPI platform.

    Attributes:
        path: Path to the Platform.
        name: Name of the Platform.
        model: Model of the platform (e.g., 'hdl', 'rcc')
        project: Project the Platform belongs to.
    """

    def __init__(self, path: Path, project: Project, model: Optional[str] = ...) -> None:
        """Platform initializer.

        Args:
            path: Path to the platform.
            project: Project the platform belongs to.
            model: Model of the platform (e.g., 'hdl', 'rcc')
        """
        self.path = path
        self.project = project
        self.name = path.name
        self._xml_path = self.path.joinpath(self.name).with_suffix('.xml')
        self._mk_path = self.path.joinpath(self.name).with_suffix('.mk')
        if model in [None, ...]:
            self.model = self.path.parent.parent.name
        else:
            self.model = model
        self._part = None
        self._target = None

    async def install(self) -> Coroutine[Any, Any, report.Case]:
        """Perform a minimal install of the platform

        Returns:
            Coroutine report.Case of the result of the install.
        """
        cmd = ['ocpiadmin', 'install', 'platform', self.name, '--minimal']
        msg = f'installing {self.model} platform [blue]{self.name}[/blue]'
        name = f'install {self.name}'
        result = await utils.exec_cmd(name, cmd, 1, self.mem, log_msg=msg)
        return result

    def _build_assets(self, assets: List['Asset'], timeout: Optional[int] = None
                      ) -> List[Coroutine[Any, Any, report.Case]]:
        """Build assets for the Platform.

        Wrapped in a utils.task decorator to manage execution of
        asynchronous tasks.

        Args:
            assets: List of Assets to build for the HdlPlatform.
            timeout: How long in seconds to allow test run to execute
                before being forcefully terminated.

        Returns:
            List of Coroutine report.Cases representing result of the 
            asset builds.
        """
        return [asset.build(self, timeout=timeout) for asset in assets]


class RccPlatform(Platform):
    """Wrapper class for OpenCPI rcc platform.

    Attributes:
        path: Path to the Platform.
        name: Name of the Platform.
        model: Model of the platform (i.e, 'rcc').
        project: Project the Platform belongs to.
        mem: Amount of memory in GB that building the Platform will
            request.
    """
    mem = int(os.getenv('RCC_PLATFORM_MEM', 8))

    def __init__(self, path: Path, project: Project) -> None:
        """RccPlatform initializer.

        Args:
            path: Path to the platform.
            project: Project the platform belongs to.
        """
        super().__init__(path, project, model='rcc')

    async def build(self, projects: List[Project]) -> Coroutine[Any, Any, report.Suite]:
        """Builds the RccPlatform.

        Args:
            projects: The Projects to build for

        Returns:
            Coroutine report.Suite representing result of the build.
        """
        projects = [project for project in projects if not project.is_osp or project == self.project]
        loop = asyncio.get_event_loop()
        project_names = [project.name for project in projects]
        if self.name.startswith('xilinx') and self.project.name in project_names:
            # Clone necessary repositories to install platform
            git_path = Path(os.getenv('OCPI_XILINX_GIT_REPOSITORY',
                                      os.getenv('OCPI_TOOLS_DIR', str(Path.cwd())) + '/git'))
            git_path.mkdir(exist_ok=True)
            tasks = [
                loop.create_task(utils.clone_repo('https://github.com/Xilinx/linux-xlnx.git',
                                 git_path.joinpath('linux-xlnx'))),
                loop.create_task(utils.clone_repo('https://github.com/Xilinx/u-boot-xlnx.git',
                                 git_path.joinpath('u-boot-xlnx')))
            ]
            results = await asyncio.gather(*tasks)
            if any(result.code for result in results) != 0:
                # Repo clone failure
                time = sum([result.time for result in results])
                return report.Suite(self.name, time, results)
            os.environ['OCPI_XILINX_GIT_REPOSITORY'] = str(git_path)
        results = []
        if self.project.name in project_names:
            # If this platform belongs to a project to build for, install platform
            result = await self.install()
            if result.code:
                return report.Suite(self.name, result.code, result.time, [result])
            results.append(result)
        # Gather and build workers
        workers = [worker for project in projects for worker in project.rcc_workers]
        result = await self._build_workers(workers)
        results += result.cases
        # Gather and build tests
        tests = [test for project in projects for test in project.tests]
        result = await self._build_tests(tests)
        results += result.cases
        time = sum([result.time for result in results])
        if self.name.startswith('xilinx') and self.project.name in project_names:
            # Cleanup repositories necessary to install platform
            shutil.rmtree(str(git_path))
        return report.Suite(self.name, result.code, time, results)

    @utils.task(task_name='workers')
    def _build_workers(self, workers: List['Asset']) -> List[Coroutine[Any, Any, report.Case]]:
        """Build workers for the RccPlatform.

        Wrapped in a utils.task decorator to manage execution of
        asynchronous tasks.

        Args:
            workers: List of workers to build for the RccPlatform.

        Returns:
            List of Coroutine report.Cases representing result of the 
            test builds.
        """
        return self._build_assets(workers)

    @utils.task(task_name='tests')
    def _build_tests(self, tests: List['Asset']) -> List[Coroutine[Any, Any, report.Case]]:
        """Build tests for the RccPlatform.

        Wrapped in a utils.task decorator to manage execution of
        asynchronous tasks.

        Args:
            tests: List of Tests to build for the RccPlatform.

        Returns:
            List of Coroutine report.Cases representing result of the 
            test builds.
        """
        return self._build_assets(tests)


class HdlPlatform(Platform):
    """Wrapper class for OpenCPI hdl platform.

    Attributes:
        path: Path to the Platform.
        name: Name of the Platform.
        model: Model of the platform (i.e, 'hdl').
        project: Project the Platform belongs to.
        mem: Amount of memory in GB that building the Platform will
            request.
    """
    mem = int(os.getenv('HDL_PLATFORM_MEM', 16))

    def __init__(self, path: Path, project: Project) -> None:
        """Platform initializer.

        Args:
            path: Path to the platform.
            project: Project the platform belongs to.
        """
        super().__init__(path, project, model='hdl')

    @property
    def part(self) -> Optional[str]:
        """Get platform part name.

        Parses, in order, the platform .xml and the platform .mk file
        to attempt to find the platform part name.
        """
        if self._part is None:
            # Attempt to find hdl part in either xml or mk file
            try:
                try:
                    # Parse xml file, searching for 'part' or 'Part
                    tree = ET.parse(self._xml_path)
                    root = tree.getroot()
                    part = root.attrib['part'] if 'part' in root.attrib else root.attrib['Part']
                    self._part = part.split('-')[0]
                except KeyError:
                    # Parse mk file, searching for "HdlPart_<platform name>"
                    with self._mk_path.open('r') as f:
                        for line in f:
                            m = match(rf'HdlPart_{self.name}:?=(\w+)', line)
                            if m:
                                self._part = m.group(1)
                                break
            except:
                # Unable to find part, keep attr set to 'None'
                pass
        return self._part

    @property
    def target(self) -> Optional[str]:
        """Get platform target name.

        Parses tools/include/hdl/hdl-targets.xml to get target from
        part name.
        """
        if self._target is not None:
            return self._target
        ocpi_root_path = Path(os.getenv('OCPI_ROOT_DIR', Path.cwd()))
        targets_xml_path = ocpi_root_path.joinpath('tools', 'include', 'hdl', 'hdl-targets.xml')
        tree = ET.parse(str(targets_xml_path))
        root = tree.getroot()
        for vendor in root.findall('vendor'):
            for family in vendor.findall('family'):
                parts = family.get('parts', '').split()
                if self.part in parts:
                    self._target = family.get('name', None)
                    return self._target
                if self.part == family.get('toolset', ''):
                    self._target = self.part
                    return self._target
        for toolset in root.findall('toolset'):
            if toolset.get('name', '') == self.part:
                self._target = self.part
                break
        return self._target

    async def build(self, projects: List[Project]) -> Coroutine[Any, Any, report.Suite]:
        """Builds the HdlPlatform.

        Args:
            projects: The Projects to build for

        Returns:
            Coroutine report.Suite representing result of the build.
        """
        projects = [project for project in projects if not project.is_osp or project == self.project]
        projects_names = [project.name for project in projects]
        results = []
        if self.project.name in projects_names:
            # If this platform belongs to a project to build for, install platform
            result = await self.install()
            if result.code:
                return report.Suite(result.name, result.code, result.time, [result])
            results.append(result)
        # Install tests and assemblies
        assemblies = [assembly for project in projects
                      for assembly in project.assemblies+project.tests]
        result = await self._build_assemblies(assemblies)
        results += result.cases
        time = sum([case.time for case in results])
        return report.Suite(self.name, result.code, time, results)

    @utils.task(task_name='assemblies')
    def _build_assemblies(self, assemblies: List['Asset']
                          ) -> List[Coroutine[Any, Any, report.Case]]:
        """Build assemblies for the HdlPlatform.

        Wrapped in a utils.task decorator to manage execution of
        asynchronous tasks.

        Args:
            assemblies: List of Assets to build for the HdlPlatform.

        Returns:
            List of Coroutine report.Cases representing result of the 
            assembly builds.
        """
        return self._build_assets(assemblies, timeout=39600)


class Target():
    """Wrapper class for OpenCPI target.

    Attributes:
        name: Name of the Target.
        model: Model of the Target.
        mem: Amount of memory in GB that building the Platform will
            request.
    """
    mem = int(os.getenv('HDL_TARGET_MEM', 12))

    def __init__(self, name: str) -> None:
        """Platform initializer.

        Args:
            name: Name of the target.
        """
        self.name = name
        self.model = 'hdl'

    async def build(self, projects: List[Project]) -> Coroutine[Any, Any, report.Suite]:
        """Builds the Target.

        Args:
            projects: The Projects to build for.

        Returns:
            Coroutine report.Suite representing result of the build.
        """
        core_primitives = None
        project_primitives = []
        cases = []
        for project in projects:
            if project.name == 'core':
                core_primitives = project.primitives
            elif project.primitives is not None:
                project_primitives.append(project.primitives)
        # Build core primitives
        result = await self._build_core_primitives(core_primitives)
        if result.code:
            return result
        cases += result.cases
        # Build all other primitives
        result = await self._build_primitives(project_primitives)
        cases += result.cases
        if not result.code:
            hdl_workers = [worker for project in projects for worker in project.hdl_workers]
            # Build hdl workers
            result = await self._build_workers(hdl_workers)
            cases += result.cases
        time = sum([case.time for case in cases])
        return report.Suite(self.name, result.code, time, cases)

    def _build_assets(self, assets: List['Asset'], timeout: Optional[int] = None
                      ) -> List[Coroutine[Any, Any, report.Case]]:
        """Build assets for the Target.

        Wrapped in a utils.task decorator to manage execution of
        asynchronous tasks.

        Args:
            assets: List of Assets to build for the HdlPlatform.
            timeout: How long in seconds to allow test run to execute
                before being forcefully terminated.

        Returns:
            List of Coroutine report.Cases representing result of the 
            asset builds.
        """
        return [asset.build(self, timeout=timeout) for asset in assets]

    @utils.task(task_name='core primitives')
    def _build_core_primitives(self, core_primitives: 'Asset'
                               ) -> List[Coroutine[Any, Any, report.Case]]:
        """Build core primitives for the Target.

        Wrapped in a utils.task decorator to manage execution of
        asynchronous tasks.

        Args:
            core_primitives: Asset to build.

        Returns:
            List of Coroutine report.Cases representing result of the 
            core_primitives build.
        """
        return self._build_assets([core_primitives], timeout=3600)

    @utils.task(task_name='primitives')
    def _build_primitives(self, primitives: List['Asset']
                          ) -> List[Coroutine[Any, Any, report.Case]]:
        """Build primitives for the Target.

        Wrapped in a utils.task decorator to manage execution of
        asynchronous tasks.

        Args:
            primitives: List of Assets to build.

        Returns:
            List of Coroutine report.Cases representing result of the 
            primitive builds.
        """
        return self._build_assets(primitives, timeout=3600)

    @utils.task(task_name='workers')
    def _build_workers(self, workers: List['Asset']) -> List[Coroutine[Any, Any, report.Case]]:
        """Build workers for Target.

        Wrapped in a utils.task decorator to manage execution of
        asynchronous tasks.

        Args:
            workers: List of Assets to build for the Target.

        Returns:
           List of Coroutine report.Cases representing result of the 
           worker builds.
        """
        return self._build_assets(workers, timeout=21600)


class Asset():
    """Wrapper class for OpenCPI assets.

    Wrapper class for OpenCPI asset.

    Attributes:
        type: Type of Asset.
        path: Path to the Asset.
        name: Name of the Asset.
    """

    def __init__(self, type: str, path: Path, name: Optional[str] = ...) -> None:
        """
        Args:
            type: The type of the asset (e.g., worker, assembly)
            path: Path to the component unit test.
            name: Name of the asset. Defaults to name of path.
        """
        self.type = type
        self.path = path
        self.name = name if name not in [None, ...] else self.path.name

    async def build(self, target: Union[Target, Platform], timeout: Optional[int] = None
                    ) -> Coroutine[Any, Any, report.Case]:
        """Builds the asset.

        Args:
            target: Target or Platform to build the asset for.
            timeout: How long in seconds to allow test run to execute
                before being forcefully terminated.

        Returns:
            Coroutine report.Case representing the result of the asset 
            build.
        """
        target_type = 'target' if isinstance(target, Target) else 'platform'
        cmd = ['ocpidev', 'build', f'-d', str(self.path), f'--{target.model}-{target_type}',
               f'{target.name}']
        if self.type == 'worker':
            cmd.append('--artifacts-only')
        if self.type in ['test', 'assembly']:
            cmd.append('--streamlined-build')
        msg = (f'building {self.type} [blue]{self.name}[/blue] for'
               f' {target_type} [cyan]{target.name}[/cyan]')
        result = await utils.exec_cmd(self.name, cmd, 1, 1, log_msg=msg, timeout=timeout)
        return result


class Test(Asset):
    """Wrapper class to represent OpenCPI component unit test.

    Attributes:
        type: Type of Asset.
        path: Path to the Asset.
        name: Name of the Asset.
    """

    def __init__(self, path: Path) -> None:
        """
        Args:
            path: Path to the component unit test.
        """
        super().__init__('test', path)
        self._cases = None

    @property
    def cases(self) -> List[str]:
        """Get list of Test case names.

        Parses cases.xml in the Test gen directory to get cases.
        Therefore, the cases must be generated to be retrieved.
        """
        if self._cases is not None:
            return self._cases
        utils.logger.debug(f'Discovering cases for test {self.name}')
        cases_xml = self.path.joinpath('gen', 'cases.xml')
        if not cases_xml.exists():
            return self._cases
        tree = ET.parse(str(cases_xml))
        root = tree.getroot()
        self._cases = []
        for case in root.findall('case'):
            name = case.attrib['name']
            utils.logger.debug(f'Discovered case {name} for test {self.name}')
            self._cases.append(name)
        utils.logger.debug(f'Discovered {len(self._cases)} cases for test {self.name}')
        return self._cases

    async def run(self, model: str, hdl_platform: str, rcc_platform: Optional[str] = None,
                  timeout: Optional[int] = None) -> Coroutine[Any, Any, report.Suite]:
        """Run test.

        Since both an HdlPlatform and RccPlatform are required for
        HWIL runs, the model must be procided to specify which
        platform the test will actually run against. For HWIL jobs,
        the task will be wrapped in an ocpiremote decorator.

        Args:
            mode: The model to run test against.
            hdl_platform: HdlPlatform to run test against.
            rcc_platform: RccPlatform to run test against.
            timeout: How long in seconds to allow test run to execute
                before being forcefully terminated.

        Returns:
            Coroutine report.Suite representing result of running 
            test.
        """
        platform = hdl_platform if model == 'hdl' else rcc_platform
        result = await self.generate(platform)
        if result.code:
            return report.Suite(self.name, result.code, result.time, [result])
        if platform.name.endswith('sim'):
            # Simulator job; run normally
            func = self._run
        else:
            # HWIL job; wrap in ocpiremote decorator
            func = utils.ocpiremote(hdl_platform, rcc_platform)(self._run)
        result = await func(platform, timeout=timeout)
        return report.Suite(self.name, result.code, result.time, result.cases)

    @utils.task(task_name='test cases')
    def _run(self, platform: Platform, timeout: Optional[int] = None
             ) -> List[Coroutine[Any, Any, report.Case]]:
        """Run test.

        Wrapped in a utils.task decorator to manage execution of
        asynchronous tasks.

        Args:
            platform: Platform to run test cases against.
            timeout: How long in seconds to allow test run to execute
                before being forcefully terminated.

        Returns:
            report.Suite representing result of running test.
        """
        return self.run_cases(platform, timeout=timeout)

    def run_cases(self, platform: Platform, timeout: Optional[int] = None
                  ) -> List[Coroutine[Any, Any, report.Case]]:
        """Run test cases.

        Args:
            platform: Platform to run test cases against.
            timeout: How long in seconds to allow test run to execute
                before being forcefully terminated.

        Returns:
            List of Coroutines to run each individual case.
        """
        return [self.run_case(case_idx, platform, timeout=timeout)
                for case_idx in range(len(self.cases))]

    async def run_case(self, case_idx: int, platform: Platform, timeout: Optional[int] = None
                       ) -> Coroutine[Any, Any, report.Case]:
        """Run an individual test case.

        Args:
            case_idx: Index of test case to run.
            platform: Platform to run test against.
            timeout: How long in seconds to allow test run to execute
                before being forcefully terminated.

        Returns:
            Coroutine report.Case representing result of test run.
        """
        case_name = self.cases[case_idx] if case_idx < len(self.cases) else ''
        msg = (f'running test [blue]{self.name}[/blue] case [blue]{case_name}[/blue] against'
               f' {platform.model} platform [cyan]{platform.name}[/cyan]')
        cmd = ['ocpidev', 'run', '-d', str(self.path), '--only-platform', platform.name,
               '--case', case_name]
        result = await utils.exec_cmd(case_name, cmd, 1, platform.mem,
                                      platform_lock_request=platform, log_msg=msg, timeout=timeout)
        return result

    async def generate(self, platform: Platform) -> Coroutine[Any, Any, report.Case]:
        """Generate test case inputs.

        Args:
            platform: Platform to gernate test cases for.

        Returns:
            Coroutine report.Case representing result of command to 
            generate the test cases.
        """
        cmd = ['ocpidev', 'build', '-d', str(self.path),
               f'--{platform.model}-platform', platform.name, '--generate']
        msg = (f'generating [blue]{self.name}[/blue] cases for {platform.model} platform'
               f' [cyan]{platform.name}[/cyan]')
        return await utils.exec_cmd(self.name, cmd, 1, 2, log_msg=msg, timeout=300)


def get_projects(ocpi_root_path: Optional[Path] = None, whitelist: Optional[List[str]] = None,
                 blacklist: Optional[List[str]] = None) -> List[Project]:
    """Discover all OpenCPI Projects.

    If whitelist not None, the discovered Projects will be filtered
    out if their names do not appear in the whitelist.

    Args:
        ocpi_root_path: Path to the root of the OpenCPI tree.
        whitelist: List of project names to include in discovery.
        blacklist: List of project name to exclude in discovery.

    Returns:
        List of discovered OpenCPI projects.
    """
    if ocpi_root_path is None:
        ocpi_root_path = utils.get_ocpi_root_path()
    projects = []
    for project_path in ocpi_root_path.joinpath('project-registry').glob('*'):
        project_path = project_path.resolve()
        if (not project_path.joinpath('Project.xml').exists()
                and not project_path.joinpath('Project.mk').exists()):
            continue
        if ((whitelist is not None and project_path.name not in whitelist)
                or (blacklist is not None and project_path.name in blacklist)):
            utils.logger.debug(f'Filtering out project at {project_path}')
            continue
        utils.logger.debug(f'Discovered project at {project_path}')
        projects.append(Project(project_path))
    return projects


def get_platform(name: str, projects: Optional[List[Project]] = None) -> Optional[Platform]:
    """Find an OpenCPI Platform by name.

    If projects is not provided, will first attempt to discover
    projects.

    Args:
        name: Name of Platform to find.
        projects: List of Projects to discover Platform in.

    Returns:
        The Platform with the provided name if it can be found;
        otherwise None.

    Raises:
        Exception if platform cannot be found.
    """
    utils.logger.debug(f'Searching for platform "{name}" ...')
    if projects is None:
        ocpi_root_path = utils.get_ocpi_root_path()
        projects = get_projects(ocpi_root_path)
    for project in projects:
        utils.logger.debug(f'Searching for platform "{name}" in project "{project.name}" ...')
        platform = project.get_platform(name)
        if platform:
            utils.logger.debug(f'Discovered platform "{name}" in project "{project.name}"')
            return platform
    raise Exception(f'Unable to find platform "{name}"')


def get_test(path: Path, projects: Optional[List[Project]] = None) -> Optional[Platform]:
    """Returns a Test located at provided path.

    Args:
        path: Path to the test to get.
        projects: Projects to search for the test within.

    Returns:
        Test located at provided path.

    Retises: Exception if a Test can not be found at provided path.
    """
    utils.logger.debug(f'Searching for test "{path}" ...')
    if projects is None:
        ocpi_root_path = utils.get_ocpi_root_path()
        projects = get_projects(ocpi_root_path)
    for project in projects:
        utils.logger.debug(f'Searching for test "{path}" in project "{project.path}" ...')
        test = project.get_test(path)
        if test:
            utils.logger.debug(f'Discovered test "{path}" in project "{project.path}"')
            return test
    raise Exception(f'Unable to find test "{path}"')
