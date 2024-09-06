import asyncio
import datetime
from functools import wraps
import logging
import os
from pathlib import Path
from rich.logging import RichHandler
from rich.progress import Progress, MofNCompleteColumn
import time
import traceback
from typing import List, Optional, TYPE_CHECKING, Coroutine, Any

import report

if TYPE_CHECKING:
    from classes import HdlPlatform, RccPlatform, Platform


format = "[ %(filename)s:%(lineno)4s - %(funcName)20s() ] %(message)s"
logging.basicConfig(level=logging.CRITICAL, format=format, datefmt="[%X]", handlers=[RichHandler()])
logger = logging.getLogger("rich")


def get_ocpi_root_path() -> Path:
    """Get root path of OpenCPI from enviroment.

    If OCPI_ROOT_DIR env var not set, uses current working directory.

    Returns:
        Path: OpenCPI root.
    """
    try:
        return Path(os.environ['OCPI_ROOT_DIR'])
    except KeyError:
        raise Exception('Unable to locate OpenCPI root directory.')


def task(task_name=None) -> report.Case:
    """Decorator to manage asynchronous tasks.

    Updates the task Progress as each individual job in the task is
    completed.

    Args:
        task_name: Name of the task to run. Only used for logging and
            for the returned report.Suite

    Returns:
        report.Suite representing the results of the tasks.
    """
    def task_manager(func: callable):
        """Inner decorator.

        Exists solely so that the outer decorator can be provided
        arguments.
        """
        @wraps(func)
        async def task_wrapper(*args, **kwargs):
            logger.debug('')
            with _PROGRESS as progress:
                event_loop = asyncio.get_event_loop()
                tasks = func(*args, **kwargs)
                total = len(tasks)
                completed = 0
                prog_id = progress.add_task(f'{task_name}', total=total)
                event_tasks = map(lambda task: event_loop.create_task(task), tasks)
                results = []
                for task in asyncio.as_completed(event_tasks):
                    result = await task
                    completed += 1
                    progress.advance(prog_id)
                    progress.log(f'{completed}/{total}')
                    results.append(result)
                time = sum([result.time for result in results])
                code = int(any(result.code for result in results))
                return report.Suite(task_name, code, time, results)
        return task_wrapper
    return task_manager


def ocpiremote(hdl_platform, rcc_platform):
    """Decorator to wrap functions in ocpiremote calls.

    The decorated function will be preceded and succeeded by calls
    to ocpiremote.

    Args:
        hdl_platform: HdlPlatform to make the ocpiremote call with.
        rcc_platform: RccPlatform to make the ocpiremote call with.

    Returns:
        report.Suite representing the results of the tasks.
    """
    def ocpiremote_manager(func):
        """Inner decorator.

        Exists solely so that the outer decorator can be provided
        arguments.
        """
        @wraps(func)
        async def ocpiremote_wrapper(*args, **kwargs):
            logger.debug('')
            result = await exec_ocpiremote('reload', hdl_platform, rcc_platform)
            if result.code:
                # Failed loading; skip executing func
                results = report.Suite(result.name, result.code, result.time, [result])
            else:
                result = await exec_ocpiremote('start', hdl_platform, rcc_platform)
                if result.code:
                    # Failed starting; skip running func
                    results = report.Suite(result.name, result.code, result.time, [result])
                else:
                    # Server loaded and started; run func
                    results = await func(*args, **kwargs)
                    await exec_ocpiremote('stop', hdl_platform, rcc_platform)
                await exec_ocpiremote('unload', hdl_platform, rcc_platform)
            return results
        return ocpiremote_wrapper
    return ocpiremote_manager


async def exec_cmd(name: str, cmd: List[str], cpu_request: int, mem_request: int,
                   platform_lock_request: Optional[str] = None, log_msg: Optional[str] = None,
                   timeout: Optional[int] = None) -> Coroutine[Any, Any, report.Case]:
    """Create and execute a subprocess command.

    Args:
        name: Name of the command to run. Used only for the returned
            report.Case.
        cmd: List of strings that make up the actual command to
            execute.
        cpu_request: Amount of CPU cores to request from the
            ResourceLock before executing the command.
        mem_request: Amount of memory (GB) to request from the
            ResourceLock before executing the command.
        platform_lock_request: Platform to request exclusive access to
            from the ResourceLock before executing the command.
        log_msg: Action to display in log messages.
        timeout: How long in seconds to allow the subprocess to run 
            before forcing it to be terminated.

    Returns:
        Coroutine report.Case representing the result of the 
        subprocess execution.
    """
    start_time = None
    resources_acquired = False
    try:
        resources_acquired = await _RESOURCE_LOCK.acquire(
            mem_request, cpu_request, platform_lock_request)
        logger.info(f'Executing command: {" ".join(cmd)}')
        start_time = time.time()
        if log_msg is not None:
            _PROGRESS.log(log_msg.capitalize() + '...')
        proc = await asyncio.create_subprocess_shell(
            ' '.join(cmd),
            stderr=asyncio.subprocess.PIPE,
            stdout=asyncio.subprocess.PIPE
        )
        stdout, stderr = await asyncio.wait_for(proc.communicate(), timeout=timeout)
        rc = proc.returncode
        status_msg = '[red]FAILED[/red]' if rc else '[green]SUCCEEDED[/green]'
    except asyncio.TimeoutError:
        if proc.returncode is None:
            proc.terminate()
        rc = -1
        stdout = stderr = None
        status_msg = '[red]TIMEOUT[/red]'
        logger.error('Timeout')
    except Exception as e:
        stdout = None
        stderr = traceback.format_exception_only(e.__class__, e)[0]
        rc = -1
        status_msg = '[red]EXCEPTION[/red]'
        logger.error(stderr)
    finally:
        if start_time is None:
            stop_time = 0
        else:
            stop_time = time.time() - start_time
        delta = datetime.timedelta(seconds=stop_time)
        if isinstance(stdout, bytes):
            stdout = stdout.decode()
            logger.debug(stdout)
        if isinstance(stderr, bytes):
            stderr = stderr.decode()
            logger.debug(stderr)
        if log_msg is not None:
            _PROGRESS.log(f'{status_msg} {log_msg} ({delta})')
        if resources_acquired is True:
            await _RESOURCE_LOCK.release(mem_request, cpu_request, platform_lock_request)
        return report.Case(name, rc, stop_time, stdout, stderr)


async def exec_ocpiremote(verb: str, hdl_platform: 'HdlPlatform', rcc_platform: 'RccPlatform'
                          ) -> Coroutine[Any, Any, report.Case]:
    """Execute an ocpiremote subprocess call.

    Creates an ocpiremote command to pass to exec_cmd() to create
    the actual subprocess.

    Args:
        verb: ocpiremote subcommand to call.
        hdl_platform: HdlPlatforn to pass to the ocpiremote command.
        rcc_platform: RccPlatform to pass to the ocpiremote command.

    Returns:
        Coroutine report.Case representing the result of the 
        subprocess execution.
    """
    logger.debug('')
    cmd = ['ocpiremote', verb, '-i', '$CI_OCPI_DEVICE_IP', '-u', '$CI_OCPI_DEVICE_USER',
           '-p', '$CI_OCPI_DEVICE_PWD']
    if verb in ['reload', 'load']:
        cmd += ['--hdl-platform', hdl_platform.name, '--rcc-platform', rcc_platform.name, '-r',
                '1000']
    if verb in ['reload', 'load', 'restart', 'start']:
        cmd.append('-b')
    if verb == 'stop':
        msg = f'stopping server on [cyan]{hdl_platform.name}[/cyan]'
    else:
        msg = f'{verb}ing server on [cyan]{hdl_platform.name}[/cyan]'
    result = await exec_cmd(f'ocpiremote {verb}', cmd, 1, 1, log_msg=msg, timeout=300)
    return result


async def clone_repo(repo: str, path: Path) -> Coroutine[Any, Any, report.Case]:
    """Clones a specified git repository.

    Args:
        repo: The git repository to clone.
        path: Path of location to clone repo to.

    Returns:
        None if the provided path already exists. Otherwise, a 
        Coroutine report.Case representing the result of the 
        subprocess execution.
    """
    logger.debug('')
    cmd = 'git', 'clone', repo, str(path)
    msg = f'cloning repository [blue]{repo}[/blue]'
    name = f'clone {repo}'
    if path.exists():
        return report.Case(name, 0, 0, None, None)
    result = await exec_cmd(name, cmd, 1, 2, log_msg=msg)
    return result


def register_dependency(dependency: str) -> Optional[Coroutine[Any, Any, report.Case]]:
    """Registers a project dependency.
    
    Args:
        dependency: Location of the project dependency to register.

    Returns:
        Coroutine report.Case representing the result of registering
        the project depedency.
    """
    if dependency is None:
        return None
    loop = asyncio.get_event_loop()
    cmd = ['ocpidev', 'register', 'project', '-d', dependency]
    msg = f'registering project [blue]{dependency}[/blue]'
    name = f'register {dependency}'
    result = loop.run_until_complete(exec_cmd(name, cmd, 1, 2, log_msg=msg))
    return result


def build_dependencies(dependencies: List[str]) -> Optional[Coroutine[Any, Any, report.Suite]]:
    """Builds project dependencies.

    Will call register_dependency() on each dependency.
    
    Args:
        dependencies: List of locations of project dependencies to 
        build.

    Returns:
        Coroutine report.Suite representing the result of building
        project dependencies.
    """
    if not dependencies:
        return None
    results = []
    loop = asyncio.get_event_loop()
    source_project = os.getenv('CI_OCPI_SOURCE_REF_NAME', None)
    for dependency in dependencies:
        dependency_name = Path(dependency).name
        is_source_project = source_project is not None and source_project == dependency_name
        if is_source_project:
        # Check out source commit
            source_commit = os.getenv('CI_OCPI_SOURCE_COMMIT_SHA', 'HEAD')
            cmd = ['cd', dependency, '&&', 'git', 'checkout', source_commit]
            msg = f'checking out commit {source_commit} in [blue]{dependency}[/blue]'
            result = loop.run_until_complete(exec_cmd('checkout', cmd, 1, 2, log_msg=msg))
        if not is_source_project or not result.code:  
        # Register project dependency
            result = register_dependency(dependency)
        if not result.code and dependency_name.startswith('ocpi.comp.'):
        # Build project dependency for host, but only if a comp project
            cmd = ['ocpidev', 'build', '-d', dependency]
            msg = f'building project [blue]{dependency}[/blue]'
            name = f'build {dependency_name}'
            result = loop.run_until_complete(exec_cmd(name, cmd, 1, 2, log_msg=msg))
        results.append(result)
        if result.code:
            break
    code = result.code
    time = sum([result.time for result in results])
    return report.Suite('build dependencies', code, time, results)
        

class ResourceRequestException(Exception):
    pass


class ResourceLock:
    """Handles requesting and releasing memory and cpu resources.

    Used to limit the number of tasks that can occur simultaneously.
    """

    def __init__(self) -> None:
        try:
            self._total_mem = int(os.getenv('KUBERNETES_MEMORY_REQUEST')[:-2])
        except:
            self._total_mem = int(
                (os.sysconf('SC_PAGE_SIZE') * os.sysconf('SC_PHYS_PAGES') / (1024.**3)))
        self._mem = self._total_mem
        self._cpu = self._total_cpu = os.cpu_count()
        self._platforms = []
        self._condition = asyncio.Condition()
        _PROGRESS.log(f'memory: {self._mem}\tcpu: {self._cpu}')

    @property
    def cpu(self):
        return self._cpu

    @property
    def mem(self):
        return self._mem

    async def acquire(self, mem: int, cpu: int = 1, platform: Optional['Platform'] = None
                      ) -> Coroutine[Any, Any, bool]:
        """Request to acquire a lock on resources.

        Asynchronously waits until the requested resources are 
        available. If a Platform is provided, The ResourceLock will
        add the name of the platform to a list of currently locked
        platforms. This means that only one task requesting that
        Platform can run at once. This will need to be augmented if
        multiple instances of the same platform are available.

        Args:
            mem: The amount of memory to request.
            cpu: The amount of cpu to request.
            platform: The Platform to acquire.

        Returns:
            A Coroutine bool indicating whether the resources were 
            acquired.
        """
        log_msg = f'resources: cpu {cpu}, mem {mem}'
        if platform is not None:
            log_msg += f', platform {platform.name}'
        logger.debug(f'Requesting {log_msg}')
        if mem > self._total_mem or cpu > self._total_cpu:
            logger.error(f'Unattainable {log_msg}')
            raise ResourceRequestException(
                f'Resource request exceeded maximum resources.'
                f' Total: {self._total_cpu}(cpu) {self._total_mem}(mem).'
                f' Requested: {cpu}(cpu) {mem}(mem).'
            )
        async with self._condition:
            await self._condition.wait_for(lambda: self._mem >= mem and self._cpu >= cpu
                                           and platform not in self._platforms)
            self._mem -= mem
            self._cpu -= cpu
            if platform is not None:
                self._platforms.append(platform)
            logger.debug(f'Acquired {log_msg}')
            logger.debug(f'Available resources: cpu {self._cpu}, mem {self._mem}')
        return True

    async def release(self, mem: int, cpu: int = 1, platform: Optional['Platform'] = None
                      ) -> Coroutine[Any, Any, bool]:
        """Release lock on resources.

        Args:
            mem: The amount of memory to release.
            cpu: The amount of cpu to release.
            platform: The Platform to release.

        Returns:
            A Coroutine bool indicating whether the resources were 
            released.
        """
        log_msg = f'resources: cpu {cpu}, mem {mem}'
        if platform is not None:
            log_msg += f', platform {platform.name}'
        logger.debug(f'Releasing {log_msg}')
        async with self._condition:
            self._mem += mem
            self._cpu += cpu
            if platform is not None and platform in self._platforms:
                self._platforms.remove(platform)
            self._condition.notify_all()
            logger.debug(f'Released {log_msg}')
            logger.debug(f'Available resources: cpu {self._cpu}, mem {self._mem}')
        return True


_PROGRESS = Progress(MofNCompleteColumn(), *Progress.get_default_columns())
_RESOURCE_LOCK = ResourceLock()
