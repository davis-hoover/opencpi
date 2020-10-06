
import json
from collections import namedtuple
from urllib.request import urlopen
from .ci_platform import Platform

Osp = namedtuple('osp', 'name url platforms')

def discover_osps(group_id='6009537', config=None):
    """ Discovers OSPs

    Uses curl command to call gitlab api to collect OSP group data.
    Calls discover_platforms() to get an OSP's rcc and hdl platforms.

    Args:
        group_id: Gitlab ID of the OSP group
        config:   Dictionary of platform overrides     

    Returns:
        List of Osp namedtuples
    """
    osps = []
    url = 'https://gitlab.com/api/v4/groups/6009537/projects'
    with urlopen(url) as response:
        projects = json.load(response)

        for project in projects:
            osp_url = project['http_url_to_repo']
            osp_id = project['id']
            osp_name = osp_url.split('/')[-1].split('.')[-2]
            osp_platforms = discover_platforms(osp_id, config=config)

            osp = Osp(osp_name, osp_url, osp_platforms)
            osps.append(osp)

    return osps


def discover_platforms(osp_id, config=None):
    """ Discovers OSPs

    Uses curl command to call gitlab api to collect OSP project repo
    data.

    Args:
        osp_id: Gitlab ID of the OSP project 
        config: Dictionary of platform overrides     

    Returns:
        List of Platform namedtuples
    """
    platforms = []
    url = '/'.join([
        'https://gitlab.com/api/v4/projects',
        str(osp_id),
        'repository/tree'
    ])
    
    rcc_url = '?'.join([url, 'path=rcc/platforms'])
    hdl_url = '?'.join([url, 'path=hdl/platforms'])

    for model_url,model in zip([rcc_url, hdl_url], ['rcc', 'hdl']):
        try:
            with urlopen(model_url) as response:
                osp_platforms = json.load(response)
                
                for osp_platform in osp_platforms:
                    platform_name = osp_platform['name']

                    if platform_name == 'Makefile':
                        continue

                    if config and platform_name in config:
                        platform_data = {key:value for key,value
                                        in config[platform_name].items()
                                        if key in ['ip', 'port']}
                    else:
                        platform_data = {}

                    platform = Platform(name=platform_name,
                                        model=model, is_host=False,
                                        is_sim=False, **platform_data)

                    platforms.append(platform)
        except:
            continue

    return platforms