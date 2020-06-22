import argparse
import subprocess

from pathlib import Path


class Container(object):
    REGISTRY = "registry.gitlab.com/opencpi/opencpi/"

    def __init__(self, path: str, tag: str):
        self.path = Path(path).resolve()
        self.tag = tag

        self.build_context = self.path.parent
        self.dockerfile = self.path.parent / "Dockerfile"
        self.name = self.path.parent.name
        self.ocpi_root = self._find_root()
        self.platform = self.path.parent.parent.name

    def build(self):
        print("Building image:   {}".format(self.image_name()))
        print("Using Dockerfile: {}".format(self.dockerfile))
        subprocess.check_call([
            "podman", "build",
            "--pull-always",
            "--tag", self.image_name(),
            "--file", self.dockerfile,
            self.build_context,
        ])

    def image_name(self) -> str:
        return self.REGISTRY + "{platform}-{name}:{tag}".format(
            platform=self.platform, name=self.name, tag=self.tag
        )

    def push(self):
        print("Pushing image {}".format(self.image_name()))
        subprocess.check_call([
            "podman", "push", self.image_name()
        ])

    @staticmethod
    def _find_root() -> Path:
        x = Path(__file__).resolve().parent
        while len(x.parts) != 1:
            # Look for ".gitlab-ci.yml" file which is at the root of the project
            if ".gitlab-ci.yml" in [i.name for i in x.iterdir() if i.is_file()]:
                return x
            x = x.parent
        raise RuntimeError("Couldn't find root of OpenCPI source tree")


class Parser(object):
    def __init__(self):
        # Common arguments for all image.py scripts
        self.parser = argparse.ArgumentParser()
        self.parser.add_argument("-t", "--tag", default="latest",
                                 help="Tag to use for docker image [default: latest]")
        self.parser.add_argument("action", choices=["build", "push"], help="Action to perform")

    def add_argument(self, *args, **kwargs):
        self.parser.add_argument(*args, **kwargs)

    def parse_args(self) -> argparse.Namespace:
        return self.parser.parse_args()
