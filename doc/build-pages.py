#!/bin/env python3.4

import argparse
import logging
import os
import pprint
import re
import shutil
import subprocess
import tempfile
from pathlib import Path

# External dependencies
from jinja2 import Environment, FileSystemLoader


class SectionData(object):
    def __init__(self, name: str, title: str, files: dict):
        self.name = name
        self.title = title
        self.files = files  # dict of UrlLink(s)

    def __str__(self):
        return "name: {}, title: {}, files: {}".format(self.name, self.title, self.files)

    def __repr__(self):
        return pprint.pformat({"name": self.name, "title": self.title, "files": self.files})


class UrlLink(object):
    def __init__(self, name: str, url: str):
        self.name = name
        self.url = url

    def __str__(self):
        return "name: {}, url: {}".format(self.name, self.url)

    def __repr__(self):
        return pprint.pformat({"name": self.name, "url": self.url})

    def anchor_tag(self):
        return '<a href="{url}">{name}</a>'.format(url=self.url, name=self.name)


def main():
    logging.debug("CURDIR        : {}".format(CURDIR))
    logging.debug("OCPI_ROOT     : {}".format(OCPI_ROOT))
    logging.debug("OCPI_TEMPLATES: {}".format(OCPI_TEMPLATES))
    logging.debug("WEBROOT       : {}".format(args.webroot))
    logging.debug("OUTPUTDIR     : {}".format(args.outputdir))

    # rm -rf pdf dir
    if args.clean_all and args.outputdir.exists():
        logging.info("Removing {}".format(args.outputdir))
        shutil.rmtree(args.outputdir.as_posix())
    os.makedirs(args.outputdir.as_posix(), exist_ok=True)

    # Get list of tags and checked out branches
    git_tags = get_tags()
    logging.debug("Tags: {}".format(git_tags))
    git_branches = get_branches()
    logging.debug("Branches: {}".format(git_branches))

    # Resolve HEAD because it doesn't work with all git commands
    head = get_name_rev("HEAD")
    if "HEAD" in args.releases:
        args.releases[args.releases.index("HEAD")] = head
    if "HEAD" in args.clean:
        args.clean[args.clean.index("HEAD")] = head

    if args.all:
        releases = git_tags.copy()
        latest_release = releases[-1]
        releases.append("develop")
    else:
        for release in args.releases:
            if release not in git_tags and release not in git_branches:
                logging.critical(
                    "'{}' is not a valid git tag or checked out branch. Exiting...".format(release)
                )
                exit(1)
        releases = args.releases  # type: list
        try:
            releases.remove("develop")
            latest_release = releases[-1] if len(releases) else "develop"
            releases.append("develop")
        except ValueError:
            latest_release = releases[-1]

    # This doesn't work because libreoffice is unable to have multiple instances
    # of it's pdf conversion tool (unoconv or soffice) running concurrently or
    # in parallel. This is commented out until this script can generate docs
    # without relying on genDocumentation.sh, or genDocumentation.sh is
    # rewritten.
    # if args.parallel:
    #     with concurrent.futures.ThreadPoolExecutor() as executor:
    #         executor.map(run, releases)
    # else:
    logging.debug("Releases: {}".format(releases))
    logging.debug("Latest release: {}".format(latest_release))
    for release in releases:
        is_latest = True if latest_release == release else False
        build(release)
        gen_release_index(release, is_latest=is_latest)

    # Create symlink so urls like https://example.com/releases/latest/doc/some.pdf will work
    latest_link = Path(args.outputdir, "latest")
    if latest_link.exists():
        os.remove(latest_link.as_posix())
    os.symlink(latest_release, latest_link.as_posix())

    gen_releases_index(latest_release)  # Create OUTPUTDIR/index.html
    gen_releases_all_index(latest_release, git_tags)  # Create OUTPUTDIR/all/index.html


def build(tag: str):
    logging.info("Processing release: {}".format(tag))
    dst_dir = Path(args.outputdir, tag, "docs").absolute()
    if dst_dir.exists():
        if dst_dir.parent.name in args.clean:
            logging.info("Removing {}".format(dst_dir))
            shutil.rmtree(dst_dir.as_posix())
        else:
            logging.info("  Not building PDFs... '{}' exists".format(dst_dir.as_posix()))
            logging.info("  Rerun with '--clean {}' to force building of PDFs".format(dst_dir.parent.name))
            return

    with tempfile.TemporaryDirectory() as tmpdir:
        # Clone repo to temporary location
        tmprepo = Path(tmpdir, 'opencpi').absolute()
        logging.info("Cloning {} to {}".format(OCPI_ROOT, tmprepo))
        os.mkdir(tmprepo.as_posix())
        # --no-hardlinks needed because cloud runner puts /tmp on different file system
        subprocess.check_call(
            "git clone --local --no-hardlinks --shared --single-branch --branch {branch} {src} {dst}".format(
                branch=tag, src=OCPI_ROOT, dst=tmprepo
            ),
            shell=True
        )

        # Builds docs for releases that require it (older releases committed pdfs to repo)
        logging.info("Building docs for release: {}".format(tag))
        build_docs(tmprepo)

        # Copy pdfs to dst_dir
        logging.info("Copying docs for release: {}".format(tag))
        copy_pdfs(tmprepo, dst_dir)

        # No RPM support for 1.6.0
        if tag.startswith("v1.6.0"):
            rpm_guide = find_file(dst_dir, "RPM_Installation_Guide.pdf")
            if rpm_guide is not None:
                os.remove(rpm_guide.as_posix())


def build_docs(repo_dir: Path):
    # Look for genDocumentation.sh
    gen_doc_script = find_file(Path(repo_dir, "doc"), "genDocumentation.sh", case_sensitive=False)
    if gen_doc_script is None:
        return
    logging.debug("Found {}".format(gen_doc_script))

    # v1.5.0rc4 had some bugs
    if Path(repo_dir, "projects/assets_ts").exists() \
            and not Path(repo_dir, "projects/assets_ts/imports").exists():
        os.symlink("../../project-registry", Path(repo_dir, "projects/assets_ts/imports").as_posix())

    # Run genDocumentation.sh
    subprocess.check_call(
        "bash {} --repopath {} --outputpath {}".format(
            gen_doc_script.as_posix(), repo_dir, Path(repo_dir, "doc/pdfs")
        ),
        shell=True
    )


def copy_pdfs(src_dir: Path, dst_dir: Path):
    # Find pdfs. Different releases put pdfs in different places.
    pdfs = []
    for d in ["doc", "pdf", "pdfs"]:
        path = Path(src_dir, d)
        if path.exists():
            pdfs += find_files(path, extension="pdf")

    # Copy pdfs
    for pdf in pdfs:  # type: Path
        pdf = pdf.resolve()

        # Get part of path that is after doc_dirname
        # ex. /src/dir/path/doc_dirname/some/file.pdf -> some/file.pdf
        parts = Path(pdf.as_posix()[len(src_dir.as_posix()) + 1:]).parts[1:]
        if parts[0] in ["internal", "old"]:
            continue  # Ignore internal and old pdfs
        if parts[0] in ["pdf", "pdfs"]:
            parts = parts[1:]
        path_frag = "/".join(parts)

        # Copy pdf to dst_dir/path_frag
        dst = Path(dst_dir, path_frag).absolute()
        os.makedirs(dst.parent.as_posix(), exist_ok=True)
        logging.debug("Copying {} -> {}".format(pdf, dst))
        shutil.copy2(pdf.as_posix(), dst.as_posix())


def gen_releases_index(latest_release: str):
    template = jinja_env.get_template("releases.index.html")
    index = template.render(url=latest_release)
    with open(Path(args.outputdir, "index.html").as_posix(), "w") as fd:
        fd.write(index)


def gen_releases_all_index(latest_release: str, git_tags):
    logging.info("Generating {}/all/index.html".format(args.outputdir))

    # Every directory under OUTPUTDIR is a released version. Gather releases and sort them.
    releases = []
    for item in Path(args.outputdir).iterdir():
        if item.is_dir() and item.name in git_tags:
            releases.append(item.name)
    releases = sort_tags(releases)

    # Make links for each release
    releases_links = []
    for release in releases:
        url = "../{}".format(release)
        if release == latest_release:
            release = release + " (latest release)"
        releases_links.append(UrlLink(name=release, url=url))

    # Render index.html and save it
    template = jinja_env.get_template("releases-all.index.html")
    index = template.render(develop_url="../develop", releases=releases_links)
    outdir = Path(args.outputdir, "all")
    os.makedirs(outdir.as_posix(), exist_ok=True)
    with open(Path(outdir, "index.html").as_posix(), "w") as fd:
        fd.write(index)


def gen_release_index(tag: str, is_latest=False):
    release_dir = Path(args.outputdir, tag)
    pdf_dir = Path(release_dir, "docs")
    if not pdf_dir.exists():
        return
    logging.info("Generating {}/index.html".format(release_dir))

    def _fix_file_name(file_name: str):
        """Cleans up file names until they can be renamed"""
        fname = file_name.lower()
        if fname == "opencpi installation":
            return file_name + " Guide"
        elif fname == "opencpi user":
            return file_name + " Guide"
        elif fname == "opencpi application development":
            return file_name + " Guide"
        elif fname == "opencpi component development":
            return file_name + " Guide"
        elif fname == "opencpi rcc development":
            return file_name + " Guide"
        elif fname == "opencpi hdl development":
            return file_name + " Guide"
        elif fname == "opencpi platform development":
            return file_name + " Guide"
        elif fname == "ide user guide":
            return "AV GUI User Guide"
        elif fname.startswith("briefing"):
            chunks = fname.split()
            chunks[1] = "{:02d}".format(int(chunks[1]))
            return " ".join(chunks)
        elif fname.startswith("tutorial"):
            chunks = fname.split()
            if chunks[1].endswith("hw"):
                chunks[1] = "{:02d}hw".format(int(chunks[1][:-2]))
            else:
                chunks[1] = "{:02d}".format(int(chunks[1]))
            return " ".join(chunks)
        return file_name

    # Generate dictionary of pdf links organized based on filesystem layout
    # Links are built relative to release_dir
    section_data = {}
    for root, _, files in os.walk(pdf_dir.as_posix()):
        depth = len(Path(root).parts) - len(pdf_dir.parts)
        base_url = "/".join(Path(root).parts[-(depth + 1):])
        if depth == 0:
            section_name = "main"
            section_title = "Main Documentation"
        else:
            section_name = os.path.basename(root).lower().replace("-", "_")
            section_title = section_name.replace("_", " ").title()
            if section_title == "Assets Ts":
                section_title = "Assets TS"
            if section_title not in ["Tutorials", "Briefings"]:
                section_title += " Project Documentation"

        file_links = {}
        for f in files:
            if f.endswith(".pdf"):
                url = "{}/{}".format(base_url, f)
                name = f[:-4]  # remove '.pdf'
                if name.startswith("Briefing") or name.startswith("Tutorial"):
                    file_links[_fix_file_name(name.replace("_", " ")).lower()] = UrlLink(
                        name=name.replace("_", " "), url=url)
                else:
                    file_links[name.lower()] = UrlLink(name=_fix_file_name(name.replace("_", " ")), url=url)
        section_data[section_name] = SectionData(name=section_name, title=section_title, files=file_links)

    # Render each section
    old_main_section = jinja_env.get_template("old-main-documentation.html")
    main_section = jinja_env.get_template("main-documentation.html")
    project_section = jinja_env.get_template("project-section.html")
    rendered_sections = {}
    for data in section_data.values():
        if data.name != "main":
            rendered_sections[data.name] = project_section.render(section_title=data.title, links=data.files)

    # Render main last as it needs data from other sections
    data = section_data["main"]
    if tag in ["OpenCPI-1.0", "OpenCPI-2015.Q1.rc0"]:
        rendered_sections[data.name] = old_main_section.render(section_title=data.title, links=data.files)
    else:
        # Main section needs some files from assets, briefings, and tutorials
        assets = section_data.get("assets")
        tutorials = section_data.get("tutorials")
        briefings = section_data.get("briefings")
        rendered_sections[data.name] = main_section.render(section_title=data.title, links=data.files,
                                                           assets=assets, tutorials=tutorials,
                                                           briefings=briefings)

    # Stitch it all together
    template = jinja_env.get_template("release.index.html")
    index = template.render(title=tag, sections=rendered_sections, is_latest=is_latest,
                            releases_all_url="../../releases/all/")
    with open(Path(release_dir, "index.html").as_posix(), "w") as fd:
        fd.write(index)


# Util functions ##############################################################

def find_file(search_dir, filename: str, case_sensitive=True) -> Path:
    if not isinstance(search_dir, Path):
        search_dir = Path(str(search_dir))
    orig_filename = filename
    if not case_sensitive:
        filename = filename.lower()
    for root, _, files in os.walk(search_dir.as_posix()):
        for file in files:
            if not case_sensitive:
                file = file.lower()
            if file == filename:
                return Path(root, orig_filename)
    return None


def find_files(search_dir, extension=None, recursive=True) -> list:
    if not isinstance(search_dir, Path):
        search_dir = Path(str(search_dir))
    pdfs = []
    if extension is not None:
        extension = "." + extension
    for root, _, files in os.walk(search_dir.as_posix()):
        for file in files:
            if extension is None or file.lower().endswith(extension):
                pdfs.append(Path(root, file))
        if not recursive:
            break
    return pdfs


def get_tags():
    # Get list of release tags
    git_tags = sort_tags(subprocess.check_output(["git", "tag", "-l"]).decode().strip("\n").split("\n"))

    # v1.3.0 has no docs
    if "v1.3.0" in git_tags:
        git_tags.remove("v1.3.0")

    return git_tags


def get_branches():
    # Get list of branches
    git_branches = [x.replace("*", "").strip() for x in subprocess.check_output(
        ["git", "branch", "--no-color"]
    ).decode().strip("\n").split("\n")]

    # Resolve detached branches to their symbolic name. This is needed because
    # of how gitlab runner checks out branch under test
    pat = re.compile(r"detached from ([a-z0-9]+)")
    for i, branch in enumerate(git_branches):
        match = pat.search(branch)
        if match is not None:
            sha = match.group(1)
            git_branches[i] = get_name_rev(sha)

    # Ensure no duplicates
    return list(set(git_branches))


def get_name_rev(rev: str):
    name = subprocess.check_output(
        ["git", "name-rev", "--name-only", "--no-undefined", rev]
    ).decode().strip("\n")
    if len(name):
        return name
    raise RuntimeError("Could not resolve {} to a branch name".format(rev))


def sort_tags(tags):
    old_versions = []
    new_versions = []
    for tag in tags:  # type: str
        if tag.startswith("OpenCPI"):
            old_versions.append(tag)
        else:
            new_versions.append(tag)

    def _swap(a, b) -> bool:
        if b[0] == a[0]:
            if b[1] == a[1]:
                if "rc" in a[2]:
                    return False
                if "rc" in b[2]:
                    return True
                if b[2] < a[2]:
                    return True
            elif b[1] < a[1]:
                return True
        elif b[0] < a[0]:
            return True
        return False

    for i in range(1, len(old_versions)):
        old = old_versions[i].split(".")
        for j in range(i + 1, len(old_versions)):
            new = old_versions[j].split(".")
            if _swap(old, new):
                old_versions[i] = ".".join(new)
                old_versions[j] = ".".join(old)
                break

    for i in range(len(new_versions)):
        old = new_versions[i].split(".")
        for j in range(i + 1, len(new_versions)):
            new = new_versions[j].split(".")
            if _swap(old, new):
                new_versions[i] = ".".join(new)
                new_versions[j] = ".".join(old)
                break

    return old_versions + new_versions


if __name__ == "__main__":
    def _find_root(x: Path):
        while not x.name.startswith("opencpi") and len(x.parts) != 1:
            x = x.parent
        return x


    # Setup some paths
    CURDIR = Path(os.curdir).resolve()
    OCPI_ROOT = _find_root(Path(__file__).resolve())
    OCPI_TEMPLATES = Path(OCPI_ROOT, "doc", "generator", "templates")
    default_webroot = Path(OCPI_ROOT, ".public")
    default_outputdir = Path(default_webroot, "releases")

    # Setup argparse
    parser = argparse.ArgumentParser(formatter_class=argparse.RawTextHelpFormatter)
    parser.add_argument("-c", "--clean", metavar="RELEASE", action="append", default=[],
                        help="Remove RELEASE before generating pdfs. Can be specified multiple times.")
    parser.add_argument("-o", "--outputdir", help="Output directory. OUTPUTDIR must be based off WEBROOT.\n"
                                                  "Default: {}".format(default_outputdir))
    parser.add_argument("-v", "--verbose", action="store_true", help="Increase output verbosity")
    parser.add_argument("-w", "--webroot", help="The WEBROOT is the base directory that a web server uses when\n"
                                                "serving files for a particular site.\n"
                                                "OUTPUTDIR must be based off WEBROOT.\n"
                                                "Default: {}".format(default_webroot))
    parser.add_argument("--all", action="store_true", help="Build docs for all releases + develop")
    parser.add_argument("--clean-all", action="store_true", help="Remove OUTPUTDIR before generating pdfs")
    # parser.add_argument("--parallel", action="store_true", help="builds docs for each release in parallel")
    parser.add_argument("releases", nargs="*", help="Release(s) to build. Must be a valid git tag, branch, or 'HEAD'")
    parser.epilog = ("Examples:\n"
                     "  {prog} --all                  Build all releases + develop\n"
                     "  {prog} --all --clean-all      Clean and build all + develop\n"
                     "  {prog} --all --clean develop  Same as --all, but only clean develop\n"
                     "  {prog} --clean develop        Clean and build develop\n"
                     "  {prog} develop                Build develop\n"
                     "  {prog} HEAD                   Build checked out branch").format(prog=parser.prog)
    args = parser.parse_args()

    # Setup logging
    logging.basicConfig(format="%(asctime)s:%(levelname)s: %(message)s", level=logging.INFO)
    if args.verbose:
        logging.getLogger().setLevel(logging.DEBUG)

    # Releases and --all cannot be used together
    if args.all and len(args.releases):
        logging.critical("Cannot specify releases when using '--all'. Exiting...")
        exit(1)
    if not args.all and len(args.releases) == 0:
        if len(args.clean):
            # allows './prog --clean RELEASE' to build and clean RELEASE
            # otherwise './prog --clean RELEASE RELEASE' would have to be used
            args.releases = args.clean
        else:
            logging.critical("A release to build must be specified or use '--all' to build all releases")
            exit(1)
    elif len(args.clean) and len(args.releases):
        # add items being cleaned to items being built
        args.releases = list(set(args.releases + args.clean))

    # Setup webroot and outputdir
    if args.webroot is None:
        args.webroot = default_webroot
    else:
        args.webroot = Path(args.webroot)
        default_outputdir = Path(args.webroot, "releases")
    if args.outputdir is None:
        args.outputdir = default_outputdir
    else:
        args.outputdir = Path(args.outputdir)
    if args.webroot.is_absolute() ^ args.outputdir.is_absolute():
        logging.critical("WEBROOT ({}) and OUTPUTDIR ({}) must both either be absolute or relative paths, not a mix."
                         .format(args.webroot, args.outputdir))
        exit(1)
    if not args.outputdir.as_posix().startswith(args.webroot.as_posix()):
        logging.critical("OUTPUTDIR ({}) must be a child of WEBROOT ({})".format(args.outputdir, args.webroot))
        exit(1)
    os.makedirs(args.outputdir.as_posix(), exist_ok=True)
    args.webroot.resolve()
    args.outputdir.resolve()

    # Setup jinja2
    jinja_env = Environment(loader=FileSystemLoader(OCPI_TEMPLATES.as_posix()))

    main()
