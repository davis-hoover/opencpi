#!/usr/bin/env python3
import asyncio
from typing import List, Tuple
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
    environ['CI_OCPI_HOSTS'] = 'centos7'
    environ['CI_OCPI_HOST'] = 'centos7'
    environ['CI_OCPI_PLATFORMS'] = 'plutosdr:adi_plutosdr0_32'
    environ['CI_OCPI_PLATFORM'] = 'plutosdr'
    environ['CI_OCPI_OTHER_PLATFORM'] = 'adi_plutosdr0_32'
    environ['CI_OCPI_PROJECTS'] = 'ocpi.comp.sdr osp/ocpi.osp.plutosdr'
    environ['CI_OCPI_ROOT_PIPELINE_ID'] = '123456789'
    environ['CI_PIPELINE_ID'] = '234567890'
    environ['CI_JOB_ID'] = '987654321'
    environ['CI_OCPI_CONTAINER_REGISTRY'] = 'dummy-registry'
    environ['CI_PROJECT_DIR'] = '/home/gitlab-runner/builds/x/opencpi/opencpi'
    environ['CI_OCPI_CONTAINER_REPO'] = 'centos7/plutosdr/adi_plutosdr0_32'
    environ['CI_OCPI_HDL_HWIL'] = 'True'
    environ['CI_OCPI_RCC_HWIL'] = 'False'
    # environ['CI_COMMIT_TAG'] = 'v2.4.0'
    environ['CI_COMMIT_REF_NAME'] = 'develop'
    environ['CI_OCPI_REF_NAME'] = 'develop'
    environ['CI_PROJECT_NAME'] = 'ocpi.osp.plutosdr'


def _get_builder(builder_type: str, dump_path: Path, config: dict=None):
    """
    Calls appropriate function to initialize a PipelineBuilder based on
    the provided builder_type
    """
    builders = {
        'platform': _make_platform_pipeline, 
        'assembly': _make_assembly_pipeline,
        'osp': _make_osp_pipeline,
    }
    if config is None:
        config = {}
    if builder_type in builders:
        return builders[builder_type](dump_path, config)
    # Unrecognized pipeline type passed; error exit
    err_msg = 'Unrecognized pipeline type "{}". Choose from: {}'.format(
        builder_type, [builder for builder in builders])
    sys.exit(err_msg)


def _make_platform_pipeline(dump_path: Path, 
    config: str=None) -> PlatformPipelineBuilder:
    """Initialize and return a HostPipelineBuilder"""
    try:
        pipeline_id = environ['CI_OCPI_ROOT_PIPELINE_ID']
    except KeyError:
        pipeline_id = environ['CI_PIPELINE_ID']
    container_registry = getenv('CI_OCPI_CONTAINER_REGISTRY', '')
    hosts = re.split(r'\s|,\s|,', getenv('CI_OCPI_HOSTS', ''))
    platforms = _parse_platforms_directive()
    projects = _parse_projects_directive()
    image_tag = base_image_tag = getenv('CI_COMMIT_TAG', None)
    if image_tag is None:
    # Not a tag pipeline; check if branch is deveop
        ref = getenv('CI_COMMIT_REF_NAME', '')
        ocpi_ref = getenv('CI_OCPI_REF_NAME', '')
        image_tag = ref if ref == 'develop' else image_tag
        base_image_tag = ocpi_ref if ocpi_ref == 'develop' else base_image_tag
    image_tags = [image_tag]
    if base_image_tag is None:
        base_image_tag = pipeline_id
    pipeline_builder = PlatformPipelineBuilder(pipeline_id, container_registry,
        base_image_tag, hosts, platforms, projects, dump_path, config, 
        image_tags=image_tags)

    return pipeline_builder


def _make_osp_pipeline(dump_path: Path, 
    config: str=None) -> OspPipelineBuilder:
    """Initialize and return a OspPipelineBuilder"""
    try:
    # Pipeline launched from opencpi project; get its pipeline ID
        pipeline_id = base_image_tag = environ['CI_OCPI_ROOT_PIPELINE_ID']
    except KeyError:
    # Pipeline not launched from opencpi project; use own pipeline ID
        pipeline_id = environ['CI_PIPELINE_ID']
        base_image_tag = getenv('CI_COMMIT_TAG', None)
        if base_image_tag is None:
        # Not a release pipeline; use 'develop' or pipeline_id for base image
            ocpi_ref = getenv('CI_OCPI_REF_NAME', '')
            base_image_tag = ocpi_ref if ocpi_ref == 'develop' else pipeline_id
    # If pipeline is a release or develop pipeline, add to list of image tags
    image_tag = getenv('CI_COMMIT_TAG', None)
    image_tags = []
    if image_tag is None:
        ref = getenv('CI_COMMIT_REF_NAME', '')
        image_tag = ref if ref == 'develop' else image_tag
    if image_tag:
        image_tags.append(image_tag)
    container_registry = getenv('CI_OCPI_CONTAINER_REGISTRY', '')
    hosts = re.split(r'\s|,\s|,', getenv('CI_OCPI_HOSTS', ''))
    platforms = _parse_platforms_directive()
    projects = _parse_projects_directive()
    project = getenv('CI_PROJECT_NAME', '')
    pipeline_builder = OspPipelineBuilder(pipeline_id, container_registry,
        base_image_tag, hosts, platforms, projects, project, dump_path, 
        config, image_tags=image_tags)

    return pipeline_builder


def _make_assembly_pipeline(dump_path: Path, 
    config: str=None) -> AssemblyPipelineBuilder:
    """Initialize and return an AssemblyPipelineBuilder"""
    try:
        pipeline_id = base_image_tag = environ['CI_OCPI_ROOT_PIPELINE_ID']
    except KeyError:
        pipeline_id = base_image_tag = environ['CI_PIPELINE_ID']
    platform = getenv('CI_OCPI_PLATFORM')
    host = getenv('CI_OCPI_HOST')
    other_platform = getenv('CI_OCPI_OTHER_PLATFORM')
    project_dirs = _get_projects()
    assembly_dirs = _get_assemblies(project_dirs)
    test_dirs = _get_tests(project_dirs)
    container_registry = getenv('CI_OCPI_CONTAINER_REGISTRY')
    container_repo = getenv('CI_OCPI_CONTAINER_REPO')
    model = _get_platform_model(platform)
    runners = config['ci']['runners']
    if platform.endswith('sim'):
        do_hwil = False
    else:
        do_hwil = getenv('CI_OCPI_{}_HWIL'.format(model.upper()), '')
        do_hwil = do_hwil.lower() in ['t', 'y', 'true', 'yes', '1']
    if model == 'hdl' and platform in config:
        config = config[platform]
    elif model == 'rcc' and other_platform and other_platform in config:
        config = config[other_platform]
    else:
        config = None
    pipeline_builder = AssemblyPipelineBuilder(pipeline_id, container_registry, 
        container_repo, base_image_tag, host, platform, model, other_platform, 
        assembly_dirs, test_dirs, dump_path, config=config, runners=runners, 
        do_hwil=do_hwil)

    return pipeline_builder  


def _get_platform_model(platform: str) -> str:
    """Returns the model of the given platform"""
    rcc_platforms,hdl_platforms = _get_platforms().values()
    if platform in rcc_platforms:
        return 'rcc'
    if platform in hdl_platforms:
        return 'hdl'

    sys.exit('Error: Unknown platform "{}"'.format(platform))


def _parse_projects_directive() -> dict:
    """Parses CI_OCPI_PROJECTS to return projects sorted by group"""
    projects_directive = re.split(r'\s|,\s|,', getenv('CI_OCPI_PROJECTS', ''))
    projects = {'osp': [], 'comp': []}
    for project in projects_directive:
        if '/' not in project:
        # Group not specified; attempt to get group by project name
            try:
                group = re.search(r'.*\.(.*)\..*', project).group(1)
                project = '{}/{}'.format(group, project)
            except AttributeError:
                continue
        group = project.split('/', 1)[0]
        if group in projects:
            projects[group].append(project)

    return projects


def _parse_platforms_directive() -> dict:
    """
    Parses CI_OCPI_PLATFORMS env var to determine platforms to build for
    as well as any associated platforms to build ontop of it

    env var is expected to be in the form of:
        platform1:platform_2,...,platform_n
    """
    platforms = {}
    platforms_directive = getenv('CI_OCPI_PLATFORMS')
    if not platforms_directive:
        return platforms
    
    platforms_directive = platforms_directive.split(' ')
    for platform_directive in platforms_directive:
        if ':' in platform_directive:
            left_platform,right_platforms = platform_directive.split(':')
            right_platforms = right_platforms.split(',')
        else:
            left_platform = platform_directive
            right_platforms = []
        if left_platform in platforms:
            platforms[left_platform] += right_platforms
        else:
            platforms[left_platform] = right_platforms

    return platforms


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