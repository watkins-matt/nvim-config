#!/usr/bin/env python3

import requests
import logging
from subprocess import call, run, PIPE
import os
import sys
import shutil
from crontab import CronTab
import datetime
import argparse
import tempfile

# Configure logging
parser = argparse.ArgumentParser(description="Neovim Updater Script")
parser.add_argument('--debug', action='store_true', help='Enable debug logging')
args = parser.parse_args()

logging.basicConfig(
    stream=sys.stdout,
    level=logging.DEBUG if args.debug else logging.ERROR,
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
    nvim_appimage_path = os.path.join(NVIM_DIR, "nvim.appimage")
    logging.debug("Attempting to download new version of Neovim AppImage")
    response = requests.get("https://github.com/neovim/neovim/releases/latest/download/nvim.appimage", stream=True)
    if response.status_code == 200:
        with open(nvim_appimage_path, "wb") as f:
            shutil.copyfileobj(response.raw, f)
        os.chmod(nvim_appimage_path, 0o755)  # Ensure the downloaded file is executable
        logging.debug("Download complete and permissions set")
        extract_appimage()
    else:
        logging.error(f"Failed to download Neovim AppImage: HTTP {response.status_code}")

def is_nvim_installed_correctly():
    """Check if Neovim is installed correctly."""
    return os.path.exists(os.path.join(NVIM_DIR, "squashfs-root/AppRun"))

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
    current_version_url = "https://api.github.com/repos/neovim/neovim/releases/latest"
    response = requests.get(current_version_url)
    if response.status_code != 200:
        logging.error(f"Failed to fetch latest Neovim version: HTTP {response.status_code}")
        return

    latest_version = response.json().get("tag_name", "")
    version_file_path = os.path.join(NVIM_DIR, "version.txt")

    if not os.path.exists(version_file_path):
        with open(version_file_path, "w") as file:
            file.write("None")
        logging.debug("Version file created")

    with open(version_file_path, "r") as file:
        current_version = file.read().strip()

    if current_version != latest_version or not is_nvim_installed_correctly():
        logging.info(
            f"Neovim update detected. Current version: {current_version}, Latest version: {latest_version}"
        )
        download_nvim()
        with open(version_file_path, "w") as file:
            file.write(latest_version)
        logging.info("Neovim has been updated.")
    else:
        logging.info("Neovim is already up to date.")

    # Ensure symlink is correct even if no update was needed
    update_symlink()

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

def clone_or_update_config_repo():
    """Clone the Neovim configuration repository or update if it exists."""
    if not is_git_installed():
        logging.error(
            "Git is not installed. Please install git and run the script again."
        )
        sys.exit(1)

    if os.path.exists(CONFIG_DIR):
        if is_correct_git_repo(CONFIG_DIR, CONFIG_REPO):
            logging.info(f"Neovim configuration is up to date.")
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
        logging.error(f"Failed to clone Neovim configuration repository: {result.stderr}")

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
                status = parts[0].strip().lower()  # Get the status part (e.g., 'm', 'a')
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
                        logging.debug(f"Backed up {abs_file_path} to {backup_file_path}")
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
        if result.returncode == 0:
            logging.info("Neovim configuration has been updated successfully.")
        else:
            logging.error(f"Failed to pull the latest changes: {result.stderr}")
            return

        # Clean untracked files and directories (git clean)
        run(["git", "clean", "-fd"], stdout=PIPE, stderr=PIPE)
        logging.debug("Removed untracked files and directories using git clean.")
    else:
        logging.error(f"Failed to fetch the latest remote changes: {result.stderr}")
        return

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
                f"Shell configuration reloaded. The 'update-nvim-config' alias should now be available."
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
            logging.info("Neovim has been updated. The update script will be refreshed shortly.")
        else:
            logging.error(f"Failed to download the new update script: HTTP {response.status_code}")
    except Exception as e:
        logging.error(f"Error during self-update: {e}")

def check_self_update():
    """Check if the update script has been updated and handle self-update."""
    # Get the current script's last modified time
    current_mtime = os.path.getmtime(__file__)

    # Fetch the latest script metadata
    response = requests.head(UPDATE_SCRIPT_URL)
    if response.status_code != 200:
        logging.error(f"Failed to fetch update script metadata: HTTP {response.status_code}")
        return

    # Get the Last-Modified header
    latest_mtime_str = response.headers.get('Last-Modified', '')
    if latest_mtime_str:
        latest_mtime = datetime.datetime.strptime(latest_mtime_str, "%a, %d %b %Y %H:%M:%S %Z").timestamp()
        if latest_mtime > current_mtime:
            handle_self_update()

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
        delete_script = f"""
import shutil
import os

dirs_to_delete = {dirs_to_remove}
for dir in dirs_to_delete:
    if os.path.exists(dir):
        shutil.rmtree(dir)
        print(f"Removed directory {{dir}}")
os.remove(__file__)
"""
        with open("/tmp/delete_nvim.py", "w") as f:
            f.write(delete_script)
        os.chmod("/tmp/delete_nvim.py", 0o755)
        # Schedule the delete script to run after this script exits
        os.system(f"(sleep 1 && python3 /tmp/delete_nvim.py)&")
    else:
        for dir in dirs_to_remove:
            if os.path.exists(dir):
                shutil.rmtree(dir)
                logging.debug(f"Removed directory {dir}")

    logging.info("Uninstallation complete")

def main():
    if not is_git_installed():
        logging.error(
            "Git is not installed. Please install git and run the script again."
        )
        sys.exit(1)

    if len(sys.argv) > 1:
        if sys.argv[1] == "--uninstall":
            uninstall()
        elif sys.argv[1] == "--config":
            clone_or_update_config_repo()
            setup_crontab()
        else:
            logging.error(f"Unknown argument: {sys.argv[1]}")
    else:
        install_script()
        check_update()
        clone_or_update_config_repo()
        setup_crontab()
        create_update_alias()
        check_self_update()

        current_script_path = os.path.abspath(__file__)
        if current_script_path != INSTALL_PATH:
            logging.debug("Initial setup complete.")
            logging.debug(f"The script has been installed to {INSTALL_PATH}")
            if not current_script_path.startswith(NVIM_DIR):
                logging.debug(
                    f"You can safely delete this script at {current_script_path}"
                )
            logging.debug(
                f"Future updates will be handled by the installed script at {INSTALL_PATH}"
            )
        else:
            logging.debug("Update process complete.")
            logging.debug(f"This script at {INSTALL_PATH} will handle future updates.")

        logging.info("Neovim and its configuration have been updated successfully.")

if __name__ == "__main__":
    main()
