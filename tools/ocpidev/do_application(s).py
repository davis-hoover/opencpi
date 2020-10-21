import os
import shutil
import subprocess
from pathlib import Path

from tools.ocpidev.ask import ask
from tools.ocpidev.dirtypes import get_dirtype
from tools.ocpidev.ocpidev_errors import bad


def do_applications():
    """Call make to build multiple applications."""
    if dirtype == project:
        subdir = Path("applications")
    elif dirtype == applications:
        subdir = Path(".")
    else:
        bad(f"This command can only be issued in a project directory or an application directory.")

    if verb == build:
        subprocess.run(['make -C $subdir ${verbose:+AT=} ${buildClean:+clean} ${swplats:+RccPlatforms=" ${swplats[@]}"} '
                        '${hwswplats:+RccHdlPlatforms=" ${hwswplats[@]}"} $OCPI_MAKE_OPTS'])
        return


def do_application(*args):
    """Create an application.

    An application in a project might have:
    An xml file
    A c++ main program
    Its own private components (and thus act like a library)
    Its own private HDL assemblies
    Some data files
    """
    input_arg = args[1]
    subdir = Path(".")
    if not standalone:
        if dirtype == "project":
            subdir = Path("applications")
        elif dirtype == "applications":
            subdir = Path(".")
        else:
            bad(f"This command can only be issued in a project directory or an applications directory.")

    a_dir = subdir / input_arg  # Make path to subdir + input argument

    if verb == "build":
        subprocess.run(['make -C $subdir$1 ${verbose:+AT=} ${buildClean:+clean} ${swplats:+RccPlatforms=" '
                        '${swplats[@]}"} ${hwswplats:+RccHdlPlatforms=" ${hwswplats[@]}"} $OCPI_MAKE_OPTS'])
        return
    elif verb == "delete":
        if xmlapp:
            if a_dir.joinpath(".xml").is_file():  # Check if a_dir.xml is a regular file
                ask(f"delete the application xml file {a_dir.joinpath('.xml')}")
                shutil.rmtree(a_dir.joinpath('.xml'))
            else:
                bad(f"The application at '{a_dir.joinpath('.xml')}' doesn't exist")
            return
        if not a_dir:
            bad(f"The application at '{a_dir}' does not exist.")
        a_dir_type = get_dirtype(a_dir)
        if dirtype != "application":
            bad(f"The directory at '{a_dir}' doesn't appear to be an application.")
        ask(f"delete the application project in the '{a_dir}' directory")
        shutil.rmtree(a_dir)
        if verbose:
            print(f"The application '{input_arg}' in the directory '{a_dir}' has been deleted.")
        return

    if str(input_arg).endswith(".xml"):
        app = str(input_arg).rstrip(".xml")
    else:
        app = str(input_arg)
    app_subdir = Path(subdir / app / ".xml")
    subdir_args = Path(subdir / input_arg)
    if xmlapp:
        if app_subdir.is_file():
            bad(f"The application {app} already exists in {topdir / subdir / app / '.xml'}.")  # TODO: Verify dir path
    elif subdir_args.is_dir():
        bad(f"The application {app} already exists in {topdir / subdir / input_arg}.")

    if dirtype == "project" and not applications:
        Path("applications").mkdir()
        try:
            os.chdir("applications")
        except OSError:
            bad(f"Unable to change to 'applications' directory.")
        with open("Makefile", "w") as app_mkfile:
            text = f"$CheckCDK\n" \
                   f"# To restrict the applications that are built or run, you can set the Applications\n" \
                   f"# variable to the specific list of which ones you want to build and run, e.g.:\n" \
                   f"# Applications=app1 app3\n" \
                   f"# Otherwise all applications will be built and run\n" \
                   f"include \$(OCPI_CDK_DIR)/include/applications.mk"
            app_mkfile.write(text)
        if verbose:
            print(f"This is the first application in this project. The '{applications}' directory has been created.")

    app_dir = ""
    if not xmlapp:
        app_dir = input_arg
        subdir_args.mkdir()
        try:
            os.chdir(subdir_args)
        except OSError:
            bad(f"Unable to change to {subdir_args} directory")
        with open("Makefile", "w") as subdir_mkfile:
            text = f"# This is the application Makefile for the '{input_arg}' application\n" \
                   f"# If there is a {input_arg}.cc (or {input_arg}.cxx) file, it will be assumed to be a C++ main " \
                   f"program to build and run\n" \
                   f"# If there is a {input_arg}.xml file, it will be assumed to be an XML app that can be run with " \
                   f"ocpirun.\n" \
                   f"# The RunArgs variable can be set to a standard set of arguments to use when executing either.\n" \
                   f"include \$(OCPI_CDK_DIR)/include/application.mk"
            subdir_mkfile.write(text)
        if verbose:
            print(f"Application '{input_arg}' created in directory '{topdir / subdir / input_arg}")
            print(f"You must create either a {input_arg}.xml or {input_arg}.cc file in the "
                  f"{topdir / subdir / input_arg} directory.")

    try:
        os.chdir(subdir / app_dir)
    except OSError:
        bad(f"Unable to change to {subdir / app_dir} directory")
    with open(f"{app + '.xml'}", "w") as xml_file:
        text = f"<!-- The $1 application xml file -->\n" \
               f"<Application>\n" \
               f"   <Instance Component='ocpi.core.nothing' Name='nothing'/>\n" \
               f"</Application>"
        xml_file.write(text)

    try:
        os.chdir(subdir / app_dir)
    except OSError:
        bad(f"Unable to change to {subdir / app_dir} directory")
    if not xmlapp and not xmldirapp:
        with open(f"{app}.cc", "w") as cc_app:
            text = "#include <iostream>\n" \
                   "#include <unistd.h>\n" \
                   "#include <cstdio>\n" \
                   "#include <cassert>\n" \
                   "#include <string>\n" \
                   "#include 'OcpiApi.hh'\n\n" \
                   "namespace OA = OCPI::API;\n\n" \
                   "int main(/*int argc, char **argv*/) {\n" \
                   "    // For an explanation of the ACI, see:\n" \
                   "    // https://opencpi.gitlab.io/releases/develop/docs/OpenCPI_Application_Development_Guide.pdf\n\n" \
                   "try {\n\n" \
                   "    OA::Application app('$app.xml');\n" \
                   "    app.initialize(); // all resources have been allocated\n" \
                   "    app.start();      // execution is started\n\n" \
                   "    // Do work here.\n\n" \
                   "    // Must use either wait()/finish() or stop(). The finish() method must\n" \
                   "    // always be called after wait(). The start() method can be called\n" \
                   "    // again after stop().\n" \
                   "    app.wait();       // wait until app is 'done'\n" \
                   "    app.finish();     // do end-of-run processing like dump properties\n" \
                   "    // app.stop();\n\n" \
                   "} catch (std::string &e) {\n" \
                   "    std::cerr << 'app failed: ' << e << std::endl;\n" \
                   "    return 1;\n" \
                   "}\n" \
                   "return 0;\n" \
                   "}"
            cc_app.write(text)
        if verbose:
            print(f"The XML application '{app}' has been created in {topdir / subdir / app_dir / app / '.xml'}.")