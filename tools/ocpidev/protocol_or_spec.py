from pathlib import Path

from tools.ocpidev.ocpidev_errors import bad


def do_protocol_or_spec(*args):
    """Create a specific file type with particular protocol or specification"""
    input_arg = str(args[1])
    sub_dir = Path(subdir / "specs")
    if project:
        sub_dir = "specs"

    # TODO: This whole code block needs to be rewritten once the errored variables are determined
    if not file:
        if input_arg.endswith(".xml"):
            file = input_arg
        elif input_arg.endswith("_prot") or input_arg.endswith("_protocol"):
            if noun == "protocol":
                bad(f"You cannot make a {noun} file with a protocol suffix")
            file = input_arg + ".xml"
        elif input_arg.endswith("_spec"):
            if noun == "spec":
                bad(f"It is a bad idea to make a {noun} file with a spec suffix.")
            file = input_arg + ".xml"
        elif input_arg.endswith("_props") or input_arg.endswith("_properties"):
            if noun == "properties":
                bad(f"It is a bad idea to make a {noun} file with a properties suffix")
            file = input_arg + ".xml"
        elif input_arg.endswith("_sigs") or input_arg.endswith("_signals"):
            if noun == "signals":
                bad(f"You cannot make a {noun} file with a signals suffix")
        else:
            if noun == "spec":
                file = input_arg + "-spec.xml"
            elif noun == "protocol":
                file = input_arg + "-prot.xml"
            elif noun == "properties":
                file = input_arg + "-props.xml"
            elif noun == "signals":
                file = input_arg + "-signals.xml"
            elif noun == "card" or noun == "slot":
                file = input_arg + ".xml"

        return file

    if verb == "delete":
        if not sub_dir / file.exists():
            bad(f"The file '{subdir / file}' does not exist")
        else:
            ask(f"delete the file '{sub_dir / file}")
            shutil.rmtree(sub_dir / file)
            if verbose:
                print(f"The {args[2]} '{input_arg}' in file {subdir / file} has been deleted.")

    if sub_dir / file.exists():
        bad(f"The file '{sub_dir / file}'already exists")

    if not sub_dir.is_dir() and verbose:
        if sub_dir == "specs":
            print(f"The 'specs' directory does not exist and will be created.")
        else:
            print(f"The 'specs' directory '{sub_dir}' does not exist and will be created.")

    Path(sub_dir).mkdir(parents=True, exist_ok=True)  # Equivalent to Bash mkdir -p

    if sub_dir == "specs" and not specs/package-id.exists():    # Record package prefix in the specs directory
        sub_dir.run(["make specs/package-id"])

    if noun == "protocol":
        with open(subdir/file, "w") as prot_spec_file:
            text = f"<!-- This is the protocol spec file (OPS) for protocol: {input_arg}\n" \
                   f"   Add <operation> elements for message types.\n" \
                   f"   Add protocol summary attributes if necessary to override attributes\n" \
                   f"   inferred from operations/messages -->\n" \
                   f"<Protocol> <!-- add protocol summary attributes here if necessary -->\n" \
                   f"   <!-- Add operation elements here -->\n" \
                   f"</Protocol>"
            prot_spec_file.write(text)
    elif noun == "spec":
        if nocontrol:
            nocontrolstr = " NoControl='true' "
            with open(sub_dir/file, "w") as spec_file:
                text = f"<!-- This is the spec file (OCS) for: {input_arg}\n" \
                       f"   Add component spec attributes, like 'protocol'.\n" \
                       f"   Add property elements for spec properties.\n" \
                       f"   Add port elements for i/o ports -->\n" \
                       f"<ComponentSpec$nocontrolstr>\n" \
                       f"   <!-- Add property and port elements here -->\n" \
                       f"</ComponentSpec>"
                spec_file.write(text)
    elif noun == "properties":
        with open(sub_dir/file, "w") as prop_file:
            text = f"<!-- This is the properties file (OPS) initially named: {input_arg}\n" \
                   f"   Add <property> elements for each property in this set -->\n" \
                   f"<Properties>\n" \
                   f"   <!-- Add property elements here -->\n" \
                   f"</Properties>"
            prop_file.write(text)
    elif noun == "signals":
        with open(sub_dir/file, "w") as sig_file:
            text = f"<!-- This is the signals file (OSS) initially named: {input_arg}\n" \
                   f"   Add <signal> elements for each signal in this set -->\n" \
                   f"<Signals>\n" \
                   f"   <!-- Add signal elements here -->\n" \
                   f"</Signals>"
            sig_file.write(text)
    elif noun == "slot":
        with open(sub_dir/file, "w") as slot_file:
            text = f"<!-- This is the slot definition file for slots of type: {input_arg}\n" \
                   f"   Add <signal> elements for each signal in the slot -->\n" \
                   f"<SlotType>\n" \
                   f"   <!-- Add signal elements here -->\n" \
                   f"</SlotType>"
            slot_file.write(text)
    elif noun == "card":
        with open(sub_dir/file, "w") as card_file:
            text = f"<!-- This is the card definition file for cards of type: {input_arg}\n" \
                   f"   Add <signal> elements for each signal in the slot -->\n" \
                   f"<Card>\n" \
                   f"   <!-- Add device elements here, with signal mappings to slot signals -->\n" \
                   f"</Card>"
            card_file.write(text)

    dir_type = get_dirtype(sub_dir/"..")
    if dir_type == "library":  # If parent is a library, update its spec links to include new one
        subprocess.run(["make", f"{speclinks}", "-C", f"{sub_dir / '..'}"])
    if verbose:
        if dir_type == "library":
            print(f"A new {args[2]}, '{input_arg}' has been created in library '{basename `ocpiReadLinkE $subdir/..`}' "
                  f"in {sub_dir/file}")
        else:
            print(f"A new {args[2]}, '{input_arg}' has been created at the project level in {sub_dir/file}")
    if createtest:
        do_test(input_arg)