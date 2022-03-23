$(if $(realpath $(OCPI_CDK_DIR)),,\
  $(error The OCPI_CDK_DIR environment variable is not set correctly.))
# This is the application Makefile for the "foo_app" application
# If there is a foo_app.cc (or foo_app.cxx) file, it will be assumed to be a C++ main program to build and run
# If there is a foo_app.xml file, it will be assumed to be an XML app that can be run with ocpirun.
# The RunArgs variable can be set to a standard set of arguments to use when executing either.
include $(OCPI_CDK_DIR)/include/application.mk
