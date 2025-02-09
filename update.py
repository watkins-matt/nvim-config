#!/usr/bin/env python3

from crontab import CronTab
from dataclasses import dataclass
from enum import Enum
from subprocess import call, run, PIPE
from typing import List, Dict, Optional
import argparse
import datetime
import logging
import os
import re
import requests
import shutil
import sys
import tempfile
import time

# Configure argument parsing
parser = argparse.ArgumentParser(description="Neovim Updater Script")
parser.add_argument("--debug", action="store_true", help="Enable debug logging")
parser.add_argument(
    "--uninstall", action="store_true", help="Uninstall Neovim and its configurations"
)
parser.add_argument(
    "--config", action="store_true", help="Update Neovim configurations"
)
args = parser.parse_args()

# Configure logging
logging.basicConfig(
    stream=sys.stdout,
    level=logging.DEBUG if args.debug else logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    datefmt="%Y-%m-%d %I:%M:%S %p",
)

INSTALL_PATH = "/opt/nvim/update.py"
NVIM_DIR = "/opt/nvim/"
SYMLINK_PATH = "/usr/bin/nvim"
APPRUN_PATH = "/opt/nvim/squashfs-root/AppRun"
CONFIG_REPO = "https://github.com/watkins-matt/nvim-config.git"
CONFIG_DIR = os.path.expanduser("~/.config/nvim")
UPDATE_SCRIPT_URL = "https://raw.githubusercontent.com/watkins-matt/nvim-config/refs/heads/main/update.py"


class Architecture(Enum):
    X86_64 = ("x86_64", ["x86_64", "amd64", "x86-64"])
    ARM64 = ("arm64", ["arm64", "aarch64", "armv8"])

    def __init__(self, canonical: str, matches: List[str]):
        self.canonical = canonical
        self.matches = matches
        # Pre-compile regex patterns for each architecture match
        self.patterns = [
            re.compile(rf"\b{re.escape(pattern)}\b") for pattern in matches
        ]

    @classmethod
    def detect_current(cls) -> "Architecture":
        """Detect the current system architecture."""
        import platform

        machine = platform.machine().lower()

        # Try to match the machine architecture against known patterns
        for arch in cls:
            if any(pattern.search(machine) for pattern in arch.patterns):
                return arch

        raise ValueError(f"Unsupported architecture: {machine}")

    @classmethod
    def detect_from_name(cls, name: str) -> Optional["Architecture"]:
        """Try to detect architecture from an asset name."""
        name_lower = name.lower()

        # Try to match against known architecture patterns
        for arch in cls:
            if any(pattern.search(name_lower) for pattern in arch.patterns):
                return arch

        return None


@dataclass
class ReleaseAsset:
    """Represents a single release asset file."""

    name: str
    browser_download_url: str
    size: int
    content_type: str
    download_count: int

    @classmethod
    def from_dict(cls, data: Dict) -> "ReleaseAsset":
        return cls(
            name=data["name"],
            browser_download_url=data["browser_download_url"],
            size=data["size"],
            content_type=data["content_type"],
            download_count=data["download_count"],
        )


@dataclass
class ReleaseInfo:
    """Represents a single Neovim release."""

    tag_name: str
    name: str
    body: str
    assets: List[ReleaseAsset]
    prerelease: bool
    draft: bool

    @classmethod
    def from_dict(cls, data: Dict) -> "ReleaseInfo":
        assets = [ReleaseAsset.from_dict(asset) for asset in data["assets"]]
        return cls(
            tag_name=data["tag_name"],
            name=data["name"],
            body=data["body"],
            assets=assets,
            prerelease=data["prerelease"],
            draft=data["draft"],
        )

    def find_appimage_asset(
        self, arch: Architecture = Architecture.X86_64
    ) -> Optional[ReleaseAsset]:
        """
        Find the AppImage asset for the specified architecture using flexible matching.

        The matching algorithm:
        1. Looks for files ending in .appimage
        2. Tries to detect architecture from the filename
        3. Prioritizes files that:
           - Contain 'linux' in the name
           - Match the requested architecture
           - Don't contain 'zsync' or other metadata extensions
        """
        appimage_assets = []

        for asset in self.assets:
            name_lower = asset.name.lower()

            # Skip non-AppImage and metadata files
            if not name_lower.endswith(".appimage") or ".appimage." in name_lower:
                continue

            # Try to detect architecture from the filename
            detected_arch = Architecture.detect_from_name(name_lower)
            if detected_arch is None:
                continue

            # Score this asset based on various factors
            score = 0
            if detected_arch == arch:
                score += 10
            if "linux" in name_lower:
                score += 5

            appimage_assets.append((score, asset))

        # Sort by score and return the best match
        if appimage_assets:
            return sorted(appimage_assets, key=lambda x: x[0], reverse=True)[0][1]

        return None

    def get_appimage_url(
        self, arch: Architecture = Architecture.X86_64
    ) -> Optional[str]:
        """Get the download URL for the AppImage of the specified architecture."""
        asset = self.find_appimage_asset(arch)
        return asset.browser_download_url if asset else None

    def get_appimage_size(
        self, arch: Architecture = Architecture.X86_64
    ) -> Optional[int]:
        """Get the expected size of the AppImage for the specified architecture."""
        asset = self.find_appimage_asset(arch)
        return asset.size if asset else None


class ReleaseManager:
    """Manages Neovim releases and updates."""

    GITHUB_API_URL = "https://api.github.com/repos/neovim/neovim/releases/latest"
    MIN_APPIMAGE_SIZE = 10 * 1024 * 1024  # 10MB minimum size
    CACHE_DURATION = 3600  # Cache duration in seconds (1 hour)

    _api_cache = {}  # Class-level cache dictionary

    def __init__(self):
        self.latest_release: Optional[ReleaseInfo] = None

    @classmethod
    def _get_cached_response(cls, url: str) -> Optional[Dict]:
        """Get cached response if it exists and is still valid."""
        cache_entry = cls._api_cache.get(url)
        if not cache_entry:
            return None

        timestamp, data = cache_entry
        if time.time() - timestamp > cls.CACHE_DURATION:
            # Cache expired
            del cls._api_cache[url]
            return None

        return data

    @classmethod
    def _cache_response(cls, url: str, data: Dict):
        """Cache response data with current timestamp."""
        cls._api_cache[url] = (time.time(), data)

    def fetch_latest_release(self) -> ReleaseInfo:
        """Fetch the latest release information from GitHub."""
        # Check cache first
        cached_data = self._get_cached_response(self.GITHUB_API_URL)
        if cached_data:
            logging.debug("Using cached release information")
            self.latest_release = ReleaseInfo.from_dict(cached_data)
            return self.latest_release

        # If not in cache, make the API call
        logging.debug("Fetching fresh release information")
        response = requests.get(self.GITHUB_API_URL)
        if response.status_code != 200:
            raise ValueError(
                f"Failed to fetch release info: HTTP {response.status_code}"
            )

        # Cache the response
        data = response.json()
        self._cache_response(self.GITHUB_API_URL, data)

        self.latest_release = ReleaseInfo.from_dict(data)
        return self.latest_release

    @staticmethod
    def validate_appimage(file_path: str, expected_size: Optional[int] = None) -> bool:
        """
        Validate the AppImage file.

        Args:
            file_path: Path to the AppImage file
            expected_size: Expected file size in bytes (if known)

        Returns:
            bool: True if the file is valid, False otherwise
        """
        if not os.path.exists(file_path):
            return False

        # Check file size
        file_size = os.path.getsize(file_path)
        if file_size < ReleaseManager.MIN_APPIMAGE_SIZE:
            logging.error(f"File too small: {file_size} bytes")
            return False

        if expected_size and file_size != expected_size:
            logging.error(f"Size mismatch: expected {expected_size}, got {file_size}")
            return False

        # Check if file is executable
        if not os.access(file_path, os.X_OK):
            logging.error("File is not executable")
            return False

        return True

    def download_latest(self, target_dir: str, arch: Architecture = None) -> bool:
        """
        Download the latest Neovim AppImage.

        Args:
            target_dir: Directory where Neovim should be installed
            arch: Target architecture (defaults to system architecture)

        Returns:
            bool: True if update successful, False otherwise
        """
        if arch is None:
            arch = Architecture.detect_current()

        if not self.latest_release:
            self.fetch_latest_release()

        download_url = self.latest_release.get_appimage_url(arch)
        if not download_url:
            raise ValueError(f"No AppImage found for architecture {arch}")

        expected_size = self.latest_release.get_appimage_size(arch)
        final_path = os.path.join(target_dir, "nvim.appimage")

        # Create temporary file in the target directory
        with tempfile.NamedTemporaryFile(dir=target_dir, delete=False) as temp_file:
            try:
                logging.info(f"Downloading Neovim AppImage from {download_url}")
                response = requests.get(download_url, stream=True)
                response.raise_for_status()

                for chunk in response.iter_content(chunk_size=8192):
                    if chunk:
                        temp_file.write(chunk)
                temp_file.flush()

                # Make the temporary file executable
                os.chmod(temp_file.name, 0o755)

                # Validate the downloaded file
                if not self.validate_appimage(temp_file.name, expected_size):
                    os.unlink(temp_file.name)
                    logging.error("Downloaded file validation failed")
                    return False

                # Move the temporary file to the final location
                shutil.move(temp_file.name, final_path)
                logging.info(
                    f"Successfully updated Neovim to {self.latest_release.tag_name}"
                )
                return True

            except Exception as e:
                if os.path.exists(temp_file.name):
                    os.unlink(temp_file.name)
                logging.error(f"Failed to download/validate Neovim: {e}")
                return False


def setup_directories():
    """Ensure the Neovim directory exists."""
    if not os.path.exists(NVIM_DIR):
        os.makedirs(NVIM_DIR)
        logging.debug(f"Created directory {NVIM_DIR}")


def update_symlink():
    """Update the symbolic link in /usr/bin for Neovim if necessary."""
    symlink_updated = False

    # Remove old symlink in /opt/nvim if it exists
    old_symlink = "/opt/nvim/nvim"
    if os.path.islink(old_symlink):
        os.unlink(old_symlink)
        logging.debug(f"Removed old symlink: {old_symlink}")
        symlink_updated = True

    # Check if the symlink needs to be updated
    if not os.path.islink(SYMLINK_PATH) or os.readlink(SYMLINK_PATH) != APPRUN_PATH:
        if os.path.exists(SYMLINK_PATH):
            os.remove(SYMLINK_PATH)
        os.symlink(APPRUN_PATH, SYMLINK_PATH)
        logging.debug(f"Updated symlink: {SYMLINK_PATH} -> {APPRUN_PATH}")
        symlink_updated = True

    if symlink_updated:
        refresh_shell_cache()


def refresh_shell_cache():
    """Refresh the shell's command cache if using Bash or Zsh."""
    shell = os.environ.get("SHELL", "").lower()
    if "bash" in shell or "zsh" in shell:
        os.system("hash -r")
        logging.debug("Refreshed shell's command cache with 'hash -r'")
    else:
        logging.debug("Shell command cache refresh may be needed.")
        logging.debug(
            "If 'nvim' command doesn't work, you may need to restart your shell or run a shell-specific cache refresh command."
        )


def extract_appimage():
    """Extract the Neovim AppImage and setup symbolic links."""
    appimage_path = os.path.join(NVIM_DIR, "nvim.appimage")
    extract_path = os.path.join(NVIM_DIR, "squashfs-root")

    if os.path.exists(extract_path):
        logging.debug("Removing old extracted AppImage directory")
        shutil.rmtree(extract_path)

    logging.debug("Extracting AppImage")
    os.chdir(NVIM_DIR)
    with open(os.devnull, "w") as FNULL:
        call([appimage_path, "--appimage-extract"], stdout=FNULL, stderr=FNULL)

    logging.debug("Extraction complete")
    update_symlink()


def download_nvim():
    """Download and update the Neovim AppImage."""
    setup_directories()
    try:
        logging.debug("Attempting to download new version of Neovim AppImage")
        manager = ReleaseManager()
        success = manager.download_latest(NVIM_DIR)
        if success:
            extract_appimage()
            return True
        return False
    except Exception as e:
        logging.error(f"Failed to download Neovim: {e}")
        return False


def is_nvim_installed_correctly():
    """Check if Neovim is installed correctly."""
    return os.path.exists(os.path.join(NVIM_DIR, "squashfs-root/AppRun"))


def get_installed_version() -> Optional[str]:
    """Get the installed Neovim version by running nvim --version."""
    try:
        result = run(
            [APPRUN_PATH, "--version"], stdout=PIPE, stderr=PIPE, text=True, timeout=5
        )

        if result.returncode == 0:
            # Parse output looking for "NVIM v0.10.2"
            first_line = result.stdout.splitlines()[0]
            if first_line.startswith("NVIM v"):
                return first_line.split("NVIM v")[1].split()[0]
    except Exception as e:
        logging.debug(f"Failed to get installed version: {e}")

    return None


def setup_crontab():
    """Set up a crontab entry to run the update script nightly."""
    cron = CronTab(user=True)
    update_command = f"python3 {INSTALL_PATH}"

    # Check if the job already exists
    update_job = next((job for job in cron if job.command == update_command), None)

    if not update_job:
        update_job = cron.new(command=update_command)
        update_job.setall("0 2 * * *")  # Run at 2 AM every day
        cron.write()
        logging.debug("Crontab entry added for nightly Neovim and config updates")
    else:
        logging.debug("Crontab entry for nightly updates already exists")


def check_update():
    """Check for updates to Neovim and download if a newer version is found."""
    setup_directories()
    logging.debug("Checking for new Neovim releases")

    try:
        manager = ReleaseManager()
        latest = manager.fetch_latest_release()
        current_version = get_installed_version()

        if current_version is None:
            logging.info(
                "No existing Neovim installation found or version check failed"
            )
            if download_nvim():
                logging.info(f"Installed Neovim version {latest.tag_name}")
                return True, True
            return False, False

        # Strip 'v' prefix if present for comparison
        current_version = current_version.lstrip("v")
        latest_version = latest.tag_name.lstrip("v")

        nvim_updated = False
        if current_version != latest_version or not is_nvim_installed_correctly():
            logging.info(
                f"Neovim update detected. Current version: {current_version}, Latest version: {latest_version}"
            )
            if download_nvim():
                logging.info("Neovim has been updated.")
                nvim_updated = True
            else:
                logging.error("Failed to update Neovim")
                return False, False
        else:
            logging.info("Neovim is already up to date.")

        # Ensure symlink is correct even if no update was needed
        update_symlink()

        return nvim_updated, True  # Neovim status and success
    except Exception as e:
        logging.error(f"Failed to check for updates: {e}")
        return False, False  # Neovim status and success


def install_script():
    """Copy the script to /opt/nvim/update.py if it doesn't exist."""
    # Ensure the directory exists
    os.makedirs(os.path.dirname(INSTALL_PATH), exist_ok=True)

    if not os.path.exists(INSTALL_PATH):
        shutil.copy2(__file__, INSTALL_PATH)
        os.chmod(INSTALL_PATH, 0o755)  # Make the script executable
        logging.debug(f"Script installed to {INSTALL_PATH}")
    else:
        logging.debug(f"Script already installed at {INSTALL_PATH}")


def is_git_installed():
    """Check if git is installed on the system."""
    return shutil.which("git") is not None


def is_correct_git_repo(directory, expected_remote):
    """Check if the given directory is a git repo with the expected remote."""
    if not os.path.exists(os.path.join(directory, ".git")):
        return False

    result = run(
        ["git", "-C", directory, "remote", "get-url", "origin"],
        stdout=PIPE,
        stderr=PIPE,
        universal_newlines=True,
    )
    return result.returncode == 0 and result.stdout.strip() == expected_remote


def clone_config_repo():
    """Clone the Neovim configuration repository."""
    logging.debug(f"Cloning Neovim config repository to {CONFIG_DIR}")
    result = run(
        ["git", "clone", CONFIG_REPO, CONFIG_DIR],
        stdout=PIPE,
        stderr=PIPE,
        universal_newlines=True,
    )
    if result.returncode == 0:
        logging.info("Neovim configuration has been cloned successfully.")
    else:
        logging.error(
            f"Failed to clone Neovim configuration repository: {result.stderr}"
        )


def update_config():
    """Update the Neovim configuration repository."""
    logging.debug("Updating Neovim configuration repository")
    os.chdir(CONFIG_DIR)

    # Check for local changes
    result = run(
        ["git", "status", "--porcelain"],
        stdout=PIPE,
        stderr=PIPE,
        universal_newlines=True,
    )
    modified_files = result.stdout.strip().splitlines()

    if modified_files:
        # Create a timestamped backup directory
        timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
        backup_dir = os.path.expanduser(f"~/nvim_config_backup/{timestamp}/")
        os.makedirs(backup_dir, exist_ok=True)
        logging.debug(
            f"Local changes detected in Neovim config repository. Backing up to {backup_dir}"
        )

        # Backup modified or added files to the timestamped directory
        for line in modified_files:
            # Split on the first space to separate the status and the file path
            parts = line.split(maxsplit=1)
            if len(parts) == 2:
                status = (
                    parts[0].strip().lower()
                )  # Get the status part (e.g., 'm', 'a')
                file_path = parts[1]  # Keep the file path

                # Check if the file is modified ('m') or added ('a')
                if status in ["m", "a"]:
                    abs_file_path = os.path.join(CONFIG_DIR, file_path)
                    backup_file_path = os.path.join(backup_dir, file_path)

                    # Log and back up the modified or added file
                    logging.debug(f"Backing up {status} file: {abs_file_path}")
                    if os.path.exists(abs_file_path):
                        os.makedirs(os.path.dirname(backup_file_path), exist_ok=True)
                        shutil.copy2(abs_file_path, backup_file_path)
                        logging.debug(
                            f"Backed up {abs_file_path} to {backup_file_path}"
                        )
                else:
                    logging.debug(f"Skipping file with status {status}: {file_path}")
            else:
                logging.error(f"Failed to parse line from git status: {line}")

    # Fetch the latest changes from the remote
    result = run(["git", "fetch"], stdout=PIPE, stderr=PIPE, universal_newlines=True)
    if result.returncode == 0:
        # Perform a hard reset to the latest commit on the current branch
        run(["git", "reset", "--hard", "origin/HEAD"], stdout=PIPE, stderr=PIPE)
        logging.debug(
            "Neovim configuration repository reset to the latest commit on the current branch."
        )

        # Pull the latest changes from the remote
        result = run(["git", "pull"], stdout=PIPE, stderr=PIPE, universal_newlines=True)
        if result.returncode != 0:
            logging.error(f"Failed to pull the latest changes: {result.stderr}")
            return

        # Clean untracked files and directories (git clean)
        run(["git", "clean", "-fd"], stdout=PIPE, stderr=PIPE)
        logging.debug("Removed untracked files and directories using git clean.")
    else:
        logging.error(f"Failed to fetch the latest remote changes: {result.stderr}")
        return


def clone_or_update_config_repo():
    """Clone the Neovim configuration repository or update if it exists."""
    if not is_git_installed():
        logging.error(
            "Git is not installed. Please install git and run the script again."
        )
        sys.exit(1)

    if os.path.exists(CONFIG_DIR):
        if is_correct_git_repo(CONFIG_DIR, CONFIG_REPO):
            logging.info("Neovim configuration is up to date.")
            try:
                update_config()
            except Exception as e:
                logging.error(f"Error updating configuration: {e}")
        else:
            logging.debug(f"Removing existing incorrect config directory: {CONFIG_DIR}")
            shutil.rmtree(CONFIG_DIR)
            clone_config_repo()
    else:
        clone_config_repo()


def create_update_alias():
    """Create an alias for instant config updates."""
    shell = os.environ.get("SHELL", "").lower()
    if "bash" in shell:
        rc_file = os.path.expanduser("~/.bashrc")
    elif "zsh" in shell:
        rc_file = os.path.expanduser("~/.zshrc")
    else:
        logging.debug("Unsupported shell. Alias creation skipped.")
        return

    alias_line = f"\nalias update-nvim-config='python3 {INSTALL_PATH} --config'\n"

    alias_added = False
    with open(rc_file, "a+") as f:
        f.seek(0)
        content = f.read()
        if "alias update-nvim-config" not in content:
            f.write(alias_line)
            alias_added = True
            logging.debug(f"Alias 'update-nvim-config' added to {rc_file}")
        else:
            logging.debug("Alias 'update-nvim-config' already exists.")

    if alias_added:
        # Attempt to reload the shell configuration
        try:
            os.system(f"source {rc_file}")
            logging.debug(
                "Shell configuration reloaded. The 'update-nvim-config' alias should now be available."
            )
        except Exception as e:
            logging.error(f"Failed to reload shell configuration: {e}")
            logging.info(
                f"Please run the following command to use the new alias in the current session:\n    source {rc_file}"
            )

    logging.debug(
        "To use the 'update-nvim-config' alias in new terminal sessions, no further action is needed."
    )


def handle_self_update():
    """Handle self-update by replacing the running script with the new version."""
    current_script = os.path.abspath(__file__)
    temp_dir = tempfile.gettempdir()
    temp_script = os.path.join(temp_dir, "update_new.py")

    # Download the new script
    try:
        response = requests.get(UPDATE_SCRIPT_URL)
        if response.status_code == 200:
            with open(temp_script, "w") as f:
                f.write(response.text)
            os.chmod(temp_script, 0o755)
            logging.debug("Downloaded new version of the update script.")

            # Create a shell script to replace the current script after exit
            replace_script = f"""#!/bin/bash
sleep 1
mv "{temp_script}" "{current_script}"
chmod +x "{current_script}"
"""

            replace_script_path = os.path.join(temp_dir, "replace_update.sh")
            with open(replace_script_path, "w") as f:
                f.write(replace_script)
            os.chmod(replace_script_path, 0o755)

            # Execute the replace script in the background
            call([replace_script_path, "&"], shell=True)
            logging.info(
                "Neovim has been updated. The update script will be refreshed shortly."
            )
        else:
            logging.error(
                f"Failed to download the new update script: HTTP {response.status_code}"
            )
    except Exception as e:
        logging.error(f"Error during self-update: {e}")


def check_self_update():
    """Check if the update script has been updated and handle self-update."""
    # Get the current script's last modified time
    current_mtime = os.path.getmtime(__file__)

    # Fetch the latest script metadata
    response = requests.head(UPDATE_SCRIPT_URL)
    if response.status_code != 200:
        logging.error(
            f"Failed to fetch update script metadata: HTTP {response.status_code}"
        )
        return

    # Get the Last-Modified header
    latest_mtime_str = response.headers.get("Last-Modified", "")
    if latest_mtime_str:
        try:
            latest_mtime = datetime.datetime.strptime(
                latest_mtime_str, "%a, %d %b %Y %H:%M:%S %Z"
            ).timestamp()
        except ValueError:
            # If timezone information is missing or incorrect, try without it
            latest_mtime = datetime.datetime.strptime(
                latest_mtime_str, "%a, %d %b %Y %H:%M:%S"
            ).timestamp()

        if latest_mtime > current_mtime:
            handle_self_update()


def uninstall():
    """Remove the crontab entries, symlink, /opt/nvim directory, and config directory."""
    # Remove crontab entries
    cron = CronTab(user=True)
    cron.remove_all(command=f"python3 {INSTALL_PATH}")
    cron.remove_all(command=f"python3 {INSTALL_PATH} --config")
    cron.write()
    logging.debug("Removed crontab entries")

    # Remove symlink
    if os.path.islink(SYMLINK_PATH):
        os.unlink(SYMLINK_PATH)
        logging.debug(f"Removed symlink from {SYMLINK_PATH}")

    # Remove /opt/nvim directory and config directory
    dirs_to_remove = [NVIM_DIR, CONFIG_DIR]
    if os.path.abspath(sys.argv[0]).startswith(os.path.abspath(NVIM_DIR)):
        logging.debug(
            f"Script is running from {NVIM_DIR}. Will delete directories after script completion."
        )
        # Create a separate script to delete the directories
        delete_script = f"""#!/usr/bin/env python3
import shutil
import os

dirs_to_delete = {dirs_to_remove}
for dir in dirs_to_delete:
    if os.path.exists(dir):
        shutil.rmtree(dir)
        print(f"Removed directory {{dir}}")
os.remove("{__file__}")
"""
        delete_script_path = os.path.join(tempfile.gettempdir(), "delete_nvim.py")
        with open(delete_script_path, "w") as f:
            f.write(delete_script)
        os.chmod(delete_script_path, 0o755)
        # Schedule the delete script to run after this script exits
        os.system(f"(sleep 1 && python3 {delete_script_path})&")
    else:
        for dir in dirs_to_remove:
            if os.path.exists(dir):
                shutil.rmtree(dir)
                logging.debug(f"Removed directory {dir}")

    logging.info("Uninstallation complete")


def main():
    if args.uninstall:
        uninstall()
        sys.exit(0)

    if args.config:
        clone_or_update_config_repo()
        setup_crontab()
        sys.exit(0)

    install_script()
    nvim_updated, nvim_status = check_update()
    config_updated = False

    # Clone or update config repository
    try:
        clone_or_update_config_repo()
        config_updated = True
    except Exception as e:
        logging.error(f"Error updating configuration: {e}")

    setup_crontab()
    create_update_alias()
    check_self_update()

    current_script_path = os.path.abspath(__file__)
    if current_script_path != INSTALL_PATH:
        logging.debug("Initial setup complete.")
        logging.debug(f"The script has been installed to {INSTALL_PATH}")
        if not current_script_path.startswith(NVIM_DIR):
            logging.debug(f"You can safely delete this script at {current_script_path}")
        logging.debug(
            f"Future updates will be handled by the installed script at {INSTALL_PATH}"
        )
    else:
        logging.debug("Update process complete.")
        logging.debug(f"This script at {INSTALL_PATH} will handle future updates.")

    if not nvim_status:
        logging.error("Failed to update Neovim.")


if __name__ == "__main__":
    main()
