#!/usr/bin/env python3
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

# TODO: integrate more inline with ocpirun -A to get information instead of metadata file

import pathlib
import os
import sys
from xml.etree import ElementTree as ET

sys.path.append(os.path.join(os.getenv("OCPI_CDK_DIR"),
                             os.getenv("OCPI_TOOL_PLATFORM"),
                             "lib"))

import _opencpi.util as ocpiutil


def addLibs(curRoot, componentsDirPath):
    libraryDirPaths = []
    for item in componentsDirPath.iterdir():
        if item.stem in ["lib", "gen", "doc"]:
            continue
        elif item.stem == "specs":
            break
        elif item.suffix in [".hdl", ".rcc", ".test", ".comp"]:
            break
        elif item.is_dir():
            libraryDirPaths.append(item)
    if len(libraryDirPaths) == 0:
        library = ET.SubElement(curRoot, "library", {"name": "components"})
        addWorkers(library, componentsDirPath)
    else:
        for libraryDirPath in libraryDirPaths:
            library = ET.SubElement(curRoot, "library", {"name": libraryDirPath.stem})
            addWorkers(library, libraryDirPath)


def addSpecs(curRoot, curDirPath):
    for child in curDirPath.iterdir():
        if child.is_dir() and child.stem == "specs":
            for specsChild in child.iterdir():
                if specsChild.stem == "package-id":
                    continue
                ET.SubElement(curRoot, "spec", {"name": specsChild.name})


def checkBuilt(dirPath):
    ret = []
    for child in dirPath.iterdir():
        if child.stem[:6] == "target":
            splitName = child.stem.split("-")
            if len(splitName) == 2:
                ret.append(splitName[1])
    return ret


def checkBuiltWorker(workerDirPath):
    ret = []  # list of tuples of targets and configs
    for child in workerDirPath.iterdir():
        if child.stem[:6] == "target":
            splitName = child.stem.split("-")
            if len(splitName) == 2:
                ret.append((splitName[1], "0"))
            elif len(splitName) == 3:
                ret.append((splitName[2], splitName[1]))
    return ret


def addWorkers(curRoot, hdlCardsDirPath):
    workersET = ET.SubElement(curRoot, "workers")
    testsET = ET.SubElement(curRoot, "tests")
    specsET = ET.SubElement(curRoot, "specs")
    addSpecs(specsET, hdlCardsDirPath)
    for workerDirPath in hdlCardsDirPath.iterdir():
        if workerDirPath.suffix in [".hdl", ".rcc"]:
            built = checkBuiltWorker(workerDirPath)
            worker = ET.SubElement(workersET, "worker", {"name": workerDirPath.name})
            for targetStr, configStr in built:
                ET.SubElement(worker, "built", {"target": targetStr, "configID": configStr})
        elif workerDirPath.suffix == ".test":
            ET.SubElement(testsET, "test", {"name": workerDirPath.name})


def addApplications(root, applicationsDirPath):
    for applicationDirPath in applicationsDirPath.iterdir():
        if applicationDirPath.is_dir():
            built = checkBuilt(applicationDirPath)
            app = ET.SubElement(root, "application", {"name": applicationDirPath.stem})
            for targetStr in built:
                ET.SubElement(app, "built", {"target": targetStr})
        else:
            if len(applicationDirPath.suffixes) != 0:
                if applicationDirPath.suffixes[-1] == ".xml":
                    ET.SubElement(root, "application", {"name": applicationDirPath.stem})


def addPlatforms(root, hdlPlatformsDirPath):
    for hdlPlatformDirPath in hdlPlatformsDirPath.iterdir():
        if not hdlPlatformDirPath.is_dir():
            continue
        if hdlPlatformDirPath.stem in ["lib"]:
            continue
        built = checkBuilt(hdlPlatformDirPath)
        plat = ET.SubElement(root, "platform", {"name": hdlPlatformDirPath.stem})
        for targetName in built:
            ET.SubElement(plat, "built", {"target": targetName})


def addAssemblies(root, assembliesDirPath):
    for assemblyDirPath in assembliesDirPath.iterdir():
        if not assemblyDirPath.is_dir():
            continue
        ET.SubElement(root, "assembly", {"name": assemblyDirPath.stem})


def addPrimitives(root, primitivesDirPath):
    for primitiveDirPath in primitivesDirPath.iterdir():
        if not primitiveDirPath.is_dir() or primitiveDirPath.stem == "lib":
            continue
        built = checkBuilt(primitiveDirPath)
        dirtype = ocpiutil.get_dirtype(str(primitiveDirPath))
        if dirtype:
            dirtype = dirtype.split("-")[1]
            prim = ET.SubElement(root, "primitive-{}".format(dirtype), {"name": primitiveDirPath.stem})
        for targetStr in built:
            ET.SubElement(prim, "built", {"target": targetStr})


def isStale(myDir, force):
    retVal = True
    # removed the functionality of this function to always return true because the find command
    # was taking longer to run then the regenerating of the metadata itself.  also the command
    # stopped returning a string into find_output.  this could likely be fixed and optimized to
    # fix these problems but not worth the time required right now
    '''find_output = ""
    if (force == False):
        if os.path.isfile(myDir + "/project-metadata.xml"):
            print("running find command: " + 'find ' + myDir + " -name" + " \"*.xml\"" +
                   ' -newer '+ myDir + "/project-metadata.xml")
            find_output = subprocess.Popen(['find', myDir, "-name", "\"*.xml\"",
                                           '-newer', myDir + "/project-metadata.xml"],
                                           stdout=subprocess.PIPE).communicate()[0]
            print(find_output)
            if find_output != b'':
                retVal = False
                print("is stale")
        else:
            print("metadata file does not exist yet")'''

    return retVal


def indent(elem, level=0):
    i = "\n" + level * "  "
    if len(elem):
        if not elem.text or not elem.text.strip():
            elem.text = i + "  "
        if not elem.tail or not elem.tail.strip():
            elem.tail = i
        for elem in elem:
            indent(elem, level + 1)
        if not elem.tail or not elem.tail.strip():
            elem.tail = i
    else:
        if level and (not elem.tail or not elem.tail.strip()):
            elem.tail = i


def main(project_dir=None):

    if project_dir is None and len(sys.argv) < 2:
        print("ERROR: need to specify the path to the project")
        sys.exit(1)

    if len(sys.argv) == 3 and sys.argv[2] == "force":
        force = True
    else:
        force = False

    mydir = project_dir if project_dir is not None else sys.argv[1]
    mydir = ocpiutil.get_path_to_project_top(mydir)
    if not mydir:
        return

    if not isStale(mydir, force):
        print("metadata is not stale, not regenerating")
        return

    # Get the project name, add it as an attribute in the project element.
    full_proj_name = ocpiutil.get_project_package(mydir)
    root = ET.Element("project", {"name": full_proj_name})

    rcc = ET.SubElement(root, "rcc")
    hdl = ET.SubElement(root, "hdl")
    assys = ET.SubElement(hdl, "assemblies")
    prims = ET.SubElement(hdl, "primitives")

    for item in pathlib.Path(mydir).iterdir():
        if item.stem == "applications":
            apps = ET.SubElement(root, "applications")
            addApplications(apps, item)
        elif item.stem == "components":
            comps = ET.SubElement(root, "components")
            addLibs(comps, item)
        elif item.stem == "specs":
            top_specs = ET.SubElement(root, "specs")
            addSpecs(top_specs, item.parent)
        elif item.stem == "hdl":
            for hdlChild in item.iterdir():
                if hdlChild.stem == "platforms":
                    platforms = ET.SubElement(hdl, "platforms")
                    addPlatforms(platforms, hdlChild)
                    for platformsChild in hdlChild.iterdir():
                        if platformsChild.is_dir():
                            for platformChild in platformsChild.iterdir():
                                if platformChild.stem == "devices":
                                    platformTag = "platform[@name='"+platformsChild.stem+"']"
                                    plat = platforms.findall(platformTag)
                                    devs = ET.SubElement(plat[0], "library", {"name": "devices"})
                                    addWorkers(devs, platformChild)
                elif hdlChild.stem == "cards":
                    hdlLibs = hdl.findall("libraries")
                    if len(hdlLibs) == 0:
                        hdlLibs = [ET.SubElement(hdl, "libraries")]
                    cards = ET.SubElement(hdlLibs[0], "library", {"name": "cards"})
                    addWorkers(cards, hdlChild)
                elif hdlChild.stem == "assemblies":
                    addAssemblies(assys, hdlChild)
                elif hdlChild.stem == "primitives":
                    addPrimitives(prims, hdlChild)
                elif hdlChild.stem == "devices":
                    hdlLibs = hdl.findall("libraries")
                    if len(hdlLibs) == 0:
                        hdlLibs = [ET.SubElement(hdl, "libraries")]
                    devs = ET.SubElement(hdlLibs[0], "library", {"name": "devices"})
                    addWorkers(devs, hdlChild)
        elif item.stem == "rcc":
            for rccChild in item.iterdir():
                if rccChild.stem == "platforms":
                    platforms = ET.SubElement(rcc, "platforms")
                    addPlatforms(platforms, rccChild)

    indent(root)
    tree = ET.ElementTree(root)
    tree.write(mydir + "/project-metadata.xml")


if __name__ == "__main__":
    main()
