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

$(if $(realpath $(OCPI_CDK_DIR)),,\
  $(error The OCPI_CDK_DIR environment variable is not set correctly.))
# This is an HDL platform Makefile for the "cyclone5_sockit" platform

Libraries=axi cyclone5 sdp

Configurations=base

export QIPFILE:=$(CURDIR)/soc_system.qip
export QSFFILE:=$(CURDIR)/cyclone5_sockit.qsf
# export SRCFILES:=$(CURDIR)/../../primitives/lib/cyclone5/cyclone5/*
export SOPCINFO:=$(CURDIR)/soc_system.sopcinfo
export QSYSFILE:=$(CURDIR)/soc_system.qsys
# export SEQEUNCER:=$(CURDIR)/sequencer/*

SourceFiles=$(QSFFILE) $(QIPFILE)


# The QSF file is included at the platform, config and container levels for QPro platforms
ExportFiles=$(QIPFILE) $(QSFFILE) $(SOPCINFO) $(QSYSFILE)



include $(OCPI_CDK_DIR)/include/hdl/hdl-platform.mk
