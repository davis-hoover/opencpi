from collections import namedtuple
import re
from typing import List, Tuple
import xml.etree.ElementTree as ET

Suite = namedtuple('Suite', 'name code time cases')
Case = namedtuple('Case', 'name code time stdout stderr')

def to_junit(name: str, suites: List[Suite]) -> Tuple[ET.ElementTree, int]:
    """Convert a list of Suites into junit report xml.
    
    Args:
        name: Name of the collection of Suites.
        suites: List of Suites to convert to a junit xml.

    Returns:
        A tuple consisting of the junit report xml tree and the number
        of Case failures in the collection of Suites.
    """
    from utils import logger

    total = total_failures = total_errors = 0
    testsuites = ET.Element('testsuites', {'name': name})
    logger.debug(f'Creating testsuites "{name}"')
    for suite in suites:
        logger.debug(f'Creating testsuite "{suite.name}" with {len(suite.cases)} cases')
        testsuite = ET.SubElement(testsuites, 'testsuite', {
            'name': suite.name,
            'tests': str(len(suite.cases))
        })
        failures = errors = 0
        for case in suite.cases:
            logger.debug(f'Creating testcase "{case.name}" with code {case.code}')
            testcase = ET.SubElement(testsuite, 'testcase', {
                'name': case.name,
                'classname': suite.name,
                'time': str(case.time)
            })
            if case.code == 1:
                failure = ET.SubElement(testcase, 'failure')
                failure.text = clean_text(case.stderr)
                failures += 1
            elif case.code != 0:
                error = ET.SubElement(testcase, 'error')
                error.text = clean_text(case.stderr)
                errors += 1
            if case.stdout:
                system_out = ET.SubElement(testcase, 'system-out')
                system_out.text = clean_text(case.stdout)
        testsuite.set('failures', str(failures))
        testsuite.set('errors', str(errors))
        testsuite.set('time', str(suite.time))
        testsuite.set('code', str(suite.code))
        total += len(suite.cases)
        total_failures += failures
        total_errors += errors
    testsuites.set('tests', str(total))
    testsuites.set('failures', str(total_failures))
    testsuites.set('errors', str(total_errors))
    tree = ET.ElementTree(testsuites)
    return tree, total_errors+total_failures

ansi_escape = re.compile(r'(\x9B|\x1B\[)[0-?]*[ -\/]*[@-~]')
def clean_text(string: str) -> str:
    """Remove unicode and ANSI characters from string.

    OpenCPI unit test stdout includes characters that are illegal in 
    xml. This function attempts to remove them so that the reports
    can be parsed properly.
    
    Args:
        string: The string to clean.

    Returns:
        The passed in string with non-ASCII characters stripped.
    """
    if not isinstance(string, str):
        return ''
    string = string.encode('ascii', 'ignore').decode()
    return ansi_escape.sub('', string)
