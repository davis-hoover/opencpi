#!/usr/bin/env python3
import subprocess
import json
from pathlib import Path
import pprint
from os import environ, chdir

def main():
    set_env()
    platforms = get_platforms()
    projects = get_projects()
    stages = get_stages(platforms)
    jobs = get_jobs(platforms, projects, stages)
    pprint.pprint(jobs)
    # pprint.pprint(platforms)
    # pprint.pprint(projects)


def set_env():
    environ['CI_PIPELINE_SOURCE'] = 'parent_pipeline'
    environ['CI_OCPI_CROSS_PLATFORM_NAME'] = 'zed'
    environ['CI_OCPI_CROSS_PLATFORM_MODEL'] = 'hdl'
    environ['CI_OCPI_HOST_PLATFORM_NAME'] = 'centos7'


def get_jobs(platforms, projects, stages):
    pipeline_source = environ.get('CI_PIPELINE_SOURCE', '')
    host_platforms = platforms['host']
    cross_platforms = platforms['cross']
    if pipeline_source != 'parent_pipeline':
        jobs = get_host_jobs(host_platforms, stages)
        if cross_platforms:
            triggers = get_triggers()
            jobs.update(triggers)

        return jobs

    cross_platform_name = environ.get('CI_OCPI_CROSS_PLATFORM_NAME', '')
    cross_platform_model = environ.get('CI_OCPI_CROSS_PLATFORM_MODEL', '')
    cross_platform = cross_platforms[cross_platform_model][cross_platform_name]
    jobs = get_cross_jobs(cross_platform, stages, projects)

    return jobs


def get_cross_jobs(cross_platform, stages, projects):
    jobs = []
    for stage in stages:
        if stage == 'install':
            job = get_cross_job(cross_platform, stage)
            jobs.append(job)

        for project in projects:
            tests = get_tests(projects[project])
            for test in tests:
                test_dir = tests[test]
                job = get_cross_job(cross_platform, stage, test_dir)
                jobs.append(job)
            if stage != 'build-assemblies':
                continue
            assemblies = get_assemblies(projects[project])
            for assembly in assemblies:
                assembly_dir = assemblies[assembly]
                job = get_cross_job(cross_platform, stage, assembly_dir)
                jobs.append(job)

    return jobs


def get_cross_job(cross_platform, stage, asset_dir=None):
    script = get_script(cross_platform, stage, asset_dir)
    return {'script': script}


def get_host_jobs(host_platforms, stages):
    pass


def get_script(platform, stage, asset_dir=None):
    if stage == 'install':
        script = 'ocpiadmin install platform {}'.format(platform['name'])
    elif stage == 'build-assemblies':
        script = 'ocpidev build -d {} --only-platform {}'.format(
            asset_dir, platform['name'])
    elif stage == 'test':
        script = 'ocpidev run test -d {} --only-platform {}'.format(
            asset_dir, platform['name'])
    else:
        script = 'script for' + stage
    return script


def get_triggers():
    pass


def get_stages(platforms):
    pipeline_source = environ.get('CI_PIPELINE_SOURCE', '')
    stages = []
    if pipeline_source != 'parent_pipeline':
        if platforms['host']:
            stages = ['prereqs', 'build', 'test', 'generate', 'trigger']
    else:
        platform_model = environ['CI_OCPI_CROSS_PLATFORM_MODEL']
        if platform_model == 'rcc':
            stages = ['install', 'build-assemblies']
        elif platform_model == 'hdl':
            stages = ['install', 'build-assemblies', 'test']

    if stages:
        return stages

    raise Exception('Could not determine stages')


def get_assemblies(project):
    project_dir = project['real_path'] 
    assemblies_path = Path(project_dir, 'hdl', 'assemblies')
    assemblies = {}
    for assembly_path in assemblies_path.glob('*'):
        if not assemblies_path.exists():
            continue
        for assembly_path in assemblies_path.glob('*'):
            if not assembly_path.is_dir():
                continue
            assemblies[assemblies_path.name] = str(assembly_path)

    return assemblies


def get_tests(project):
    project_dir = project['real_path'] 
    tests_raw = ocpidev_show('tests', project_dir, 'local')
    tests = {}
    for test_raw in tests_raw:
        libraries = tests_raw[test_raw]['libraries']
        for library in libraries:
            library_tests = libraries[library]['tests']
            for library_test in library_tests:
                tests[library_test] = library_tests[library_test]

    return tests


def get_projects():
    projects = ocpidev_show('projects')['projects']

    return projects


def get_platforms():
    platforms = ocpidev_show('platforms')
    rcc_platforms = platforms['rcc']
    host_platforms = {}
    cross_platforms = {'hdl': platforms['hdl'], 'rcc': {}}
    for hdl_platform in cross_platforms['hdl']:
        cross_platforms['hdl'][hdl_platform]['name'] = hdl_platform
        cross_platforms['hdl'][hdl_platform]['model'] = 'hdl'
        directory = Path(cross_platforms['hdl'][hdl_platform]['directory'])
        if Path(directory, 'runSimExec.{}'.format(hdl_platform)).exists():
            cross_platforms['hdl'][hdl_platform]['is_sim'] = True
        else:
            cross_platforms['hdl'][hdl_platform]['is_sim'] = False
    for rcc_platform in rcc_platforms:
        directory = Path(rcc_platforms[rcc_platform]['directory'])
        rcc_platforms[rcc_platform]['name'] = rcc_platform
        rcc_platforms[rcc_platform]['model'] = 'rcc'
        rcc_platforms[rcc_platform]['is_sim'] = False
        if Path(directory, '{}-check.sh'.format(rcc_platform)).exists():
            host_platforms[rcc_platform] = rcc_platforms[rcc_platform]
        else:
            cross_platforms['rcc'][rcc_platform] = rcc_platforms[rcc_platform]
        
    platforms = {
        'host': host_platforms,
        'cross': cross_platforms
    }

    return platforms


def ocpidev_show(what, directory='.', scope=None):
    cmd = ['ocpidev', 'show', what, '--json']
    # if directory:
    #     cmd.append('-d {}'.format(directory))
    if scope:
        cmd.append('--{}-scope'.format(scope))
    cur_dir = Path.cwd()
    chdir(directory)
    process = subprocess.run(
        cmd, 
        stdout=subprocess.PIPE, 
        stdin=subprocess.PIPE, 
        encoding='utf-8')
    chdir(cur_dir)

    return json.loads(process.stdout)


if __name__ == '__main__':
    main()