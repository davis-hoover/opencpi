Supported Versions
==================
The ocpidev2 script is generally meant to work for any OpenCPI project. Many
pre-2.0 OpenCPI mechanisms, nameonly GNU Make variables in makefiles across a
project, still exist in 2.0-and-after OpenCPI projects. The ocpidev2 script
makes it all "just work". Pre-OpenCPI-2.0 documentation can be seen
here: https://gitlab.com/opencpi/opencpi/-/blob/v1.7.0/doc/odt/OpenCPI_Component_Development_Guide.fodt

Architecture
============
OpenCPI concepts are typically created as small data structures correspond to
their documentation/XML definitions. Objects do not known about their
containing directories or what they represent. This helps keep each concept
class small and scoped similar to their corresponding Dev Guide documentation.
The Project and ProjectDatabase classes do a lot of the heavy lifting
for project traversion. Assets undergo build/clean/show/etc from the perspective
of a ProjectDatabase.

.. image:: ocpidev2_import_diagram.svg

Testing
=======
A unit tests is written in python. There
is also a tools/ocpidev2/test.sh which tests the CLI.

Attribute Handling
==================

XML tags are always defined in the python code in the same upper camel case as
the documentation, e.g., HdlAssembly is defined in a certain get_root_tags()
method. The attribute case variants, e.g., hdlassembly occuring in an XML file,
are handled within the XML parsing classes (AttributeBase) that compare the
lower case of everything.

Registry Behavior
=================

1. If a broken symlink exists in the registry, produce warning

Component Library Behavior
==========================

A directory is a Component Library
1)  if and only if it does not contain directories that are themselves component libraries
2)  if and only if it does not contain an XML file containing the root tag Libraries
3)  if and only if its path is within one of the following standard locations within an OpenCPI project
  * <project>/components/
  * <project>/components/<library>/
  * <project>/hdl/devices/
  * <project>/hdl/cards/
  * <project>/hdl/adapters/
  * <project>/hdl/platforms/<platform>/devices/

Furthermore, none of <project>/specs, <library>/specs, or <project>/hdl/platforms/<platform> are themselves a component library.

Asset objects
=============

        CLI   XML   makefiles
         |     |      |
         V     V      V
    asset object (inherits from AssetBase) self.attrs

Top-Level Attribute, Exposing to CLI
====================================

Note that 'git grep cli_dict' is helpful in tying the following description to the codebase.

1. Top-level attributes, e.g. SourceFiles, and all of their associated information are defined by the list returned in each asset class's get_attr_infos() method
2. Top-level attributes are typically exposed to the CLI, in a name that is similar to the attribute (sometimes not)

    args.include_dirs (matches attribute cli[1] defined in get_attr_infos())

      =DICT()=>

    mydict["include_dir"]

      =replaceunderscore=>

    mydict["includedir"]

      =lowercase=>

    cli_dict["includedir"]

      <=COMPARE=>

    "includedir"

      <== lower()

    "IncludeDir" (matches attribute name defined in get_attr_infos())

      <=

    self.attrs["IncludeDir"]

Troubleshooting
===============
It is VERY useful to run OCPI_LOG_LEVEL=10 ocpidev2 ...args.... 2> log, and then less -r log to peruse the colorized output
