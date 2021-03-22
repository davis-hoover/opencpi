#!/usr/bin/env python3

from os import getenv
from pathlib import Path
from urllib.request import urlopen

def get_downstream_branch(project_id, ci_env):
    """Gets matchings downstream branch

    If a downstream branch matches ci_env.commit_ref_name branch,
    return that branch name. A downstream branch is considered a match
    if the name is identical with addition of upstream branch's group
    name and a hyphen as a prefix.

    Args:
        project_id: ID of opencpi project to find matching downstream 
                    branch for
        ci_env:     Object with CI environment variables as attributes
    Returns:
        name of matching downstream branch if found; 'develop' otherwise
    """
    project_id = str(project_id)
    downstream_ref = '-'.join([ci_env.project_name, 
                               ci_env.commit_ref_name])
    url =  '/'.join(['https://gitlab.com', 'api', 'v4', 'projects', 
                     project_id, 'repository', 'branches', downstream_ref])

    try:
        with urlopen(url):
            return downstream_ref
    except: 
        return 'develop'


def get_upstream_branch():
    """Gets matchings upstream branch

    If an upstream branch matches current branch, return that branch 
    name. An upstream branch is considered a match if the name is 
    identical minus the 'opencpi-' prefix. If the current branch does
    not contain an 'opencpi-' prefix, do not search for a match.

    Returns:
        name of matching upstream branch if found; 'develop' otherwise
    """
    commit_ref_name = getenv('CI_COMMIT_REF_NAME')

    if not commit_ref_name.startswith('opencpi-'):
        return 'develop'

    upstream_ref = commit_ref_name.replace('opencpi-', '')
    project_id = '12747880'
    url =  '/'.join(['https://gitlab.com', 'api', 'v4', 'projects', 
                     project_id, 'repository', 'branches', upstream_ref])
    
    try:
        with urlopen(url):
            return upstream_ref
    except:   
        return 'develop'