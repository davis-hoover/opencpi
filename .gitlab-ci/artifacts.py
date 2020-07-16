#!/usr/bin/env python3
# This file is protected by Copyright. Please refer to the COPYRIGHT file
# distributed with this source distribution.
#
# This file is part of OpenCPI <http://www.opencpi.org>
#
# OpenCPI is free software: you can redistribute it and/or modify it under the
# terms of the GNU Lesser General Public License as published by the Free
# Software Foundation, either version 3 of the License, or (at your option) any
# later version.
#
# OpenCPI is distributed in the hope that it will be useful, but WITHOUT ANY
# WARRANTY; without even the implied warranty of MERCHANTABILITY or FITNESS FOR
# A PARTICULAR PURPOSE. See the GNU Lesser General Public License for more
# details.
#
# You should have received a copy of the GNU Lesser General Public License along
# with this program. If not, see <http://www.gnu.org/licenses/>.

import subprocess
from argparse import ArgumentParser
import os
import tarfile
import sys

def main():
    PROJECT_DIR = os.getenv('CI_PROJECT_DIR')

    if not PROJECT_DIR:
        sys.exit('Error: Script is intended to run from within CI pipeline. Set CI environment variables for testing.')
    elif os.getcwd() != PROJECT_DIR:
        sys.exit('Error: Script in intended to run in CI_PROJECT_DIR.')

    parser = make_parser()
    args = parser.parse_args()

    if 'func' in args:
        args.func(args)
    else:
        parser.print_help()


def make_parser():
    parser = ArgumentParser()
    subparsers = parser.add_subparsers()

    # Download subparser
    subparser = subparsers.add_parser(name='download', help='download artifacts from aws')
    subparser.set_defaults(func=download)
    subparser.add_argument('artifact', help='artifact name to download from aws. Default is entire pipeline dir', 
        nargs='?', default='')
    subparser.add_argument('-r', '--recursive', help='indicates artifact to download is a directory', 
        action='store_true')
    subparser.add_argument('-e', '--exclude', help='artifacts to exclude from download', metavar='')
    subparser.add_argument('-i', '--include', help='artifacts to include in download', metavar='')

    # Upload subparser
    subparser = subparsers.add_parser(name='upload', help='upload artifacts to aws')
    subparser.set_defaults(func=upload)
    subparser.add_argument('artifact', help='directory or file to upload to aws. Default is cwd',
        nargs='?', default='.')
    subparser.add_argument('-s', '--timestamp', help='upload artifacts in directory updated/created since timestamp', metavar='')
    subparser.add_argument('-t', '--tag', help='tag to give the artifact', metavar='')

    return parser


def upload(args):
    JOB_STAGE = os.getenv('CI_JOB_STAGE')
    JOB_NAME = os.getenv('CI_JOB_NAME')
    PIPELINE_ID = os.getenv('CI_PIPELINE_ID')
    s3_object = '/'.join([PIPELINE_ID, JOB_STAGE, JOB_NAME]) + '.tar'
    artifact = '{}.tar'.format(JOB_NAME)

    if args.timestamp:
        cmd = ['find', args.artifact, '-not', '-type', 'd', '-newerct', args.timestamp]
        process = subprocess.Popen(cmd, stdout=subprocess.PIPE, universal_newlines=True)
        files = process.stdout.read().split('\n')
    else:
        files = [args.artifact]

    with tarfile.open(artifact, "w:gz") as tar:
        for f in files:
            if f:
                arcname = ''
                if f[:2] == './':
                    arcname = f[2:]
                arcname = 'opencpi/' + arcname
                tar.add(f, arcname=arcname)

    cmd = ['aws', 's3', 'cp', '{}.tar'.format(JOB_NAME), 
        's3://opencpi-ci-artifacts/{}'.format(s3_object),
        '--no-progress']
    process = subprocess.Popen(cmd, stdout=subprocess.PIPE, universal_newlines=True)
    print(process.stdout.read())

    if args.tag:
        tag(args, s3_object)

    os.remove(artifact)


def download(args):
    os.chdir('..')
    PIPELINE_ID = os.getenv('CI_PIPELINE_ID')
    s3_object = '/'.join([PIPELINE_ID, args.artifact])
    temp = os.path.join('.', 'temp', '')

    if s3_object == PIPELINE_ID + '/':
        args.recursive = True

    cmd = ['aws', 's3', 'cp', 
        's3://opencpi-ci-artifacts/{}'.format(s3_object), temp,
        '--no-progress']

    if args.recursive:
        cmd.append('--recursive')
    
    if args.exclude:
        cmd += ['--exclude', args.exclude]

    if args.include:
        cmd += ['--include', args.include]

    process = subprocess.Popen(cmd, stdout=subprocess.PIPE, universal_newlines=True)
    print(process.stdout.read())

    dirs = []
    for dirpath, dirnames, filenames in os.walk(temp):
        for filename in filenames:
            filepath = os.path.join(dirpath, filename)
            cmd = ['tar', '-xf', filepath]
            process = subprocess.Popen(cmd, stdout=subprocess.PIPE, universal_newlines=True)
            out = process.stdout.read()

            if out:
                print(out)

            os.remove(filepath)
        dirs.insert(0, dirpath)

    for directory in set(dirs):
        os.rmdir(directory)


def tag(args, s3_object):
    cmd = ['aws', 's3api', 'put-object-tagging', '--bucket', 
        "opencpi-ci-artifacts", '--key', s3_object, 
        '--tagging', 'TagSet=[{{Key=type,Value={}}}]'.format(args.tag)]
    
    process = subprocess.Popen(cmd, stdout=subprocess.PIPE, universal_newlines=True)
    out = (process.stdout.read())

    if out:
        print(out)
    
    cmd = ['aws', '--output', 'yaml', 's3api', 'head-object', '--bucket', 'opencpi-ci-artifacts', '--key', s3_object]
    process = subprocess.Popen(cmd, stdout=subprocess.PIPE, universal_newlines=True)
    out = process.stdout.read()
    expiration = out.split('Expiration', 1)[1].split('"')[1]

    print('Expires on {}'.format(expiration))


main()