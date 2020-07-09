#!/usr/bin/env python3
import subprocess
import sys
from pathlib import Path

if __name__ != "__main__":
    print("This script is not a module and is meant to be executed!", file=sys.stderr)
    exit(1)

my_path = Path(__file__).resolve()
my_dir = my_path.parent

# Discover image build scripts
base_images = []
other_images = []
for f in list(my_dir.glob("**/image.py")):
    if f.parent.name == "base":
        base_images.append(f)
    else:
        other_images.append(f)

# Build all base images first as other images depend on these
for f in base_images:
    subprocess.check_call([f.as_posix(), "build"])  # Note: tag will be 'latest'
    print()  # for readability

# Build rest of images
for f in other_images:
    subprocess.check_call([f.as_posix(), "build"])  # Note: tag will be 'latest'
    print()  # for readability
