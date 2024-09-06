#!/usr/bin/python3

from argparse import ArgumentParser
import logging
from os import getenv
from pathlib import Path
import yaml

from classes import get_projects
from utils import logger, get_ocpi_root_path

def main(output_path: Path) -> None:
    """Generates job yaml.

    Generates GitLab CI/CD job against a parallel matrix of
    dynamically discovered tests.

    Args:
        output_path: Path to write generated job to.
    """
    ocpi_root_path = get_ocpi_root_path()
    tests = [str(test.path) for project in get_projects(ocpi_root_path) for test in project.tests]
    tag = getenv('CI_PIPELINE_ID')
    job = {
        'include': '.gitlab-ci/yaml/include.yml',
        'test': {
            'extends': '.artifacts',
            'image': f'${{CI_OCPI_CONTAINER_REGISTRY}}/${{IMAGE}}:{tag}',
            'timeout': '6h',
            'tags': ['opencpi', '$HDL_PLATFORM'],
            'dependencies': [],
            'variables': {
                'GIT_SUBMODULE_PATHS': "",
                'GIT_STRATEGY': 'none'
            },
            'script': [
                'mkdir -p ${CI_PROJECT_DIR}/.gitlab-ci/artifacts',
                'cd /home/user/opencpi',
                'source /home/user/opencpi/cdk/opencpi-setup.sh -r',
                '.gitlab-ci/scripts/test.py $MODEL --hdl-platform $HDL_PLATFORM'
                    ' --rcc-platform $RCC_PLATFORM'
                    '--report-path ${CI_PROJECT_DIR}/.gitlab-ci/artifacts/job-report.xml'
                    ' $TEST'
            ],
            'parallel': {'matrix': [{'TEST': test} for test in tests]},
            'rules': [
                {'if': '$RCC_PLATFORM != null && $RCC_PLATFORM != ""',
                    'variables': {'IMAGE': '${HOST}/${HDL_PLATFORM}/${RCC_PLATFORM}'},
                    'when': 'on_success'
                },
                {'if': '$HDL_PLATFORM != null && $HDL_PLATFORM != ""',
                    'variables': {'IMAGE': '${HOST}/${HDL_PLATFORM}'},
                    'when': 'on_success'
                },
                {'when': 'on_success'}
            ]
        }
    }
    with output_path.open('w+') as f:
        yaml.safe_dump(job, f)


if __name__ == '__main__':
    parser = ArgumentParser(
        prog='OpenCPI CI/CD matrix job builder',
        description='Dynamically creates parallel matrix job'
    )
    parser.add_argument('output_path', type=Path, help='Path to where to dump yaml to')
    parser.add_argument('-d', '--debug', action='store_const', dest='log_level',
                        const=logging.DEBUG, default=logging.CRITICAL, help='Set log level to DEBUG')
    parser.add_argument('-v', '--verbose', action='store_const', dest='log_level',
                        const=logging.INFO, help='Set log level to INFO')
    args = parser.parse_args()
    logger.setLevel(args.log_level)
    main(args.output_path)
