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

from argparse import ArgumentParser
import sys
import collections
import os
import glob
import tarfile
import tempfile
import subprocess
import datetime
import _opencpi.util as ocpiutil

Option = collections.namedtuple('Option', 'short long help default required action')
Subcommand = collections.namedtuple('Subcommand', 'name func help options')
Command = collections.namedtuple('Command', 'cmd rc stderr')


def main():
    """Creates ArgumentParser and parse user args.

    Create options and commands for an argparse ArgumentParser, parse the
    user's arguments, and call the function specified by the user, passing
    the parsed arguments.
    """
    ocpi_server_addresses = os.environ.get('OCPI_SERVER_ADDRESSES')
    ip = None
    port = None

    if ocpi_server_addresses and ':' in ocpi_server_addresses:
        ip = ocpi_server_addresses.split(':')[0]
        port = ocpi_server_addresses.split(':')[1]

    option_ip = make_option(
        '-i', '--ip_addr',
        'remote server IP address; first address in OCPI_SERVER_ADDRESSES',
        default=ip,
        required=True)
    option_port = make_option(
        '-r', '--port',
        'remote server port; first port in OCPI_SERVER_ADDRESSES',
        default=port,
        required=True)
    option_user = make_option(
        '-u', '--user',
        'user name for login on remote device',
        default='root')
    option_password = make_option(
        '-p', '--password',
        'user password for login on remote device',
        default='root')
    option_ssh_opts = make_option(
        '-o', '--ssh_opts',
        'ssh options for connecting to remote device; \
            default: -q -o StrictHostKeyChecking=no -o UserKnownHostsFile=/dev/null',
        default='-q -o StrictHostKeyChecking=no -o UserKnownHostsFile=/dev/null')
    option_scp_opts = make_option(
        '-c', '--scp_opts',
        'scp options for copying files to remote device; \
            default: -q -o StrictHostKeyChecking=no -o UserKnownHostsFile=/dev/null',
        default='-q -o StrictHostKeyChecking=no -o UserKnownHostsFile=/dev/null')
    option_remote_dir = make_option(
        '-d', '--remote_dir',
        'directory on remote device to create/use as the server sandbox',
        default='sandbox')
    option_sw_platform = make_option(
        '-s', '--sw_platform',
        'software platform for server environment; default: xilinx13_4',
        default='xilinx13_4')
    option_hw_platform = make_option(
        '-w', '--hw_platform',
        'hardware platform for server environment; default: zed',
        default='zed')
    option_valgrind = make_option(
        '-v', '--valgrind',
        'load/use Valgrind',
        action='store_true')
    option_log_level = make_option(
        '-l', '--log_level',
        'specify log level',
        default=0)

    common_options = [option_user, option_password, option_ip,
                      option_remote_dir, option_ssh_opts, option_scp_opts]

    commands = []
    commands.append(make_subcommand(
        'load', load,
        'Create and send the server package to the remote sandbox directory',
        common_options
        + [option_port, option_valgrind, option_hw_platform,
           option_sw_platform]))
    commands.append(make_subcommand(
        'unload', unload,
        'delete a server sandbox directory',
        common_options))
    commands.append(make_subcommand(
        'reload', reload_,
        'delete a server sandbox directory and then reload it',
        common_options + [option_port, option_valgrind, option_hw_platform,
                          option_sw_platform]))
    commands.append(make_subcommand(
        'start', start,
        'start server on remote device',
        common_options + [option_log_level, option_valgrind]))
    commands.append(make_subcommand(
        'restart', restart,
        'stop and then start server on remote device',
        common_options + [option_log_level, option_valgrind]))
    commands.append(make_subcommand(
        'status', status,
        'get status of server on remote device',
        common_options))
    commands.append(make_subcommand(
        'stop', stop,
        'stop server on remote device',
        common_options))
    commands.append(make_subcommand(
        'test', test,
        'test basic connectivity',
        common_options))
    commands.append(make_subcommand(
        'log', log,
        'watch server log in realtime',
        common_options))
    commands.append(make_subcommand(
        'reboot', reboot,
        'reboot the remote device',
        common_options))
    commands.append(make_subcommand(
        'deploy', deploy,
        'Deploy Opencpi boot files onto the remote device and reboot',
        common_options + [option_hw_platform, option_sw_platform]))

    parser = make_parser(commands)
    args = parser.parse_args()

    # If a subcommand was passed, call it. Else print help message
    if 'func' in args:
        args.func(args)
    else:
        parser.print_help()


def make_option(short, long, help, default=None, required=False, action='store'):
    """ Returns an Option NamedTuple.

    Args:
        short: short form of option flag
        long: long form of option flag
        help: message to display when -h is passed
        default: default value for option (default None)
        required: whether an option is required (default False)
        action: the action that an option performs (default 'store')

    Returns:
        Otion NamedTuple with all args set as its members
    """
    option = Option(short, long, help, default, required, action)

    return option


def make_subcommand(name, func, help, options):
    """ Returns a Subcommand NamedTuple.

    Args:
        name: what user passes to invoke subcommand
        func: function to be invoked by subcommand
        help: help message to display when -h is passed
        options: list of Option NamedTuples that correspond to subcommand

    Returns:
        Subcommand NamedTuple with all args set as its members
    """
    command = Subcommand(name, func, help, options)

    return command


def make_command(cmd, args, ocpiserver=False, ssh=True, rc=0, stderr=True):
    """ Returns a string containing a command formatted to be executed on
        remote device.

    Args:
        cmd: string containing command before formatted to execute
            on remote server
        args: parsed user arguments
        ocpiserver: if True, will format cmd to be passed to ocpiserver.sh
            (default False)
        ssh: if True, will format cmd to be passed through ssh command to
            remote device (default True)
    """
    rc = [rc] if not isinstance(rc, list) else rc

    if ocpiserver:
        cmd = 'cd "{}" && ./ocpiserver.sh "{}"'.format(args.remote_dir, cmd)
    if ssh:
        cmd = 'ssh {} {}@{} sh -c \'{}\''.format(
            args.ssh_opts, args.user, args.ip_addr, cmd)

    command = Command(cmd, rc, stderr)

    return command


def make_parser(commands):
    """ Returns an argparse ArgumentParser.

    Args:
        commands: list of Command NamedTuples to add to the parser
    """
    parser = ArgumentParser()
    subparsers = parser.add_subparsers()

    for command in commands:
        subparser = subparsers.add_parser(name=command.name, help=command.help)
        subparser.set_defaults(func=command.func)

        for option in command.options:
            if option.default is not None:
                subparser.add_argument(option.short, option.long, default=option.default,
                                       action=option.action, help=option.help)
            else:
                subparser.add_argument(option.short, option.long, required=option.required,
                                       action=option.action, help=option.help)

    return parser


def make_tar(tar_files, arcnames, tempdir):
    """ Creates a tar file and returns the path.

    Args:
        tar_files: list of files to add to the tar
        arcnames: list of file paths to achive tar_files to
        tempdir: staging directory for the tar
    """
    mode = "w:gz"
    tar_path = os.path.join(tempdir, 'tar.tgz')

    with tarfile.open(tar_path, mode,
                      format=tarfile.PAX_FORMAT, dereference=True) as tar:
        for tar_file,arcname in zip(tar_files,arcnames):
            tar.add(tar_file, arcname=arcname)

    return tar_path


def execute_commands(commands, args):
    """ Calls execute_command for each command in commands

    Args:
        commands: list of Command NamedTuples
        args: parsed user arguments
    """
    for command in commands:
        if execute_command(command, args) not in command.rc:
            sys.exit()

    return 0


def execute_command(command, args):
    """ Executes a command using subprocess.

    Args:
        command: Command NamedTuple containing data for the command to execute
        args: parsed user arguments

    Returns:
        The subprocess's return code, stdout, and stderr
    """
    with tempfile.TemporaryDirectory() as tmpdir:
        with tempfile.NamedTemporaryFile(dir=tmpdir, mode='w+b',
                                         buffering=0, delete=False) as passwd_file:
            passwd_file_path = passwd_file.name
            passwd_file.write(bytes('echo ' + args.password, 'utf-8'))
            os.chmod(passwd_file_path, 0o700)
        try:
            stderr=''
            with subprocess.Popen(
                    command.cmd.split(),
                    env={'SSH_ASKPASS': passwd_file_path, 'DISPLAY': 'DUMMY'},
                    start_new_session=True,
                    stdin=subprocess.PIPE,
                    stdout=subprocess.PIPE,
                    stderr=subprocess.PIPE,
                    universal_newlines=True) as process:
                for stdout in process.stdout:
                    print(stdout, end='')
                if process.stderr:
                    stderr = process.stderr.read().strip()

        except Exception as e:
            raise ocpiutil.OCPIException(
                'SSH/SCP call failed in a way we cannot handle; quitting. {}'.format(e))

        if stderr and command.stderr:
            print(stderr)

        return process.returncode


def load(args):
    """ Gather files for ocpiserver package and send to remote device.

    Args:
        args: parsed user arguments
    """
    cdk = os.environ['OCPI_CDK_DIR']

    driver_list = os.path.join(cdk,args.sw_platform,'lib','driver-list')
    with open(driver_list) as driver_file:
        drivers = ['libocpi_{}_s.so'.format(driver) for line in driver_file
                   for driver in line.strip().split()]
        drivers = [os.path.join(cdk, args.sw_platform, 'lib', driver) for driver in drivers]

    localtime = os.path.join('/etc', 'localtime')
    os_driver = os.path.join(cdk, 'scripts', 'ocpi_linux_driver')
    ocpiserver = os.path.join(cdk, 'scripts', 'ocpiserver.sh')
    kernel_objects = glob.glob(os.path.join(cdk, args.sw_platform, 'lib', '*.ko'))
    rules = glob.glob(os.path.join(cdk, args.sw_platform, 'lib', '*.rules'))
    bin_files = ['ocpidriver', 'ocpiserve', 'ocpihdl', 'ocpizynq']
    bin_files = [os.path.join(cdk, args.sw_platform, 'bin', bin_file) for bin_file in bin_files]
    sdk = glob.glob(os.path.join(cdk, args.sw_platform, 'sdk', 'lib', '*'))

    # List of files to add to tar
    tar_files = (drivers
             + kernel_objects
             + rules
             + bin_files
             + sdk
             + [localtime, ocpiserver, os_driver])

    # Where to extract files to on remote device
    arcnames = [os.path.join(args.remote_dir, *tar_file[len(cdk):].split('/'))
                if tar_file.startswith(cdk) else tar_file
                for tar_file in tar_files]

    # Check for hw system.xml. If it doesn't exist, get sw system.xml
    hw_system_xml = os.path.join(cdk, 'deploy', args.hw_platform, 'opencpi', 'system.xml')
    sw_system_xml = os.path.join(cdk, args.sw_platform, 'system.xml')
    system_xml = hw_system_xml if os.path.isfile(hw_system_xml) else sw_system_xml

    tar_files.append(system_xml)
    system_xml_arc = os.path.join(args.remote_dir, *system_xml[len(cdk):].split('/'))
    arcnames.append(system_xml_arc)

    if args.valgrind:
        tar_files.append(
            os.path.join(cdk, '..', 'prerequisites', 'valgrind', args.sw_platform))
        arcnames.append(
            os.path.join(args.remote_dir, 'prerequisites', 'valgrind', args.sw_platform))

    with tempfile.TemporaryDirectory() as tempdir:
        # Prepare sandbox
        commands = []
        commands.append(make_command(
            'mkdir {}'.format(args.remote_dir),
            args))
        commands.append(make_command(
            'date -s "{}"'.format(datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")),
            args))
        commands.append(make_command(
            'echo {} > {}/swplatform'.format(args.sw_platform, args.remote_dir),
            args))
        commands.append(make_command(
            'echo {} > {}/port'.format(args.port, args.remote_dir),
            args))
        commands.append(make_command(
            'ln -s scripts/ocpiserver.sh {}'.format(args.remote_dir),
            args))
        commands.append( make_command(
            'ln -s ../{} {}'.format(system_xml_arc, args.remote_dir),
            args))

        print('Preparing remote sandbox...')
        rc = execute_commands(commands, args)

        # Create server package
        print('Creating server package...')
        tar_commands = []
        tar_path = make_tar(tar_files, arcnames, tempdir)
        tar_commands.append(make_command(
            'scp {} {} {}@{}:./{}'.format(
                args.scp_opts, tar_path, args.user, args.ip_addr, args.remote_dir),
            args,
            ssh=False))
        tar_commands.append(make_command(
            'gunzip -c {}/tar.tgz | tar xf -'.format(args.remote_dir),
            args))

        print('Sending server package...')
        rc = execute_commands(tar_commands, args)

        if rc == 0:
            print('Server package sent successfully.')

    return rc


def reboot(args):
    """ Reboot the remote device.

    Args:
        args: parsed user arguments
    """
    if status(args, stderr=False) == 0:
        if stop(args) != 0:
            return 1

    command = make_command('/sbin/reboot', args)
    rc = execute_command(command, args)

    if rc in command.rc:
        print("Rebooting remote device...")

    return rc


def deploy(args):
    """ Copy boot files to the remote device and call reboot().

    Args:
        args: parsed user arguments
    """
    cdk = os.environ['OCPI_CDK_DIR']
    local_dir = '{}/{}/sdcard-{}'.format(cdk, args.hw_platform, args.sw_platform)

    if not os.path.isdir(local_dir):
        print("Error: {} does not exist".format(local_dir))
        print("Try running 'scripts/deploy-opencpi.sh {} {}'".format(
                    args.hw_platform, args.sw_platform)
            )

        return 1

    tar_files = [os.path.join(local_dir, f) for f in os.listdir(local_dir) if f != 'opencpi']

    with tempfile.TemporaryDirectory() as tempdir:
        tar_commands = []
        tar_path = make_tar(tar_files, tar_files, tempdir)

        tar_commands.append(make_command(
            'if [ ! -d {} ]; then mkdir {}; fi'.format(args.remote_dir),
            args))
        tar_commands.append(make_command(
            'scp {} {} {}@{}:./{}'.format(
                args.scp_opts, tar_path, args.user, args.ip_addr, args.remote_dir),
            args,
            ssh=False))
        tar_commands.append(make_command(
            'gunzip -c {}/tar.tgz | tar xf -'.format(args.remote_dir),
            args))

        print('Deploying Opencpi boot files to remote device from {} ...'.format(local_dir))
        rc = execute_commands(tar_commands, args)

    if rc == 0:
        print('Opencpi boot files deployed successfully.')
        rc = reboot(args)

    return rc


def unload(args):
    """ Unload ocpiserver package from remote device.

    First attempts to stop server in case it's still running.

    Args:
        args: parsed user arguments
    """
    if status(args, stderr=False) == 0:
        if stop(args) != 0:
            return 1

    command = 'rm -r {}'.format(args.remote_dir)
    command = make_command(command, args)
    rc = execute_command(command, args)

    if rc in command.rc:
        print("Server unloaded successfully.")

    return rc


def reload_(args):
    """ Reload the remote server package on the remote device by calling unload()
        followed by load().

    Args:
        args: parsed user arguments
    """
    rc = unload(args)

    if rc == 0:
        rc = load(args)

    return rc


def start(args):
    """ Start ocpiserver on remote device.

    Args:
        args: parsed user arguments
    """
    command = 'start'
    if args.valgrind:
        command += ' -V '
    if int(args.log_level) > 0:
        command += ' -l {} '.format(args.log_level)
    command = make_command(command, args, ocpiserver=True)

    rc = execute_command(command, args)

    return rc


def stop(args):
    """ Stop ocpiserver on remote device.

    Args:
        args: parsed user arguments
    """
    command = make_command('stop', args, ocpiserver=True)
    rc = execute_command(command, args)

    return rc


def restart(args):
    """ Restart the server on the remote device by calling stop() followed by start().

    Args:
        args: parsed user arguments
    """
    rc = stop(args)

    if rc == 0:
        rc = start(args)

    return rc


def status(args, stderr=True):
    """ Get the status of the ocpiserver running on remote device.

    Args:
        args: parsed user arguments
    """
    command = make_command('status', args, ocpiserver=True, stderr=stderr)
    rc = execute_command(command, args)

    return rc


def test(args):
    """ Test basic connectivity to remote device.

    Args:
        args: parsed user arguments
    """
    command = make_command('pwd', args)
    rc = execute_command(command, args)

    return rc


def log(args):
    """ Get the status of the ocpiserver running on remote device.

    Args:
        args: parsed user arguments
    """
    command = make_command('log', args, ocpiserver=True)
    rc = execute_command(command, args)

    return rc


if __name__ == '__main__':
    main()
