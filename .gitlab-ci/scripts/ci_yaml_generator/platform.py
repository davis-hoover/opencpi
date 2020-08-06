from pathlib import Path


class Platform():


    def __init__(self, path, name=None, model=None, links=None, is_host=False, is_osp=False):
        self.path = path
        self.name = name if name else path.stem
        self.model = model if model else path.parents[1].stem
        self.is_host = is_host
        self.is_osp = is_osp

        if not links:
            links = []

        self.links = list(links)

    
    @classmethod
    def discover_platforms(cls, projects, platform_directive=None):
        platforms = []
        osps = []

        if not isinstance(projects, list):
            projects = [projects]

        for project in projects:
            hdl_platforms_path = Path(project.path, 'hdl', 'platforms')
            rcc_platforms_path = Path(project.path, 'rcc', 'platforms')

            for platforms_path in [hdl_platforms_path, rcc_platforms_path]:
                if platforms_path.is_dir():

                    for platform_path in platforms_path.glob('*'):
                        if platform_directive and platform_path.stem not in platform_directive.keys():
                            continue
                        
                        if platform_path is hdl_platforms_path:
                            makefile = Path(platform_path, 'Makefile')
                            is_host = False
                        else:
                            makefile = Path(platform_path, '{}.mk'.format(platform_path.stem))
                            is_host = Path(platform_path, '{}-check.sh'.format(platform_path.stem)).is_file()

                        if makefile.is_file():
                            links = platform_directive[platform_path.stem] if platform_directive else None
                            platform = cls(platform_path, links=links, is_host=is_host)
                            platforms.append(platform)

        # response = requests.get('https://gitlab.com/api/v4/groups/6009537/projects').json()

        # for osp in response:
        #     platform_path = osp['http_url_to_repo']
        #     platform_name = osp['name'].lower().replace(' ', '')
        #     links = platform_directive[platform_name]
        #     platform = Platform(platform_path, name=platform_name, model='hdl', links=links, is_osp=True)
        #     platforms.append(platform)

        return platforms


    @staticmethod
    def get_platform(platforms, platform_name):
        for platform in platforms:
            if platform.name == platform_name:
                return platform


    @staticmethod
    def get_model_platforms(platforms, model):
        return [platform for platform in platforms if platform.model == model]


    @staticmethod
    def get_hdl_platforms(platforms):
        return get_model_platforms(platforms, 'hdl')

    
    @staticmethod
    def get_rcc_platforms(platforms):
        return get_model_platforms(platforms, 'rcc')


    @staticmethod
    def get_host_platforms(platforms):
        return [platform for platform in platforms if platform.is_host]


    @staticmethod
    def get_cross_platforms(platforms):
        return [platform for platform in platforms if not platform.is_host]
        