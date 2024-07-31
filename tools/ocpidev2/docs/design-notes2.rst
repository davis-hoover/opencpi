Authors
=======
Davis Hoover (git@davishoover.com)
Joel Palmer (jpalmer@geontech.com)

Supported Versions
==================
The ocpidev2 script is generally meant to work across OpenCPI projects, according
to the various Development Guides (Component Dev Guide, HDL Dev Guide, RCC Dev
Guide, Platform Dev Guide, etc). Many
pre-2.0 OpenCPI mechanisms, namely GNU Make variables in makefiles across a
project, still exist in 2.0-and-after OpenCPI projects. The ocpidev2 script
is written to generally make projects out in the wild "just work", in that
build/show finds them and can build them. Pre-OpenCPI-2.0 documentation can be seen
here, for example: https://gitlab.com/opencpi/opencpi/-/blob/v1.7.0/doc/odt/OpenCPI_Component_Development_Guide.fodt

Coding Style
============
PEP-8 was used during development. The python pycodestyle command was used to
confirm compliance.
XML tags and attributes are always defined in the python code in the same upper camel case as
the documentation (Dev Guides), e.g., HdlAssembly is defined in a certain
get_root_tags()
method. Created assets use the same upper camel case for their XML files.

Comparison with ocpidev
=======================
The ocpidev script supports the verbs
build/clean/create/delete/register/run/set/show/unregister/unset.
The ocpidev2 script supports the verbs
build/clean/create/delete/register/show/unregister but not set/unset/delete.
The set/unset operations are not recommended with ocpidev2 (use OCPI_PROJECT_REGISTRY_DIR instead).
The delete/run are not implemented but it is recommended to implement these in
ocpidev2 in the future and delete ocpidev entirely. At the time of this writing,
ocpidev2 is about 5500 lines whereas ocpidev is about 7000 lines.
The separation of files in tools/ocpidev2 is similar to tools/ocpidev
The ocpidev2 script does not depend in ocpidev code.

Architecture
============
OpenCPI concepts are typically created as small data structures correspond to
their documentation/XML definitions. Objects do not known about their
containing directories or what they represent (this is an important key
concept - eventually portions of ocpidev2 could be ported to C++ and merged
with the respective asset classes to reduce software entropy). This helps keep
each concept
class small and scoped similar to their corresponding Dev Guide documentation.
The Project and ProjectDatabase classes do a lot of the heavy lifting
for project traversion. Assets undergo build/clean/show/etc from the perspective
of a ProjectDatabase.

.. image:: ocpidev2_import_diagram.svg
   :scale: 20%

The AttributeBase class normalizes parsing across XML and makefiles and
for all asset type. The AssetBase class inherits from AttributeBase and is
common to all asset classes. Asset classes exist per OpenCPI concept
(Component/Worker/etc) and are generally named according to their XML root
tags.

Discovery
=========
Existing assets are performed autonomously by a discovery mechanism. All
asset classes have a discover() method which creates a database
in internal program memory which represents the discoverable assets
on the filesystem. This database exists as the ProjectDatabase
class's self.projects list of projects.
Assets are discovered 1) from the local project
and 2) from the project registry. Refer to the Component Dev Guide
for more info. Discovery is a core mechanism for 'show' and 'build',
and is used for other verbs, e.g. 'create', as needed.

Attribute Handling
==================
All of an asset's attributes (or at least the top-level ones)
exist in the asset class's self.attrs dictionary.
Discovery performs parsing of XML and makefiles and populates self.attrs.
When performing asset creation, self.attrs is populated from the Command Line
Interface (CLI).
ALl asset classes have a parse() method. All parsed attributes
(at least the top-level ones) are logged at log level 10, regardless of
what file or file type they come from. The AttributeBase
class normalizes this behavior across XML and makefile alike.
The attribute case variants, e.g., hdlassembly vs HdlAssembly
occuring in an XML file,
are handled within the XML parsing classes (AttributeBase) that compare the
lower case of everything.

Building
========
The ocpidev2 script has a much more sophisticated build engine than ocpidev.
The HDL build dependency hierarchy is determined during discovery,
then a GNUMakefile class object is constructed for which represents
a makefile with recipes that have their dependencies properly defined.
The recipes are generated via a recursive call to the ProjectDatabase
class's append_asset_rules_to_makefile_variable() method.
The LegacyBuildTool class provides an API for defining the recipe for
each build artifact's GNU Make rule, and is currently
implemented in a way that simply
interfaces with the Tool Layer(s)
corresponding to worker.mk, hdl-assembly.mk, etc. It is
intended for this class to eventually become user-extensible
to more easily support new vendor tools.
The GNUMakefile object, after appending all rules,
is emitted (saved to the filesystem) in a temporary
temporary makefile containing a recipe for each artifact, 
and a system call to 'make -j <jobs> <makefilepath>' is made
to perform the build in a optimal, fast, well-defined fashion.
It is recommended to read up on GNU Make rules, recipes,
and targets: 
https://www.gnu.org/software/make/manual/html_node/Rules.html

Note that RCC builds are also supported, but any
implied application dependency on a hdl assembly
is not automatically determined and therefore not built.
This relationship (deployment) is one of the most complicated
mechanisms in OpenCPI.

Testing
=======
A unit tests is written in python. Coverage at the time if this writing
is somewhere around 50% by lines of code. There
is also a tools/ocpidev2/test.sh which performs all existing ocpidev2 tests.
This includes the python unit tests and various CLI commands.

Component Library Behavior
==========================
The following expands on the Dev Guides by clarifying what is considered a
component library. The 'ocpidev2 show libraries' command shows components
libraries.

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

Command Line Interface (CLI)
============================

The command line interface is exposed to the ProjectDatabase
as a variable cli_dict which is a dictionary of noun, verb, name, and other
options. The man pages, e.g. 'man ocpidev2' and 'man ocpidev2-build'
define the supported CLI. The cli_dict is associated with
the asset top-level attributes (contained in each asset class's self.attrs)
via the dictionairy returned by
each asset class's get_attr_infos() method.
Note that 'git grep cli_dict' is helpful in tying the following description to the codebase.

1. Top-level attributes, e.g. SourceFiles, and all of their associated information are defined by the list returned in each asset class's get_attr_infos() method
2. Top-level attributes are typically exposed to the CLI, in a name that is similar to the attribute (sometimes not).

    args.include_dirs (matches attribute cli[1] defined in get_attr_infos())

      =DICT()=>

    mydict["include_dir"]

      =replaceunderscore=>

    mydict["includedir"]

      =lowercase=>

    cli_dict["includedir"]

      =>

    "includedir"

      <=COMPARE=>

    "includedir"

      <== lower()

    "IncludeDir" (matches attribute name defined in get_attr_infos())

      <=

    self.attrs["IncludeDir"]

Troubleshooting
===============
It is VERY useful to run OCPI_LOG_LEVEL=10 ocpidev2 ...args.... 2> log, and then less -r log to peruse the colorized output
