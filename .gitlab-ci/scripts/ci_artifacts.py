#!/usr/bin/env python3

import subprocess
import os
import tarfile
import sys
import ci_utils
from collections import namedtuple
from shutil import rmtree
from argparse import ArgumentParser


def main():
    """Gets user arguments, CI environment variables, and calls appropriate function.

    Calls make_parser() to get parser and parses user args.
    Calls get_env() to get CI environment variables. 
    Calls function specified by user argument, passing user args and CI env vars.
    """
    parser = make_parser()
    args = parser.parse_args()
    ci_utils.set_test_env()
    ci_env = ci_utils.get_ci_env()

    if 'func' in args:
        rc = args.func(args, ci_env)
        exit(rc)
    else:
        parser.print_help()


def make_parser():
    """ Creates an argparse ArgumentParser.

    Returns:
        argparse ArgumentParser
    """
    # Create parser
    parser = ArgumentParser()
    subparsers = parser.add_subparsers()

    # Create download subparser
    subparser = subparsers.add_parser(
        name='download', 
        help='download artifacts from aws. ' \
             'Default: all pipeline artifacts not in current stage and not failed')
    subparser.add_argument(
        '-e', '--exclude', 
        help='artifacts to exclude from download. Can take any number of arguments', 
        nargs='+', metavar='')
    subparser.add_argument(
        '-i', '--include', 
        help='artifacts to include in download. Can take any number of arguments', 
        nargs='+', metavar='')
    subparser.add_argument(
        'pipeline_id', 
        help='ID of pipeline to download artifacts from', 
        metavar='pipeline_id')
    subparser.set_defaults(func=download)

    # Create upload subparser
    subparser = subparsers.add_parser(
        name='upload', 
        help='upload artifacts to aws')
    subparser.add_argument('artifact', 
        help='directory or file to upload to aws. Default: cwd',
        nargs='?', default='.')
    subparser.add_argument(
        '-s', '--timestamp', 
        help='upload artifacts in directory updated/created since timestamp', 
        metavar='')
    subparser.add_argument(
        '-t', '--tag', 
        help='tag to give the artifact', 
        metavar='')
    subparser.add_argument(
        'pipeline_id', 
        help='ID of pipeline to upload artifacts to', 
        metavar='pipeline_id')
    subparser.set_defaults(func=upload)


    return parser


def exclude_paths(path):
    """ Excludes certain path from being added to tar.

    Args:
        path: Path to be validated for exclusion

        Returns:
            True if path should be excluded; else False
    """
    if '.git' in path:
        return True
    
    return False


def upload(args, ci_env):
    """ Uploads artifacts to aws.

    Tars artifacts and constructs and executes command to upload artifacts to aws.
    Calls tag() if a tag is passed as user argument.

    Args:
        args: User command line arguments
        ci_env:  CI envinronment variables
    """
    # Set s3 object
    # Will appear on aws as:
    # 's3://opencpi-ci-artifacts/CI_PIPELINE_ID/CI_JOB_STAGE[-failed]/CI_JOB_NAME'
    stage = '{}-{}'.format(ci_env.stage, 'failed') if args.tag == 'failed-job' else ci_env.stage
    s3_object = '{}.tar.gz'.format('/'.join([args.pipeline, stage, ci_env.job]))
    s3_url = 'https://opencpi-ci-artifacts.s3.us-east-2.amazonaws.com/{}'.format(s3_object)
    files = []

    # If timestamp passed, find all files created/updated since the timestamp
    if args.timestamp:
        timestamp = os.lstat(args.timestamp).st_ctime
        recursive = False

        for dirpath, dirnames, filenames in os.walk('.'):
            paths = [os.path.join(dirpath, name) for name in dirnames + filenames]

            for path in paths:
                if os.lstat(path).st_ctime > timestamp:
                    files.append(path)              
    else:
        files.append(args.artifact)
        recursive =  True

    # Create the tar
    with tarfile.open('tar', "w:gz") as tar:
        for f in files:
            if f:
                tar.add(f, exclude=exclude_paths, recursive=recursive)
    
    # Create and execute command to upload tar
    cmd = ['aws', 's3', 'cp', 'tar', 
        's3://opencpi-ci-artifacts/{}'.format(s3_object),
        '--no-progress']
    print('Executing: "{}"'.format(' '.join(cmd)))
    print('Uploading artifacts to: {}'.format(s3_url))
    process = subprocess.Popen(cmd, stdout=subprocess.PIPE, universal_newlines=True)
    process.wait()

    if process.stderr:
        print(process.stderr.read().strip())

    # If tag passed, tag uploaded artifact
    if args.tag:
        tag(args, s3_object)

    # Delete tar
    os.remove('tar')

    return process.returncode


def download(args, ci_env):
    """ Downloads artifacts from aws.

    Constructs and executes command to download tar artifacts from aws into temp folder
    and extracts the files from the tar artifacts.

    Args:
        args: User command line arguments
        ci_env:  CI envinronment variables
    """
    # temp dir to download artifact into
    temp_dir = os.path.join('.', 'temp', '')

    # Create command to download artifacts, appending optional arguments
    cmd = ['aws', 's3', 'cp', 
        's3://opencpi-ci-artifacts/{}'.format(args.pipeline_id), temp_dir,
        '--no-progress', '--recursive']

    if args.exclude:
        for exclude in args.exclude:
            cmd += ['--exclude', exclude]
    if args.include:
        # By default in aws, '--include' does nothing unless '--exclude "*"' is passed first
        cmd += ['--exclude', '*']
        for include in args.include:
            cmd += ['--include', include]

    # Do not download failed jobs
    cmd += ['--exclude', '*-failed/*']
    print('Executing: "{}"'.format(' '.join(cmd)))

    # Execute command to download artifacts
    process = subprocess.Popen(cmd, stdout=subprocess.PIPE, universal_newlines=True)
    process.wait()

    if process.stdout:
        print(process.stdout.read().strip())
    
    if process.stderr:
        print(process.stderr.read().strip())

    # Walk temp_dir and extract tar files
    for dirpath, _, filenames in os.walk(temp_dir):
        for filename in filenames:
            filepath = os.path.join(dirpath, filename)
            print('Extracting: {}'.format(filepath))
            with tarfile.open(filepath) as tar:
                tar.extractall()

    # Delete temp_dir and its contents
    rmtree(temp_dir)

    return process.returncode


def tag(args, s3_object):
    """ Tags artifacts on aws.

    Constructs and executes command to tag artifacts on aws.
    Constructs and executes command to get artifact expiration date based on applied tag.

    Args:
        args:       User command line arguments
        s3_object:  The aws s3 object to tag
    """
    # Create command to tag artifact
    cmd = ['aws', 's3api', 'put-object-tagging', '--bucket', 
        "opencpi-ci-artifacts", '--key', s3_object, 
        '--tagging', 'TagSet=[{{Key=type,Value={}}}]'.format(args.tag)]
    
    # Execute command to tag artifact
    process = subprocess.Popen(cmd, stdout=subprocess.PIPE, universal_newlines=True)
    process.wait()
    out = (process.stdout.read())

    if out:
        print(out)
    
    # Get expiration date of artifact based on applied tag
    cmd = ['aws', '--output', 'yaml', 's3api', 'head-object', 
        '--bucket', 'opencpi-ci-artifacts', '--key', s3_object]
    process = subprocess.Popen(cmd, stdout=subprocess.PIPE, universal_newlines=True)
    
    if process.stderr:
        print(process.stderr.read().strip())
    elif process.stdout:
        # Command returns yaml
        # Grab only the necessary part
        out = process.stdout.read().strip()
        expiration = out.split('Expiration', 1)[1].split('"')[1]
        print('Expires on {}'.format(expiration))


main()