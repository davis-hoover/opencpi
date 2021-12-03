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

import argparse
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
Command = collections.namedtuple('Command', 'cmd rc stderr ssh')

def main():
    """Creates ArgumentParser and parse user args.

    Create options and commands for an argparse ArgumentParser, parse the
    user's arguments, and call the function specified by the user, passing
    the parsed arguments.
    """
    ocpi_server_addresses = os.environ.get('OCPI_SERVER_ADDRESSES')
    ip = None
    port = None
    if ocpi_server_addresses:
      # server addresses separated by comma or spaces
      ocpi_server_addresses = ocpi_server_addresses.replace(',', ' ').split()
      if ':' in ocpi_server_addresses[0]:
        ip,port = ocpi_server_addresses[0].split(':')
      else:
        ip = ocpi_server_addresses[0]

    option_ip = make_option(
        '-i', '--ip-addr',
        'remote server IP address; first address in OCPI_SERVER_ADDRESSES',
        default=ip,
        required=ip==None)
    option_port = make_option(
        '-r', '--port',
        'remote server port; first port in OCPI_SERVER_ADDRESSES',
        default=port,
        required=port==None)
    option_user = make_option(
        '-u', '--user',
        'user name for login on remote device',
        default='root')
    option_password = make_option(
        '-p', '--password',
        'user password for login on remote device',
        default='root')
    option_ssh_opts = make_option(
        '-o', '--ssh-options',\
        'ssh options for connecting to remote device;'\
            '\ndefault: -q -o StrictHostKeyChecking=no -o UserKnownHostsFile=/dev/null',
        default='-q -o StrictHostKeyChecking=no -o UserKnownHostsFile=/dev/null')
    option_scp_opts = make_option(
        '-c', '--scp-options',
        'scp options for copying files to remote device;'\
            '\ndefault: -q -o StrictHostKeyChecking=no -o UserKnownHostsFile=/dev/null',
        default='-q -o StrictHostKeyChecking=no -o UserKnownHostsFile=/dev/null')
    option_remote_dir = make_option(
        '-d', '--remote-dir',
        'directory on remote device to create/use as the server sandbox, or'\
            ' the boot directory for the "deploy" subcommand',
        default='sandbox')
    option_sw_platform = make_option(
        '-s', '--sw_platform',
        'deprecated:  use --rcc-platform')
    option_rcc_platform = make_option(
        None, '--rcc-platform',
        'RCC/software platform for server environment; default:  xilinx19_2_aarch32',
        default='xilinx19_2_aarch32')
    option_optimize = make_option(
        '--optimize', '--optimized',
        'Use the optimized (vs. debug) version of the RCC/software platform"',
        action='store_true')
    option_hdl_platform = make_option(
        None, '--hdl-platform',
        'HDL/hardware platform for server environment; default:  zed',
        default='zed')
    option_hw_platform = make_option(
        '-w', '--hw_platform',
        'deprecated:  use --hdl-platform')
    option_bitstream = make_option(
        '-b', '--bitstream',
        'load the opencpi testbias bitstream manually whether or not there is one already loaded',
        action='store_true')
    option_valgrind = make_option(
        None, '--valgrind',
        'load/use Valgrind',
        action='store_true')
    option_verbose = make_option(
        '-v', '--verbose',
        'be more verbose about what is happening',
        action='store_true')
    option_log_level = make_option(
        '-l', '--log-level',
        'specify log level',
        default=0)
    option_memory = make_option(
        '-m', '--memory',
        'specify DMA memory allocation',
        default=0)
    option_environment = make_option(
        '-e', '--environment',
        'specify environment settings to ocpiserve',
        default=0)

    common_options = [option_user, option_password, option_ip,
                      option_ssh_opts, option_scp_opts, option_verbose,
                      option_remote_dir]

    commands = []
    commands.append(make_subcommand(
        'load', load,
        'Create and send the server package to the remote sandbox directory',
        [option_port, option_valgrind, option_hdl_platform, option_optimize, 
         option_rcc_platform, option_hw_platform, option_sw_platform]))
    commands.append(make_subcommand(
        'unload', unload,
        'delete a server sandbox directory'))
    commands.append(make_subcommand(
        'reload', reload_,
        'delete a server sandbox directory and then reload it',
        [option_port, option_valgrind, option_hdl_platform, option_optimize,
         option_rcc_platform, option_hw_platform, option_sw_platform]))
    commands.append(make_subcommand(
        'start', start,
        'start server on remote device',
        [option_log_level, option_valgrind, option_bitstream, option_memory, 
         option_environment]))
    commands.append(make_subcommand(
        'restart', restart,
        'stop and then start server on remote device',
        [option_log_level, option_valgrind, option_bitstream, option_memory, 
         option_environment]))
    commands.append(make_subcommand(
        'status', status,
        'get status of server on remote device'))
    commands.append(make_subcommand(
        'stop', stop,
        'stop server on remote device'))
    commands.append(make_subcommand(
        'test', test,
        'test basic connectivity'))
    commands.append(make_subcommand(
        'log', log,
        'watch server log in realtime'))
    commands.append(make_subcommand(
        'reboot', reboot,
        'reboot the remote device'))
    commands.append(make_subcommand(
        'deploy', deploy,
        'Deploy Opencpi boot files to device and reboot. If a boot directory'\
            ' is not provided, will attempt to determine correct directory by'\
            ' searching for existence of "opencpi/release". NOTE: Clears'\
            ' contents of boot directory',
        [option_hdl_platform, option_rcc_platform, option_hw_platform, 
         option_sw_platform]))

    parser = make_parser(commands, common_options)
    preprocessed_args = preprocess_args(commands)
    args = parser.parse_args(preprocessed_args)

    # If a subcommand was passed, call it. Else print help message
    if 'func' in args:
        rc = 0
        if args.func != test:
            rc = test(args)
        if rc == 0:
            rc = args.func(args)
        sys.exit(rc)
    else:
        parser.print_help()


def preprocess_args(commands):
    """ Preprocessed user args

        Moves options appearing on the left side of the subcommand
        to the right side

    Args: 
        commands: list of possible Subcommands

    Returns:
        string of preprocessed user args
    """
    user_args = sys.argv[1:]
    left_options = []
    processed_args = []
    verbs = [command.name for command in commands]
    for i,user_arg in enumerate(user_args):
        if user_arg in verbs:
            processed_args += user_args[i:]
            processed_args += left_options
            break
        left_options.append(user_arg)

    return processed_args


def test(args):
    """ Test basic connectivity to remote device.

    Args:
        args: parsed user arguments
    """
    if not isinstance(args.ip_addr, str):
      sys.exit("Error: an IP address is required for this command (use the -i or'\
          ' --ip-addr option, or the OCPI_SERVER_ADDRESSES environment variable)")
    cmd = 'ping -q -c 3 '
    cmd += '-o -t 10 ' if os.uname().sysname == 'Darwin' else '-W 10 '
    cmd += args.ip_addr
    command = make_command(cmd, args, ssh=False)
    rc = execute_command(command, args, stdout=subprocess.DEVNULL)
    if rc != 0:
        sys.exit("Error: Unable to ping remote system at address " + args.ip_addr)
    if args.verbose:
        print("Successfully reached remote system with ping at address " + args.ip_addr)
    cmd = 'echo "hello world" > /dev/null'
    command = make_command(cmd, args, stderr=True)
    rc = execute_command(command, args)

    if rc == 255:
        sys.exit('Error: Unable to reach remote device using ssh at address ' + args.ip_addr)
    if rc == 0 and args.verbose:
        print("Successfully reached remote system with ssh at address " + args.ip_addr)
    return rc


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


def make_subcommand(name, func, help, options=None):
    """ Returns a Subcommand NamedTuple.

    Args:
        name: what user passes to invoke subcommand
        func: function to be invoked by subcommand
        help: help message to display when -h is passed
        options: list of Option NamedTuples that correspond to subcommand

    Returns:
        Subcommand NamedTuple with all args set as its members
    """
    if options == None:
        options = []
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
        rc: the return code of the command when successful 
        stderr: boolean of wether to include stderr output
    """
    rc = [rc] if not isinstance(rc, list) else rc

    if ocpiserver:
        cmd = 'cd "{}" && ./ocpiserver.sh {}'.format(args.remote_dir, cmd)
    if ssh:
        cmd = 'ssh {} {}@{} sh -c \'{}\' '.format(
            args.ssh_options, args.user, args.ip_addr, cmd)

    command = Command(cmd, rc, stderr, ssh)

    return command


def make_argument(parser, option, do_required=True, do_default=True):
    """ Adds an argument, dealing with there being no short version
    
    Args: 
        parser: Argparse Parser to add argument to
        option: Option to add as an argument to parser
        is_required: whether to allow the option to be required
        do_default: whether to allow the option to have a default value
    """
    args = {}
    for arg in ['default', 'action', 'required', 'help']:
        try:
            if arg == 'required' and not do_required:
                continue
            elif arg == 'default' and not do_default:
                continue
            args[arg] = option._asdict()[arg]
        except:
            continue
        
    if option.short != None:
        parser.add_argument(option.short, option.long, **args)
    else:
        parser.add_argument(option.long, **args)


def make_parser(commands, common_options):
    """ Returns an argparse ArgumentParser.

    Args:
        commands: list of Command NamedTuples to add to the parser
        common_options: list of common Options to add to main parser
    """

    # This HelpFormatter removes the metavar for the help message
    # Example: "-u USER, --user USER" becomes "-u, --user"
    class HelpFormatter(argparse.HelpFormatter):
        def _format_action_invocation(self, action):
            if not action.option_strings or action.nargs == 0:
                return super()._format_action_invocation(action)
            return ', '.join(action.option_strings)

    formatter = lambda prog: HelpFormatter(prog)
    epilog = "Run 'ocpiremote COMMAND --help' for more information on COMMAND"
    parser = argparse.ArgumentParser(epilog=epilog, formatter_class=formatter)
    parser._optionals.title = 'common options'
    parser._positionals.title = 'verbs'
    subparsers = parser.add_subparsers()
    for option in common_options:
        make_argument(parser, option, do_required=False)

    # Add subcommand options
    for command in commands:
        subparser = subparsers.add_parser(name=command.name, help=command.help, 
                                          formatter_class=formatter, add_help=False)
        subparser.set_defaults(func=command.func)
        required_group = subparser.add_argument_group('required arguments')
        optional_group = subparser.add_argument_group('optional arguments')
        optional_group .add_argument('-h', '--help', action='help', 
            help='show this help message and exit')

        for option in common_options + command.options:
            if command.name == 'deploy' and option.short == '-d':
                make_argument(optional_group, option, do_default=False)
            elif option.required:
                make_argument(required_group, option)
            else:
                make_argument(optional_group, option)

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


def execute_command(command, args, stdin=subprocess.PIPE, stdout=subprocess.PIPE):
    """ Executes a command on the remote device using a subprocess

    Args:
        command: Command NamedTuple containing data for the command to execute
        args: parsed user arguments
        stdin: the subprocess's stdin source
        stdout: the subprocess's stdout source

    Returns:
        The subprocess's return code, stdout, and stderr
    """
    with tempfile.TemporaryDirectory() as tmpdir:
        with tempfile.NamedTemporaryFile(dir=tmpdir, mode='w+b',
                                         buffering=0, delete=False) as passwd_file:
            # Create a password file and set SSH_ASKPASS env var to it.
            # Needed to log into device for remote commands
            passwd_file_path = passwd_file.name
            passwd_file.write(bytes('echo ' + args.password, 'utf-8'))
            os.chmod(passwd_file_path, 0o700)
            env = os.environ
            env['SSH_ASKPASS'] = passwd_file_path
            env['DISPLAY'] = 'DUMMY'
        try:
            stderr=''
            with subprocess.Popen(
                    command.cmd.split(),
                    env=env,
                    start_new_session=True,
                    stdin=stdin,
                    stdout=stdout,
                    stderr=subprocess.PIPE,
                    universal_newlines=True) as process:
                if process.stdout:
                    for stdout_str in process.stdout:
                        print(stdout_str, end='')
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
    rcc = args.sw_platform or args.rcc_platform
    if args.optimize:
        rcc += "-o"
    hdl = args.hw_platform or args.hdl_platform
    plugin_list = os.path.join(cdk, rcc, 'lib', 'plugin-list')
    if not os.path.exists(plugin_list):
       sys.exit('Error:  RCC/software platform "{}" not found or not built:'\
                ' did not find: {}'.format(rcc, plugin_list))
    with open(plugin_list) as plugin_file:
        plugins = ['libocpi_{}_s.so'.format(plugin) for line in plugin_file
                   for plugin in line.strip().split()]
        plugins = [os.path.join(cdk, rcc, 'lib', plugin) for plugin in plugins]

    localtime = os.path.join('/etc', 'localtime')
    os_driver = os.path.join(cdk, 'scripts', 'ocpi_linux_driver')
    ocpiserver = os.path.join(cdk, 'scripts', 'ocpiserver.sh')
    kernel_objects = glob.glob(os.path.join(cdk, rcc, 'lib', '*.ko'))
    rules = glob.glob(os.path.join(cdk, rcc, 'lib', '*.rules'))
    bin_files = ['ocpidriver', 'ocpiserve', 'ocpihdl', 'ocpizynq']
    bin_files = [os.path.join(cdk, rcc, 'bin', bin_file) for bin_file in bin_files]
    sdk = glob.glob(os.path.join(cdk, rcc, 'sdk', '*'))
    bitstream = glob.glob(os.path.join(cdk, hdl, '*.bitz'))
    # List of files to add to tar
    tar_files = (plugins
             + kernel_objects
             + rules
             + bin_files
             + sdk
             + bitstream
             + [localtime, ocpiserver, os_driver])
    # Where to extract files to on remote device
    arcnames = [os.path.join("", *tar_file[len(cdk):].split('/'))
                if tar_file.startswith(cdk) else tar_file
                for tar_file in tar_files]

    # Check for hw system.xml. If it doesn't exist, get sw system.xml
    hw_system_xml = os.path.join(cdk, 'deploy', hdl, 'opencpi', 'system.xml')
    sw_system_xml = os.path.join(cdk, rcc, 'system.xml')
    system_xml = hw_system_xml if os.path.isfile(hw_system_xml) else sw_system_xml

    tar_files.append(system_xml)
    system_xml_arc = os.path.join("", *system_xml[len(cdk):].split('/'))
    arcnames.append(system_xml_arc)


    if args.valgrind:
        tar_files.append(
            os.path.join(cdk, '..', 'prerequisites', 'valgrind', rcc))
        arcnames.append(
            os.path.join("", 'prerequisites', 'valgrind', rcc))

    with tempfile.TemporaryDirectory() as tempdir:
        # Prepare sandbox
        commands = []
        commands.append(make_command(
            'mkdir {}'.format(args.remote_dir),
            args))
        commands.append(make_command(
            'date -s "{}"'.format(
                datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")),
            args))
        commands.append(make_command(
            'echo {} > {}/swplatform'.format(rcc, args.remote_dir),
            args))
        commands.append(make_command(
            'echo {} > {}/hwplatform'.format(hdl, args.remote_dir),
            args))
        commands.append(make_command(
            'echo {} > {}/port'.format(args.port, args.remote_dir),
            args))
        commands.append(make_command(
            'ln -s scripts/ocpiserver.sh {}'.format(args.remote_dir),
            args))
        commands.append( make_command(
            'ln -s {} {}'.format(system_xml_arc, args.remote_dir),
            args))
        print('Preparing remote sandbox...')
        rc = execute_commands(commands, args)

        # Create server package
        print('Creating server package...')
        tar_path = make_tar(tar_files, arcnames, tempdir)
        print('Sending server package...')

        with open(tar_path) as tar_file:
            cmd = make_command(
                    'cd {} && gunzip | tar xf -'.format(args.remote_dir),
                    args)
            rc = execute_command(cmd, args, stdin=tar_file)
        if rc == 0:
            print('Server package sent successfully')
            print('Getting status (no server expected to be running):')
            status(args)
        else:
            print('Sending server package failed.')
    return rc


def reboot(args):
    """ Reboot the remote device.

    Args:
        args: parsed user arguments
    """
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
    rcc = args.sw_platform or args.rcc_platform
    hdl = args.hw_platform or args.hdl_platform
    cdk = os.environ['OCPI_CDK_DIR']
    local_dir = '{}/{}/sdcard-{}'.format(cdk, hdl, rcc)

    if not os.path.isdir(local_dir):
        err_msg = '\n'.join([
            "Error: {} does not exist".format(local_dir),
            "Try running 'ocpiadmin deploy platform {} {}'".format(
                rcc, hdl)
        ])

        return err_msg

    if not args.remote_dir:
        remote_dirs = ['/mnt/card', '/run/media/mmcblk0p1']
        remote_dir = find_deploy_dir(args, remote_dirs)

        if not remote_dir:
            expected_locations = '\n\t'.join(
                [''] + [remote_dir for remote_dir in remote_dirs])
            err_msg = '\n'.join([
                'Error: Unable to locate opencpi/release',
                'Expected locations:{}'.format(expected_locations),
                'Specify another location to deploy to with \'-d\''
            ])

            return err_msg
    else:
        remote_dir = args.remote_dir

    tar_files = [os.path.join(local_dir, f) 
                 for f in os.listdir(local_dir) 
                 if f != 'opencpi']
    if os.path.isfile('{}/opencpi/release'.format(local_dir)):
        tar_files.append('{}/opencpi/release'.format(local_dir))
    arcnames = [tar_file[len(local_dir)+1:] for tar_file in tar_files]

    with tempfile.TemporaryDirectory() as tempdir:
        tar_commands = []
        tar_path = make_tar(tar_files, arcnames, tempdir)
        tar_commands.append(make_command('rm -rf "{}"/*'.format(remote_dir), args))
        tar_commands.append(make_command(
            'scp {} {} {}@{}:{}'.format(
                args.scp_options, tar_path, args.user, args.ip_addr, remote_dir),
            args,
            ssh=False))
        tar_commands.append(make_command(
                'cd "{}" && pwd && ls -l tar.tgz && gunzip -c tar.tgz | tar xf -'.format(remote_dir),
            args))
        print('Deploying Opencpi boot files...')
        print('\tLocal: {}'.format(local_dir))
        print('\tRemote: {}'.format(remote_dir))
        rc = execute_commands(tar_commands, args)

    if rc == 0:
        print('Opencpi boot files deployed successfully.')
        rc = reboot(args)

    return rc


def find_deploy_dir(args, remote_dirs):
    """ Attempts to find location on remote device opencpi was last 
        deployed to

    Args:
        args: parsed user arguments

    Returns:
        If found, directory opencpi was last deployed to; otherwise None
    """
    for remote_dir in remote_dirs:
        cmd = make_command(
            'ls {}/opencpi/release > /dev/null'.format(remote_dir), 
            args, stderr=False)
        rc = execute_command(cmd, args)

        if rc == 0:
            break

    if rc != 0:
        remote_dir = None

    return remote_dir


def unload(args):
    """ Unload ocpiserver package from remote device.

    First attempts to stop server in case it's still running.

    Args:
        args: parsed user arguments
    """

    if status(args, stderr=False) == 0:
      if stop(args) != 0:
          return 1
    
    command = 'if [[ -e {} ]]; then true; else false; fi'.format(args.remote_dir)
    command = make_command(command, args)
    rc = execute_command(command, args)
 
    if rc == 0:
      command = 'rm -r {}'.format(args.remote_dir)
      command = make_command(command, args)
      rc = execute_command(command, args)

      if rc in command.rc:
        print("Server unloaded successfully.")
    else:
      rc = 0
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
    if args.bitstream:
        command += ' -B '
    if args.valgrind:
        command += ' -V '
    if int(args.log_level) > 0:
        command += ' -l {} '.format(args.log_level)
    if args.memory and int(args.memory, 0) > 0:
        command += ' -m 0x{:x} '.format(int(args.memory,0))
    if args.environment:
        command += ' -e "{}" '.format(args.environment)
    command = make_command(command, args, ocpiserver=True)
    return execute_command(command, args)


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
    rc = start(args)

    return rc


def status(args, stderr=True):
    """ Get the status of the ocpiserver running on remote device.

    Args:
        args: parsed user arguments
    """
    cmd = 'ls -d {} >/dev/null'.format(args.remote_dir)
    command = make_command(cmd, args, stderr=None)
    rc = execute_command(command, args)

    if rc not in command.rc:
        err_msg = 'Error: Unable to find remote directory "{}"'.format(
            args.remote_dir)
        sys.exit(err_msg)
    elif args.verbose:
        print('Discovered remote directory "{}"'.format(args.remote_dir))
        
    command = make_command('status', args, ocpiserver=True, stderr=stderr)
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
