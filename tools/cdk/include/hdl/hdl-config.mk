# This is the makefile for platform configuration directories where the platform is elsewhere.
# If configurations are built in subdirectories of platforms, then the platform is ..
# One configuration will be built here.
# The HdlPlatformWorker variable must be set to point to the relative or absolute path
# to the platform's directory, ending in the name of the platform.
HdlMode:=config
include $(OCPI_CDK_DIR)/include/hdl/hdl-make.mk
# These next lines are similar to what worker.mk does
override Workers:=$(CwdName:config-%=%)
override Worker:=$(Workers)
XmlName:=$(Worker).xml
Worker_$(Worker)_xml:=$(or $(wildcard $(XmlName)),\
                           $(wildcard $(HdlPlatformWorker)/$(XmlName)),\
                           $(wildcard $(HdlPlatformWorker)/gen/$(XmlName)),\
                           $(wildcard $(GeneratedDir)/$(XmlName)))
Worker_xml:=$(Worker_$(Worker)_xml)
ifndef Worker_xml
  $(error The XML for the platform configuration, $(Worker).xml, is missing)
endif
OcpiLanguage:=vhdl
override HdlLibraries+=platform
PlatformName=$(notdir $(HdlPlatformWorker))
LibDir=$(HdlPlatformWorker)/lib/hdl
override HdlPlatforms:=$(notdir $(HdlPlatformWorker))
override HdlPlatform:=$(HdlPlatforms)
override HdlPart:=$(HdlPart_$(HdlPlatforms))
override HdlTargets:=$(call HdlGetFamily,$(HdlPart))
override HdlTarget:=$(HdlTargets)
override Platform:=$(HdlPlatform)
override XmlIncludeDirsInternal+=$(HdlPlatformDir_$(Platform)) $(HdlPlatformDir_$(Platform))/hdl
# Platforms need all these.  We can also accept some from the platform if we are below it.
# otherwise the config's makefile can supply more?
override ComponentLibraries=\
  $(call Unique,devices cards $(HdlPlatformDir_$(Platform)) $(wildcard $(HdlPlatformDir_$(Platform))/devices) $(ComponentLibrariesInternal))
include $(OCPI_CDK_DIR)/include/hdl/hdl-pre.mk
ifneq ($(MAKECMDGOALS),clean)
  ifndef HdlSkip
    $(eval $(HdlPrepareAssembly))
    include $(OCPI_CDK_DIR)/include/hdl/hdl-worker.mk
  endif # skip from hdl-pre.mk
endif # cleaning
