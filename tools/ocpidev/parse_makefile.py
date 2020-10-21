from pathlib import Path


def parse_makefile(file):
    """Get the make file type from Makefile.

    Per the original sed command, it should return the last match in the file.
    """
    required = ("include", "$(OCPI_CDK_DIR)", "/include/", ".mk")

    with open(file) as make_file:
        for line in make_file:
            if all(string in line for string in required):  # Identify necessary lines
                line_path = Path(line)  # Convert line to Path type for parsing
                file_name = line_path.stem  # Get just the name of the file
                if "rcc" in file_name:
                    file_type = "rcc"
                elif "hdl" in file_name:
                    file_type = "hdl"
                else:
                    file_type = ""

    return file_type
