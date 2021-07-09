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

from xml.etree import ElementTree as ET
import os
import sys
import subprocess
sys.path.append(os.getenv('OCPI_CDK_DIR') + '/' + os.getenv('OCPI_TOOL_PLATFORM') + '/lib/')
import _opencpi.util as ocpiutil

def addLibs(curRoot, libs):
    allWorkersLocal = False
    libraryDirectories = []
    for a in libs:
        if a in ["lib","gen","doc"]:
            continue
        if a == "specs":
            allWorkersLocal = True
            continue

        if a.endswith(".hdl") or a.endswith(".rcc") or a.endswith(".test"):
            allWorkersLocal = True
        else:
            libraryDirectories.append(a)

    # Opencpi Rules - either the components directory is
    # the library directory or if has library sub directories.
    if allWorkersLocal:
        ET.SubElement(curRoot, "library", {"name" : "components"})
    else:
        for libDir in libraryDirectories:
            ET.SubElement(curRoot, "library", {"name" : libDir})

def addSpecs(curRoot, curDir):
    for dirName in os.listdir(curDir):
        if (dirName == "specs"):
            for a in os.listdir(curDir + "/" + dirName):
                if a == "package-id":
                    continue
                comp = ET.SubElement(curRoot, "spec")
                comp.set('name', a)

def getWorkerPlatforms(dirName, name):
    buildFile = dirName + "/" + name.split('.', 1)[0] + "-build.xml"

def checkBuiltApp (appName, appDir):
    fileList = os.listdir(appDir)
    targets = []
    appList = set([appName + ".cxx", appName + ".cpp", appName + ".cc"])
    if (1 == len(appList.intersection(fileList))):
        for fileName in fileList:
            if fileName.startswith("target"):
                fileName = fileName.split('-')
                if len(fileName) == 5 :
                    targets.append(fileName[3])
                elif len(fileName) == 2 :
                    targets.append(fileName[1])
                elif len(fileName) == 3 :
                    targets.append(fileName[2])
                else:
                    targets.append(fileName[2])
        retVal = targets
    else:
        retVal = ["N/A"]
    return retVal

def checkBuilt (primDir):
    fileList = os.listdir(primDir)
    targets = []
    for fileName in fileList:
        if fileName.startswith("target"):
            fileName = fileName.split('-')
            if len(fileName) == 2 :
                targets.append(fileName[1])
    retVal = targets
    return retVal

def checkBuiltWorker (workerDir):
    fileList = os.listdir(workerDir)
    targets = []
    configs = []
    for fileName in fileList:
        if fileName.startswith("target"):
            fileName = fileName.split('-')
            if len(fileName) == 5 :
                targets.append(fileName[3])
                configs.append(fileName[1])
            elif len(fileName) == 2 :
                targets.append(fileName[1])
                configs.append("0")
            elif len(fileName) == 3 :
                targets.append(fileName[2])
                configs.append(fileName[1])
            else:
                targets.append(fileName[2])
                configs.append("0")
    retVal = list(zip(targets, configs))
    return retVal

def addWorkers(curRoot, workers, dirName):
    workersET = ET.SubElement(curRoot, "workers")
    testsET = ET.SubElement(curRoot, "tests")
    specsET = ET.SubElement(curRoot, "specs")
    addSpecs(specsET, dirName)
    for a in workers:
        if(not a.endswith(".test") and (a not in ["lib","specs","gen","doc","include"])):
            built = checkBuiltWorker(dirName + '/' + a)
            worker = ET.SubElement(workersET, "worker")
            worker.set('name', a)
            for targetStr, configStr in built:
                target = ET.SubElement(worker, "built")
                target.set('target', targetStr)
                target.set('configID', configStr)
        # plat = getWorkerPlatforms(dirName + "/" + a, a)
        elif(a.endswith(".test") and (a not in ["lib","specs","gen","doc","include"])):
            test = ET.SubElement(testsET, "test")
            test.set('name', a)

def dirIsLib(dirName, comps):
    if comps:
        for name in comps.findall("library"):
            if (dirName.endswith(name.get("name"))):
                return (True, name)
    return (False, [])

def addApplications (root, apps, dirName):
    for a in apps:
        built = checkBuiltApp(a, dirName + '/' + a)
        app = ET.SubElement(root, "application")
        app.set('name', a)
        for targetStr in built:
                target = ET.SubElement(app, "built")
                target.set('target', targetStr)

def addPlatforms (root, plats, dirName):
    for a in plats:
        if(a not in ["lib"]):
            built = checkBuilt(dirName + '/' + a)
            plat = ET.SubElement(root, "platform")
            plat.set('name', a)
            for targetStr in built:
                target = ET.SubElement(plat, "built")
                target.set('target', targetStr)

def addAssemblies (root, assys, dirName):
    for a in assys:
        app = ET.SubElement(root, "assembly")
        app.set('name', a)

def addPrimitives (root, primitives, dirName):
    for a in primitives:
        if a == "lib":
            continue
        built = checkBuilt(dirName + '/' + a)
        prim = ET.SubElement(root, "primitive")
        prim.set('name', a)
        for targetStr in built:
                target = ET.SubElement(prim, "built")
                target.set('target', targetStr)

def isStale (myDir, force):
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
    i = "\n" + level*"  "
    if len(elem):
        if not elem.text or not elem.text.strip():
            elem.text = i + "  "
        if not elem.tail or not elem.tail.strip():
            elem.tail = i
        for elem in elem:
            indent(elem, level+1)
        if not elem.tail or not elem.tail.strip():
            elem.tail = i
    else:
        if level and (not elem.tail or not elem.tail.strip()):
            elem.tail = i

def main(project_dir=None):
    
    if not project_dir and len(sys.argv) < 2 :
        print("ERROR: need to specify the path to the project")
        sys.exit(1)

    if ((len(sys.argv) == 3) and (sys.argv[2] == "force")):
        force = True
    else:
        force = False

    mydir = project_dir if project_dir else sys.argv[1]
    mydir = ocpiutil.get_path_to_project_top(mydir)

    if (isStale(mydir, force)):
        # Get the project name, add it as an attribute in the project element.
        strings = mydir.split("/")
        splitLen = strings.__len__()
        if splitLen == 1:
            projectName = strings[0]
        else:
            projectName = strings[splitLen -1]

        full_proj_name = ocpiutil.get_project_package(mydir)
        root = ET.Element("project", {"name" : full_proj_name})

        hdl = ET.SubElement(root, "hdl")
        rcc = ET.SubElement(root, "rcc")
        assys = ET.SubElement(hdl, "assemblies")
        prims = ET.SubElement(hdl, "primitives")

        if os.path.isdir(mydir + "/specs"):
            top_specs = ET.SubElement(root, "specs")
            addSpecs(top_specs, mydir)
        comps = None
        if os.path.isdir(mydir + "/components"):
            comps = ET.SubElement(root, "components")

        if os.path.isdir(mydir + "/applications"):
            apps = ET.SubElement(root, "applications")
            sub_dirs = onlyfiles = [dir for dir in os.listdir(mydir + "/applications")
                                    if not os.path.isfile(os.path.join(mydir + "/applications", dir))]
            addApplications(apps, sub_dirs, mydir + "/applications")

        for dirName, subdirList, fileList in os.walk(mydir):
            if "exports" in dirName or "imports" in dirName:
                continue
            elif dirName == mydir + "/components":
                if ocpiutil.get_dirtype(dirName) == "library":
                    addLibs(comps, ["components"])
                else:
                    addLibs(comps, subdirList)
            elif dirName.endswith("/hdl/platforms"):
                platforms = ET.SubElement(hdl, "platforms")
                addPlatforms(platforms, subdirList, dirName)
            elif dirName.endswith("/rcc/platforms"):
                platforms = ET.SubElement(rcc, "platforms")
                addPlatforms(platforms, subdirList, dirName)

            elif dirName.endswith("/cards"):
                hdlLibs = hdl.findall("libraries")
                if hdlLibs.__len__() == 0:
                    hdlLibs = [ET.SubElement(hdl, "libraries")]
                cards = ET.SubElement(hdlLibs[0], "library")
                cards.set('name', "cards")
                addWorkers(cards, subdirList, dirName)

            elif dirName.endswith("/devices"):
                if "/platforms/" not in dirName:
                    # This is the hdl/devices directory
                    hdlLibs = hdl.findall("libraries")
                    if hdlLibs.__len__() == 0:
                        hdlLibs = [ET.SubElement(hdl, "libraries")]
                    devs = ET.SubElement(hdlLibs[0], "library")
                    devs.set('name', "devices")
                    addWorkers(devs, subdirList, dirName)
                else:
                    # this is a devices directory under a platform
                    dirSplit = dirName.split('/')
                    platName = [];
                    index = list(range(0, len(dirSplit)-1))
                    for i, sub in zip(index, dirSplit):
                        if (sub == "platforms"):
                            platName = dirSplit[i+1]
                    platformsEl =   hdl.findall("platforms")
                    if  platformsEl.__len__() >0:
                        plats = platformsEl[0]
                        platformTag = "platform[@name='"+platName+"']"
                        plat = plats.findall(platformTag)
                        if plat.__len__() > 0:
                            devs = ET.SubElement(plat[0], "library")
                            devs.set('name',"devices")
                            addWorkers(devs, subdirList, dirName)

            elif dirName.endswith("hdl/assemblies"):
                addAssemblies(assys ,subdirList, dirName)
            elif dirName.endswith("hdl/primitives"):
                addPrimitives(prims, subdirList, dirName)

            retVal = dirIsLib(dirName, comps)
            if (retVal[0]):
                addWorkers(retVal[1], subdirList, dirName)

        # This message talks about something that is meaningless and undocumented to users
        #print("Updating project metadata...")
        indent(root)
        tree = ET.ElementTree(root)
        tree.write(mydir+"/project-metadata.xml")
    else:
        print("metadata is not stale, not regenerating")

if __name__ == '__main__':
    main()
