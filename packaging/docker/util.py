import logging
import re
import subprocess
from pathlib import Path
from typing import Dict, List

logger = logging.getLogger(__name__)

# Forward declare to allow type hinting
class Image(object): pass


class Platforms(object):
    def __init__(self, root_dir: str):
        self._root_dir = Path(root_dir).resolve()

        self._platforms = dict()  # type: Dict[str,Platform]

    def __str__(self):
        rv = "root_dir: {}\n".format(self._root_dir)
        rv += "platforms:\n"
        for p in self._platforms:
            rv += "  {}:\n".format(p)
            for line in str(self._platforms[p]).split("\n"):
                rv += "    {}\n".format(line)
        return rv.rstrip("\n")

    def discover(self) -> None:
        for x in self._root_dir.iterdir():
            if not x.is_dir():
                continue
            if x.name.startswith((".", "__")):
                continue
            platform = Platform(x)
            self._platforms[platform.name] = platform

    def build_image(self, platform: str, image: str, build_deps: bool) -> None:
        self._platforms[platform].build_image(image=image, build_deps=build_deps)

    def discover_all_images(self, **kwargs) -> None:
        for platform in self._platforms.values():
            platform.discover_images(**kwargs)

    def get_image(self, platform: str, image: str) -> Image:
        return self._platforms[platform].get_image(image)

    def get_platform_image_names(self, platform: str) -> List[str]:
        return self._platforms[platform].get_image_names()

    def get_platform_names(self) -> List[str]:
        return list(self._platforms.keys())

    def push_image(self, platform: str, image: str) -> None:
        self._platforms[platform].push_image(image=image)


class Platform(object):
    def __init__(self, path: Path):
        self._path = path.resolve()

        self._images = dict()  # type: Dict[str,Image]

    def __str__(self):
        rv = "name: {}\n".format(self.name)
        rv += "path: {}\n".format(self._path.as_posix())
        rv += "images:\n"
        for image in self._images:
            rv += "  {}:\n".format(image)
            for line in str(self._images[image]).split("\n"):
                rv += "    {}\n".format(line)
        return rv.rstrip("\n")

    @property
    def name(self) -> str:
        return self._path.name

    def build_image(self, image: str, build_deps: bool) -> None:
        img = self._images[image]
        if build_deps:
            if img.dependency_name.find("-") != -1:  # most likely NOT our image
                logging.info("Building dependency {} for {}".format(img.dependency_name, img.name))
                if logger.level == logging.DEBUG:
                    print(img)
                self.build_image(image=img.dependency_subname, build_deps=build_deps)
        logging.info("Building image {}".format(img.name))
        if logger.level == logging.DEBUG:
            print(img)
        img.build()

    def discover_images(self, **kwargs) -> None:
        build_args = kwargs.pop("build_args")
        no_cache = kwargs.pop("no_cache")
        pull_always = kwargs.pop("pull_always")
        repo = kwargs.pop("repo")
        tag = kwargs.pop("tag")
        for x in self._path.iterdir():
            if x.is_dir():
                image = Image(x, build_args=build_args, no_cache=no_cache, pull_always=pull_always, repo=repo, tag=tag)
                self._images[image.subname] = image

    def get_image(self, image: str) -> Image:
        if len(self._images):
            return self._images[image]

    def get_image_names(self) -> List[str]:
        if len(self._images):
            return list(self._images.keys())

        # Do a "light" discovery as discover_images() hasn't been called yet
        names = list()
        for x in self._path.iterdir():
            if x.is_dir():
                names.append(x.name)
        return names

    def push_image(self, image: str) -> None:
        self._images[image].push()


class Image(object):
    def __init__(self, path: Path, build_args: List[str], no_cache: bool, pull_always: bool, repo: str, tag: str):
        self._build_args = build_args
        self._path = path.resolve()
        self._repo = repo.rstrip("/")
        self._tag = tag

        self._additional_build_args = list()
        for arg in self._build_args:
            self._additional_build_args += ["--build-arg", arg]
        if no_cache:
            self._additional_build_args.append("--no-cache")
        if pull_always:
            self._additional_build_args.append("--pull-always")
        self._build_context = self._path
        self._dockerfile = self._path / "Dockerfile"
        self._platform = self._path.parent.name

        # Dockerfile may contain additional image settings
        # These are set when parsing Dockerfile
        self._available_build_args = dict()
        self._dependency = ""
        self._dependency_tag = ""
        self._parse_dockerfile()

        # These should be set by now
        if self._dependency == "" or self._dependency is None:
            raise RuntimeError("Could not determine image dependency. Is FROM directive missing?")
        if self._dependency_tag == "" or self._dependency_tag is None:
            raise RuntimeError("Could not determine image dependency tag.")

    def __str__(self):
        rv = "full_name:             {}\n".format(self.full_name)
        rv += "dependency:            {}\n".format(self.dependency)
        rv += "dockerfile:            {}\n".format(self._dockerfile)
        rv += "build_context:         {}\n".format(self._build_context)
        rv += "additional build args: {}\n".format(self._additional_build_args)
        rv += "available build args:  {}\n".format(self._available_build_args)
        return rv.rstrip("\n")

    @property
    def dependency(self) -> str:
        if self._dependency_tag == "":
            return "{}".format(self._dependency)
        return "{}:{}".format(self._dependency, self._dependency_tag)

    @property
    def dependency_name(self) -> str:
        return self._dependency.split("/")[-1]

    @property
    def dependency_subname(self) -> str:
        return self.dependency_name.split("-")[-1]

    @property
    def full_name(self) -> str:
        return "{}/{}:{}".format(self._repo, self.name, self._tag)

    @property
    def name(self) -> str:
        return "{}-{}".format(self._platform, self.subname)

    @property
    def subname(self) -> str:
        return self._path.name

    def build(self) -> None:
        logger.debug("Building image:   {}:{}".format(self.name, self._tag))
        logger.debug("Repo:             {}".format(self._repo))
        logger.debug("Dockerfile:       {}".format(self._dockerfile))
        args = [
            "podman", "build",
            "--tag", self.full_name,
            "--file", self._dockerfile.as_posix(),
        ]
        args += self._additional_build_args
        args.append(self._build_context.as_posix())  # must be last
        subprocess.check_call(args)

    def push(self) -> None:
        logger.debug("Pushing image {}".format(self.name))
        subprocess.check_call([
            "podman", "push", self.full_name
        ])

    def _parse_dockerfile(self) -> None:
        """
        Parses dockerfile for additional configuration and overrides of supported image properties.

        Parsed properties:
            - image dependency and tag
            - all ARGs

        Optional configuration directives:
            - build_context: Define build context used when building image. Build context is a path to a directory
              containing files to expose to the build environment. By default, it is the directory containing
              the Dockerfile for the image being built.
            - build_mount: Additional host volumes to expose to build environment. Same format as '-v' flag.
              Can specify multiple times for each additional build mount.
        :return: None
        """

        # path to root of opencpi source tree
        opencpi_root = self._find_root().resolve().as_posix()

        logging.debug("Loading dockerfile: {}".format(self._dockerfile.as_posix()))
        with open(self._dockerfile.as_posix(), "r") as fd:
            lines = fd.readlines()

        # parse build context
        logging.debug("Looking for build_context")
        pattern = re.compile(r"^#\s+-\s+build_context:\s+(.+)$", re.IGNORECASE)
        for line in lines:
            match = pattern.match(line)
            if match is None:
                continue
            build_context = match.group(1)
            if build_context.startswith("..."):
                build_context = build_context.replace("...", opencpi_root, 1)
            if not Path(build_context).exists():
                raise RuntimeError("Build context doesn't exist or is not readable: {}".format(build_context))
            logging.debug("Found build_context: {}".format(build_context))
            self._build_context = build_context
            break

        # parse build mount(s)
        pattern = re.compile(r"^#\s+-\s+build_mount:\s+(.+)$", re.IGNORECASE)
        for line in lines:
            match = pattern.match(line)
            if match is None:
                continue
            build_mount = match.group(1)
            if build_mount.startswith("..."):
                build_mount = build_mount.replace("...", opencpi_root, 1)
            host_path = build_mount.split(":")[0]
            if not Path(host_path).exists():
                raise RuntimeError(
                    "Host part of build mount doesn't exist or is not readable: {}".format(host_path)
                )
            logging.debug("Found build_mount: {}".format(build_mount))
            self._additional_build_args += ["-v", build_mount]
            # no break as we accept multiple build_mount args

        # parse all ARGs
        logging.debug("Parsing all ARGs")
        pattern = re.compile(r"^ARG\s+(.+)=(.+)$")
        for line in lines:
            match = pattern.match(line)
            if match is not None:
                logging.debug("Found ARG {}={}".format(match.group(1), match.group(2)))
                self._available_build_args[match.group(1)] = match.group(2)

        # parse dependency
        logging.debug("Parsing image dependency")
        pattern = re.compile(r"^FROM\s+(.+)$", re.IGNORECASE)
        tag = None
        for line in lines:
            match = pattern.match(line)
            if match is None:
                continue
            dependency = match.group(1)
            if ":" in dependency:
                dependency, tag = match.group(1).split(":")
            logging.debug("Found dependency: {}".format(dependency))
            self._dependency = dependency
            break

        # tag can be multiple things, figure out what it is and set appropriately
        if tag is None:
            self._dependency_tag = "latest"
        elif tag == "$DEPENDENCY_TAG":
            # set to empty string just in case it was set by accident somewhere else
            self._dependency_tag = ""
            # favor commandline value, if specified
            for build_arg in self._build_args:
                if build_arg.startswith("DEPENDENCY_TAG"):
                    self._dependency_tag = build_arg.split("=")[1]
                    break
            # if still the empty string, it wasn't specified on commandline.
            # use the value defined in the dockerfile.
            if self._dependency_tag == "":
                self._dependency_tag = self._available_build_args.get("DEPENDENCY_TAG", "")
                if self._dependency_tag == "":
                    raise RuntimeError("$DEPENDENCY_TAG used in Dockerfile but no default was defined")
        else:
            # use value specified on FROM line
            self._dependency_tag = tag

    def _find_root(self) -> Path:
        logging.debug("Finding root of OpenCPI source tree")
        x = Path(self._path).resolve().parent
        while len(x.parts) != 1:
            # Look for ".gitlab-ci.yml" file which is at the root of the project
            if ".gitlab-ci.yml" in [i.name for i in x.iterdir() if i.is_file()]:
                logging.debug("Found OpenCPI root: {}".format(x.as_posix()))
                return x
            x = x.parent
        raise RuntimeError("Couldn't find root of OpenCPI source tree")
