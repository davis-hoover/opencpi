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
include $(OCPI_CDK_DIR)/include/util.mk

###############################################################################
# Determine the package of the current asset
#
# Hierarchy of Package naming
# Generally, the full package qualifier is PackagePrefix.PackageName
# PackagePrefix defaults to full package qualifier of the parent (ParentPackage)
# PackageName defaults to notdir of the current directory
#   (unless notdir is components, in which case it is empty)
# If Package is set, it overrides the full package qualifier.
#   This means that if Package is set, all other *Package* variables are ignored
#
# For legacy support:
#   One exception where Package does not override PackagePrefix.PackageName
#   is if Package starts with a '.'. In this case, Prefix.Package is used.
#
# Arg1 is directory to operate on
###############################################################################

define OcpiCreatePackageId
  $(infox OcpiCreatePackageId1:$1:$2:$3:$(realpath $1):$(ParentPackage):$(PackagePrefix)=)
  $$(infox OcpiCreatePackageId2:$1:$2:$3:$$(realpath $1):$$(ParentPackage):$$(PackagePrefix)=)
###############################################################################
# Determine where the 'lib' directory is relative to the current location
# TODO this list of directory-types that are supported for where the 'lib/'
#      directory might be should be a distributed list that is collected here.
#      So, there should be some sort of flag that can be set in library.mk or
#      hdl-platforms.mk for example that flags it as "a dir that can have lib/".
#      This hardcoded list here is not very scalable.
#  Note "application" is in the list here to allow applications to have private libraries in the same dir
#  as long as the last include line is "application"

# For legacy support, we need to expect Package= in library/Makefile
# So, we grep for it here to include if building from the worker level
#   (if building from the worker level, <library>/Library.mk is included,
#    but not <library>/Makefile)
# This is for overriding the default based on parent.
$$(foreach p,$$(shell [ -f $1/Makefile ] && grep "^\s*Package\s*:\?=\s*.*" $1/Makefile),\
  $$(eval $$p))

$$(infox P0:$$(PackagePrefix):$$(PackageName):$$(Package):$$(ParentPackage))
###############################################################################
# If ParentPackage is unset, assume the parent is the project
ifeq ($$(ParentPackage),)
  export ParentPackage:=$$(OCPI_PROJECT_PACKAGE)
endif

# If the PackagePrefix is not set, set it to ParentPackage
ifeq ($$(PackagePrefix),)
  export PackagePrefix:=$$(ParentPackage)
endif

###############################################################################
# If the PackageName is not set, set it to dirname
#   (or blank if dirname == components)
$$(infox P1:$$(PackagePrefix):$$(PackageName):$$(Package):$$(ParentPackage))
ifeq ($$(PackageName),)
  export PackageName:=$$(foreach d,$$(notdir $$(realpath $1)),$$(filter-out components,$$d))
endif
$$(infox P2:$$(PackagePrefix):$$(PackageName):$$(Package):$$(ParentPackage))

# If PackageName is nonempty, prepend it with '.'
export PackageName:=$$(if $$(PackageName),.$$(patsubst .%,%,$$(PackageName)))
$$(infox P3:$$(PackagePrefix):$$(PackageName):$$(Package):$$(ParentPackage))

###############################################################################
# Arg2 to OcpiCreatePackageId is an optional Authoring Model Prefix Segment
# Basically, if this is provided, the PackagePrefix will be appended with
# the authoring model. E.g for hdl/primitives, we have <project>.hdl.primitives
ifneq ($2,)
  export PackageAuth:=$$(if $2,.$$(patsubst .%,%,$2))
  export PackagePrefix:=$$(PackagePrefix)$$(PackageAuth)
endif

###############################################################################
# If package is not set, set it to Package
#   set it to $$(PackagePrefix)$$(PackageName)
# Otherwise, if Package starts with '.',
#   set it to $$(CurrentPackagePrefix)$$(Package)
ifeq ($$(Package),)
  override Package:=$$(PackagePrefix)$$(PackageName)
else
  ifneq ($$(filter .%,$$(Package)),)
    override Package:=$$(PackagePrefix)$$(Package)
  endif
endif
export Package # note that older versions of make cannot use "export override..."
###############################################################################
# Check/Generate the package-id file
#
# Do nothing about packages if we are cleaning
$$(infox P4:$$(PackagePrefix):$$(PackageName):$$(Package):$$(PackageFile))
ifeq ($$(filter clean%,$$(MAKECMDGOALS)),)
  ifneq ($$(filter application lib library %-platform %-platforms %-primitives,$3),)
    PackageFile:=$1/lib/package-id
    $$(infox PACKAGE_FILE:$$(PackageFile):$$(realpath $$(PackageFile)):$(CURDIR))
    $$(shell mkdir -p $1/lib)
    # If package-id file does not yet exist, create it based on Package
    ifeq ($$(call OcpiExists,$$(PackageFile)),)
      $$(shell echo $$(Package) > $$(PackageFile))
    else
      # If package-id file already exists, make sure its contents match Package
      PackageFromFile:=$$(shell cat $$(PackageFile))
      ifneq ($$(Package),$$(PackageFromFile))
        $$(error Package "$$(Package)" and "$$(PackageFromFile)" do not match. You must make clean after changing the package name.)
      endif
    endif
  endif
endif

###############################################################################
$$(infox P5:$$(PackagePrefix):$$(PackageName):$$(Package):$$(PackageFile))

endef # define OcpiCreatePackageId

# Create the Package-ID for dir $1 and return it (the Package variable)
OcpiSetAndGetPackageId=$(strip \
  $(infox CSGP:$1:$2:$3:$(PackagePrefix))\
  $(eval $(call OcpiCreatePackageId,$1,$2,$3))\
  $(infox PACKAGE RETURNED:$(Package)))
