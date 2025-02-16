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
import platform

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
UPDATE_SCRIPT_URL = (
    "https://raw.githubusercontent.com/watkins-matt/nvim-config/refs/heads/main/update.py"
)


class Architecture(Enum):
    """Represents supported CPU architectures for AppImage assets."""

    X86_64 = ("x86_64", ["x86_64", "amd64", "x86-64"])
    ARM64 = ("arm64", ["arm64", "aarch64", "armv8"])

    def __init__(self, canonical: str, matches: List[str]) -> None:
        self.canonical = canonical
        self.matches = matches
        # Pre-compile regex patterns for each architecture match
        self.patterns = [
            re.compile(rf"\b{re.escape(pattern)}\b") for pattern in matches
        ]

    @classmethod
    def detect_current(cls) -> "Architecture":
        """Detect the current system architecture."""
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

    def __init__(self) -> None:
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
    def _cache_response(cls, url: str, data: Dict) -> None:
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
    def validate_appimage(
        file_path: str, expected_size: Optional[int] = None
    ) -> bool:
        """
        Validate the AppImage file.

        Args:
            file_path: Path to the AppImage file
            expected_size: Expected file size in bytes (if known)

        Returns:
            True if the file is valid, False otherwise
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

    def download_latest(
        self, target_dir: str, arch: Optional[Architecture] = None
    ) -> bool:
        """
        Download the latest Neovim AppImage.

        Args:
            target_dir: Directory where Neovim should be installed
            arch: Target architecture (defaults to system architecture)

        Returns:
            True if update successful, False otherwise
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


class NvimUpdater:
    """Handles updating the Neovim AppImage, extraction, and symlink updates."""

    def __init__(
        self,
        nvim_dir: str = NVIM_DIR,
        symlink_path: str = SYMLINK_PATH,
        apprun_path: str = APPRUN_PATH,
    ) -> None:
        self.nvim_dir = nvim_dir
        self.symlink_path = symlink_path
        self.apprun_path = apprun_path

    @property
    def appimage_path(self) -> str:
        """Return the path to the downloaded AppImage."""
        return os.path.join(self.nvim_dir, "nvim.appimage")

    @property
    def extract_path(self) -> str:
        """Return the extraction directory for the AppImage."""
        return os.path.join(self.nvim_dir, "squashfs-root")

    def download_and_install(self) -> bool:
        """
        Download the latest Neovim AppImage and install it.

        Returns:
            True if the update and installation succeeded, False otherwise.
        """
        manager = ReleaseManager()
        if not manager.download_latest(self.nvim_dir):
            return False
        self.extract_appimage()
        self.update_symlink()
        return True

    def extract_appimage(self) -> None:
        """Extract the downloaded Neovim AppImage."""
        if os.path.exists(self.extract_path):
            logging.debug("Removing old extracted AppImage directory")
            shutil.rmtree(self.extract_path)
        logging.debug("Extracting AppImage")
        os.chdir(self.nvim_dir)
        with open(os.devnull, "w") as FNULL:
            call([self.appimage_path, "--appimage-extract"], stdout=FNULL, stderr=FNULL)
        logging.debug("Extraction complete")

    def update_symlink(self) -> None:
        """Update the symbolic link for Neovim."""
        symlink_updated = False
        old_symlink = os.path.join(self.nvim_dir, "nvim")
        if os.path.islink(old_symlink):
            os.unlink(old_symlink)
            logging.debug(f"Removed old symlink: {old_symlink}")
            symlink_updated = True

        if not os.path.islink(self.symlink_path) or os.readlink(self.symlink_path) != self.apprun_path:
            if os.path.exists(self.symlink_path):
                os.remove(self.symlink_path)
            os.symlink(self.apprun_path, self.symlink_path)
            logging.debug(f"Updated symlink: {self.symlink_path} -> {self.apprun_path}")
            symlink_updated = True

        if symlink_updated:
            self.refresh_shell_cache()

    def refresh_shell_cache(self) -> None:
        """Refresh the shell's command cache if using Bash or Zsh."""
        shell = os.environ.get("SHELL", "").lower()
        if "bash" in shell or "zsh" in shell:
            os.system("hash -r")
            logging.debug("Refreshed shell's command cache with 'hash -r'")
        else:
            logging.debug("Shell command cache refresh may be needed. "
                          "Restart your shell if the 'nvim' command is not found.")

    def get_installed_version(self) -> Optional[str]:
        """
        Get the installed Neovim version by running the AppRun executable.

        Returns:
            The version string if detected, or None otherwise.
        """
        try:
            result = run(
                [self.apprun_path, "--version"],
                stdout=PIPE,
                stderr=PIPE,
                text=True,
                timeout=5,
            )
            if result.returncode == 0:
                first_line = result.stdout.splitlines()[0]
                if first_line.startswith("NVIM v"):
                    return first_line.split("NVIM v")[1].split()[0]
        except Exception as e:
            logging.debug(f"Failed to get installed version: {e}")
        return None

    def is_installed_correctly(self) -> bool:
        """
        Check if Neovim is installed correctly by verifying the AppRun file.

        Returns:
            True if AppRun exists, False otherwise.
        """
        return os.path.exists(self.apprun_path)


class ConfigRepoManager:
    """Manages cloning and updating of the Neovim configuration repository."""

    def __init__(
        self,
        config_dir: str = CONFIG_DIR,
        repo_url: str = CONFIG_REPO,
    ) -> None:
        self.config_dir = config_dir
        self.repo_url = repo_url

    @staticmethod
    def is_git_installed() -> bool:
        """
        Check if git is installed on the system.

        Returns:
            True if git is available, False otherwise.
        """
        return shutil.which("git") is not None

    def is_correct_git_repo(self) -> bool:
        """
        Check if the configuration directory is a git repo with the expected remote.

        Returns:
            True if the repo is correct, False otherwise.
        """
        git_dir = os.path.join(self.config_dir, ".git")
        if not os.path.exists(git_dir):
            return False
        result = run(
            ["git", "-C", self.config_dir, "remote", "get-url", "origin"],
            stdout=PIPE,
            stderr=PIPE,
            text=True,
        )
        return result.returncode == 0 and result.stdout.strip() == self.repo_url

    def clone_repo(self) -> None:
        """
        Clone the configuration repository into the designated directory.
        """
        logging.debug(f"Cloning config repo to {self.config_dir}")
        result = run(
            ["git", "clone", self.repo_url, self.config_dir],
            stdout=PIPE,
            stderr=PIPE,
            text=True,
        )
        if result.returncode == 0:
            logging.info("Config repository cloned successfully.")
        else:
            logging.error(f"Failed to clone config repo: {result.stderr}")

    def update_repo(self) -> None:
        """
        Update the configuration repository, backing up local changes if necessary.
        """
        logging.debug("Updating config repository")
        os.chdir(self.config_dir)
        result = run(
            ["git", "status", "--porcelain"],
            stdout=PIPE,
            stderr=PIPE,
            text=True,
        )
        modified_files = result.stdout.strip().splitlines()
        if modified_files:
            timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
            backup_dir = os.path.expanduser(f"~/nvim_config_backup/{timestamp}/")
            os.makedirs(backup_dir, exist_ok=True)
            logging.debug(f"Local changes detected. Backing up to {backup_dir}")
            for line in modified_files:
                parts = line.split(maxsplit=1)
                if len(parts) == 2:
                    status = parts[0].strip().lower()
                    file_path = parts[1]
                    if status in ["m", "a"]:
                        abs_file_path = os.path.join(self.config_dir, file_path)
                        backup_file_path = os.path.join(backup_dir, file_path)
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
                    logging.error(f"Failed to parse git status line: {line}")
        result = run(["git", "fetch"], stdout=PIPE, stderr=PIPE, text=True)
        if result.returncode == 0:
            run(
                ["git", "reset", "--hard", "origin/HEAD"],
                stdout=PIPE,
                stderr=PIPE,
            )
            logging.debug("Repository reset to latest commit.")
            result = run(["git", "pull"], stdout=PIPE, stderr=PIPE, text=True)
            if result.returncode != 0:
                logging.error(f"Failed to pull changes: {result.stderr}")
                return
            run(["git", "clean", "-fd"], stdout=PIPE, stderr=PIPE)
            logging.debug("Cleaned untracked files with git clean.")
        else:
            logging.error(f"Failed to fetch remote changes: {result.stderr}")

    def clone_or_update(self) -> None:
        """
        Clone the configuration repository if not present, or update it if it exists.
        """
        if not self.is_git_installed():
            logging.error("Git is not installed. Please install git and retry.")
            sys.exit(1)
        if os.path.exists(self.config_dir):
            if self.is_correct_git_repo():
                logging.info("Config repository is up to date.")
                try:
                    self.update_repo()
                except Exception as e:
                    logging.error(f"Error updating config: {e}")
            else:
                logging.debug(f"Removing incorrect config directory: {self.config_dir}")
                shutil.rmtree(self.config_dir)
                self.clone_repo()
        else:
            self.clone_repo()


class SelfUpdater:
    """Handles self-updating of the update script by comparing file contents
    across multiple target locations.
    """

    def __init__(
        self,
        target_scripts: Optional[List[str]] = None,
        update_script_url: str = UPDATE_SCRIPT_URL,
    ) -> None:
        """
        Initialize with a list of target script paths to update.

        Args:
            target_scripts: List of file paths to update. If None, defaults to
                            [INSTALL_PATH, ~/.config/nvim/update.py].
            update_script_url: URL to download the latest update script.
        """
        if target_scripts is None:
            self.target_scripts = [
                INSTALL_PATH,
                os.path.join(os.path.expanduser("~/.config/nvim"), "update.py"),
            ]
        else:
            self.target_scripts = target_scripts
        self.update_script_url = update_script_url

    def check_and_update(self) -> None:
        """
        Download the new version of the update script and compare contents with
        each target script. If any differences are found, schedule an update.
        """
        try:
            response = requests.get(self.update_script_url)
            if response.status_code != 200:
                logging.error(
                    f"Failed to download update script: HTTP {response.status_code}"
                )
                return
            new_content = response.text
            for script in self.target_scripts:
                try:
                    with open(script, "r") as f:
                        current_content = f.read()
                    if new_content != current_content:
                        logging.info(
                            f"New update script version detected in {script}."
                        )
                        self.perform_update(script, new_content)
                    else:
                        logging.debug(f"Script at {script} is already up to date.")
                except Exception as e:
                    logging.error(f"Failed to check script at {script}: {e}")
        except Exception as e:
            logging.error(f"Self-update check failed: {e}")

    def perform_update(self, target_script: str, new_content: str) -> None:
        """
        Write the new script content to a temporary file and schedule its replacement
        for the given target script.

        Args:
            target_script: The file path to update.
            new_content: The new script content.
        """
        temp_dir = tempfile.gettempdir()
        temp_script = os.path.join(temp_dir, "update_new.py")
        try:
            with open(temp_script, "w") as f:
                f.write(new_content)
            os.chmod(temp_script, 0o755)
            logging.debug(
                f"Downloaded new update script content for {target_script}."
            )
            replace_script = f"""#!/bin/bash
sleep 1
mv "{temp_script}" "{target_script}"
chmod +x "{target_script}"
"""
            replace_script_path = os.path.join(temp_dir, "replace_update.sh")
            with open(replace_script_path, "w") as f:
                f.write(replace_script)
            os.chmod(replace_script_path, 0o755)
            call([replace_script_path, "&"], shell=True)
            logging.info(
                f"Update script at {target_script} will be refreshed shortly."
            )
        except Exception as e:
            logging.error(f"Error during self-update for {target_script}: {e}")


class SchedulerManager:
    """Manages scheduling of the update script via crontab."""

    @staticmethod
    def setup_crontab() -> None:
        """
        Set up a crontab entry to run the update script nightly.
        """
        cron = CronTab(user=True)
        update_command = f"python3 {INSTALL_PATH}"
        # Check if the job already exists
        job_exists = any(job.command == update_command for job in cron)
        if not job_exists:
            job = cron.new(command=update_command)
            job.setall("0 2 * * *")
            cron.write()
            logging.debug("Crontab entry added for nightly updates")
        else:
            logging.debug("Crontab entry for nightly updates already exists")


class Installer:
    """Handles installation and uninstallation of the update script."""

    @staticmethod
    def install_script() -> None:
        """
        Copy the update script to the designated install path if not already present.
        """
        os.makedirs(os.path.dirname(INSTALL_PATH), exist_ok=True)
        if not os.path.exists(INSTALL_PATH):
            shutil.copy2(__file__, INSTALL_PATH)
            os.chmod(INSTALL_PATH, 0o755)
            logging.debug(f"Script installed to {INSTALL_PATH}")
        else:
            logging.debug(f"Script already installed at {INSTALL_PATH}")

    @staticmethod
    def create_update_alias() -> None:
        """
        Create a shell alias for updating the Neovim configuration.
        """
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
            try:
                os.system(f"source {rc_file}")
                logging.debug("Shell configuration reloaded with source command.")
            except Exception as e:
                logging.error(f"Failed to reload shell configuration: {e}")
                logging.info(f"Please run 'source {rc_file}' to reload shell config.")

    @staticmethod
    def uninstall() -> None:
        """
        Remove crontab entries, symlink, Neovim directory, and configuration repository.
        """
        cron = CronTab(user=True)
        cron.remove_all(command=f"python3 {INSTALL_PATH}")
        cron.remove_all(command=f"python3 {INSTALL_PATH} --config")
        cron.write()
        logging.debug("Removed crontab entries")
        if os.path.islink(SYMLINK_PATH):
            os.unlink(SYMLINK_PATH)
            logging.debug(f"Removed symlink {SYMLINK_PATH}")
        dirs_to_remove = [NVIM_DIR, CONFIG_DIR]
        if os.path.abspath(sys.argv[0]).startswith(os.path.abspath(NVIM_DIR)):
            logging.debug(
                f"Script is running from {NVIM_DIR}. Scheduling deletion."
            )
            delete_script = f"""#!/usr/bin/env python3
import shutil
import os
dirs_to_delete = {dirs_to_remove}
for d in dirs_to_delete:
    if os.path.exists(d):
        shutil.rmtree(d)
        print(f"Removed directory {{d}}")
os.remove("{__file__}")
"""
            delete_script_path = os.path.join(tempfile.gettempdir(), "delete_nvim.py")
            with open(delete_script_path, "w") as f:
                f.write(delete_script)
            os.chmod(delete_script_path, 0o755)
            os.system(f"(sleep 1 && python3 {delete_script_path})&")
        else:
            for d in dirs_to_remove:
                if os.path.exists(d):
                    shutil.rmtree(d)
                    logging.debug(f"Removed directory {d}")
        logging.info("Uninstallation complete")


def main() -> None:
    """
    Main entry point that coordinates updates, configuration management,
    self-update, and scheduling.
    """
    if args.uninstall:
        Installer.uninstall()
        sys.exit(0)

    if args.config:
        config_manager = ConfigRepoManager()
        config_manager.clone_or_update()
        SchedulerManager.setup_crontab()
        sys.exit(0)

    # Ensure the update script is installed at the primary location
    Installer.install_script()

    nvim_updater = NvimUpdater(nvim_dir=NVIM_DIR)
    current_version = nvim_updater.get_installed_version()
    latest_release = ReleaseManager().fetch_latest_release()

    if (current_version is None or
        current_version.lstrip("v") != latest_release.tag_name.lstrip("v") or
        not nvim_updater.is_installed_correctly()):
        logging.info(
            f"Updating Neovim. Current version: {current_version}, "
            f"Latest: {latest_release.tag_name}"
        )
        if nvim_updater.download_and_install():
            logging.info(f"Installed Neovim version {latest_release.tag_name}")
        else:
            logging.error("Failed to update Neovim")
    else:
        logging.info("Neovim is already up to date.")
        nvim_updater.update_symlink()

    config_manager = ConfigRepoManager()
    config_manager.clone_or_update()
    SchedulerManager.setup_crontab()
    Installer.create_update_alias()

    # Trigger self-update for both target script locations
    SelfUpdater().check_and_update()

    logging.debug("Update process complete.")

if __name__ == "__main__":
    main()
