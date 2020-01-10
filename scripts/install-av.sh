#!/bin/bash --noprofile
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

# Just check if it looks like we are in the source tree.
[ -d runtime -a -d build -a -d scripts -a -d tools ] || {
  echo "Error:  this script ($0) is not being run from the top level of the OpenCPI source tree."
  exit 1
}
mkdir -p av
cd av
# install the OpenCPI AV IDE from the net, prebuilt

YUMS="oxygen-icon-theme jre"
MIRROR=https://downloads.yoctoproject.org
ECLIPSE=eclipse-full/technology/epp/downloads/release/neon/3
FILE=eclipse-cpp-neon-3-linux-gtk-x86_64.tar.gz
DOWNLOAD=https://www.eclipse.org/downloads/packages/release/neon/3
AVFILE=av.proj.ide.plugin_1.5.jar
AVURL=https://opencpi.github.io/ide
set -e
#echo Ensuring that the prerequisite packages are available and installed on this system...
#sudo yum install $YUMS ||
#    (echo Failed to obtain the required packages from CentOS repository using: yum install $YUMS && exit 1)
if [ -r $FILE ]; then
    echo The Eclipse download file already exists here and will be used, not downloaded: $FILE
else
    echo Downloading the eclipse package that the AV IDE is based on...
    if ! curl -fLO $MIRROR/$ECLIPSE/$FILE; then
	echo Failed to download the eclipse package from: $MIRROR
	echo You may want to try downloading it in a browser at:
	echo '   '$DOWNLOAD
	echo Be sure to download the version for Linux 64 bit.
	echo The resulting file is expected to be: $FILE
	echo After the manual download via browser, you can run this script again here.
	exit 1
    fi
fi
if [ -d eclipse ]; then
    echo Removing the existing eclipse directory to prepare to unpack the download file.
    rm -r -f eclipse
fi
echo Extracting the eclipse download file: $FILE
tar xf $FILE
[ -d eclipse ] ||
    (echo 'Extracting the eclipase download file did not create an "eclipse" directory as expected.' && exit 1)
if true; then
echo Installing the Sapphire Eclipse plug-in required by AV
# This list is taken from the list of sapphire plugins in the installation-details and plugins pane
# from eclipse after loading the sapphire plugin manually via the "marketplace".
# It is a superset of what is in the MANIFEST.MF of the av.ide jar file, which has proven to be necessary.
# It is possible it could be pruned.
./eclipse/eclipse -application org.eclipse.equinox.p2.director \
		  -repository http://download.eclipse.org/releases/neon \
		  -installIU org.eclipse.sapphire.modeling \
		  -installIU org.eclipse.sapphire.ui.swt.gef \
		  -installIU org.eclipse.sapphire.doc \
		  -installIU org.eclipse.sapphire.platform \
		  -installIU org.eclipse.sapphire.workspace \
		  -installIU org.eclipse.sapphire.workspace.ui \
		  -installIU org.eclipse.sapphire.java.jdt \
		  -installIU org.eclipse.sapphire.java.jdt.ui \
		  -installIU org.eclipse.sapphire.java \
		  -installIU org.eclipse.sapphire.osgi \
		  -installIU org.eclipse.sapphire.osgi.fragment \
		  -installIU org.eclipse.sapphire.sdk \
		  -installIU org.eclipse.sapphire.ui \
		  -installIU org.eclipse.sapphire.ui.swt.xml.editor \
		  -installIU org.eclipse.sapphire.modeling.xml \
		  -nosplash
else
    echo OK DO SAPPHIRE MANUALLY
    ./eclipse/eclipse
fi
echo Downloading the OpenCPI AV ecplipse plugin from Github
if ! curl -fLO $AVURL/$AVFILE; then
    echo Failed to download the OpenCPI AV eclipse plugin from $AV
    exit 1
fi
mv $AVFILE eclipse/dropins
if true; then
echo Preconfiguring Eclipse for the AV workspace in this OpenCPI installation.
# Set default workspace to the AV installation
ed -s eclipse/configuration/config.ini <<'EOF'
g/osgi.instance.area.default=/s+=.*$+=@config.dir/../workspace+
w
EOF
# Avoid the initial workspace dialog so we start in the right place
mkdir -p eclipse/configuration/.settings
cat > eclipse/configuration/.settings/org.eclipse.ui.ide.prefs <<EOF
MAX_RECENT_WORKSPACES=10
RECENT_WORKSPACES=`pwd`/workspace
RECENT_WORKSPACES_PROTOCOL=3
SHOW_RECENT_WORKSPACES=false
SHOW_WORKSPACE_SELECTION_DIALOG=false
eclipse.preferences.version=1
EOF
mkdir -p workspace/.metadata/.plugins/org.eclipse.ui.intro
cat > workspace/.metadata/.plugins/org.eclipse.ui.intro/introstate <<EOF
<?xml version="1.0" encoding="UTF-8"?>
<state reopen="false"/>
EOF
fi
cat<<EOF
Running AV to make some final installation settings.  Log output is in av/av.log.  Do these steps:
If the "Force Quit or Wait" window comes up, click "Wait" to allow it to start
1. Close the Welcome Tab, clicking the X in the Welcome window's tab.
2. Select: Window->Perspective->Open Perspective->Other...
3. Choose the "ANGRYVIPER Perspective" then click OK.
4. Select: File->Import, open the General category and select Existing Projects into Workspace, Click OK.
5. Use Select root directory, and the Browse next to it to select the project-registry directory
   OpenCPI built-in projects should appear in the lower level Project Explorer window
6. Select the Refresh button in the OpenCPI Projects window.
7. After a few minutes (patience...) those same projects will appear in the OpenCPI Projects window.
8. Select: Window->Show View->Other...
9. Under General, select Console, and then OK
10.Select File->Exit to exit the program.
EOF
. ../cdk/opencpi-setup.sh -r
./eclipse/eclipse > av.log 2>&1
cat <<-'EOF'
	The AV installation is complete and can be used via the ocpiav tool, using "ocpiav run".
	To access this tool from the Applications->Programming menu bar you must put a file under your home directory.
	To do that, use the "ocpiav desktop" command.
	The ocpiav command must be run in a normal user environment (after opencpi-setup.sh is run).
EOF
