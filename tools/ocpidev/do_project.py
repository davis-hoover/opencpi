def do_project(*args):
    """Handle all aspects of project creation, registration, deregistration, etc."""
    input_arg = args[1]
    if verb == "register":
        try:
            register_project(input_arg)
            if verbose:
                print(f"Successfully registered project {input_arg} in project registry.")
                return
        except OSError:
            sys.exit(1)
    elif verb == "unregister":
        pj_title = str(input_arg)  # TODO: Seems like this and the following if statement could be combined
        if not input_arg:
            pj_title = current

        ask(f"unregister the {pj_title} project/package from its project registry")

        try:
            unregister_project(input_arg)
            if verbose:
                print(f"Successfully unregistered project '{input_arg}' in project registry.")
                return
        except OSError:
            sys.exit(1)
    elif verb == "delete":
        return delete_project(input_arg)  # Return the sys.exit code from delete_project()
    elif verb == "refresh":
        gpmd = cdk_dir / "scripts" / "genProjMetaData.py"
        try:
            if shutil.which(gpmd) is None: # Check if file exists and is executable
                raise OSError
            else:
                gpmd = Path.cwd()  # Set gpmd variable to current working directory
        except OSError:
            return
    elif verb == "build":
        if not buildRcc and not buildHdl and buildClean:
            clean_target = "clean"
        if buildRcc and buildClean:
            buildRcc = ""
            clean_target = " cleanrcc"
        if buildHdl and buildClean:
            buildHdl = ""
            clean_target = " cleanhdl"
        # TODO: Verify the functionality of these make calls; just a copy/paste for now
        subprocess.run(["make -C $subdir/$1 ${verbose:+AT=} imports"])
        subprocess.run(["make -C $subdir/$1 ${verbose:+AT=} ${cleanTarget:+$cleanTarget} ${buildRcc:+rcc}"
                        "${buildHdl:+hdl} ${buildNoAssemblies:+Assemblies=} ${assys:+Assemblies=\" ${assys[@]}\"} "
                        "${hdlplats:+HdlPlatforms=\" ${hdlplats[@]}\"} ${hdltargets:+HdlTargets=\" ${hdltargets[@]}\"} "
                        "${swplats:+RccPlatforms=\" ${swplats[@]}\"} ${hwswplats:+RccHdlPlatforms=\"${hwswplats[@]}\"}"
                        "$OCPI_MAKE_OPTS"])
        if buildClean and not hardClean:
            subprocess.run(["make -C $subdir/$1 ${verbose:+AT=} imports"])
            subprocess.run(["make -C $subdir/$1 ${verbose:+AT=} exports"])
        return
    if dirtype:
        bad(f"The directory '{directory}' where the project directory would be created is inside an OpenCPI project")
    if top or platform or prebuilt or library:
        bad(f"Illegal options present for creating project.")

    no_slash(input_arg)
    no_exist(input_arg)

    arg_dir = Path(input_arg)
    try:  # This is not part of the Bash script but isn't a bad idea
        arg_dir.mkdir()
        os.chdir(arg_dir)
    except FileExistsError:
        bad(f"Directory {arg_dir} already exists.")
    except FileNotFoundError:
        bad(f"Cannot change directories. Directory {arg_dir} does not exist")

    if not packagename:
        packagename = input_arg

    with open("Project.exports", "w") as exports_file:
        text = "# This file specifies aspects of this project that are made available to users,\n" \
               "# by adding or subtracting from what is automatically exported based on the\n" \
               "# documented rules.\n" \
               "# Lines starting with + add to the exports\n" \
               "# Lines starting with - subtract from the exports"
        exports_file.write(text)

    # TODO: Check whether the variables at the end need to be Pythonized or as-is
    with open("Project.mk", "w") as mk_file:
        text = f"# This Makefile fragment is for the '{input_arg} project\n\n" \
               f"# Package identifier is used in a hierarchical fashion from Project to Libraries....\n" \
               f"# The PackageName, PackagePrefix and Package variables can optionally be set here:\n" \
               f"# PackageName defaults to the name of the directory\n" \
               f"# PackagePrefix defaults to local\n" \
               f"# Package defaults to PackagePrefix.PackageName\n" \
               f"#\n" \
               f"# ***************** WARNING ********************\n" \
               f"# When changing the PackageName or PackagePrefix of an existing project the\n" \
               f"# project needs to be both unregistered and re-registered then cleaned and\n" \
               f"# rebuilt. This also includes cleaning and rebuilding any projects that\n" \
               f"# depend on this project.\n" \
               f"# ***************** WARNING ********************\n" \
               f"#\n" \
               f"${packagename:+PackageName=$packagename}\n" \
               f"${packageprefix:+PackagePrefix=$packageprefix}\n" \
               f"${package:+Package=$package}\n" \
               f"ProjectDependencies=${dependencies[@]}\n" \
               f"${liblibs:+Libraries=${liblibs[@]}}\n" \
               f"${includes:+IncludeDirs=${includes[@]}}\n" \
               f"${xmlincludes:+XmlIncludeDirs=${xmlincludes[@]}}\n" \
               f"${complibs:+ComponentLibraries=${complibs[@]}}"
        mk_file.write(text)

    with open("Makefile", "w") as Makefile:
        text = f"$CheckCDK\n" \
               f"# This is the Makefile for the '{input_arg} project.\n" \
               f"include \$(OCPI_CDK_DIR)/include/project.mk"

    package_id = ocpi_module.util.get_project_package()

    with open(".project", "w") as proj_file:
        text = "<?xml version="1.0" encoding="UTF-8"?>\n" \
                                                   "<projectDescription>\n" \
                                                   "<name>$package_id</name>\n" \
                                                   "<comment></comment>\n" \
                                                   "<projects></projects>\n" \
                                                   "<buildSpec></buildSpec>\n" \
                                                   "<natures></natures>\n" \
                                                   "</projectDescription>"
        proj_file.write(text)

    with open(".gitignore", "w") as gitignore:
        text = "# Lines starting with '#' are considered comments.\n" \
               "# Ignore (generated) html files,\n" \
               "#*.html\n" \
               "# except foo.html which is maintained by hand.\n" \
               "#!foo.html\n" \
               "# Ignore objects and archives.\n" \
               "*.rpm\n" \
               "*.obj\n" \
               "*.so\n" \
               "*~\n" \
               "*.o\n" \
               "target-*/\n" \
               "*.deps\n" \
               "gen/\n" \
               "*.old\n" \
               "*.hold\n" \
               "*.orig\n" \
               "*.log\n" \
               "lib/\n" \
               "#Texmaker artifacts\n" \
               "*.aux\n" \
               "*.synctex.gz\n" \
               "*.out\n" \
               "**/doc*/*.pdf\n" \
               "**/doc*/*.toc\n" \
               "**/doc*/*.lof\n" \
               "**/doc*/*.lot\n" \
               "run/\n" \
               "exports/\n" \
               "imports\n" \
               "*.pyc"
        gitignore.write(text)

    with open(".gitattributes", "w") as git_attribs:
        text = "*.ngc -diff\n" \
               "*.edf -diff\n" \
               "*.bit -diff"
        git_attribs.write(text)

    # Register project link in project registry
    if register_enable:
        try:
            register_project(input_arg)
            if keep:
                print(f"The project directory has been created, but not registered \(which may be fine\). If the "
                      f"project must be registered, resolve the conflict and run: ocpidev register project {input_arg}")
            else:
                print(f"Removing the project directory '{input_arg}' due to errors.")
                os.chdir("..")
                shutil.rmtree({input_arg})
        except OSError:
            sys.exit(1)

    subprocess.run(["make", f"{exports}"])
    subprocess.run(["make", f"{imports}"])

    if verbose:
        print(f"A new project named '{input_arg}' has been created in {Path.cwd()}")

