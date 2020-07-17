#!/usr/bin/env python3

import subprocess
import os
import tarfile
import sys
from collections import namedtuple
from shutil import rmtree
from argparse import ArgumentParser


def main():
    parser = make_parser()
    args = parser.parse_args()
    env = get_env(args)

    if 'func' in args:
        args.func(args, env)
    else:
        parser.print_help()


def get_env(args):
    Env = namedtuple('Env', 'project_dir, pipeline, stage, job')

    try:
        job_stage = os.getenv('CI_JOB_STAGE')

        # Append failed status to job stage if tagged as failed-job
        # Makes it easier to exclude when downloading artifacts
        if 'tag' in args and args.tag == 'failed-job':
            job_stage += '-failed'

        env = Env(os.getenv('CI_PROJECT_DIR'),
                  os.getenv('CI_PIPELINE_ID'),
                  job_stage,
                  os.getenv('CI_JOB_NAME'))
    except:
        sys.exit('Error: Script is intended to run from within CI pipeline. ' \
                 'Set CI environment variables for testing.')
    os.getcwd()
    if os.getcwd() != env.project_dir:
        sys.exit('Error: Script in intended to run in CI_PROJECT_DIR: {}'.format(env.project_dir))


    return env


def make_parser():
    # Create parser
    parser = ArgumentParser()
    subparsers = parser.add_subparsers()

    # Download subparser
    subparser = subparsers.add_parser(name='download', 
        help='download artifacts from aws. ' \
             'Default: all pipeline artifacts not in current stage and not failed')
    subparser.add_argument('-e', '--exclude', 
        help='artifacts to exclude from download. Can take any number of arguments', 
        nargs='+', metavar='')
    subparser.add_argument('-i', '--include', 
        help='artifacts to include in download. Can take any number of arguments', 
        nargs='+', metavar='')
    subparser.set_defaults(func=download)


    # Upload subparser
    subparser = subparsers.add_parser(name='upload', 
        help='upload artifacts to aws')
    subparser.add_argument('artifact', 
        help='directory or file to upload to aws. Default: cwd',
        nargs='?', default='.')
    subparser.add_argument('-s', '--timestamp', 
        help='upload artifacts in directory updated/created since timestamp', metavar='')
    subparser.add_argument('-t', '--tag', 
        help='tag to give the artifact', metavar='')
    subparser.set_defaults(func=upload)

    return parser


def upload(args, env):
    # Set s3 object
    # Will appear on aws as:
    # 's3://opencpi-ci-artifacts/CI_PIPELINE_ID/CI_JOB_STAGE[-failed]/CI_JOB_NAME'
    s3_object = '/'.join([env.pipeline, env.stage, env.job]) + '.tar'

    # If timestamp passed, find all files created/updated since the timestamp
    if args.timestamp:
        cmd = ['find', args.artifact, '-not', '-type', 'd', '-newerct', args.timestamp]
        process = subprocess.Popen(cmd, stdout=subprocess.PIPE, universal_newlines=True)
        files = process.stdout.read().split('\n')
    else:
        files = [args.artifact]

    # Create the tar
    with tarfile.open('tar', "w:gz") as tar:
        for f in files:
            if f:
                tar.add(f)

    # Create and execute command to upload tar
    cmd = ['aws', 's3', 'cp', 'tar', 
        's3://opencpi-ci-artifacts/{}'.format(s3_object),
        '--no-progress']
    print(' '.join(cmd))
    process = subprocess.Popen(cmd, stdout=subprocess.PIPE, universal_newlines=True)
    print(process.stdout.read())

    # If tag passed, tag uploaded artifact
    if args.tag:
        tag(args, s3_object)

    # Delete tar
    os.remove('tar')


def download(args, env):
    # temp dir to download artifact into
    temp_dir = os.path.join('.', 'temp', '')

    # Create command to download artifacts, appending optional arguments
    cmd = ['aws', 's3', 'cp', 
        's3://opencpi-ci-artifacts/{}'.format(env.pipeline), temp_dir,
        '--no-progress', '--recursive']
    if args.exclude:
        for exclude in args.exclude:
            cmd += ['--exclude', exclude]
    if args.include:
        # By default in aws, '--include' does nothing unless '--exclude "*"' is passed first
        cmd += ['--exclude', '*']
        for include in args.include:
            cmd += ['--include', include]
    # Do not download artifacts from same stage
    # Necessary in case a job is restarted
    cmd += ['--exclude', '/'.join([env.stage, '*'])]
    # Do not download failed jobs
    cmd += ['--exclude', '/'.join(['*-failed', '*'])]
    print(' '.join(cmd))

    # Execute command to download artifacts
    process = subprocess.Popen(cmd, stdout=subprocess.PIPE, universal_newlines=True)
    print(process.stdout.read())

    # Walk temp_dir and extract tar files
    for dirpath, dirnames, filenames in os.walk(temp_dir):
        for filename in filenames:
            filepath = os.path.join(dirpath, filename)
            cmd = ['tar', '-xf', filepath]
            process = subprocess.Popen(cmd, stdout=subprocess.PIPE, universal_newlines=True)
            out = process.stdout.read()

            if out:
                print(out)

    # Delete temp_dir and its contents
    rmtree(temp_dir)


def tag(args, s3_object):
    # Create command to tag artifact
    cmd = ['aws', 's3api', 'put-object-tagging', '--bucket', 
        "opencpi-ci-artifacts", '--key', s3_object, 
        '--tagging', 'TagSet=[{{Key=type,Value={}}}]'.format(args.tag)]
    
    # Execute command to tag artifact
    process = subprocess.Popen(cmd, stdout=subprocess.PIPE, universal_newlines=True)
    out = (process.stdout.read())

    if out:
        print(out)
    
    # Get expiration date of artifact based on applied tag
    cmd = ['aws', '--output', 'yaml', 's3api', 'head-object', 
        '--bucket', 'opencpi-ci-artifacts', '--key', s3_object]
    process = subprocess.Popen(cmd, stdout=subprocess.PIPE, universal_newlines=True)
    out = process.stdout.read()

    # Command returns yaml
    # Grab only the necessary part
    expiration = out.split('Expiration', 1)[1].split('"')[1]
    print('Expires on {}'.format(expiration))


main()