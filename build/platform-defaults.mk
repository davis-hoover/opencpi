# This file provides defaults for platform-specific build variables
# Any platform can override these except that the "required" flags should only be
# "translated" if needed, not removed.

ifndef __PLATFORM_DEFAULTS_MK__
__PLATFORM_DEFAULTS_MK__:=1

# The list of all variables defaulted and settable by platforms
OcpiAllPlatformVars:=\
  OcpiLibraryPathEnv OcpiRpathOrigin \
  OcpiStaticLibrarySuffix OcpiStaticLibraryFlags OcpiStaticProgramFlags \
  OcpiDynamicLibrarySuffix OcpiDynamicLibraryFlags OcpiDynamicProgramFlags OcpiDriverFlags\
  OcpiAsNeeded OcpiExtraLibs OcpiOclLibs OcpiCrossCompile \
  OcpiCFlags OcpiCC OcpiCxxFlags OcpiCXX OcpiLd OcpiSWIG OcpiKernelDir \
  OcpiDebugOnFlags OcpiDebugOffFlags \
  OcpiRequiredCPPFlags OcpiRequiredCFlags OcpiRequiredCXXFlags \
  OcpiOptionalCWarnings OcpiOptionalCXXWarnings OcpiUnknownWarningsError \
  OcpiStrictCFlags OcpiStrictCXXFlags \
  OcpiPlatformTarget OcpiPlatformOs OcpiPlatformOsVersion OcpiPlatformArch \
  OcpiPlatformDir OcpiPlatform OcpiCanRemoveNeeded
# This list of all variables requiring platform compiler testing
OcpiAllOptionalWarningsVars:=\
  OcpiOptionalCWarnings OcpiOptionalCXXWarnings

# Set common linux defaults
OcpiCanRemoveNeeded:=1
OcpiLibraryPathEnv:=LD_LIBRARY_PATH
OcpiRpathOrigin:=$${ORIGIN}
OcpiStaticLibrarySuffix:=.a
OcpiStaticProgramFlags:=-Xlinker -export-dynamic
OcpiStaticLibraryFlags:=
OcpiDynamicLibrarySuffix:=.so
OcpiDynamicLibraryFlags:=-shared -Xlinker --no-undefined -Xlinker -soname=$(@F)
OcpiDynamicProgramFlags:=
OcpiDriverFlags=$(OcpiDynamicLibraryFlags)
OcpiAsNeeded:=-Xlinker --no-as-needed
OcpiExtraLibs:=rt dl pthread
OcpiOclLibs:=-lOpenCL
OcpiCrossCompile:=
# These -g flags are not intended to suppress optimization, just keep sym info around
OcpiCFlags:=-g
OcpiCxxFlags:=-g
OcpiCC:=gcc
OcpiCXX:=c++
OcpiLD:=ld
OcpiAR:=ar
OcpiSTRIP:=strip
OcpiKernelDir=$(OcpiPlatformDir)/kernel-headers
# Other than -g, there is no need to force optimization off
OcpiDebugOnFlags:=
OcpiDebugOffFlags:=-O2
# For all code:
# We require these or their equivalent be supported.  If not its an error
OcpiRequiredCPPFlags:= -D__STDC_FORMAT_MACROS -D__STDC_LIMIT_MACROS
OcpiRequiredCFlags:= -Wall -Wfloat-equal -Wextra -fno-strict-aliasing -Wformat -Wuninitialized \
                    -Winit-self -Wshadow -frecord-gcc-switches -fstack-protector -Wno-conversion \
                    -Wno-sign-conversion -std=c99
OcpiRequiredCXXFlags:=$(filter-out -std%,$(OcpiRequiredCFlags)) -std=c++0x
# For all code:
# We prefer these warnings or their equivalent be supported.  It is not an error if they are not.
# If they are supported they are "error" warnings in strict cases, otherwise normal warnings
OcpiOptionalCWarnings:=maybe-uninitialized misleading-indentation null-dereference \
                       unused-result unused-but-set-variable
OcpiOptionalCXXWarnings:=$(OcpiOptionalCWarnings)
# For "native" OpenCPI code (as opposed to imported code):
# We prefer to ADD these or their equivalent.  It is not an error if they are not supported.
OcpiStrictCFlags:=-Wconversion -Werror=parentheses -Werror=unused-parameter -Werror=empty-body \
	          -Werror=write-strings -Werror=reorder -Werror=extra -Werror=comment \
                  -Werror=format -Werror=init-self -Wsign-conversion
OcpiStrictCXXFlags:=$(OcpiStrictCFlags)
# Set this to the option that cause unknown warnings to be errors
# The default is that unknown warnings are expected to be errors.
OcpiUnknownWarningsError:=
endif
