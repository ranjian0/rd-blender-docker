"""
A script to automatically generate Dockerfiles based on a manifest
To run this simply `python generate.py --m manifest.json`
For manifest structure see manifest.json

Written by juniorxsound <https://orfleisher.com>
"""

import os
import json
import getpass
import argparse
from datetime import datetime


def lookahead(iterable: list):
    """Pass through all values from the given iterable, augmented by the
    information if there are more values to come after the current one
    (True), or if it is the last value (False).

    Thanks to the fantastic https://stackoverflow.com/questions/1630320/what-is-the-pythonic-way-to-detect-the-last-element-in-a-for-loop
    """
    # Get an iterator and pull the first value.
    it = iter(iterable)
    last = next(it)
    # Run the iterator to exhaustion (starting from the second value).
    for val in it:
        # Report the *previous* value (more to come).
        yield last, True
        last = val
    # Report the last value.
    yield last, False


def create_dockerfile(base_os: str,
                      title: str,
                      author: str,
                      env: list,
                      deps: list,
                      blender_download_url: str,
                      workdir: str) -> str:
    """
    Create a stringified Dockerfile based on arguments provided
    """
    dockerfile = "# Dockerfile autogenerated on {} by {} \n".format(
        datetime.now().strftime("%m/%d/%Y, %H:%M:%S"), getpass.getuser())
    dockerfile += "# Please do not edit this file directly \n\n"

    dockerfile += "FROM {}\n\n".format(base_os)
    dockerfile += "LABEL Author=\"{}\"\n".format(author)
    dockerfile += "LABEL Title=\"{}\"\n\n".format(title)

    dockerfile += "# Enviorment variables\n"
    for enviorment_variable in env:
        dockerfile += "ENV {}\n".format(enviorment_variable)
    dockerfile += "\n"

    dockerfile += "# Install dependencies\n"
    dockerfile += "RUN apt-get update && apt-get install -y \ \n"
    for dependency, has_more in lookahead(deps):
        is_multiline = " \ " if has_more else ""
        dockerfile += "\u0009{}{}\n".format(dependency, is_multiline)
    dockerfile += "\n"

    dockerfile += "# Download and install Blender\n"
    dockerfile += "RUN wget {} \ \n".format(blender_download_url)
    dockerfile += "\u0009&& tar -xvjf {} --strip-components=1 -C /bin \ \n".format(
        blender_download_url.split("/")[-1])
    dockerfile += "\u0009&& rm -rf {} \ \n".format(
        blender_download_url.split("/")[-1])
    dockerfile += "\u0009&& rm -rf {} \n\n".format(
        blender_download_url.split("/")[-1].split(".tar.bz2")[0])

    dockerfile += "# Download the Python source since it is not bundled with Blender\n"
    dockerfile += "RUN wget https://www.python.org/ftp/python/3.6.8/Python-3.6.8.tgz \ \n"
    dockerfile += "\u0009&& tar -xzf Python-3.6.8.tgz \ \n"
    dockerfile += "\u0009&& cp Python-3.6.8/Include/* $BLENDER_PATH/python/include/python3.7m/ \ \n"
    dockerfile += "\u0009&& rm -rf Python-3.6.8.tgz \ \n"
    dockerfile += "\u0009&& rm -rf Python-3.6.8 \n\n"

    dockerfile += "# Blender comes with a super outdated version of numpy (which is needed for matplotlib / opencv) so override it with a modern one\n"
    dockerfile += "RUN rm -rf ${BLENDER_PATH}/python/lib/python3.7/site-packages/numpy \n\n"

    dockerfile += "# Must first ensurepip to install Blender pip3 and then new numpy\n"
    dockerfile += "RUN ${BLENDERPY} -m ensurepip && ${BLENDERPIP} install --upgrade pip && ${BLENDERPIP} install numpy\n\n"

    dockerfile += "# Set the working directory\n"
    dockerfile += "WORKDIR {}".format(workdir)

    return dockerfile


if __name__ == "__main__":

    # @todo should be a CLI argument
    output_folder = "./dist/"

    # Open the manifest file and start generating Dockerfiles
    with open("./manifest.json", "r") as r:
        manifest = json.load(r)

        for image in manifest["images"]:
            # Check if folder exists and if not create one
            if (os.path.exists(output_folder + image["tag"]) is False):
                os.mkdir(output_folder + image["tag"])

            dockerfile = create_dockerfile(
                base_os=image["base_os_image"],
                title=manifest["title"],
                author=manifest["author"],
                env=manifest["env"] + image["env"],
                deps=manifest["deps"],
                blender_download_url=image["blender_download_url"],
                workdir="/"
            )

            with open("{}/Dockerfile".format(output_folder + image["tag"]), "w") as w:
                w.write(dockerfile)
