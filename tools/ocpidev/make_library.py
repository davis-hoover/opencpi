import subprocess
from pathlib import Path

from tools.ocpidev.ocpidev_errors import bad


def make_library(*args):
    """Make a library with the name of args[1] in the directory of args[2]"""
    Path(args[2]).mkdir(parents=True, exist_ok=True)  # Equivalent to Bash mkdir -p
    with open(args[2]/"Makefile") as lib_mkfile:
        text = f"# This is the {args[1]} library\n\n" \
               f"# All workers created here in *.<model> will be built automatically\n" \
               f"# All tests created here in *.test directories will be built/run automatically\n" \
               f"# To limit the workers that actually get built, set the Workers= variable\n" \
               f"# To limit the tests that actually get built/run, set the Tests= variable\n\n" \
               f"# Any variable definitions that should apply for each individual worker/test\n" \
               f"# in this library belong in Library.mk\n\n" \
               f"include \$(OCPI_CDK_DIR)/include/library.mk"
        lib_mkfile.write(text)

    with open(args[2]/"library.mk") as lib_mk_file:
        text = f"# This is the {args[1]} library\n\n" \
               f"# This makefile contains variable definitions that will apply when building each\n" \
               f"# individual worker and test in the library\n\n" \
               f"# Package identifier is used in a hierarchical fashion from Project to Libraries....\n" \
               f"# The PackageName, PackagePrefix and Package variables can optionally be set here:\n" \
               f"# PackageName defaults to the name of the directory\n" \
               f"# PackagePrefix defaults to package of parent (project)\n" \
               f"# Package defaults to PackagePrefix.PackageName\n" \
               f"${packagename:+PackageName=$packagename}\n" \
               f"${packageprefix:+PackagePrefix=$packageprefix}\n" \
               f"${package:+Package=$package}\n" \
               f"${liblibs:+Libraries=${liblibs[@]}}\n" \
               f"${complibs:+ComponentLibraries=${complibs[@]}}\n" \
               f"${includes:+IncludeDirs=${includes[@]}}\n" \
               f"${xmlincludes:+XmlIncludeDirs=${xmlincludes[@]}}"
        lib_mk_file.write(text)
        try:
            subprocess.run(["make", "--no-print-directory", "-C", args[2]])
            if verbose:
                print(f"A new library named {args[1]} has been created in {args[2]}.")
        except OSError:
            bad(f"Library creation failed. You may want to do: 'ocpidev delete library {args[1]}'")