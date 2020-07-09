import argparse
import re
import sys


PLATFORMS = {
    "alst4": "alst4",
    "centos6": "centos6",
    "centos7": "centos7",
    "centos 7": "centos7",
    "e310(pl)": "e3xx)",
    "e3xx": "e3xx",
    "isim": "isim",
    "matchstiq-z1(pl)": "matchstiq\\_{}z1",
    "matchstiq\\_{}z1": "matchstiq\\_{}z1",
    "ml605": "ml605",
    "ml605 (x86\\_{}64 centos 7)": "ml605",
    "ml605 (fmc lpc slot)": "ML605 (FMC LPC slot)",
    "modelsim": "modelsim",
    "xilinx13\\_{}3": "xilinx13\\_{}3",
    "xilinx13\\_{}3 (limited)": "xilinx13\\_{}3 (limited)",
    "xilinx13\\_{}4": "xilinx13\\_{}4",
    "xsim": "xsim",
    "zed": "zed",
    "zedboard": "zed",
    "zedboard(pl)": "zed",
    "zedboard (xilinx13\\_{}3)": "zed\\_{}ise",
    "zedboard (vivado)": "Zedboard (Vivado)",
}

def sort_tested_platforms(platforms):
    if len(platforms) == 0:
        return ""
    platforms = platforms.strip(",")
    #x = sorted([PLATFORMS[a.strip().lower()] for a in platforms.split(",")], key=str.lower)
    x = sorted([a.strip() for a in platforms.split(",")], key=str.lower)
    x = ", ".join(x)
    return x


def parse_table(table_lines, data):
    for line in table_lines:
        parts = [x.strip() for x in line.split("&")]
        if len(parts) < 2:
            continue
        key = parts[0].lower().replace("`", "").replace('"', "")
        if len(key) > 0 and key not in ["name", "version"]:
          value = parts[1].replace("\\\\", "").strip()
          match = re.search(r"\\_[^{]", value)
          if match is not None:
              value = value.replace("\\_", "\\_{}")
          match = re.search(r"(\\[a-zA-Z][a-zA-Z_]+)", value)
          if match is not None:
              value = value.replace(match.group(1), match.group(1) + "{}")
          data[key] = value
          if args.verbose:
              print("{:20}{}".format(key, value))



def parse_worker(table_lines):
    data = {
        "package prefix": "",
        "component": "",
        "name": "\\comp",
        "authoring model": "",
        "version": "\\ocpiversion",
        "tested platforms": "",
        "slaves": "",
        "aci slaves": "",
    }

    parse_table(table_lines, data)
    print((
        "\\def\\packageprefix{{{package_prefix}}}\n"
        "\\def\\component{{{component}}}\n"
        "\\def\\name{{{name}}}\n"
        "\\def\\authoringmodel{{{authoring_model}}}\n"
        "\\def\\version{{{version}}}\n"
        "\\def\\testedplatforms{{{tested_platforms}}}\n"
        "\\def\\slaves{{{slaves}}}\n"
        "\\def\\acislaves{{{aci_slaves}}}\n"
        "\\input{{\\snippetpath/worker_summary_table}}"
    ).format(package_prefix=data["package prefix"], component=data["component"],
             name=data["name"], authoring_model=data["authoring model"],
             version=data["version"],
             tested_platforms=sort_tested_platforms(data["tested platforms"]),
             slaves=data["slaves"], aci_slaves=data["aci slaves"]))


def parse_component(table_lines):
    data = {
        "name": "\\comp",
        "worker type": "",
        "version": "\\ocpiversion",
        "release date": "",
        "component library": "",
        "workers": "",
        "tested platforms": "",
    }

    parse_table(table_lines, data)
    #print(data)
    print((
        "\\def\\name{{{name}}}\n"
        "\\def\\workertype{{{worker_type}}}\n"
        "\\def\\version{{{version}}}\n"
        "\\def\\releasedate{{{release_date}}}\n"
        "\\def\\componentlibrary{{{component_library}}}\n"
        "\\def\\workers{{{workers}}}\n"
        "\\def\\testedplatforms{{{tested_platforms}}}\n"
        "\\input{{\\snippetpath/component_summary_table}}"
    ).format(name=data["name"], worker_type=data["worker type"], version=data["version"],
             release_date=data["release date"],
             component_library=data["component library"], workers=data["workers"],
             tested_platforms=sort_tested_platforms(data["tested platforms"])))

##### Main #####

parser = argparse.ArgumentParser()
parser.add_argument("filename")
parser.add_argument("-w", "--worker", action="store_true")
parser.add_argument("-v", "--verbose", action="store_true")
args = parser.parse_args()

table_lines = []
with open(args.filename, "r") as fd:
    in_table = False
    for line in fd.readlines():
        if not in_table:
            if re.match(r"\s*\\begin{tabular}", line) or re.match(r"\s*\\begin{longtable}", line):
                in_table = True
            else:
                continue
        elif re.match(r"\s*\\end{tabular}", line) or re.match(r"\s*\\end{longtable}", line):
            break
        else:
            table_lines.append(line)

if args.worker:
    parse_worker(table_lines)
else:
    parse_component(table_lines)

