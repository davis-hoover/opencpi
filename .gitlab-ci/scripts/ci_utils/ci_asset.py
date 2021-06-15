from pathlib import Path

class Asset():

    def __init__(self, name, path, project, is_buildable=False, 
                 is_testable=False):
        self.name = name
        self.path = path
        self.project = project
        self.is_buildable = is_buildable
        self.is_testable = is_testable


def discover_assets(project, blacklist=None):
    """Discovers assets in an opencpi Project if the project is local

    Args:
        project:   Project to discover assets for
        blacklist: List of asset names not to include

    Returns:
        List of project assets if project is loca; empty list otherwise
    """

    # Don't discover remote project assets
    if not project.path:
        return []

    assets = []
    components_path = Path(path, 'components')
    hdl_path = Path(path, 'hdl')
    asset_paths = [asset_path 
                   for asset_paths in (hdl_path.glob('*'), path.glob('*')) 
                   for asset_path in asset_paths 
                   if asset_path.stem != 'components']

    for asset_path in asset_paths:

        asset_name = asset_path.stem

        if blacklist and asset_name in blacklist:
            continue

        asset = Asset(asset_name, asset_path, project, is_buildable=True, 
                      is_testable=False)
        assets.append(asset)

    if Path(components_path, 'specs').is_dir():
        asset_name = components_path.stem
        asset = Asset(asset_name, components_path, project, is_buildable=True, 
                      is_testable=True)
        assets.append(asset)
    else:
        for asset_path in components_path.glob('*'):

            if not Path(asset_path, 'specs').is_dir():
                continue

            asset_name = asset_path.stem
            asset = Asset(name=asset_name, path=asset_path, project=project, 
                          is_buildable=True, is_testable=True)
            assets.append(asset)

    return assets
