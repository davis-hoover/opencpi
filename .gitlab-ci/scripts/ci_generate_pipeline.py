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

def main(pipeline_type: str) -> None:
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
    print('Dumping pipeline yaml to: {}'.format(pipeline.dump_path.resolve()))
    pipeline.dump()
    executionTime = (time.time() - startTime)
    print('Execution time in seconds: ' + str(executionTime))


def _set_env():
    """Set environment variables to simulate a pipeline's environment"""
    environ['CI_PIPELINE_SOURCE'] = 'parent_pipeline'
    environ['CI_OCPI_HOSTS'] = 'centos7'
    environ['CI_OCPI_HOST'] = 'centos7'
    environ['CI_OCPI_PLATFORMS'] = '"zed:xilinx19_2_aarch32,xsim"'
    environ['CI_OCPI_PLATFORM'] = 'zed'
    environ['CI_OCPI_OTHER_PLATFORM'] = 'xilinx19_2_aarch32'
    environ['CI_OCPI_PROJECTS'] = ' '
    environ['CI_OCPI_ROOT_PIPELINE_ID'] = '123456789'
    environ['CI_PIPELINE_ID'] = '234567890'
    environ['CI_JOB_ID'] = '987654321'
    environ['CI_OCPI_CONTAINER_REGISTRY'] = 'dummy-registry'
    environ['CI_PROJECT_DIR'] = '/home/gitlab-runner/builds/x/opencpi/opencpi'
    environ['CI_OCPI_CONTAINER_REPO'] = 'centos7/xsim'
    environ['CI_OCPI_HDL_HWIL'] = 'True'
    environ['CI_OCPI_RCC_HWIL'] = 'False'
    environ['CI_OCPI_ASSEMBLIES'] = 'True'
    # environ['CI_COMMIT_TAG'] = 'v2.4.0'
    environ['CI_COMMIT_REF_NAME'] = 'develop'
    environ['CI_OCPI_REF_NAME'] = 'develop'
    environ['CI_PROJECT_NAME'] = 'ocpi.comp.sdr'
    environ['CI_PROJECT_NAMESPACE'] = 'opencpi/ocpi.comp.sdr'


def _get_builder(builder_type: str, dump_path: Path, 
    config: dict=None) -> PipelineBuilder:
    """
    Calls appropriate function to initialize a PipelineBuilder based on
    the provided builder_type
    """
    builders = {
        'platform': _make_platform_pipeline, 
        'assembly': _make_assembly_pipeline,
        'osp': _make_osp_pipeline,
        'comp': _make_comp_pipeline
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
    pipeline_id = _get_pipeline_id()
    base_image_tag = pipeline_id
    image_tags = _get_image_tags()
    container_registry = getenv('CI_OCPI_CONTAINER_REGISTRY', '')
    hosts = re.split(r'\s|,\s|,', getenv('CI_OCPI_HOSTS', '').strip('"'))
    whitelist = _get_platforms(do_ocpishow=False, do_model_split=False)
    platforms = _parse_platforms_directive(whitelist=whitelist, 
        whitelist_mode='and')
    projects = _parse_projects_directive()
    do_assemblies = getenv('CI_OCPI_ASSEMBLIES', 'True')
    do_assemblies = do_assemblies.lower() in ['t', 'y', 'true', 'yes', '1']
    pipeline_builder = PlatformPipelineBuilder(pipeline_id, container_registry,
        base_image_tag, hosts, platforms, projects, dump_path, config, 
        image_tags=image_tags, do_assemblies=do_assemblies)

    return pipeline_builder


def _make_osp_pipeline(dump_path: Path, 
    config: str=None) -> OspPipelineBuilder:
    """Initialize and return a OspPipelineBuilder"""
    pipeline_id = _get_pipeline_id()
    base_image_tag = _get_base_image_tag(pipeline_id=pipeline_id)
    image_tags = _get_image_tags()
    container_registry = getenv('CI_OCPI_CONTAINER_REGISTRY', '')
    hosts = re.split(r'\s|,\s|,', getenv('CI_OCPI_HOSTS', '').strip('"'))
    whitelist = _get_platforms(do_ocpishow=False, do_model_split=False)
    platforms = _parse_platforms_directive(whitelist=whitelist, 
        whitelist_mode='or')
    projects = _parse_projects_directive()
    project = getenv('CI_PROJECT_NAME', '')
    do_assemblies = getenv('CI_OCPI_ASSEMBLIES', 'True')
    do_assemblies = do_assemblies.lower() in ['t', 'y', 'true', 'yes', '1']
    pipeline_builder = OspPipelineBuilder(pipeline_id, container_registry,
        base_image_tag, hosts, platforms, projects, project, dump_path, 
        config, image_tags=image_tags, do_assemblies=do_assemblies)

    return pipeline_builder


def _make_comp_pipeline(dump_path: Path, 
    config: str=None) -> CompPipelineBuilder:
    """Initialize and return a CompPipelineBuilder"""
    pipeline_id = _get_pipeline_id()
    base_image_tag = _get_base_image_tag(pipeline_id=pipeline_id)
    image_tags = _get_image_tags()
    hosts = re.split(r'\s|,\s|,', getenv('CI_OCPI_HOSTS', '').strip('"'))
    platforms = _parse_platforms_directive()
    projects = _parse_projects_directive()
    project = getenv('CI_PROJECT_NAME', '')
    container_registry = getenv('CI_OCPI_CONTAINER_REGISTRY')
    do_assemblies = getenv('CI_OCPI_ASSEMBLIES', 'True')
    do_assemblies = do_assemblies.lower() in ['t', 'y', 'true', 'yes', '1']
    pipeline_builder = CompPipelineBuilder(pipeline_id, container_registry, 
        base_image_tag, hosts, project, platforms, projects, dump_path, 
        config=config, image_tags=image_tags, do_assemblies=do_assemblies)

    return pipeline_builder  


def _make_assembly_pipeline(dump_path: Path, 
    config: str=None) -> AssemblyPipelineBuilder:
    """Initialize and return an AssemblyPipelineBuilder"""
    pipeline_id = _get_pipeline_id()
    base_image_tag = pipeline_id
    platform = getenv('CI_OCPI_PLATFORM')
    model = _get_platform_model(platform)
    host = getenv('CI_OCPI_HOST')
    other_platform = getenv('CI_OCPI_OTHER_PLATFORM')
    project_group = environ['CI_PROJECT_NAMESPACE'].split('/', 1)[-1]
    project_name = environ['CI_PROJECT_NAME']
    whitelist = [project_name] if project_group == 'comp' else None
    project_dirs = _get_projects(whitelist=whitelist, blacklist=['tutorial'])
    assembly_dirs = _get_assemblies(project_dirs)
    test_dirs = _get_tests(project_dirs, model=model)
    container_registry = getenv('CI_OCPI_CONTAINER_REGISTRY')
    container_repo = getenv('CI_OCPI_CONTAINER_REPO')
    if model == 'hdl' and platform in config:
        config = config[platform]
    elif model == 'rcc' and other_platform and other_platform in config:
        config = config[other_platform]
    else:
        config = None
    if platform.endswith('sim'):
    # Don't do HWIL for simulators
        do_hwil = False
    elif not config or 'ip' not in config:
    # Don't do HWIL for platforms without a device to run on
        do_hwil = False
    else:
        do_hwil = getenv('CI_OCPI_{}_HWIL'.format(model.upper()), '')
        do_hwil = do_hwil.lower() in ['t', 'y', 'true', 'yes', '1']
    pipeline_builder = AssemblyPipelineBuilder(pipeline_id, container_registry, 
        container_repo, base_image_tag, host, platform, model, other_platform, 
        assembly_dirs, test_dirs, dump_path, config=config, do_hwil=do_hwil)

    return pipeline_builder


def _get_pipeline_id() -> str:
    """Returns the pipeline id based on environment"""
    try:
    # Pipeline launched from opencpi project; get its pipeline ID
        pipeline_id = environ['CI_OCPI_ROOT_PIPELINE_ID']
    except KeyError:
    # Pipeline not launched from opencpi project; use own pipeline ID
        pipeline_id = environ['CI_PIPELINE_ID']
        
    return pipeline_id


def _get_base_image_tag(pipeline_id: str=None) -> str:
    """Returns the base image tag based on environment
    
    Will return whichever of the following is true first:
        Commit tag if a release pipeline
        Ref name if ref name is develop
        Pipeline ID
    """
    base_image_tag = getenv('CI_COMMIT_TAG', None)
    if base_image_tag is None:
    # Not a release pipeline; use 'develop' or pipeline_id for base image
        ocpi_ref = getenv('CI_OCPI_REF_NAME', '')
        if ocpi_ref == 'develop':
            base_image_tag = ocpi_ref
        elif pipeline_id is not None:
            base_image_tag = pipeline_id
        else:
            base_image_tag = _get_pipeline_id()

    return base_image_tag


def _get_image_tags() -> List[str]:
    """Returns a List of image tags based one environment"""
    image_tags = []
    image_tag = getenv('CI_COMMIT_TAG', None)
    if image_tag is None:
        ref = getenv('CI_COMMIT_REF_NAME', None)
        image_tag = ref if ref == 'develop' else image_tag
    if image_tag is not None:
        image_tags.append(image_tag)

    return image_tags


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
    projects_directive = getenv('CI_OCPI_PROJECTS', '').strip('"')
    projects_directive = re.split(r'\s|,\s|,', projects_directive)
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


def _parse_platforms_directive(whitelist: List[str]=None, 
    whitelist_mode: str='and') -> dict:
    """
    Parses CI_OCPI_PLATFORMS env var to determine platforms to build for
    as well as any associated platforms to build ontop of it

    env var is expected to be in the form of:
        platform1:platform_2,...,platform_n

    If whitelist mode is 'and', platforms will be allowed only if all
    platforms on both sides of a ':' are in whitelist.
    If whitelist mode is 'or', all platforms on both side of ':' will
    be allowed as long as any platform is in whitelist.
    """
    platforms = {}
    platforms_directive = getenv('CI_OCPI_PLATFORMS').strip('"')
    if not platforms_directive:
        return platforms
    
    platforms_directive = re.split(r'\s|,\s|,', platforms_directive)
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
    
    if whitelist is None or whitelist_mode not in ['and', 'or']:
        return platforms

    filtered_platforms = {}
    if whitelist_mode == 'and':
    # Only allow platforms if all platforms on either side of ':' are in
    # whitelist
        for left_platform,right_platforms in platforms.items():
            if left_platform not in whitelist:
                continue
            if all([platform in whitelist for platform in right_platforms]):
                filtered_platforms[left_platform] = right_platforms
    else:
    # Only allow platforms if a platform on either side of ':' are in whitelist
        for left_platform,right_platforms in platforms.items():
            if left_platform not in whitelist:
                if not any([platform in whitelist 
                            for platform in right_platforms]):
                    continue
            filtered_platforms[left_platform] = right_platforms

    return filtered_platforms


async def _ocpidev_show(noun: str, directory: str='.', scope=None) -> dict:
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


def _get_projects(whitelist: List[str]=None, 
    blacklist: List[str]=None) -> List[str]:
    """Returns opencpi registered project directories"""
    loop = asyncio.get_event_loop()
    projects = loop.run_until_complete(_ocpidev_show('projects'))['projects']
    projects = [project['real_path'] for project in projects.values()]
    if whitelist is not None:
        projects = [project for project in projects
                    if Path(project).name in whitelist]
    if blacklist is not None:
        projects = [project for project in projects
                    if Path(project).name not in blacklist]

    return projects


def _get_platforms(do_ocpishow=True, do_model_split=True) -> List[str]:
    """Returns opencpi platforms
    
    If do_ocpishow is True, will use ocpidev show to get platforms;
    otherwise, will search for platforms in file structure.

    If do_model_split is True, will return a dict of 'rcc' and 'hdl'
    platforms; otherwise, will return a list of all platforms.
    """
    platforms = {'rcc': [], 'hdl': []}
    if do_ocpishow:
        loop = asyncio.get_event_loop()
        platforms = loop.run_until_complete(_ocpidev_show('platforms'))
        platforms['rcc'] = [platform for platform in platforms['rcc'].keys()]
        platforms['hdl'] = [platform for platform in platforms['hdl'].keys()]
    else:
        projects_path = Path('projects')
        if projects_path.exists():
            project_paths = projects_path.glob('*')
        else:
            project_paths = [Path.cwd()]
        for project_path in project_paths:
            for model in ['rcc', 'hdl']:
                platforms_path = Path(project_path, model, 'platforms')
                project_platforms = [platform.name for platform 
                                    in platforms_path.glob('*') 
                                    if platform.is_dir()]
                platforms[model] += project_platforms

    if not do_model_split:
        platforms = platforms['rcc'] + platforms['hdl']
    return platforms


def _get_assemblies(project_dirs: List[str]) -> List[str]:
    """Returns directories of opencpi assemblies"""
    assemblies = []
    for project_dir in project_dirs:
        assemblies_path = Path(project_dir, 'hdl', 'assemblies')
        if not assemblies_path.exists():
            continue
        blacklist = []
        whitelist = []
        makefile = Path(assemblies_path, 'Makefile')
        if makefile.exists():
            with makefile.open() as f:
                for line in f.readlines():
                    m = re.search('^Assemblies=(.*$)', line)
                    if m:
                        whitelist = m.group(1).split()
                    m = re.search('^ExcludeAssemblies=(.*$)', line)
                    if m:
                        blacklist = m.group(1).split()
        for assembly_path in assemblies_path.glob('*'):
            if not assembly_path.is_dir():
                continue
            if whitelist and assembly_path.name not in whitelist:
                continue
            if assembly_path.name in blacklist:
                continue
            relative_path = assembly_path.relative_to(
                environ['OCPI_ROOT_DIR'])
            assemblies.append(str(relative_path))

    return assemblies


def _get_tests(project_dirs: List[str], model=None) -> List[str]:
    """Returns directories of opencpi tests"""
    tests = []
    workers = None
    if model:
    # Gather workers of specified models
        futures = asyncio.gather(
            *[_ocpidev_show('workers', project_dir, 'local') 
              for project_dir in project_dirs])
        results = asyncio.get_event_loop().run_until_complete(futures)
        results = [list(val['workers'].values()) 
                   for value in results for val in value.values()]
        workers = [Path(worker).with_suffix('') for workers in results 
                   for worker in workers 
                   if Path(worker).suffix[1:] == model]
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
                if workers is not None:
                # If no worker of specified model for unit test, continue
                    if library_path.with_suffix('') not in workers:
                        continue
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