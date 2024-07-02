#!/usr/bin/python3
import argparse
import asyncio
from functools import partial
import logging
import os
from pathlib import Path
from typing import List, Union
import sys

from classes import Target, Project, HdlPlatform, RccPlatform, get_projects, get_platform
import report
from utils import logger, get_ocpi_root_path, build_dependencies


def main(platforms: List[Union[HdlPlatform, RccPlatform]], targets: List[Target],
         projects: List[Project]) -> List[report.Suite]:
    """Builds OpenCPI projects for specified platforms and targets

    Args:
        platforms: List of Platforms to build for.
        targets: List of Targets to build for.
        projects: List of Projects to build.
    """
    loop = asyncio.get_event_loop()
    tasks = map(lambda target: loop.create_task(target.build(projects)), targets)
    results = loop.run_until_complete(asyncio.gather(*tasks))
    tasks = map(lambda platform: loop.create_task(platform.build(projects)), platforms)
    results += loop.run_until_complete(asyncio.gather(*tasks))
    cases = [case for result in results for case in result.cases]
    failures = len(list(filter(lambda case: case.code, cases)))
    successes = len(cases) - failures
    print(f'successes: {successes}\tfailures:{failures}')
    return results


if __name__ == '__main__':
    parser = argparse.ArgumentParser(
        prog='OpenCPI CI/CD builder',
        description='Wrapper script to build OpenCPI in CI/CD pipelines'
    )
    parser.add_argument('--platforms', type=str, nargs='+', default=[],
                        help='Platforms to build')
    parser.add_argument('--hdl-targets', type=Target, nargs='+', default=[],
                        help='HDL targets to build')
    parser.add_argument('--report-path', type=Path, default=None,
                        help='Path to read/write report from/to')
    parser.add_argument('-d', '--debug', action='store_const', dest='log_level', 
                        const=logging.DEBUG, help='Set log level to DEBUG', 
                        default=logging.CRITICAL)
    parser.add_argument('-v', '--verbose', action='store_const', dest='log_level', 
                        const=logging.INFO, help='Set log level to INFO')
    parser.add_argument('--dependencies', type=str, nargs='*', default=[],
                        help='Paths to dependencies to build and register before installing platform')
    try:
        args = parser.parse_args()
    except Exception as e:
        parser.error(e)
    logger.setLevel(args.log_level)
    loop = asyncio.get_event_loop()
    result = build_dependencies(args.dependencies)
    if result is not None and result.code:
        results = [result]
    else:
        ci_project_name = os.getenv('CI_PROJECT_NAME', 'opencpi')
        if ci_project_name != 'opencpi':
            # If running in a project outside of the main OpenCPI project, only build said project.
            whitelist = [ci_project_name]
            blacklist = None
        else:
            # If running in main OpenCPI project, do not build COMP projects.
            blacklist =  [path.name for path in 
                        get_ocpi_root_path().joinpath('projects', 'comps').glob('*')]
            whitelist = None
        projects = get_projects(whitelist=whitelist, blacklist=blacklist)
        try:
            args.platforms = [get_platform(platform_name, projects) 
                              for platform_name in args.platforms]
        except Exception as e:
            parser.error(e)
        if not any(args.platforms+args.hdl_targets):
            parser.error('At least one platform or hdl target must be provided.')
        results = main(args.platforms, args.hdl_targets, projects)
    junit_report, code = report.to_junit('build', results)
    if args.report_path:
        junit_report.write(args.report_path, encoding='utf-8', xml_declaration=True)
    sys.exit(code)
