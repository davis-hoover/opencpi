# - OpenCPI concepts are typically created as small data structures correspond
#   to their documentation/XML definitions, and the each concept is
#   built from the perspective of the project it exists within. This helps
#   keep each concept class small, and aids in project traversion that is
#   intrinsic to the build process.
# - Unit tests are written with a test per class member variable
# - assets are always built from the perspective of a project, and projects
#   can search other projects in the registry
# - XML tags are always defined in the same upper camel case as the
#   documentation, e.g., HdlAssembly as defined in get_root_tags(), and then
#   case variants, e.g., hdlassembly occuring in an XML file, are handled
#   within the XML parsing classes (AttributeBase) that compare the lower case
#   of everything

OpenCPI-2.0-and-after documentation here: https://opencpi.gitlab.io/releases/v2.4.7/docs/OpenCPI_Component_Development_Guide.pdf

pre-OpenCPI-2.0 documentation here: https://gitlab.com/opencpi/opencpi/-/blob/v1.7.0/doc/odt/OpenCPI_Component_Development_Guide.fodt

OpenCPI v2.4.7 is here: https://gitlab.com/opencpi/opencpi/-/tree/v2.4.7/projects


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
