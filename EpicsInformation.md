
OpenCPI Epics Information
=========================

EPIC - GitLab Tools Creation
============================

DESCRIPTION:
------------
Develop GitLab management tools that support various elements of the development and deployment cycle.

ISSUES:
-------

EPIC - ENABLE VALGRIND (leak checking) ALTERNATIVE EXECUTION IN TESTING.  Roadmap Item #18
==========================================================================================

DESCRIPTION:
------------
Valgrind is an instrumentation framework for building dynamic analysis tools. Valgrind can automatically detect many memory management and threading bugs, and profile your programs in detail. 

This is a modest effort to reap some extensive test coverage. The goal is to allow testing with Valgrind to the greatest extent possible (i.e. the CI will need to run with and without Valgrind).

ISSUES:
-------

EPIC - CREATE RCC <-> HDL (HW/SW) THROUGHPUT TESTS AND REPORTS.  Roadmap Item #17
=================================================================================

DESCRIPTION:
------------
As part of tests we need to create new test applications that do performance characterization and measurements in an effort to baseline performance metrics throughput

ISSUES:
-------

EPIC - FINALIZE/RELEASE DIGITAL RADIO CONTROL INTERFACES BASED ON ROADMAP ITEM #15.  Roadmap Item #16
=====================================================================================================

DESCRIPTION:
------------
Digital Radio Control (DRC) is the interface for how you use a piece of radio hardware. In OpenCPI we need to determine how to map bindings that the users sees to the right connectors. The goal of this effort is to update the DRC design to use the portability enhancements as we determine what they are in roadmap item 15.   

Release of this capability in 1.7 is dependent on successful completion of Major Application Portability Enhancements completed in Roadmap Item 15.

ISSUES:
-------

EPIC - MAJOR APPLICATION PORTABILITY ENHANCEMENTS. Roadmap Item #15
===================================================================

DESCRIPTION:
------------
This part of the system determines how to deploy an application. Meaning which binary runs where for each component. An effort needs to be made to address inferred slaves, inferred connections to slaves, and dynamic slaves. The goal of this effort is to prevent inclusion of specific devices that only exists on unique radios.

ISSUES:
-------

EPIC - MOVE OpenCL GPU SUPPORT FROM EXPERIMENTAL TO FULLY SUPPORTED + UPDATE VERSION. Roadmap Item #14
======================================================================================================

DESCRIPTION:
------------
We need to update the OpenCL version we are using. This is a deprecated feature in the framework that requires refresh. Goal is to identify configuration alternatives and what things/modes we will support then revive the capability.

ISSUES:
-------
  
#167 Define Options for Moving OpenCL GPU Support from Experimental to Fully Supported and Update Version


EPIC - SUPPORT IT/FIREWALL-FRIENDLY REMOTE CONTAINER CONNECTION OPTIONS. Roadmap Item #13
=========================================================================================

DESCRIPTION:
------------
This is to add some features that allows more firewall configurable friendliness. The remote container functionality right now is only useful in a lab environment. Distributed capabilities for openCPI aren’t being used because of this restriction. Example efforts include: passive mode FTP, configurable port ranges, a control connection and a connection per stream, etc

ISSUES:
-------

EPIC - NEW EXAMPLE APPLICATIONS AND COMPONENTS WITH TIMESTAMPING (fsk-rx). Roadmap Item #12
===========================================================================================

DESCRIPTION:
------------
This is an application level task and not something new that is building on the GEON work to support applications that use GEO location. Goal is to port an application to do directional finding using capabilities built by GEON in 1.6 release cycle.

ISSUES:
-------

EPIC - ENGAGE WITH (some) ACADEMIA OR ORGANIZATIONS (co-ops, courseware).  Roadmap Item #11
===========================================================================================

DESCRIPTION:
------------
This is a joint Parera/CNF effort to determine how to get opencpi into courseware and engage collegiate professors in using it for there courses. Initial target areas are (San Antonio & New England areas)

ISSUES:
-------

EPIC - PROPER LINUX/UNIX MAN PAGES FOR COMMANDS. Roadmap Item #10
=================================================================

DESCRIPTION:
------------
Develop man pages for user facing command line interfaces (example ocpi* should have a man page).

ISSUES:
-------

EPIC - COMPLETE TRANSITION TO MAKE-LESS DEVELOPMENT UI.  Roadmap Item #7
========================================================================

DESCRIPTION:
------------
This is a focus on existing bugs/issues for ocpidev with the goal to improve robustness and coverage of ocpidev. The ultimate goal would be to relocate any call to Make in ocpidev. The goal is to ensure a  user does not have to type MAKE into the command line. Users need to use ocpidev. Areas to consider:  
* Search all documentation to identify calls to make (including the Java IDE)
* Keep in mind anything that touches ocpidev

ISSUES:
-------

EPIC - GNU RADIO COMPANION INTEGRATION (refresh existing hopefully in python3).  Roadmap Item #9
================================================================================================

DESCRIPTION:
------------
OpenCPI's GNU Radio Companion integration is an independent Python flavored GUI (there is minimal GUI work with this capability). Goal of this item is to revive this capability while keeping in mind other alternatives to what this capability is trying to do. During this release we will focus on identifying what needs to be done for OpenCPI v2.0. 

Item requires a preliminary document written that describes the following:
* What the capability is doing. 
* Identify capabilities, parameters, etc.

ISSUES:
-------

EPIC - UPDATE CODEBASE TO COMPLY WITH CURRENT CODING/NAMING CONVENTIONS. Roadmap Item #8
========================================================================================

DESCRIPTION:
------------
Purely lexical effort that is not fundamentally changing code or removing current testing integrity, but cleaning up the codebase to come in line with contribution guide coding standards.

ISSUES:
-------

EPIC - ROLL FORWARD FPGA TOOLS VERSIONS AND STANDARD PLATFORM OS VERSIONS. Roadmap Item #6
==========================================================================================

DESCRIPTION:
------------
Technical refresh to change recommended tool versions to current ones (e.g. we use Xilinx 19* but we don’t have it identified. We need it clear that OpenCPI uses modern tools. Modelsim is a priority for this.

ISSUES:
-------
  
#207 Roll forward Support Using Quartus Prime Standard FPGA tool to v19.3

  
#141 tl2: automate zynq release support

  
#165 Roll forward Support Using Quartus Prime Pro FPGA tool to v19.3


EPIC - DOCKER CONTAINER PACKAGING FEASIBILITY STUDY. Roadmap Item #5
====================================================================

DESCRIPTION:
------------
Research effort to determine feasibility of streamlining development, third party usage, testing, etc.

ISSUES:
-------
  
#93 ADD DOCKER & VM OPTIONS TO THE OPEN CPI PACKAGING SYSTEM


EPIC - INTEGRATE COVERITY (and similar) SCANNING INTO BUILD WORKFLOW.  Roadmap Item #4
======================================================================================

DESCRIPTION:
------------
Integrating Coverity's static binary analysis into the build as a build option in order to discover source level defects in the code. Coverity can detect security issues as well as code quality.

ISSUES:
-------

EPIC - ADD UBUNTU/DEBIAN LINUX SUPPORT Roadmap Item #3
======================================================

DESCRIPTION:
------------
Add support for a non Red Hat Operating System so that Ubuntu operators can utilize OpenCPI with less difficulty. Also, consider package hierarchy and improve it with a top level installation package that has dependencies on other artifacts for organizational purposes, but we are not trying to solve artifact problems.

ISSUES:
-------

EPIC - N310 INTEGRATION Roadmap Item #2
=======================================

DESCRIPTION:
------------
This is initially a deep dive with Naim from APL to understand, document (can be in form of issues), and implement any additional changes that are required to integrate the N310 with the OpenCPI framework.

ISSUES:
-------
  
#170 osp: integrate ettus n310


EPIC - NEW CHEAPEST-HETEROGENEOUS STARTER PLATFORM (PlutoSDR) Roadmap Item # 1
==============================================================================

DESCRIPTION:
------------
Introduce a new SDR that is cheap, subsidized, and current; and that allows people to get started on the heterogeneous framework

ISSUES:
-------
  
#294 support zynq 7010 or smaller

  
#4 osp: add plutosdr to ci/cd pipeline

  
#3 osp: document plutosdr support project

  
#1 osp: create plutosdr support project


EPIC - INTEGRATE ZYNQ-ULTRASCALE SUPPORT (CURRENT 3RD PARTY CONTRIBUTION)
=========================================================================

DESCRIPTION:
------------
See issue for current scope

ISSUES:
-------
  
#88 Update Zynq FPGA loading to support linux kernels from 2013 to 2019, including non-Xilinx kernels

  
#69 INTEGRATE ZYNQ-ULTRASCALE SUPPORT (CURRENT 3RD PARTY CONTRIBUTION)


EPIC - ADD DOCKER TO THE OPENCPI PACKAGING SYSTEM
=================================================

DESCRIPTION:
------------
Some discussions have been had about either adding docker as an additional packaging option, or replacing RPMs with docker images.

ISSUES:
-------

EPIC - DEVELOP BEST-PRACTICE/OPEN CONTRIBUTION MODEL
====================================================

DESCRIPTION:
------------
See issue for current scope


ISSUES:
-------
  
#94 DEVELOP BEST-PRACTICE/OPEN CONTRIBUTION MODEL


EPIC - IMPLEMENT OSS PUBLIC BUG/ISSUE SYSTEM
============================================

DESCRIPTION:
------------
See issue for current scope

ISSUES:
-------
  
#95 IMPLEMENT OSS PUBLIC BUG/ISSUE SYSTEM


EPIC - IMPLEMENT AN OSS PUBLIC DEVELOPMENT MODEL
================================================

DESCRIPTION:
------------
See issue for current scope

ISSUES:
-------
  
#96 IMPLEMENT AN OSS PUBLIC DEVELOPMENT MODEL


EPIC - ORGANIZE DOCUMENTATION, REFERENCES FOR EASY AND CONSISTENT ACCESS
========================================================================

DESCRIPTION:
------------
See issue for current scope

ISSUES:
-------
  
#100 ORGANIZE DOCUMENTATION, REFERENCES FOR EASY AND CONSISTENT ACCESS


EPIC - REPLACE/UPDATE OVERVIEW DOCUMENT AND GLOSSARY
====================================================

DESCRIPTION:
------------
See issue for current scope

ISSUES:
-------
  
#101 REPLACE/UPDATE OVERVIEW DOCUMENT AND GLOSSARY


EPIC - OpenCPI 1.6
==================

DESCRIPTION:
------------
This Epic has no description

ISSUES:
-------

EPIC - Gpsd available as a prerequisite
=======================================

DESCRIPTION:
------------
OpenCPI uses the widely used OSS package called "gpsd" to interface to GPS devices to obtain a time-of-day value that is properly synchronized with a PPS hardware signal, when both are produced by a GPS reciever. The GPSD package supports a variety of GPS devices, and will generally support any GPS device that is avialable in a platform.

If the GPS device that a system contains is not supported by gpsd, then supporting that system will generally require creating a new GPS device driver within the gpsd package (or fixing/patching one that is there).  

If a system has no GPS device, then the sytem time-of-day will by used for this purpose. In any case, framework software will attempt to use gpsd to initialize the time service of each HDL platform with the appropriate time-of-day. 

Configuration of how OpenCPI uses gpsd will be controlled by via the system.xml configuration file.

ISSUES:
-------
  
#97 Centos6: scons too low version

  
#60 Gpsd available as a prerequisite


EPIC - Run through all existing training/tutorials
==================================================

DESCRIPTION:
------------
Verify training material and tutorials. Any issues encountered should be documented, in separate issue if necessary, so they can be addressed.

Make sure tutorials can be completed using GUI and CLI

[OpenCPI Training](https://gitlab.com/opencpi/training)   
[OpenCPI Guides](https://www.opencpi.org/documentation)   
[OpenCPI IO](http://opencpi.github.io/)

---

[Progress tracker](opencpi/transition%"OpenCPI Training Material")

ISSUES:
-------
  
#82 Lab 9

  
#81 Lab 8

  
#80 Lab 7

  
#79 Lab 6

  
#78 Lab 5

  
#77 Lab 4

  
#76 Lab 3

  
#75 Lab 2

  
#74 Lab 1

  
#73 Platform development feedback

  
#72 Device support development feedback

  
#71 Training course 14 feedback

  
#70 Training course 13 feedback

  
#69 Training course 12 feedback

  
#68 Training course 11 feedback

  
#67 Training course 10 feedback

  
#66 Training course 9 feedback

  
#65 Training course 8 feedback

  
#64 Training course 7 feedback

  
#63 Training course 6 feedback

  
#62 Training course 5 feedback

  
#61 Training course 4 feedback

  
#60 Training course 3 feedback

  
#59 Training course 2 feedback

  
#58 Training course 1 feedback

  
#57 Break feedback on training courses into separate pages


EPIC - SPLIT CLOCK SUPPORT
==========================

DESCRIPTION:
------------
Split clock tasks support using multiple clocks in the FPGA with the goal of making FPGA practitioners comfortable that they can use the clocks they want/need to, to get their job done.

This will allow for, or provide the following features:
- Worker `data` and `TOD` ports will be able to be in different clock domains than the control port
- Workers can define worker-level clocks that are not tied to a port
- Workers can specify the source of their input clock (control, external, another port, worker defined)
- Workers can specify that they will output a clock
- ADC workers can emit data with sample clock
- DAC workers can accept data with sample clock
- SDP (scalable/simulatable data plane) input/output in own clock domain

ISSUES:
-------

EPIC - Timestamping HDL worker
==============================

DESCRIPTION:
------------
The timestamping worker applies timestamps to data messages received at its input port. The time-of-day is supplied by a time interface to the time service. By adding/inserting timestamps into the data stream the amount of data output is more than the amount of data input, so the output data path and clock rate must support a higher data rate than the input data rate.

ISSUES:
-------
  
#75 Finalize interfaces for timestamping HDL worker

  
#70 Timestamping HDL worker


EPIC - Framework initialization of time service
===============================================

DESCRIPTION:
------------
The generic framework code already initializes the platform worker and time service worker for HDL platforms. The time service initialization must include setting the time-of-day either from `gpsd` if available or system time-of-day if not available.

ISSUES:
-------
  
#65 Framework initialization of time service


EPIC - TIMESTAMPING SUPPORT
===========================

DESCRIPTION:
------------
Timestamping (time tagging) support in OpenCPI requires capabilities that are:
- Configured for a given system type (e.g. radio), but supplied by the framework.
- Supplied by the platform or device developer (e.g. as part of a BSP)
- Implemented by generic framework modules/workers.

Each of these aspects is discussed in separate epics with the existing capabilities (release 1.5) described and the additional work required to achieve the goals of this effort.

ISSUES:
-------

EPIC - Post transition roadmap
==============================

DESCRIPTION:
------------
This Epic has no description

ISSUES:
-------
  
#21 Chip Process for CSP

  
#23 Group Events/Confrences

  
#37 GNU Radio Fork

  
#6 Add Angry Viper GUI to pre-built VM

  
#5 Pluto SDR

  
#31 CI Pipeline Dashboard

  
#46 A populated post 1.6 roadmap

  
#48 Identify 2.0 code changes


EPIC - Post 1.5 OpenCPI enhancements
====================================

DESCRIPTION:
------------
This Epic has no description

ISSUES:
-------
  
#18 Finish time tagging and split clocks


EPIC - Setup automated testing (CI/CD)
======================================

DESCRIPTION:
------------
Automated testing will leverage [GitLab Runners](https://docs.gitlab.com/runner/) and [GitLab CI](https://about.gitlab.com/product/continuous-integration/) to accomplish all automated tasks. GitLab Runner is used in conjunction with GitLab CI in order to run jobs and report results back to GitLab. 

The general hierarchy of a GitLab CI Pipeline is as follows:
1. A _pipeline_ is made up of _stages_
2. _Stages_ are made up of _jobs_
3. _Stages_ run sequentially
4. _Jobs_ within each stage are ran in parallel

GitLab runners can be assigned labels during and after their creation. After the runners are created and registered, the labels assigned to each runner can be changed using GitLab.

ISSUES:
-------
  
#112 Stand up opencpi.net

  
#106 License Server

  
#102 CentOS6: building ocpi framework libraries fails

  
#102 Install Xilinx tools on runner host

  
#92 CI: default cache key not working as intended

  
#72 Init .gitlab-ci.yml

  
#30 CI Joining Interface

  
#7 Lab Space Requirements

  
#9 Verify aquisition of RF Testing Tools

  
#12 Hardware requirements for test lab

  
#25 Define/Document User Access to Test Infrastructure

  
#26 CI Setup

  
#42 Build Artifacts

  
#51 Have minimal regression vs. previous devops


EPIC - Support separate DevOps instances
========================================

DESCRIPTION:
------------
This Epic has no description

ISSUES:
-------
  
#10 Stand up JWICS DevOps Instance

  
#11 Stand up SIPR DevOps Instance

  
#28 Gather requirements for Classified DevOps instance

  
#29 Gather requirements for private DevOps instance

  
#45 DevOps instance for controlled-access collaboration

  
#27 Well-defined movements between gitlab instances

  
#2 Support related/aligned/sync'd devops instances


EPIC - Present OpenCPI as typical, best practice OSS project
============================================================

DESCRIPTION:
------------
Issues that comprise this epic will deal with:
- Increasing OpenCPI's public presence and awareness
- Applying and following OSS best practices
- Facilitate contributions

Basically anything that needs to be done before the real work can begin.

One of the major goals for the transition effort is to reemphasize and get back to the roots of what it means to be _Open Source Software (OSS)_ and best software practices in general.


ISSUES:
-------
  
#50 Document continuity concerns/requirements

  
#20 Determine what it means to be OpenCPI Compliant for Systems/Radios

  
#22 Vendor Process for BSP

  
#24 User contributed OpenCPI Project

  
#38 Open CPI Contribution Guidelines

  
#15 GitLab Trial

  
#33 Get 30 day Gold Trial

  
#14 Create Issue Templates

  
#16 Setup Issue Board

  
#17 Define Workflow

  
#32 Apply for GitLab OSS

  
#35 Web Site

  
#36 Email discussion list

  
#39 BSP Project Organization

  
#43 Migrate from GitHub to GitLab

  
#44 Define DevOps instance

  
#1 Align with OSS best practices

