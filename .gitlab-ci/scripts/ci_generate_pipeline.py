#!/usr/bin/env python3
import asyncio
from typing import List
import json
from pathlib import Path
from os import environ, getenv
import re
import subprocess
from ci_classes import *
import time

def main(pipeline_type: str):
    """Create Pipeline of provided type and dump to yaml file"""
    startTime = time.time()
    for key,val in sorted(environ.items()):
        if key.startswith('CI_') or key.startswith('OCPI_'):
            print('{}: {}'.format(key,val))
    config_path = Path(Path(__file__).parent, 'config.yml')
    if config_path.exists():
        with open(str(config_path)) as yml:
            config = yaml.safe_load(yml)
    else:
        config = None
    dump_path = Path('.gitlab-ci.yml')
    pipeline_builder: PipelineBuilder = _get_builder(
        pipeline_type, dump_path, config)
    pipeline: Pipeline = pipeline_builder.build()
    print('Dumping pipeline yaml to: {}'.format(pipeline.dump_path))
    pipeline.dump()
    executionTime = (time.time() - startTime)
    print('Execution time in seconds: ' + str(executionTime))


def _set_env():
    """Set environment variables to simulate a pipeline's environment"""
    environ['CI_PIPELINE_SOURCE'] = 'parent_pipeline'
    environ['CI_OCPI_HOSTS'] = 'centos7 ubuntu18_04'
    environ['CI_OCPI_HOST'] = 'centos7'
    environ['CI_OCPI_PLATFORMS'] = 'zed matchstiq_z1'
    environ['CI_OCPI_PLATFORM'] = 'xsim'
    environ['CI_OCPI_PROJECTS'] = 'ocpi.comp.sdr ocpi.osp.plutosdr'
    environ['CI_OCPI_ROOT_PIPELINE_ID'] = '123456789'
    environ['CI_JOB_ID'] = '987654321'
    environ['CI_OCPI_CONTAINER_REGISTRY'] = 'dummy-registry'
    environ['CI_PROJECT_DIR'] = '/home/gitlab-runner/builds/x/opencpi/opencpi'


def _get_builder(builder_type: str, dump_path: Path, config: dict=None):
    """
    Calls appropriate function to initialize a PipelineBuilder based on
    the provided builder_type
    """
    builders = {
        'host': _make_host_pipeline, 
        'cross': _make_cross_pipeline
    }
    if config is None:
        config = {}
    if builder_type in builders:
        return builders[builder_type](dump_path, config)
    # Unrecognized pipeline type passed; error exit
    err_msg = 'Unrecognized pipeline type "{}". Choose from: {}'.format(
        builder_type, [builder for builder in builders])
    sys.exit(err_msg)


def _make_host_pipeline(dump_path: Path, 
    config: str=None) -> HostPipelineBuilder:
    """Initialize and return a HostPipelineBuilder"""
    try:
        pipeline_id = environ['CI_OCPI_ROOT_PIPELINE_ID']
    except KeyError:
        pipeline_id = environ['CI_PIPELINE_ID']
    container_registry = getenv('CI_OCPI_CONTAINER_REGISTRY', '')
    hosts = re.split(r'\s|,\s|,', getenv('CI_OCPI_HOSTS', ''))
    platforms = re.split(r'\s|,\s|,', getenv('CI_OCPI_PLATFORMS', ''))
    projects = re.split(r'\s|,\s|,', getenv('CI_OCPI_PROJECTS', ''))
    pipeline_builder = HostPipelineBuilder(pipeline_id, container_registry, 
        hosts, platforms, projects, dump_path, config)

    return pipeline_builder


def _make_cross_pipeline(dump_path: Path, 
    config: str=None) -> CrossPipelineBuilder:
    """Initialize and return a CrossPipelineBuilder"""
    try:
        pipeline_id = environ['CI_OCPI_ROOT_PIPELINE_ID']
    except KeyError:
        pipeline_id = environ['CI_PIPELINE_ID']
    platforms = _get_platforms()
    platform = getenv('CI_OCPI_PLATFORM')
    if platform in platforms['rcc']:
        model = 'rcc'
    elif platform in platforms['hdl']:
        model = 'hdl'
    else:
        sys.exit('Error: Unkown platform: {}'.format(platform))
    project_dirs = _get_projects()
    assembly_dirs = _get_assemblies(project_dirs)
    test_dirs = _get_tests(project_dirs)
    container_registry = getenv('CI_OCPI_CONTAINER_REGISTRY')
    host = getenv('CI_OCPI_HOST')
    pipeline_builder = CrossPipelineBuilder(pipeline_id, container_registry, 
        host, platform, model, assembly_dirs, test_dirs, dump_path, config)

    return pipeline_builder   


async def _ocpidev_show(noun, directory='.', scope=None) -> dict:
    """
    Call ocpidev show with provided arguments
    
    Loads json into a dictionary to return. Runs asynchronously to make
    up for "ocpidev show" being slow.
    """
    cmd = ' '.join(['ocpidev', 'show', noun, '--json'])
    if scope:
        cmd += ' --{}-scope'.format(scope)
    process = await asyncio.create_subprocess_shell(
        cmd, 
        stdout=subprocess.PIPE, 
        stdin=subprocess.PIPE,
        stderr=subprocess.PIPE, 
        encoding='utf-8',
        cwd=directory)
    stdout, stderr = await process.communicate()
    stdout = stdout.decode().rstrip()
    stderr = stderr.decode().rstrip()
    if stderr:
        sys.exit('Error: {}'.format(stderr))

    return json.loads(stdout)


def _get_projects() -> List[str]:
    """Returns opencpi registered project directories"""
    loop = asyncio.get_event_loop()
    projects = loop.run_until_complete(_ocpidev_show('projects'))['projects']
    projects = [project['real_path'] for project in projects.values() 
                if project != 'tutorial']

    return projects

def _get_platforms() -> List[str]:
    """Returns opencpi platforms"""
    loop = asyncio.get_event_loop()
    platforms = loop.run_until_complete(_ocpidev_show('platforms'))
    rcc_platforms = [platform for platform in platforms['rcc'].keys()]
    hdl_platforms = [platform for platform in platforms['hdl'].keys()]

    return {'rcc': rcc_platforms, 'hdl': hdl_platforms}


def _get_assemblies(project_dirs) -> List[str]:
    """Returns directories of opencpi assemblies"""
    assemblies = []
    for project_dir in project_dirs:
        assemblies_path = Path(project_dir, 'hdl', 'assemblies')
        for assembly_path in assemblies_path.glob('*'):
            if not assemblies_path.exists():
                continue
            for assembly_path in assemblies_path.glob('*'):
                if not assembly_path.is_dir():
                    continue
                try:
                    relative_path = assembly_path.relative_to(
                        environ['OCPI_ROOT_DIR'])
                except:
                    relative_path = assembly_path.relative_to(
                        environ['CI_PROJECT_DIR'])
                assemblies.append(str(relative_path))

    return assemblies


def _get_tests(project_dirs) -> List[str]:
    """Returns directories of opencpi tests"""
    tests = []
    futures = asyncio.gather(
        *[_ocpidev_show('tests', project_dir, 'local') 
            for project_dir in project_dirs])
    results = asyncio.get_event_loop().run_until_complete(futures)
    for result in results:
        libraries = result['project']['libraries']
        for library in libraries:
            library_tests = libraries[library]['tests']
            for library_test in library_tests:
                library_path = Path(library_tests[library_test])
                try:
                    relative_path = library_path.relative_to(
                        environ['OCPI_ROOT_DIR'])
                except:
                    relative_path = library_path.relative_to(
                        environ['CI_PROJECT_DIR'])
                tests.append(str(relative_path))

    return tests


if __name__ == '__main__':
    """
    Called when run from command line

    First argument is type of pipeline.
    Provide '--simulate' to set env vars to simulate a pipeline
    """
    import sys
    if [h for h in ['help', '--help'] if h in sys.argv]:
        usage = 'Usage: ci_generate_pipeline.py <pipeline-type> [--simulate]'
        sys.exit(usage)
    if len(sys.argv) < 2:
    # Get pipeline type
        sys.exit('Must supply pipeline type as argument')
    pipeline_type = sys.argv[1]
    if '--simulate' in sys.argv:
    # Set environment to simulate pipeline
        _set_env()
        sys.argv.pop(sys.argv.index('--simulate'))
    
    main(pipeline_type)