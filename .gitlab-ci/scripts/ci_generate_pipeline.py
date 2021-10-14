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

startTime = time.time()
def main(pipeline_type: str):
    """Create Pipeline of provided type and dump to yaml file"""
    config_path = Path(__file__, 'config.yml')
    if config_path.exists():
        with open(str(config_path)) as yml:
            config = yaml.safe_load(yml)
    else:
        config = None
    pipeline_builder: PipelineBuilder = _get_builder(pipeline_type, config)
    pipeline: Pipeline = pipeline_builder.build()
    for key,val in sorted(environ.items()):
        print('{}: {}'.format(key,val))
    pipeline.dump()
    executionTime = (time.time() - startTime)
    print('Execution time in seconds: ' + str(executionTime))


def _set_env():
    """Set environment variables to simulate a pipeline's environment"""
    environ['CI_PIPELINE_SOURCE'] = 'parent_pipeline'
    environ['CI_OCPI_HOSTS'] = 'centos7 ubuntu18_04'
    environ['CI_OCPI_HOST'] = 'centos7'
    environ['CI_OCPI_PLATFORMS'] = 'zed matchstiq_z1'
    environ['CI_OCPI_PLATFORM'] = 'zed'
    environ['CI_OCPI_PROJECTS'] = 'ocpi.comp.sdr ocpi.osp.plutosdr'
    environ['CI_OCPI_ROOT_PIPELINE_ID'] = '123456789'
    environ['CI_OCPI_CONTAINER_REGISTRY'] = 'dummy-registry'


def _get_builder(builder_type: str=None, config: str=None):
    """
    Calls appropriate function to initialize a PipelineBuilder based on
    the provided builder_type
    """
    builders = {
        'host': _make_host_pipeline, 
        'cross': _make_cross_pipeline
    }
    if builder_type in builders:
        return builders[builder_type](config)
    # Unrecognized pipeline type passed; error exit
    err_msg = 'Unrecognized pipeline type "{}". Choose from: {}'.format(
        builder_type, [builder for builder in builders])
    sys.exit(err_msg)


def _make_host_pipeline(config: str=None) -> HostPipelineBuilder:
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
        hosts, platforms, projects, config)

    return pipeline_builder


def _make_cross_pipeline(config: str=None) -> CrossPipelineBuilder:
    """Initialize and return a CrossPipelineBuilder"""
    try:
        pipeline_id = environ['CI_OCPI_ROOT_PIPELINE_ID']
    except KeyError:
        pipeline_id = environ['CI_PIPELINE_ID']
    project_dirs = _get_projects()
    assembly_dirs = _get_assemblies(project_dirs)[0:3]
    test_dirs = _get_tests(project_dirs)[0:3]
    container_registry = getenv('CI_OCPI_CONTAINER_REGISTRY')
    host = getenv('CI_OCPI_HOST')
    platform = getenv('CI_OCPI_PLATFORM')
    pipeline_builder = CrossPipelineBuilder(pipeline_id, container_registry, 
        host, platform, assembly_dirs, test_dirs, config)

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
        encoding='utf-8',
        cwd=directory)
    stdout, _ = await process.communicate()
    stdout = stdout.decode().rstrip()

    return json.loads(stdout)


def _get_projects() -> List[str]:
    """Returns opencpi registered project directories"""
    loop = asyncio.get_event_loop()
    projects = loop.run_until_complete(_ocpidev_show('projects'))['projects']
    projects = [project['real_path'] for project in projects.values() 
                if project != 'tutorial']

    return projects


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
                assemblies.append(str(assembly_path))

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
                tests.append(library_tests[library_test])

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