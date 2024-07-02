#!/usr/bin/python3

import argparse
import asyncio
import logging
from pathlib import Path
import sys

import report
from classes import get_projects, get_platform, get_test, Test, HdlPlatform, RccPlatform
from utils import get_ocpi_root_path, logger


def main(test: Test, model: str, hdl_platform: HdlPlatform, rcc_platform: RccPlatform
         ) -> report.Suite:
    """Runs OpenCPI test on specified platforms.

    For non-simulator platforms, both an hdl_platform and an
    rcc_platform are required. Due to this, the model must be 
    specified to determine which of the two platforms the Tests are to 
    actually run against.

    Args:
        test: Test to run.
        model: The model of the platform to run the test against.
        hdl_platform: The HdlPlatform to run the test on.
        rcc_platform: The associated RccPlatform.

    Returns:
       report.Suite representing the results of the Test run.
    """
    loop = asyncio.get_event_loop()
    timeout = 18000
    return loop.run_until_complete(test.run(model, hdl_platform, rcc_platform, timeout=timeout))


if __name__ == '__main__':
    parser = argparse.ArgumentParser(
        prog='OpenCPI CI/CD test script',
        description='Wrapper script to test OpenCPI in CI/CD pipelines'
    )
    parser.add_argument('model', choices=['rcc', 'hdl'])
    parser.add_argument('test_path', metavar='test-path', type=Path, 
                        help='Path to the test to execute.')
    parser.add_argument('--hdl-platform', required=True, type=str,
                        help='HDL platform to test')
    parser.add_argument('--rcc-platform', nargs='?', type=str, default=None, 
                        help='RCC platform to test')
    parser.add_argument('--report-path', type=Path, default=None,
                        help='Path to read/write report from/to')
    parser.add_argument('-d', '--debug', action='store_const', dest='log_level', const=logging.DEBUG, 
                        default=logging.CRITICAL, help='Set log level to DEBUG')
    parser.add_argument('-v', '--verbose', action='store_const', dest='log_level', 
                        const=logging.INFO, help='Set log level to INFO')
    try:
        args = parser.parse_args()
    except Exception as e:
        parser.error(e)
    logger.setLevel(args.log_level)
    ocpi_root_path = get_ocpi_root_path()
    projects = get_projects(ocpi_root_path)
    try:
        test = get_test(args.test_path.resolve(), projects)
        hdl_platform = get_platform(args.hdl_platform, projects)
        if args.rcc_platform is not None:
            args.rcc_platform = get_platform(args.rcc_platform, projects)
    except Exception as e:
        parser.error(e)
    result = main(test, args.model, hdl_platform, args.rcc_platform)
    name = hdl_platform.name if args.model == 'hdl' else args.rcc_platform.name
    junit_report, code = report.to_junit(name, [result])
    if args.report_path:
        junit_report.write(args.report_path, encoding='utf-8', xml_declaration=True)
    sys.exit(code)
