[//]: # (These are reference links used in the body of this note and get 
         stripped out when the markdown processor does its job. The blank lines
         before and after these references are important for portability across
         different markdown parsers.)

[doc]:  <https://opencpi.gitlab.io>

[issues]: <https://gitlab.com/opencpi/opencpi/-/issues>

[mailing_list]: <http://lists.opencpi.org>

[src_install]: <https://opencpi.gitlab.io/releases/develop/docs/OpenCPI_Installation_Guide.pdf>

[releases]:   <https://gitlab.com/opencpi/opencpi/-/releases>

[repo]: <https://gitlab.com/opencpi/opencpi>

[rpm_install]: <https://opencpi.gitlab.io/releases/develop/docs/RPM_Installation_Guide.pdf>

[tags]: <https://gitlab.com/opencpi/opencpi/-/tags>

[website]: <https://www.opencpi.org>


**Open Component Portability Infrastructure (OpenCPI)** is an open source
software (OSS) framework for developing and executing component-based
applications on heterogeneous embedded systems.

This is the source distribution of OpenCPI, which is hosted on
gitlab.com, and is located [here][repo].

As a framework for both development and execution, OpenCPI supports defining,
implementing, building and testing components, as well as executing
applications based on those components in the targeted embedded systems.  By
targeting heterogeneous systems, the framework supports development and
execution across diverse processing technologies including general purpose
processors (GPP), field programmable gate arrays (FPGA), and graphics
processing units (GPU) assembled into mixed systems.  Component implementations
(a.k.a. _workers_) are written in the language commonly used to target the type
of processor being used.  Thus workers for GPPs are written in C or C++, workers
for FPGAs are written in VHDL or Verilog, and workers for GPUs are written in
the OpenCL dialect of C.

A common use of OpenCPI is for software-defined radio applications on platforms
that contain both CPU and FPGA computing resources, a type of system on a chip
(SoC).

**An overview of OpenCPI based on the latest release is available on the
[website][website].**

**Users are highly encouraged to file issues (bugs/suggestions/questions) using
the [issue][issues] tracker.**

**An alternative discussion fourm and announcement email list for OpenCPI is
_discuss_ at lists.opencpi.org.  Subscribe at [lists.opencpi.org][mailing_list].**


# Installation
There are two ways to install and use OpenCPI, from source or RPMs.  Both
installation methods require that the user have `sudo` privileges, which may be
a sysadmin task in some environments.

## Source-Based Installation
For any supported development OS, you can download, build, install, and use
OpenCPI starting from source.  To obtain and use OpenCPI this way, you must
select a _tagged release_.  [Releases][releases] and [tags][tags] are listed at
the OpenCPI GitLab repository.  The default git branch, `develop`, is the most
up-to-date branch and is **_not_** guaranteed to be stable, although every
effort is made to try and make it so.  Therefore, using `develop` is "at your
own risk" and documentation is likely not up-to-date, especially for new
features being added.

The source installation method downloads, builds and uses
the software in a directory of the user's choosing (_e.g._ `~/opencpi`).  Thus
multiple versions can be downloaded and coexist, but not execute simultaneously.

Source installations make no global changes to the user's system other than:
- Installing or updating some required standard packages using the `yum install`
  or equivalent command.
- Dynamically/temporarily loading and using the OpenCPI kernel driver in order
  to test it.

Both of the above steps require `sudo` privileges.  The installation process is
described in detail in the install-from-source [installation guide][src_install],
but the steps described here are sufficient if you understand them. You can
either download a tar file for the release, which results in a ~300MB directory
before building, or you can clone the git repository with the complete source
history, which results in a ~650MB directory before building.

### Downloading Sources
The following sections describe ways of downloading and obtaining OpenCPI source
code.

#### Obtaining Sources via Downloading a tar File.
To download the tar file associated with a release, select the release on the
OpenCPI repository releases[releases] page and select the tar file to download.
When the tar file is extracted it will create a directory called
<code>opencpi-<em>\<release-tag\></em></code>, which you should `cd` into.
Some browsers will automatically extract the file, but the first command below
assumes it does not.
```bash
tar xzf opencpi-<release-tag>.tar.gz
cd opencpi-<release-tag>
```

#### Obtaining Sources via Cloning the OpenCPI git Repository.
To download via cloning the entire OpenCPI repo, first ensure that you have
`git` installed on your system.  If `git` is not installed, it can be installed
(on CentOS7) by executing the following command:
```bash
sudo yum install git
```

After git is installed, execute the following commands.  Note the output of the `git tag`
command will show available releases.
```bash
git clone https://gitlab.com/opencpi/opencpi.git
cd opencpi
git tag
git checkout <release-tag>
```

### Build and Test OpenCPI
After downloading the source distribution of OpenCPI you will need to build it
and run some tests to verify everything installed correctly. To do so run the
following:
```bash
./scripts/install-opencpi.sh
```

This command will take a while, and will require you to provide the `sudo`
password twice during the process.  The password for `sudo` is required for the
two _global_ actions described [earlier](#source-based-installation).  If you
are not present to provide the password the installation script may fail, but
can be rerun.  Internet access will be required to download and build various
dependencies and prerequisites needed by OpenCPI.  There are ways around this
requirement that are described in the install-from-source
[installation guide][src_install]. The testing done by this script only executes
software-based components and applications for the host system.


### Environment Setup
After OpenCPI is built and all tests have passed, you will need to setup some
environment variables to start developing with OpenCPI. This is done by sourcing
the `opencpi-setup.sh` script.  OpenCPI only supports the **bash** shell. 

There are two ways to setup your environment.

#### Manually Setup Environment
If you want to manually set up your environment in each shell window as you need
it, you simply _source_ the script where it lives, under the `cdk` subdirectory.
_E.g._ if OpenCPI was downloaded into the `~/opencpi` directory, you would run
the following:
```bash
source ~/opencpi/cdk/opencpi-setup.sh -s
```

#### Automatically Setup Environment
If you want to set up the environment automatically once on each login, you need
to add the above command to your `~/.profile` file (or `~/.bash_login` or
`~/.bash_profile`).  Note that this will only take effect when you login, or
when you start a new **login shell** using `bash -l`.


## YUM/RPM Installation
> Currently not availale for OpenCPI 1.7.x

For CentOS7 Linux, there is a binary/pre-built RPM installation
available using the `yum` command.

To install OpenCPI this way, use the following commands:
```bash
sudo yum install yum-utils epel-release
sudo yum-config-manager --add-repo=http://opencpi.github.io/repo/opencpi.repo
sudo yum install 'opencpi*'
```

This installs the latest release of OpenCPI globally on your system, in standard
locations (_e.g._ /usr/share/doc, /usr/lib/debug, etc.). For additional
information to complete the installation consult the
[YUM/RPM Installation Guide][rpm_install].


# Documentation
The available documentation is located [here][doc].  Much of it is oriented
toward those using the CentOS7 YUM/RPM installation, although all the
**development guides** cover both types of installations, described next.

## Building OpenCPI Documentation Locally
Although the current documentation is accessible [here][doc], all the OpenCPI
documentation can be rebuilt (creating PDF files) from the source tree.  This
requires the installation of a number of additional standard packages for
compiling and converting LaTeX and OpenOffice documents.  This process is only
supported on a CentOS7 development host.  The following script installs the
require packages (using `sudo yum install`), builds all the document PDF files,
and creates an `index.html` file, all in the `./doc/pdfs` directory.
```bash
./scripts/install-opencpi-docs.sh
make doc
```

When this script completes successfully, you can view the documents by opening
the `doc/pdfs/index.html` file in your browser.

# License
OpenCPI is Open Source Software (OSS), licensed with the LGPL3. See the
[license file](LICENSE.txt).


