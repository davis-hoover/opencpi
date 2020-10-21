#!/usr/bin/env python3
import argparse
import logging
import subprocess
import sys
from datetime import date
from pathlib import Path

# Our imports
from util import Platforms

if __name__ != "__main__":
    print("This script is not a module and is meant to be executed!", file=sys.stderr)
    exit(-1)

# Setup logger (further config is done later)
logging.basicConfig(level=logging.INFO)

# Define some necessary "constants"
MY_PATH = Path(__file__).resolve()
MY_DIR = MY_PATH.parent
DEFAULT_REPO = "registry.gitlab.com/opencpi/opencpi"
DEFAULT_TAG = date.today().strftime("%Y%m%d")

# Discover platforms
platforms = Platforms(root_dir=MY_DIR)
platforms.discover()  # this is needed for dynamic help output


def parse_args():
    parser = argparse.ArgumentParser(
        description="Builds the specified image for the specified platform, ignoring dependent images.\n"
                    "To (re)build an image and it's dependencies use the '--build-deps' flag.\n\n"
                    "Additional help per discovered platform is available via:\n"
                    "  {script_name} IMAGE --help.".format(script_name=MY_PATH.name),
    )
    parser.formatter_class = argparse.RawDescriptionHelpFormatter
    parser.add_argument(
        "--all",
        help="(NOT IMPLEMENTED) build all discovered images, honoring image dependencies",
        action="store_true"
    )
    parser.add_argument(
        "--build-arg",
        help="Override an ARG that is defined in the Dockerfile. Can be specified multiple times.",
        action="append",
        default=[]
    )
    parser.add_argument(
        "--build-deps",
        help="(re)builds the image this image depends on, ensuring this image and all dependent images are as "
             "up-to-date as possible",
        action="store_true"
    )
    parser.add_argument(
        "--list",
        help="list images for specified platform",
        metavar="PLATFORM"
    )
    parser.add_argument(
        "--list-all",
        help="list all discovered platforms and their images",
        action="store_true"
    )
    parser.add_argument(
        "--local",
        help="do not pass '--pull-always' when building an image. This will allow the local cache to be used when "
             "building an image. Usually only used for local development/testing to prevent the need to push an image "
             "to the repo. just to pull it again. Should NOT be used for CI/CD purposes as the local cache cannot be "
             "guaranteed to be up-to-date.",
        action="store_true"
    )
    parser.add_argument(
        "--no-cache",
        help="do not use existing cached images for the container build. Build from the start with a new set of "
             "cached layers.",
        action="store_true"
    )
    parser.add_argument(
        "--push",
        help="push image after building. Note: You must `podman login <REPO>` for this to work",
        action="store_true"
    )
    parser.add_argument(
        "--repo",
        help="image repository [default: {}]".format(DEFAULT_REPO),
        default=DEFAULT_REPO
    )
    parser.add_argument(
        "--tag",
        help="image tag [default: {}]".format(DEFAULT_TAG),
        default=DEFAULT_TAG
    )
    parser.add_argument(
        "-v", "--verbose",
        help="be verbose",
        action="store_true"
    )

    # Platform subparser
    subparsers = parser.add_subparsers(
        title="discovered platforms",
        help="platform to build an image for. To see available images, do `{} PLATFORM -h`".format(parser.prog),
        dest="platform"
    )

    # This adds discovered images for each discovered platform
    for platform in sorted(platforms.get_platform_names()):
        images = sorted(platforms.get_platform_image_names(platform))
        subparser = subparsers.add_parser(platform)
        subparser.add_argument(
            "image",
            help="Image to build",
            choices=images
        )
        subparser.add_argument(
            "--info",
            help="Dump image info",
            action="store_true",
            dest="image_info"
        )

    if len(sys.argv) == 1:
        parser.print_help()
        exit(-1)

    return parser.parse_args()


def list_images(platform: str):
    try:
        images = platforms.get_platform_image_names(platform)
        logging.info("Available images for {}: {}".format(platform, ", ".join(images)))
    except KeyError:
        logging.error("Unknown platform '{}'".format(platform))


################################################################################
# Main
################################################################################

# Parse args
args = parse_args()

if args.verbose:
    logging.getLogger().setLevel(logging.DEBUG)

# Finish discovering images now that we have all arguments
platforms.discover_all_images(build_args=args.build_arg, no_cache=args.no_cache, pull_always=not args.local,
                              repo=args.repo, tag=args.tag)

# Handle informational options
if args.list_all:
    print(platforms)  # don't use logger
    exit(0)
if args.list:
    list_images(args.list)
    exit(0)
if args.image_info:
    print(platforms.get_image(args.platform, args.image))
    exit(0)

# Build all images?
if args.all:
    raise NotImplemented("Building all images is not implemented yet")

if args.platform is None:
    logging.error("A platform is required")
    exit(-1)

# If we are pushing, we better be logged in. Check this before building the image.
if args.push:
    # Extract hostname from URL
    n = args.repo.find("/")
    registry = args.repo[:n] if n >= 0 else args.repo
    try:
        subprocess.check_call(["podman", "login", "--get-login", registry], stdout=subprocess.DEVNULL,
                              stderr=subprocess.DEVNULL)
    except subprocess.CalledProcessError:
        logging.error("Not logged in to registry '{}'".format(registry))
        logging.error("Use 'podman login {}' to log in and then try again".format(registry))
        exit(-1)

# Build specified image and optionally push it
platforms.build_image(platform=args.platform, image=args.image, build_deps=args.build_deps)
if args.push:
    platforms.push_image(platform=args.platform, image=args.image)

exit(0)
