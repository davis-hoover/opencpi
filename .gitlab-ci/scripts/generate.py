#!/usr/bin/python3

from argparse import ArgumentParser
import logging
import os
from pathlib import Path
from re import split
from typing import List
import yaml

from classes import get_projects, RccPlatform, HdlPlatform
from utils import logger, get_ocpi_root_path


def get_directive_dict(directive_str: str) -> dict:
    """Parses the platform directive from a string.

    The platform directive dictates what platforms to build and test
    for. For non-simulator platforms, the directive must combine an
    hdl_platform and an rcc platform with a ":" for those platforms
    to be tested against. Only one platform may appear on the left
    side of the colon; however, multple platforms may appear on the
    right side of the colon, separated by a comma.

    Args:
        directive_str: The string to parse for the platform directive.
            Example: "xsim zed:xilinx19_2_aarch64 zcu104"

    Returns:
        A dictionary representation of the platform directive.
        Example: {'xsim': set(), 'zed': {'xilinx19_2_aarch32'}, 
                  'xilinx19_2_aarch64': set(), 'zcu104': set()}
    """
    directive_dict = {}
    for platform in split('\s+', directive_str):
        # Delineate platforms by space
        if ':' in platform:
            # Dileneate associated platforms by colon
            key, values = platform.split(':')
            # Dileneate individual associated platform by comma
            values = set(values.split(','))
        else:
            key = platform
            values = set()
        if key in directive_dict:
            directive_dict[key].update(values)
        else:
            directive_dict[key] = values
    return directive_dict


def deploy(yml: dict, rcc_platforms: List[RccPlatform], hdl_platforms: List[HdlPlatform],
           directive_dict: dict) -> dict:
    """Creates a parallel matrix to deploy images for platforms.

    Creates a matrix for each platform in the lists of platforms. 
    Also adds to the matrix the hdl target belonging to each
    non-simulator platform in the list of hdl_platforms. Goes through 
    the directive_dict to also add each key,value pair to the matrix.

    Args:
        yml: The dict representation of the yaml template file 
            for the job.
        rcc_platforms: List of RccPlatforms to add to the matrix.
        hdl_platforms: List of HdlPlatforms to add to the matrix.
        directive_dict: Dictionary containing the directive of
            platforms to add to the matrix.

    Returns:
        A dictionary containing the contents of the passed in yml
        template with the addition of a parallel matrix for the hdl
        and rcc platforms.
    """
    job = yml.get('deploy')
    if not job:
        return yml
    if 'parallel' not in job:
        job['parallel'] = {'matrix': []}
    elif 'matrix' not in job['parallel']:
        job['parallel']['matrix'] = []
    matrix = job['parallel']['matrix']
    for platform in hdl_platforms:
        matrix.append({'HDL_PLATFORM': platform.name})
        if platform.name != platform.target:
            # Avoid deploying images in cases where platform name == target name
            # Ex: platform xsim has target xsim
            matrix.append({'HDL_TARGET': platform.target})
    for platform in rcc_platforms:
        matrix.append({'RCC_PLATFORM': platform.name})
    hdl_platform_names = [platform.name for platform in hdl_platforms]
    rcc_platform_names = [platform.name for platform in rcc_platforms]
    for key, values in directive_dict.items():
        if not values:
            continue
        if key in hdl_platform_names:
            matrix_job = {'HDL_PLATFORM': key, 'RCC_PLATFORM': list(values)}
        elif key in rcc_platform_names:
            matrix_job = {'RCC_PLATFORM': key, 'HDL_PLATFORM': list(values)}
        else:
            continue
        matrix.append(matrix_job)
    matrix.append({'HOST': os.getenv('HOST', '')})
    return yml


def install(yml: dict, rcc_platforms: List[RccPlatform], hdl_platforms: List[HdlPlatform]
            ) -> dict:
    """Creates a parallel matrix to install each platform.

    Also adds rules to the hdl platforms installation job to set a
    variable specifying the appropriate HDL_TARGET for each individual
    job in the matrix. This variable is necessary to pull to correct
    hdl target cache.

    Args:
        yml: The dict representation of the yaml template file 
            for the jobs.
        rcc_platforms: List of RccPlatforms to add to the matrix.
        hdl_platforms: List of HdlPlatforms to add to the matrix.

    Returns:
        A dictionary containing the contents of the passed in yml
        template with the addition of a parallel matrix for the
        hdl and rcc platforms.
    """
    hdl_platforms_job = yml.get('hdl_platforms')
    rcc_platforms_job = yml.get('rcc_platforms')
    hdl_targets_job = yml.get('hdl_targets')
    if rcc_platforms_job and not rcc_platforms:
        yml.pop('rcc_platforms')
    if hdl_platforms_job and not hdl_platforms:
        yml.pop('hdl_platforms')
        yml.pop('hdl_targets')

    if rcc_platforms_job:
        # Add rcc platforms to matrix
        rcc_platforms_job['parallel'] = {
            'matrix': [{'RCC_PLATFORM': [platform.name for platform in rcc_platforms]}]
        }
        rcc_platforms_job['rules'] = []
        for platform in rcc_platforms:
            variables = get_submodule_variables(platform)
            if variables:
                rcc_platforms_job['rules'].append({
                    'if': f'$RCC_PLATFORM == "{platform.name}"',
                    'variables': variables
                })
        rcc_platforms_job['rules'].append({'when': 'on_success'})
    if hdl_targets_job:
        # Add hdl targets to matrix
        hdl_targets_job['parallel'] = {
            'matrix': [{'HDL_TARGET': list(set(platform.target for platform in hdl_platforms
                                               if platform.target is not None))}]
        }
        hdl_targets_job['rules'] = [{'when': 'on_success'}]
    if hdl_platforms_job:
        # Add hdl platforms to matrix and set its hdl target as a variable
        hdl_platforms_job['parallel'] = {
            'matrix': [{'HDL_PLATFORM': [platform.name for platform in hdl_platforms]}]
        }
        hdl_platforms_job['rules'] = []
        for platform in hdl_platforms:
            variables = get_submodule_variables(platform)
            variables.update({'HDL_TARGET': platform.target})
            hdl_platforms_job['rules'].append({
                'if': f'$HDL_PLATFORM == "{platform.name}"',
                'variables': variables
            })
        hdl_platforms_job['rules'].append({'when': 'on_success'})
    return yml


def test(yml: dict, rcc_platforms, hdl_platforms, directive_dict: dict, hwil_whitelist: dict = None
         ) -> dict:
    """Creates a parallel matrix to test each platform.

    Checks environment to determine if sim and/or hwil testing should
    be done. If DO_SIM is not true, tests will not run on simulators.
    if DO_HWIL is not true, tests will not run on hardware. Parses
    directive dict to determine what associated platform is needed to
    run tests for HWIL. If hwil_whitelist is provided, hwil jobs will 
    only be created for whitelisted hdl/rcc platform associations.

    Args:
        yml: The dict representation of the yaml template file 
            for the jobs.
        rcc_platforms: List of RccPlatforms to add to the matrix.
        hdl_platforms: List of HdlPlatforms to add to the matrix.
        directive_dict: Dictionary containing the directive of
            platforms to add to the matrix.
        hwil_whitelist: Dictionary containing whitelisted hdl
            platforms and associated rcc platforms.

    Returns:
        A dictionary containing the contents of the passed in yml
        template for each provided platform, with the addition of a 
        parallel matrix for each test.
    """
    template = yml.get('.test')
    if not template:
        return yml
    hdl_platform_names = [platform.name for platform in hdl_platforms]
    rcc_platform_names = [platform.name for platform in rcc_platforms]
    do_hwil = os.getenv('DO_HWIL', 'False').lower() in ['true', 'yes', 'y']
    do_sim = os.getenv('DO_SIM', 'False').lower() in ['true', 'yes', 'y']
    script = ('.gitlab-ci/scripts/test.py {} --hdl-platform {} --rcc-platform {}'
              ' --report-path ${{CI_PROJECT_DIR}}/test-report.xml projects/${{TEST_PATH}}')
    ocpi_root_dir = get_ocpi_root_path()
    tests = [str(test.path.relative_to(ocpi_root_dir.joinpath('projects')))
             for project in get_projects()
             for test in project.tests]
    template['parallel'] = {'matrix': [{'TEST_PATH': tests}]}
    for platform, platforms in directive_dict.items():
        # Iterator through entries in platform directive.
        if platform in hdl_platform_names:
            # Hdl platforms
            if platform.endswith('sim') and do_sim:
                # Simulators
                image = f'${{IMAGE_REPO}}/${{HOST}}/{platform}:${{IMAGE_TAG}}'
                job = {'image': image, 'extends': '.test', 'tags': ['opencpi', platform],
                       'script': script.format('hdl', platform, '')}
                yml[platform] = job
            elif do_hwil:
                # HWIL for hdl platforms
                if not is_whitelisted(platform, whitelist=hwil_whitelist):
                    continue
                for rcc_platform in platforms:
                    # Created HWIL job for hdl platform and each associated rcc platform
                    if not is_whitelisted(platform, rcc_platform=rcc_platform,
                                          whitelist=hwil_whitelist):
                        continue
                    image = f'${{IMAGE_REPO}}/${{HOST}}/{platform}/{rcc_platform}:${{IMAGE_TAG}}'
                    job = {'image': image, 'extends': '.test', 'tags': ['opencpi', platform],
                           'script': script.format('hdl', platform, rcc_platform)}
                    yml[f'{platform}:{rcc_platform}'] = job
                    job = {'image': image, 'extends': '.test', 'tags': ['opencpi', platform],
                           'script': script.format('rcc', platform, rcc_platform)}
                    yml[f'{rcc_platform}:{platform}'] = job
        elif platform in rcc_platform_names and platforms and do_hwil:
            # HWIL for rcc platforms.
            for hdl_platform in platforms:
                # Created HWIL job for rcc platform and each associated hdl platform
                if not is_whitelisted(
                        hdl_platform, rcc_platform=platform, whitelist=hwil_whitelist):
                    continue
                image = f'${{IMAGE_REPO}}/${{HOST}}/{hdl_platform}/{platform}:${{IMAGE_TAG}}'
                job = {'image': image, 'extends': '.test', 'tags': ['opencpi', platform],
                       'script': script.format('rcc', platform, hdl_platform)}
                yml[f'{platform}:{hdl_platform}'] = job
                job = {'image': image, 'extends': '.test', 'tags': ['opencpi', platform],
                       'script': script.format('hdl', platform, hdl_platform)}
                yml[f'{hdl_platform}:{platform}'] = job
    return yml


def is_whitelisted(hdl_platform: str, rcc_platform: str = None, whitelist: dict = None) -> bool:
    """Determines if a combination platforms is in a whitelist.
    
    Args:
        hdl_platform: Name of hdl platform to look for in whitelist.
        rcc_platforms: Name of rcc platform to look for under the
            hdl platform's entry in the whitelist.
        whitelist: The whitelist to look through.

    Returns:
        Whether the platforms are whitelisted.
    """
    if whitelist is None:
        return True
    if hdl_platform not in whitelist:
        return False
    if rcc_platform is not None and rcc_platform not in whitelist[hdl_platform]:
        return False
    return True


def get_submodule_dependencies(platform) -> List[str]:
    """Returns the comp submodule dependencies for a Platform.
    
    Args:
        platform: Platform to get comp submodule dependencies for.

    Returns:
        The comp submodule dependencies for a given Platform.
    """
    submodule_dependencies = [str(Path('projects', 'comps', project))
                              for project in platform.project.project_dependencies
                              if project.startswith('ocpi.comp.')]
    return submodule_dependencies


def get_submodule_variables(platform) -> dict:
    """Sets variables for a Platform to pull necessary submodules.
    
    Args:
        platform: Platform to set variables for.

    Returns:
        Dictionary containing variables necessary to pull submodules
        for a platform.
    """
    variables = {}
    submodules = get_submodule_dependencies(platform)
    if platform.project.is_osp:
        # Register and install the OSP the platform belongs to
        submodules.append(str(platform.project.path.relative_to(get_ocpi_root_path())))
    if submodules:
        # Register and install COMP projects the platform depends on
        variables.update({
            'GIT_SUBMODULE_STRATEGY': 'normal',
            'GIT_SUBMODULE_PATHS': ' '.join(submodules),
        })
    return variables


def main(mode, input_path: Path, output_path: Path, rcc_platforms, hdl_platforms,
         directive_dict: dict) -> None:
    """Generates job yaml.

    Calls appropriate function to generate the appropriate yaml based
    on the mode. Write yaml to output_path.

    Args:
        mode: What kind of job to generator: test, install, or deploy.
        input_path: Path of job template.
        output_path: Path to write generated job to.
        rcc_platforms: List of RccPlatforms to generate job for.
        hdl_platforms: List of HdlPlatforms to generate job for.
        directive_dict: Dictionary containing the directive of
            platforms.
    """
    with input_path.open('r') as f:
        yml_template = yaml.safe_load(f)
    if mode == 'deploy':
        yml = deploy(yml_template, rcc_platforms, hdl_platforms, directive_dict)
    elif mode == 'install':
        yml = install(yml_template, rcc_platforms, hdl_platforms)
    elif mode == 'test':
        hwil_whitelist_path = Path(__file__).parent.parent.joinpath('yaml', 'hwil-whitelist.yml')
        if hwil_whitelist_path.exists():
            with hwil_whitelist_path.open() as f:
                hwil_whitelist = yaml.safe_load(f)
        else:
            hwil_whitelist = None
        yml = test(yml_template, rcc_platforms, hdl_platforms, directive_dict,
                   hwil_whitelist=hwil_whitelist)
    else:
        return None
    with output_path.open('w+') as f:
        yaml.safe_dump(yml, f)


if __name__ == '__main__':
    parser = ArgumentParser(
        prog='OpenCPI CI/CD matrix job builder',
        description='Dynamically creates parallel matrix jobs'
    )
    parser.add_argument('mode', choices=['deploy', 'install', 'test'],
                        help='The type of job to generate')
    parser.add_argument('input_path', type=Path, help='Path to yaml template')
    parser.add_argument('output_path', type=Path, help='Path to where to dump yaml to')
    parser.add_argument('-d', '--debug', action='store_const', dest='log_level',
                        const=logging.DEBUG, default=logging.CRITICAL, help='Set log level to DEBUG')
    parser.add_argument('-v', '--verbose', action='store_const', dest='log_level',
                        const=logging.INFO, help='Set log level to INFO')
    parser.add_argument(
        '--dependencies', type=str, nargs='+', default=[],
        help='Paths to dependencies to build and register before installing platform')
    args = parser.parse_args()
    logger.setLevel(args.log_level)
    platforms = [platform for project in get_projects(Path.cwd()) for platform in project.platforms]
    directive_dict = get_directive_dict(os.getenv('PLATFORMS', ''))
    # Flatten platforms from directive to get a list of unique platform names
    platforms_whitelist = set(directive_dict.keys()).union(
        set(value for values in directive_dict.values() for value in values))
    platforms = [platform for platform in platforms if platform.name in platforms_whitelist]
    rcc_platforms = [platform for platform in platforms if platform.model == 'rcc']
    hdl_platforms = [platform for platform in platforms if platform.model == 'hdl']
    main(args.mode, args.input_path, args.output_path, rcc_platforms, hdl_platforms, directive_dict)
