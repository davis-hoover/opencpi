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

# This Makefile fragment is for the "interfaces" project

# Package identifier is used in a hierarchical fashion from Project to Libraries....
# The PackageName, PackagePrefix and Package variables can optionally be set here:
# PackageName defaults to the name of the directory
# PackagePrefix defaults to local
# Package defaults to PackagePrefix.PackageName
#
# ***************** WARNING ********************
# When changing the PackageName or PackagePrefix of an existing project the
# project needs to be both unregistered and re-registered then cleaned and
# rebuilt. This also includes cleaning and rebuilding any projects that
# depend on this project.
# ***************** WARNING ********************
#
PackageName=interfaces
PackagePrefix=ocpi


ProjectDependencies=




