$(if $(realpath $(OCPI_CDK_DIR)),,\
  $(error The OCPI_CDK_DIR environment variable is not set correctly.))
# This is the application Makefile for the "data_src_qadc_ext_test_app" application
# If there is a data_src_qadc_ext_test_app.cc (or data_src_qadc_ext_test_app.cxx) file, it will be assumed to be a C++ main program to build and run
# If there is a data_src_qadc_ext_test_app.xml file, it will be assumed to be an XML app that can be run with ocpirun.
# The RunArgs variable can be set to a standard set of arguments to use when executing either.
include $(OCPI_CDK_DIR)/include/application.mk
clean::
	$(AT)rm -rf simulations
	$(AT)rm -rf case00.00.in case00.00.out
