from pathlib import Path

class Asset():

    def __init__(self, name, path, project, is_buildable=False, 
                 is_testable=False):
        self.name = name
        self.path = path
        self.project = project
        self.is_buildable = is_buildable
        self.is_testable = is_testable


def discover_assets(path, project, blacklist=None, whitelist=None):
    """Discovers local assets in a provided Path

    Args:
        path:      Path to discover assets for
        blacklist: List of asset names not to include
        whitelist: List of asset names to only include. 
                   Precedence over blacklist

    Returns:
        List of project assets if project is loca; empty list otherwise
    """

    # Don't discover remote project assets
    if not path:
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

        if whitelist and asset_name not in whitelist:
            continue
        elif blacklist and asset_name in blacklist:
            continue

        if asset_path.stem in ['cards', 'devices']:
            is_testable = True
        else:
            is_testable = False

        if asset_path.parent.stem != 'hdl':
            asset_name = ':'.join([asset_path.parent.stem, asset_name])
        asset = Asset(asset_name, asset_path, project,
                      is_buildable=True, is_testable=is_testable)
        assets.append(asset)

    if Path(components_path, 'specs').is_dir():
        asset_name = components_path.stem
        asset = Asset(asset_name, components_path, project,
                      is_buildable=True, is_testable=True)
        assets.append(asset)
    else:
        for asset_path in components_path.glob('*'):
            if not Path(asset_path, 'specs').is_dir():
                continue

            asset_name = asset_path.stem
            asset = Asset(asset_name, asset_path, project,
                          is_buildable=True, is_testable=True)
            assets.append(asset)

    return assets
