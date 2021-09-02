#!/bin/env python3
#
# This script only runs on CentOS 7 so it is safe to use python 3.6 features.
#
# N.B.: This is overdue for a rewrite, but the "best time" to accomplish
# that depends on how quickly the RST documentation replaces ".fodt" and
# ".tex" sources.  In the meantime, this should be kept as maintainable
# as possible, i.e., extend and/or replace functionality logically.  The
# current strategy is to make project section headers (names) clickable
# for each project having RST documentation available.  This should allow
# for a more seamless transition as old documents are retired, while
# preserving the page layout to which people have become accustomed.
#

import argparse
import logging
import os
import pprint
import re
import shutil
import subprocess
import tempfile
from functools import cmp_to_key
from pathlib import Path
from typing import Dict, List, Union

# External dependencies
from jinja2 import Environment, FileSystemLoader

# Supported OSPs
OSPS = ["ocpi.osp.analog", "ocpi.osp.e3xx", "ocpi.osp.plutosdr", "ocpi.osp.ettus"]
OSP_TAGS = dict()  # Will be filled in later

# Supported COMPs
COMPS = ["ocpi.comp.sdr"]
COMP_TAGS = dict()


class SectionData(object):
    def __init__(self, name: str, title: str, files: dict):
        self.name = name
        self.title = title
        self.files = files  # dict of UrlLink(s)

    def __str__(self):
        return f"name: {self.name}, title: {self.title}, files: {self.files}"

    def __repr__(self):
        return pprint.pformat({"name": self.name, "title": self.title, "files": self.files})


class UrlLink(object):
    def __init__(self, name: str, url: str):
        self.name = name
        self.url = url

    def __str__(self):
        return f"name: {self.name}, url: {self.url}"

    def __repr__(self):
        return pprint.pformat({"name": self.name, "url": self.url})

    def anchor_tag(self):
        return f'<a href="{self.url}">{self.name}</a>'


def main():
    logging.debug(f"CURDIR        : {CURDIR}")
    logging.debug(f"OCPI_ROOT     : {OCPI_ROOT}")
    logging.debug(f"OCPI_TEMPLATES: {OCPI_TEMPLATES}")
    logging.debug(f"REPODIR       : {args.repodir}")
    logging.debug(f"OUTPUTDIR     : {args.outputdir}")
    logging.debug(f"WEBROOT       : {args.webroot}")

    # rm -rf pdf dir
    if args.clean_all and args.outputdir.exists():
        logging.info(f"Removing {args.outputdir}")
        shutil.rmtree(str(args.outputdir))
    os.makedirs(str(args.outputdir), exist_ok=True)

    # Resolve HEAD because it doesn't work with all git commands
    head = get_name_rev(args.repodir / ".git", "HEAD")
    if "HEAD" in args.releases:
        args.releases[args.releases.index("HEAD")] = head
    if "HEAD" in args.clean:
        args.clean[args.clean.index("HEAD")] = head

    if args.all:
        releases = GIT_TAGS.copy()
        latest_release = releases[-1]
        releases.append("develop")
    else:
        for release in args.releases:
            if release not in GIT_TAGS and release not in GIT_BRANCHES:
                logging.critical(
                    f"'{release}' is not a valid release or checked out branch. "
                    f"Run '{parser.prog} -l' to see a list of valid releases and branches."
                )
                exit(1)
        releases = args.releases  # type: list
        try:
            # develop is always last
            releases.remove("develop")
            latest_release = releases[-1] if len(releases) else "develop"
            releases.append("develop")
        except ValueError:
            latest_release = releases[-1]
    logging.debug(f"Releases: {releases}")
    logging.debug(f"Latest release: {latest_release}")

    # Download supported OSPs
    for osp in OSPS:
        download_osp(osp)
        OSP_TAGS[osp] = get_tags(OCPI_OSPDIR / osp / ".git")
        OSP_TAGS[osp].append("develop")  # develop will always be a valid git revision

    # Download supported COMPs
    for comp in COMPS:
        download_comp(comp)
        COMP_TAGS[comp] = get_tags(OCPI_COMPDIR / comp / ".git")
        COMP_TAGS[comp].append("develop")  # develop will always be a valid git revision

    # Build each release and its OSPs and COMPs
    for release in releases:
        is_latest = True if latest_release == release else False
        build(release)
        gen_release_index(release, is_latest=is_latest)  # Create OUTPUTDIR/RELEASE/index.html

    # Create symlink so urls like https://example.com/releases/latest/doc/some.pdf will work
    latest_link = args.outputdir / "latest"
    if latest_link.exists():
        os.remove(str(latest_link))
    os.symlink(latest_release, str(latest_link))

    # Cleanup output dir, removing any tags that have been superseded.
    # This helps keep the runner cache clean
    for item in args.outputdir.glob("v*"):
        if item.is_dir() and item.name not in GIT_TAGS:
            logging.debug(f"Removing superseded release {item.name}")
            shutil.rmtree(str(item))

    gen_releases_index()  # Create OUTPUTDIR/index.html
    gen_releases_all_index(latest_release, GIT_TAGS)  # Create OUTPUTDIR/all/index.html


def build(tag: str) -> None:
    """
    Main workhorse function. This function will clone each "tag" into a temporary build
    directory and build the documentation for that "tag". After the docs have been built,
    they are copied to the OUTPUTDIR for further processing when the HTML is generated.

    Args:
        tag: the git tag or branch to build docs for

    Returns:
        None
    """
    logging.info(f"Processing release: {tag}")
    release_dir = Path(args.outputdir, tag).absolute()
    if release_dir.exists():
        if release_dir.name in args.clean:
            logging.info(f"Removing {release_dir}")
            shutil.rmtree(str(release_dir))
        else:
            logging.info(f"  Not building PDFs... '{release_dir}' exists")
            logging.info(
                f"  Rerun with '--clean {release_dir.name}' to force building of PDFs"
            )
            return

    with tempfile.TemporaryDirectory() as tmpdir:
        # Clone repo to temporary location
        tmprepo = Path(tmpdir, 'opencpi').absolute()
        logging.info(f"Cloning {args.repodir} to {tmprepo}")
        os.mkdir(str(tmprepo))
        # --no-hardlinks needed because cloud runner puts /tmp on different file system
        base_cmd = ["git", "clone", "--local", "--no-hardlinks", "--shared", "--single-branch"]
        cmd = base_cmd + ["--branch", tag, str(args.repodir), str(tmprepo)]
        logging.debug(f"Executing cmd: {cmd}")
        subprocess.check_call(cmd)

        # Clone supported OSPs
        for osp in OSPS:
            osp_src = OCPI_OSPDIR / osp
            if Path(tmprepo, "projects", "bsps").exists():
                # Older versions of OpenCPI used 'bsps' instead of 'osps'
                osp_dst = tmprepo / "projects" / "bsps" / osp
            else:
                osp_dst = tmprepo / "projects" / "osps" / osp
            osp_tags = OSP_TAGS[osp]
            logging.debug(f"{osp} tags: {osp_tags}")
            if tag not in osp_tags:
                logging.info(f"Tag '{tag}' doesn't exist for osp '{osp}'. Skipping...")
                continue
            if tag in ["v1.4.0", "v1.5.0", "v1.6.2", "v2.0.0"]:
                # temporarily skip these until a patch release is made for each version
                # to fix where the pdfs are placed.
                # See https://gitlab.com/opencpi/opencpi/-/merge_requests/396
                continue
            try:
                logging.info(f"Cloning {osp_src} to {osp_dst}")
                cmd = base_cmd + ["--branch", tag, str(osp_src), str(osp_dst)]
                logging.debug(f"Executing cmd: {cmd}")
                subprocess.check_call(cmd)
            except subprocess.CalledProcessError as e:
                logging.critical(f"Command failed: {e.cmd}")
                exit(-1)

        # Clone supported COMPs
        for comp in COMPS:
            comp_src = OCPI_COMPDIR / comp
            comp_dst = tmprepo / "projects" / comp
            comp_tags = COMP_TAGS[comp]
            logging.debug(f"{comp} tags: {comp_tags}")
            if tag not in comp_tags:
                logging.info(f"Tag '{tag}' doesn't exist for comp '{comp}'. Skipping...")
                continue
            try:
                logging.info(f"Cloning {comp_src} to {comp_dst}")
                cmd = base_cmd + ["--branch", tag, str(comp_src), str(comp_dst)]
                logging.debug(f"Executing cmd: {cmd}")
                subprocess.check_call(cmd)
            except subprocess.CalledProcessError as e:
                logging.critical(f"Command failed: {e.cmd}")
                exit(-1)

        # Builds docs for releases that require it (older releases committed pdfs to repo)
        logging.info(f"Building docs for release: {tag}")
        build_docs(tmprepo)

        # Copy pdfs to release dir
        logging.info(f"Copying docs for release: {tag}")
        copy_pdfs(tmprepo, release_dir / "docs")

        # No RPM support for 1.6.0
        if tag.startswith("v1.6.0"):
            rpm_guide = find_file(release_dir / "docs", "RPM_Installation_Guide.pdf")
            if rpm_guide is not None:
                os.remove(str(rpm_guide))

        # Generate (if necessary) and copy man pages to release dir
        logging.info(f"Copying man pages for release: {tag}")
        gen_copy_man(tmprepo, release_dir / "man")

        # Generate and copy RST docs to release dir
        logging.info(f"Generating and copying RST docs for release: {tag}")
        gen_copy_rst(tmprepo, release_dir / "rst")


def build_docs(repo_dir: Path):
    # Look for genDocumentation.sh
    gen_doc_script = find_file(repo_dir / "doc", "genDocumentation.sh", case_sensitive=False)
    if gen_doc_script is None:
        return
    logging.debug(f"Found {gen_doc_script}")

    # Run genDocumentation.sh
    cmd = ["bash", str(gen_doc_script), "--repopath", str(repo_dir), "--outputpath",
           str(repo_dir / "doc" / "pdfs")]
    logging.debug(f"Executing cmd: {cmd}")
    subprocess.check_call(cmd)


def gen_copy_man(src_dir: Path, dst_dir: Path):
    """
    Copy HTML man pages if they exist.  Prior to v2.2.0, the man
    pages were supplied pre-rendered in HTML: effective with that
    release, the HTML man pages are generated as part of doing an
    OpenCPI installation using the source located at doc/man/src/
    """
    html_man_dir = src_dir / "doc" / "man" / "html"
    if not html_man_dir.exists():
        logging.info(f"No HTML man pages found at {html_man_dir}")
        man_mk = src_dir / "doc" / "man" / "Makefile"
        if man_mk.exists():
            # post-v2.1.1: build the man pages.
            logging.info(f'"{man_mk}" found: building man pages')
            # Unfortunately, any man page source patching for a particular
            # version must happen here rather than in the context of that
            # version.  As long as the list of patches remains small, the
            # overhead of checking to see if the patch is required for a
            # particular version exceeds simply attempting the patch.
            #   v2.2.0: "ocpidev-application.1.txt", "ocpidev-run.1.txt",
            #           "ocpiav.1.txt", "ocpigr.1.txt", "ocpihdl.1.txt",
            #           "ocpirun.1.txt"
            # N.B.: We do not need to do anything for the man page build
            # except "install-packages.sh" and "install-prerequisites.sh",
            # but "ocpidoc" (needed by gen_copy_rst() function) will not be
            # available with anything less than a full "minimal" (oxymoron?)
            # install of the framework.  Incur the pain once here.
            cmd = ["bash", "-c", fr'cd {src_dir} ; \
sed -e "s/\xe2\x80\x99/\'/g" -e "s/\xe2\x80\x93/\-/g" -e "s/\xe2\x80\x9c/\"/g" -e "s/\xe2\x80\x9d/\"/g" doc/man/src/ocpidev-application.1.txt > doc/man/src/ocpidev-application.1.txt.new ; \
mv doc/man/src/ocpidev-application.1.txt.new doc/man/src/ocpidev-application.1.txt ; \
sed -e "s/\xe2\x80\x99/\'/g" -e "s/\xe2\x80\x93/\-/g" -e "s/\xe2\x80\x9c/\"/g" -e "s/\xe2\x80\x9d/\"/g" doc/man/src/ocpidev-run.1.txt > doc/man/src/ocpidev-run.1.txt.new ; \
mv doc/man/src/ocpidev-run.1.txt.new doc/man/src/ocpidev-run.1.txt ; \
sed -e "s/\xe2\x80\x99/\'/g" -e "s/\xe2\x80\x93/\-/g" -e "s/\xe2\x80\x9c/\"/g" -e "s/\xe2\x80\x9d/\"/g" doc/man/src/ocpiav.1.txt > doc/man/src/ocpiav.1.txt.new ; \
mv doc/man/src/ocpiav.1.txt.new doc/man/src/ocpiav.1.txt ; \
sed -e "s/\xe2\x80\x99/\'/g" -e "s/\xe2\x80\x93/\-/g" -e "s/\xe2\x80\x9c/\"/g" -e "s/\xe2\x80\x9d/\"/g" doc/man/src/ocpigr.1.txt > doc/man/src/ocpigr.1.txt.new ; \
mv doc/man/src/ocpigr.1.txt.new doc/man/src/ocpigr.1.txt ; \
sed -e "s/\xe2\x80\x99/\'/g" -e "s/\xe2\x80\x93/\-/g" -e "s/\xe2\x80\x9c/\"/g" -e "s/\xe2\x80\x9d/\"/g" doc/man/src/ocpihdl.1.txt > doc/man/src/ocpihdl.1.txt.new ; \
mv doc/man/src/ocpihdl.1.txt.new doc/man/src/ocpihdl.1.txt ; \
sed -e "s/\xe2\x80\x99/\'/g" -e "s/\xe2\x80\x93/\-/g" -e "s/\xe2\x80\x9c/\"/g" -e "s/\xe2\x80\x9d/\"/g" doc/man/src/ocpirun.1.txt > doc/man/src/ocpirun.1.txt.new ; \
mv doc/man/src/ocpirun.1.txt.new doc/man/src/ocpirun.1.txt ; \
export LANG=en_US.utf8 ; \
scripts/install-opencpi.sh --minimal --no-kernel']
            logging.debug(f'Executing "{cmd}" in directory "{src_dir}"')
            subprocess.check_call(cmd)
            html_man_dir = src_dir / "doc" / "man" / "gen" / "html"
        else:
            return

    os.makedirs(str(dst_dir), exist_ok=True)
    for f in find_files(html_man_dir, recursive=False):
        dst = dst_dir / f.name
        logging.debug(f"Copying {f} -> {dst}")
        shutil.copy2(str(f), str(dst))


def gen_copy_rst(src_dir: Path, dst_dir: Path):
    """
    Generate HTML renderings of RST document sources and copy
    them to project-specific subdirectories under the specified
    destination directory.
    """
    #
    # The check for "doc/man/Makefile" does not make much sense
    # until one realizes that RST docs were introduced about the
    # same time as it became necessary to build the man pages.
    #
    man_mk = src_dir / "doc" / "man" / "Makefile"
    if man_mk.exists():
        # post-v2.1.1: RST document sources may exist.
        logging.info(f'"{man_mk}" found: attempting to process RST documents')
        #
        # gen_copy_rst() must be called after gen_copy_man(), because we depend
        # on the presence of the same minimal framework in "src_dir".  No idea
        # whether setting LANG is required here, but it does not hurt to do so.
        #
        # Easier to comment on the bash code below here vs. in-line, so...
        # What happens if "ocpidoc" fails is a question, which is why we look
        # for the expected "ocpidoc" build products directory before doing
        # anything else.  The code that generates "ddir" will convert project
        # names like "ocpi.ptype.name" to "ptype_name", which is consistent
        # with how OSPS are handled in "generator/genDocumentation.sh".
        #
        # Unless a way can be found to do a minimally-sufficient subset of
        # "scripts/install-opencpi.sh --minimal --no-kernel", there does not
        # seem to be a better way to make "ocpidoc" available.
        #
        cmd = ["bash", "-c", fr'cd {src_dir} ; \
source cdk/opencpi-setup.sh -s ; \
export LANG=en_US.utf8 ; \
for pdir in projects/* projects/osps/* ; \
do if [ -f $pdir/index.rst ] ; \
then ocpidoc -d $pdir build -b ; \
if [ -d $pdir/gen/doc ] ; \
then ddir=`basename $pdir | sed -e "s/\./_/g" -e "s/ocpi_//"` ; \
mkdir -p {dst_dir}/$ddir ; \
( cd $pdir/gen/doc ; cp -pr . {dst_dir}/$ddir ) ; \
fi ; \
fi ; \
done']
        logging.debug(f'Executing "{cmd}" in directory "{src_dir}"')
        subprocess.check_call(cmd)
        html_man_dir = src_dir / "doc" / "man" / "gen" / "html"
    else:
        # Nothing to process for this release.
        return


def copy_pdfs(src_dir: Path, dst_dir: Path):
    # Find pdfs. Different releases put pdfs in different places.
    pdfs = []
    for d in ["doc", "pdf", "pdfs"]:
        path = src_dir / d
        if path.exists():
            pdfs += find_files(path, extension="pdf")

    # Copy pdfs
    for pdf in pdfs:  # type: Path
        pdf = pdf.resolve()

        # Get part of path that is after doc_dirname
        # ex. /src/dir/path/doc_dirname/some/file.pdf -> some/file.pdf
        parts = Path(str(pdf)[len(str(src_dir)) + 1:]).parts[1:]
        if parts[0] in ["internal", "old"]:
            continue  # Ignore internal and old pdfs
        if parts[0] in ["pdf", "pdfs"]:
            parts = parts[1:]
        path_frag = "/".join(parts)

        # Copy pdf to dst_dir/path_frag
        dst = Path(dst_dir, path_frag).absolute()
        os.makedirs(str(dst.parent), exist_ok=True)
        logging.debug(f"Copying {pdf} -> {dst}")
        shutil.copy2(str(pdf), str(dst))


def gen_releases_index():
    """
    Generates example.com/releases/index.html which redirects to
    example.com/releases/latest/index.html
    """
    template = jinja_env.get_template("releases.index.html")
    index = template.render(url="latest")  # always latest until someone has a "better" idea
    with open(args.outputdir / "index.html", "w") as fd:
        fd.write(index)


def gen_releases_all_index(latest_release: str, git_tags):
    """
    Generates example.com/releases/all/index.html which provides a listing of
    all releases for which docs are available.
    """
    logging.info(f"Generating {args.outputdir}/all/index.html")

    # Every directory under OUTPUTDIR is a released version. Gather releases and sort them.
    releases = []
    for item in args.outputdir.iterdir():
        if item.is_dir() and item.name in git_tags:
            releases.append(item.name)
    releases = sort_tags(releases)

    # Make links for each release
    releases_links = []
    for release in releases:
        url = f"../{release}"
        if release == latest_release:
            release = release + " (latest release)"
        releases_links.append(UrlLink(name=release, url=url))

    # Render index.html and save it
    template = jinja_env.get_template("releases-all.index.html")
    index = template.render(develop_url="../develop", releases=releases_links)
    outdir = args.outputdir / "all"
    os.makedirs(str(outdir), exist_ok=True)
    with open(outdir / "index.html", "w") as fd:
        fd.write(index)


def gen_release_index(tag: str, is_latest=False):
    """
    Generates the index.html file for each release. This html page is made up
    of multiple templates.
    The layout template is release.index.html, which organizes the content the
    other templates provide.
    Beyond this, each release is made up of either old-main-documentation.html or
    main-documentation.html, and project-section.html.
    """
    release_dir = args.outputdir / tag
    man_dir = release_dir / "man"
    pdf_dir = release_dir / "docs"
    rst_dir = release_dir / "rst"
    # At some point as old docs get retired, this check will
    # probably need to be extended to look for rst_dir as well.
    if not pdf_dir.exists():
        return
    logging.info(f"Generating {release_dir}/index.html")

    # Generate a list of projects having RST documentation.
    rst_projects = list()
    if rst_dir.exists():
        rst_projects = os.listdir(rst_dir)

    def _fix_file_name(file_name: str):
        """Standardize file names across all the releases, sigh."""
        fname = file_name.lower()
        if fname in [
            "opencpi installation", "opencpi user", "opencpi application development",
            "opencpi component development",
            "opencpi rcc development", "opencpi hdl development", "opencpi platform development"
        ]:
            return file_name + " Guide"
        elif fname.endswith("getting started"):
            return file_name + " Guide"
        elif fname == "ide user":
            return "AV GUI User Guide"
        elif fname.startswith("briefing"):
            chunks = fname.split()
            chunks[1] = f"{int(chunks[1]):02d}"
            return " ".join(chunks)
        elif fname.startswith("tutorial"):
            chunks = fname.split()
            if chunks[1].endswith("hw"):
                chunks[1] = f"{int(chunks[1][:-2]):02d}hw"
            else:
                chunks[1] = f"{int(chunks[1]):02d}"
            return " ".join(chunks)
        return file_name

    # Generate dictionary of pdf links organized based on filesystem layout.
    # Links are built relative to release_dir.
    section_data = dict()  # type: Dict[str, SectionData]
    project_names = list()  # type: List[str]
    for root, _, files in os.walk(str(pdf_dir)):
        rootpath = Path(root)

        # Remove $(dirname pdf_dir) common prefix from rootpath:
        #   pdf_dir  = /release_dir/docs
        #   rootpath = /release_dir/docs/some/path
        #   base_url = docs/some/path
        base_url = str(rootpath).replace(str(pdf_dir.parent) + "/", "")
        logging.debug(f"pdf_dir:  {pdf_dir}")
        logging.debug(f"rootpath: {rootpath}")
        logging.debug(f"base_url: {base_url}")

        # Create dict of UrlLinks indexed by pdf name
        file_links = dict()  # type: Dict[str, UrlLink]

        if pdf_dir == rootpath:
            section_name = "main"
            section_title = "Main Documentation"
            # For now, just for the main "opencpi" project.
            file_links["changelog"] = UrlLink(name="Changelog", url=f'https://gitlab.com/opencpi/opencpi/-/blob/{tag}/CHANGELOG.md')
        else:
            # Projects
            section_name = rootpath.name.lower().replace("-", "_")
            section_title = section_name.replace("_", " ").title()
            if section_name == "assets_ts":
                section_title = "Assets TS"
                if Path(rst_dir, section_name, "index.html").exists():
                    file_links[section_name] = UrlLink(name=section_title, url=f"rst/{section_name}/")
            if section_name.startswith("osp_"):
                section_name = section_name[4:]  # remove osp_
                if section_name == "analog":
                    section_title = "Analog OSP Documentation"
                elif section_name == "e3xx":
                    section_title = "E3xx OSP Documentation"
                elif section_name == "plutosdr":
                    section_title = "PlutoSDR OSP Documentation"
                elif section_name == "ettus":
                    section_title = "Ettus OSP Documentation"
                else:
                    section_title = section_title[4:] + " OSP Documentation"
                if Path(f"{rst_dir}/osp_{section_name}/index.html").exists():
                    file_links[section_name] = UrlLink(name=section_title, url=f"rst/osp_{section_name}/")
            elif section_name.startswith("comp_"):
                section_name = section_name[5:]  # remove comp_
                if section_name == "sdr":
                    section_title = "SDR Components Documentation"
                else:
                    section_title = section_title[4:] + " Components Documentation"
                if Path(f"{rst_dir}/comp_{section_name}/index.html").exists():
                    file_links[section_name] = UrlLink(name=section_title, url=f"rst/comp_{section_name}/")
            elif section_title not in ["Tutorials", "Briefings"]:
                section_title += " Project Documentation"
                if Path(rst_dir, section_name, "index.html").exists():
                    file_links[section_name] = UrlLink(name=section_title, url=f"rst/{section_name}/")
            project_names.append(section_name)

        for f in files:
            if f.endswith(".pdf"):
                url = f"{base_url}/{f}"
                name = f[:-4]  # remove '.pdf'
                name = name.replace("_", " ")
                if name.startswith("Briefing") or name.startswith("Tutorial"):
                    file_links[_fix_file_name(name).lower()] = UrlLink(name=name, url=url)
                else:
                    if name.lower().endswith("guide"):
                        name = name[:-6]
                    file_links[name.lower()] = UrlLink(name=_fix_file_name(name), url=url)

        # See if we have man pages. Add a link to main section if so.
        if section_name == "main" and man_dir.exists():
            file_links["man pages"] = UrlLink(name="Man Pages", url="man/")

        # Store all found pdfs for section being processed
        section_data[section_name] = SectionData(name=section_name, title=section_title,
                                                 files=file_links)

    #
    # Now, iterate over the RST projects and add those that have
    # not already been handled in the "Projects" section above.
    # Much code duplication: a refactoring is probably called for.
    #
    # This has to be done outside the above "for" loop, because
    # changing the value of "section_name" while in the middle of
    # the loop is guaranteed to cause problems (duh!).  Luckily,
    # there is no danger of overwriting previous settings of
    # "section_data[section_name]" because, if we are adding RST
    # URLs here, these are projects not previously seen/processed.
    #
    for proj in rst_projects:
        file_links = dict()  # type: Dict[str, UrlLink]
        section_name = proj
        section_title = section_name.replace("_", " ").title()
        if section_name.startswith("osp_"):
            section_name = section_name[4:]  # remove osp_
            if not section_name in section_data:
                if section_name == "analog":
                    section_title = "Analog OSP Documentation"
                elif section_name == "e3xx":
                    section_title = "E3xx OSP Documentation"
                elif section_name == "plutosdr":
                    section_title = "PlutoSDR OSP Documentation"
                elif section_name == "ettus":
                    section_title = "Ettus OSP Documentation"
                else:
                    section_title = section_title[4:] + " OSP Documentation"
                file_links[section_name] = UrlLink(name=section_title, url=f"rst/osp_{section_name}/")
                project_names.append(section_name)
                section_data[section_name] = SectionData(name=section_name, title=section_title,
                                                         files=file_links)
        elif section_name.startswith("comp_"):
            section_name = section_name[5:]  # remove comp_
            if not section_name in section_data:
                if section_name == "sdr":
                    section_title = "SDR Components Documentation"
                else:
                    section_title = section_title[4:] + " Components Documentation"
                file_links[section_name] = UrlLink(name=section_title, url=f"rst/comp_{section_name}/")
                project_names.append(section_name)
                section_data[section_name] = SectionData(name=section_name, title=section_title,
                                                         files=file_links)
        elif not section_name in section_data:
            section_title += " Project Documentation"
            file_links[section_name] = UrlLink(name=section_title, url=f"rst/{section_name}/")
            project_names.append(section_name)
            section_data[section_name] = SectionData(name=section_name, title=section_title,
                                                     files=file_links)

    # The "project-section.html" Jinja template accomplishes the magic of
    # replacing plain section titles with URLs having the same displayed
    # text and pointing to the RST docs for that section (if present).

    # Render each section (main is rendered last)

    project_section = jinja_env.get_template("project-section.html")
    rendered_sections = dict()
    for data in section_data.values():
        if data.name != "main":
            rendered_sections[data.name] = project_section.render(
                section_title=data.title, section_name=data.name, links=data.files
            )

    # Render main last as it needs data from other sections
    data = section_data["main"]
    if tag in ["v1.0.0"]:
        old_main_section = jinja_env.get_template("old-main-documentation.html")
        rendered_sections[data.name] = old_main_section.render(section_title=data.title,
                                                               links=data.files)
    else:
        # Main section needs some files from assets, briefings, and tutorials
        assets = section_data.get("assets")
        briefings = section_data.get("briefings")
        tutorials = section_data.get("tutorials")
        main_section = jinja_env.get_template("main-documentation.html")
        rendered_sections[data.name] = main_section.render(
            section_title=data.title, section_name=data.name, links=data.files, assets=assets,
            briefings=briefings, tutorials=tutorials, project_names=project_names
        )

    # Stitch it all together
    template = jinja_env.get_template("release.index.html")
    index = template.render(title=tag, sections=rendered_sections, is_latest=is_latest,
                            releases_all_url="../../releases/all/")
    with open(release_dir / "index.html", "w") as fd:
        fd.write(index)


# Util functions ##############################################################

def download_osp(osp: str):
    osp_path = OCPI_OSPDIR / osp
    if osp_path.exists():
        logging.info(f"Updating existing OSP {osp} located at {osp_path}")
        cmd = ["git", "--git-dir", str(osp_path / ".git"), "fetch"]
        logging.debug(f"Executing cmd: {cmd}")
        subprocess.check_call(cmd)
    else:
        # We want the full repo as it will be used later when building each tagged release
        logging.info(f"Downloading OSP {osp} to {osp_path}")
        # Force local branch to be "develop", which should
        # be the default branch (pointed to by HEAD) anyway.
        cmd = ["git", "clone", "--branch", "develop", f"https://gitlab.com/opencpi/osp/{osp}.git", osp_path]
        logging.debug(f"Executing cmd: {cmd}")
        subprocess.check_call(cmd)


def download_comp(comp: str):
    comp_path = OCPI_COMPDIR / comp
    if comp_path.exists():
        logging.info(f"Updating existing COMP {comp} located at {comp_path}")
        cmd = ["git", "--git-dir", str(comp_path / ".git"), "fetch"]
        logging.debug(f"Executing cmd: {cmd}")
        subprocess.check_call(cmd)
    else:
        # We want the full repo as it will be used later when building each tagged release
        logging.info(f"Downloading COMP {comp} to {comp_path}")
        # Force local branch to be "develop", which should
        # be the default branch (pointed to by HEAD) anyway.
        cmd = ["git", "clone", "--branch", "develop", f"https://gitlab.com/opencpi/comp/{comp}.git", comp_path]
        logging.debug(f"Executing cmd: {cmd}")
        subprocess.check_call(cmd)


def find_file(search_dir: Union[str, Path], filename: str,
              case_sensitive=True) -> Union[Path, None]:
    if not isinstance(search_dir, Path):
        search_dir = Path(str(search_dir))
    orig_filename = filename
    if not case_sensitive:
        filename = filename.lower()
    for root, _, files in os.walk(str(search_dir)):
        for file in files:
            if not case_sensitive:
                file = file.lower()
            if file == filename:
                return Path(root, orig_filename)
    return None


def find_files(search_dir, extension=None, recursive=True) -> List[Path]:
    if not isinstance(search_dir, Path):
        search_dir = Path(str(search_dir))
    pdfs = []
    if extension is not None:
        extension = "." + extension
    for root, _, files in os.walk(str(search_dir)):
        for file in files:
            if extension is None or file.lower().endswith(extension):
                pdfs.append(Path(root, file))
        if not recursive:
            break
    return pdfs


def get_tags(git_dir: Path) -> List[str]:
    cmd = ["git", "--git-dir", str(git_dir.resolve()), "tag", "-l", "v*"]
    logging.debug(f"Executing cmd: {cmd}")
    tags = subprocess.check_output(cmd).decode().strip("\n").split("\n")
    tags = sort_tags(tags, reverse=True)  # reverse required for proper filtering later
    logging.debug(f"sorted tags: {tags}")

    # Filter releases by using "latest" patch release
    # Ex. if 1.6.1 and 1.6.0 exists, then 1.6.0 will be removed
    # This relies on the tags already being sorted in "latest to oldest" order
    filtered_tags = list()
    minor_releases = set()
    for tag in tags:
        minor = tag[:tag.index(".", tag.index(".") + 1)]
        if minor not in minor_releases:
            minor_releases.add(minor)
            filtered_tags.append(tag)

    logging.debug(f"latest tags: {filtered_tags}")
    filtered_tags.reverse()  # put in oldest -> newest order
    return filtered_tags


def get_branches(git_dir: Path) -> List[str]:
    # Get list of branches
    cmd = ["git", "--git-dir", str(git_dir.resolve()), "branch", "--no-color"]
    branches = [
        x.replace("*", "").strip() for x in
        subprocess.check_output(cmd).decode().strip("\n").split("\n")
    ]

    # Resolve detached branches to their symbolic name. This is needed because
    # of how gitlab runner checks out branch under test. This will either be a
    # sha or a tag.
    pat = re.compile(r"detached from ([^)]+)")
    for i, branch in enumerate(branches):
        match = pat.search(branch)
        if match is not None:
            sha = match.group(1)
            branches[i] = get_name_rev(git_dir, sha)

    # Ensure no duplicates
    return list(set(branches))


def get_name_rev(git_dir: Path, rev: str):
    cmd = ["git", "--git-dir", str(git_dir.resolve()), "name-rev", "--name-only",
           "--no-undefined", rev]
    name = subprocess.check_output(cmd).decode().strip("\n")
    if len(name):
        return name
    raise RuntimeError(f"Could not resolve {rev} to a branch name")


def sort_tags(tags: List[str], reverse: bool = False):
    def _semver_sort(x: str, y: str):
        # Remove 'v' from start of string
        x = x[1:]
        y = y[1:]

        # Extended semver strings have extra info after the hyphen
        x_extra_a = ""
        x_extra_b = 0
        y_extra_a = ""
        y_extra_b = 0
        if "-" in x:
            x, x_extra = x.split("-")
            x_extra_a, x_extra_b = x_extra.split(".")
            x_extra_b = int(x_extra_b)
        if "-" in y:
            y, y_extra = y.split("-")
            y_extra_a, y_extra_b = y_extra.split(".")
            y_extra_b = int(y_extra_b)

        # Split into major, minor, patch, and extra
        x_major, x_minor, x_patch = [int(n) for n in x.split(".")]
        y_major, y_minor, y_patch = [int(n) for n in y.split(".")]

        # Do numerical comparison
        if x_major == y_major:
            if x_minor == y_minor:
                if x_patch == y_patch:
                    if x_extra_a == y_extra_a:
                        return x_extra_b - y_extra_b
                    if x_extra_a == "":
                        return 1
                    if y_extra_a == "":
                        return -1
                    return 1 if x_extra_a > y_extra_a else -1
                return x_patch - y_patch
            return x_minor - y_minor
        return x_major - y_major

    return sorted(tags, key=cmp_to_key(_semver_sort), reverse=reverse)


if __name__ == "__main__":
    def _find_root(x: Path):
        while not x.name.startswith("opencpi") and len(x.parts) != 1:
            x = x.parent
        return x


    # Setup some paths
    CURDIR = Path(os.curdir).resolve()
    OCPI_ROOT = _find_root(Path(__file__).resolve())
    OCPI_TEMPLATES = OCPI_ROOT / "doc" / "generator" / "templates"
    default_webroot = OCPI_ROOT / ".public"
    default_outputdir = default_webroot / "releases"
    default_repodir = OCPI_ROOT

    # Setup argparse
    parser = argparse.ArgumentParser(formatter_class=argparse.RawTextHelpFormatter)
    parser.add_argument("-c", "--clean", metavar="RELEASE", action="append", default=[],
                        help="Remove RELEASE before generating pdfs. Can be specified multiple "
                             "times.")
    parser.add_argument("-l", "--list-releases", action="store_true",
                        help="List available releases and branches for the git repo specified by "
                             "--repodir",
                        )
    parser.add_argument("-o", "--outputdir",
                        help="Output directory. OUTPUTDIR must be based off WEBROOT.\n"
                             f"Default: {default_outputdir}")
    parser.add_argument("-r", "--repodir", help="Path to the root of the repo to build docs for.\n"
                                                f"Default: {OCPI_ROOT}")
    parser.add_argument("-v", "--verbose", action="store_true", help="Increase output verbosity")
    parser.add_argument("-w", "--webroot",
                        help="The WEBROOT is the base directory that a web server uses when\n"
                             "serving files for a particular site.\n"
                             "OUTPUTDIR must be based off WEBROOT.\n"
                             f"Default: {default_webroot}")
    parser.add_argument("--all", action="store_true", help="Build docs for all releases + develop")
    parser.add_argument("--clean-all", action="store_true",
                        help="Remove OUTPUTDIR before generating pdfs")
    parser.add_argument("releases", nargs="*",
                        help="Release(s) to build. Must be a valid git tag, branch, or 'HEAD'")
    parser.epilog = (
        "Examples:\n"
        f"  {parser.prog} --all                  Build all releases + develop\n"
        f"  {parser.prog} --all --clean-all      Clean and build all + develop\n"
        f"  {parser.prog} --all --clean develop  Same as --all, but only clean develop\n"
        f"  {parser.prog} --clean develop        Clean and build develop\n"
        f"  {parser.prog} develop                Build develop\n"
        f"  {parser.prog} HEAD                   Build checked out branch"
    )

    args = parser.parse_args()

    # Setup logging
    logging.basicConfig(format="%(asctime)s:%(levelname)s: %(message)s", level=logging.INFO)
    if args.verbose:
        logging.getLogger().setLevel(logging.DEBUG)

    # Setup repodir
    if args.repodir:
        args.repodir = Path(args.repodir).resolve()
    else:
        args.repodir = default_repodir
    OCPI_OSPDIR = args.repodir / "projects" / "osps"
    OCPI_COMPDIR = args.repodir / "projects"

    # Get list of tags and checked out branches
    GIT_TAGS = get_tags(args.repodir / ".git")
    GIT_BRANCHES = get_branches(args.repodir / ".git")
    if args.list_releases:
        logging.info("Valid Releases:")
        logging.info(f"  Tags: {GIT_TAGS}")
        logging.info(f"  Branches: {GIT_BRANCHES}")
        exit(0)
    else:
        logging.debug(f"Tags: {GIT_TAGS}")
        logging.debug(f"Branches: {GIT_BRANCHES}")

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
            logging.critical(
                "A release to build must be specified or use '--all' to build all releases"
            )
            exit(1)
    elif len(args.clean) and len(args.releases):
        # add items being cleaned to items being built
        args.releases = list(set(args.releases + args.clean))

    # Setup webroot and outputdir
    if args.webroot is None:
        args.webroot = default_webroot
    else:
        args.webroot = Path(args.webroot)
        default_outputdir = args.webroot / "releases"
    if args.outputdir is None:
        args.outputdir = default_outputdir
    else:
        args.outputdir = Path(args.outputdir)
    if args.webroot.is_absolute() ^ args.outputdir.is_absolute():
        logging.critical(
            f"WEBROOT ({args.webroot}) and OUTPUTDIR ({args.outputdir}) must both either be "
            "absolute or relative paths, not a mix."
        )
        exit(1)
    if not str(args.outputdir).startswith(str(args.webroot)):
        logging.critical(
            f"OUTPUTDIR ({args.outputdir}) must be a child of WEBROOT ({args.webroot})"
        )
        exit(1)
    os.makedirs(str(args.outputdir), exist_ok=True)
    args.webroot.resolve()
    args.outputdir.resolve()

    # Setup jinja2
    jinja_env = Environment(loader=FileSystemLoader(str(OCPI_TEMPLATES)))

    main()
