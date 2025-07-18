"""
MIT License.

Copyright (c) 2023 - present Vocard Development

Permission is hereby granted, free of charge, to any person obtaining a copy
of this software and associated documentation files (the "Software"), to deal
in the Software without restriction, including without limitation the rights
to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
copies of the Software, and to permit persons to whom the Software is
furnished to do so, subject to the following conditions:

The above copyright notice and this permission notice shall be included in all
copies or substantial portions of the Software.

THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
SOFTWARE.
"""

import argparse
import os
import shutil
import subprocess
import sys
import zipfile
from io import BytesIO

import requests


ROOT_DIR = os.path.dirname(os.path.abspath(__file__))
__version__ = "v2.7.1"

# URLs for update and migration
PYTHON_CMD_NAME = os.path.basename(sys.executable)
GITHUB_API_URL = "https://api.github.com/repos/ChocoMeow/Vocard/releases/latest"
VOCARD_URL = "https://github.com/ChocoMeow/Vocard/archive/"
MIGRATION_SCRIPT_URL = f"https://raw.githubusercontent.com/ChocoMeow/Vocard-Magration/main/{__version__}.py"
IGNORE_FILES = ["settings.json", "logs", "last-session.json"]


class bcolors:
    WARNING = "\033[93m"
    FAIL = "\033[91m"
    OKGREEN = "\033[92m"
    ENDC = "\033[0m"


def check_version(with_msg=False):
    """
    Check for the latest version of the project.

    Args:
        with_msg (bool): option to print the message.

    Returns:
        str: the latest version.
    """
    response = requests.get(GITHUB_API_URL)
    latest_version = response.json().get("name", __version__)
    if with_msg:
        pass
    return latest_version


def download_file(version=None):
    """
    Download the latest version of the project.

    Args:
        version (str): the version to download. If None, download the latest version.

    Returns:
        Response: the downloaded zip file content.
    """
    version = version if version else check_version()
    response = requests.get(VOCARD_URL + version + ".zip")
    if response.status_code == 404:
        sys.exit(1)
    return response


def install(response, version) -> None:
    """
    Install the downloaded version of the project.

    Args:
        response (Response): the downloaded zip file content.
        version (str): the version to install.
    """
    user_input = input(
        f"{bcolors.WARNING}--------------------------------------------------------------------------\n"
        "Note: Before proceeding, please ensure that there are no personal files or\n"
        "sensitive information in the directory you're about to delete. This action\n"
        "is irreversible, so it's important to double-check that you're making the \n"
        f"right decision. {bcolors.ENDC} Continue with caution? (Y/n) "
    )

    if user_input.lower() in ["y", "yes"]:
        zfile = zipfile.ZipFile(BytesIO(response.content))
        zfile.extractall(ROOT_DIR)

        # Remove 'v' from the version string for folder name.
        version_without_v = version.replace("v", "")
        source_dir = os.path.join(ROOT_DIR, f"Vocard-{version_without_v}")
        if os.path.exists(source_dir):
            for filename in os.listdir(ROOT_DIR):
                if filename in [*IGNORE_FILES, f"Vocard-{version_without_v}"]:
                    continue

                filename_path = os.path.join(ROOT_DIR, filename)
                if os.path.isdir(filename_path):
                    shutil.rmtree(filename_path)
                else:
                    os.remove(filename_path)
            for filename in os.listdir(source_dir):
                shutil.move(os.path.join(source_dir, filename), os.path.join(ROOT_DIR, filename))
            os.rmdir(source_dir)
    else:
        pass


def run_migration() -> None:
    """Download, execute, and remove the migration script."""
    confirm = input(
        f"{bcolors.WARNING}WARNING: Please ensure you have taken a backup before proceeding.\n"
        f"Are you sure you want to run the migration? (Y/n): {bcolors.ENDC} "
    )
    if confirm.lower() not in ["y", "yes"]:
        return

    response = requests.get(MIGRATION_SCRIPT_URL)
    if response.status_code != 200:
        sys.exit(1)

    migration_filename = "temp_migration.py"
    with open(migration_filename, "w", encoding="utf-8") as f:
        f.write(response.text)

    try:
        subprocess.run([PYTHON_CMD_NAME, migration_filename], check=True)
    except subprocess.CalledProcessError:
        pass
    finally:
        if os.path.exists(migration_filename):
            os.remove(migration_filename)


def parse_args():
    """Parse command line arguments."""
    parser = argparse.ArgumentParser(description="Update and migration script for Vocard.")
    parser.add_argument(
        "-c",
        "--check",
        action="store_true",
        help="Check the current version of the Vocard",
    )
    parser.add_argument("-v", "--version", type=str, help="Install the specified version of the Vocard")
    parser.add_argument(
        "-l",
        "--latest",
        action="store_true",
        help="Install the latest version of the Vocard from Github",
    )
    parser.add_argument(
        "-b",
        "--beta",
        action="store_true",
        help="Install the beta version of the Vocard from Github",
    )
    parser.add_argument(
        "-m",
        "--migration",
        action="store_true",
        help="Download and run the migration script from Github",
    )
    return parser.parse_args()


def main() -> None:
    """Main function."""
    args = parse_args()

    if args.check:
        check_version(with_msg=True)

    elif args.version:
        version = args.version
        response = download_file(version)
        install(response, version)

    elif args.latest:
        response = download_file()
        version = check_version()
        install(response, version)

    elif args.beta:
        response = download_file("refs/heads/beta")
        install(response, "beta")

    elif args.migration:
        run_migration()
    else:
        pass


if __name__ == "__main__":
    main()
