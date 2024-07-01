1. OpenCPI concepts are typically created as small data structures correspond to their documentation/XML definitions, and the each concept is built from the perspective of the project it exists within. This helps keep each concept class small, and aids in project traversion that is intrinsic to the build process.
2. Unit tests are written with a test per class member variable
3. assets are always built from the perspective of a project, and projects can search other projects in the registry
4. XML tags are always defined in the same upper camel case as the documentation, e.g., HdlAssembly as defined in get_root_tags(), and then case variants, e.g., hdlassembly occuring in an XML file, are handled within the XML parsing classes (AttributeBase) that compare the lower case of everything

OpenCPI-2.0-and-after documentation here: https://opencpi.gitlab.io/releases/v2.4.7/docs/OpenCPI_Component_Development_Guide.pdf

pre-OpenCPI-2.0 documentation here: https://gitlab.com/opencpi/opencpi/-/blob/v1.7.0/doc/odt/OpenCPI_Component_Development_Guide.fodt

OpenCPI v2.4.7 is here: https://gitlab.com/opencpi/opencpi/-/tree/v2.4.7/projects

# Registry Behavior

1. If a broken symlink exists in the registry, produce warning

# Component Library Behavior


| `<library-name>`.xml exists | Library.mk exists | Makefile exists | Behavior | Known Examples |
| ------ | ------ | ------ | ------ | ------ |
|   N     |    N    |    N   |   Because the Component Development Guide lists `<lib>.xml` as optional in Figure 1, this is an expected and supported scenario. All directories (in the standard locations, within a project, as per Component Dev Guide 14.2.3") whose paths DO NOT end with .hdl or .rcc or .ocl are considered component libraries. This also means that, for the nested directory components/<library>/ scenario, both components and components.<library> are considered component libraries. |   OpenCPI core/components. There are probably other examples.   |
|   N     |    N    |    Y   |   Documented, pre-OpenCPI-2.0 scenario. Library is discovered if and only if library.mk is included in the Makefile. |   OpenCPI assets/components/base_comps    |
|   N     |    Y    |    N   |   Undocumented pre-OpenCPI-2.0 scenario which is invalid. Library is not discovered. |       |
|   N     |    Y    |    Y   |   Documented, pre-OpenCPI-2.0 scenario. Library is discovered if and only if library.mk is included in the Makefile. Both files are parsed.  |   OpenCPI assets/components/dsp_comps    |
|   Y     |    N    |    N   |   Documented OpenCPI-2.0-and-after scenario which is current best practice. Library is discovered if and only if the case-insensitive `library` XML root tag exists.       |   OpenCPI platform/components    |
|   Y     |    N    |    Y   |    Wild scenario. The XML file is the only one parsed. Library is discovered if and only if the case-insensitive `library` XML root tag exists.   |       |
|   Y     |    Y    |    N   |    Wild scenario. The XML file is the only one parsed. Library is discovered if and only if the case-insensitive `library` XML root tag exists.    |       |
|   Y     |    Y    |    Y   |    Wild scenario. The XML file is the only one parsed. Library is discovered if and only if the case-insensitive `library` XML root tag exists.  |       |

# Asset objects

        CLI   XML   makefiles
         |     |      |
         V     V      V
    asset object (inherits from AssetBase)
         |     |      |
         V     V      V
       clean  build  create  

# Top-Level Attribute, Exposing to CLI

1. Top-level attributes are defined in the list returned be each asset class's get_attr_infos() method
2. Top-level attributes are typically exposed to the CLI, in a name that is similar to the attribute (sometimes not)
3. Typical CLI-to-XML flow during 'ocpidev2 create' is, e.g.,

    args.include_dirs

      =DICT()=>

    mydict["include_dir"]

      =replaceunderscore=>

    mydict["includedir"]

      =>

    "includedir"

      <=COMPARE=>

    "includedir"

      <== lower()

    "IncludeDir" (matches attribute name defined in get_attr_infos()

      <=

    self.attrs["IncludeDir"]

# Troubleshooting
It is VERY useful to run OCPI_LOG_LEVEL=10 ocpidev2 ...args.... 2> log, and then less -r log to peruse the colorized output
