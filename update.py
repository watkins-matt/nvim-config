#!/usr/bin/env python3

import requests
import logging
from subprocess import call, run, PIPE
import os
import sys
import shutil
from crontab import CronTab

# Configure logging
logging.basicConfig(
    stream=sys.stdout,
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    datefmt="%Y-%m-%d %I:%M:%S %p",
)

INSTALL_PATH = '/opt/nvim/update.py'
NVIM_DIR = '/opt/nvim/'
SYMLINK_PATH = '/usr/bin/nvim'
APPRUN_PATH = '/opt/nvim/squashfs-root/AppRun'
CONFIG_REPO = 'https://github.com/watkins-matt/nvim-config.git'
CONFIG_DIR = os.path.expanduser('~/.config/nvim')

def setup_directories():
    """Ensure the Neovim directory exists."""
    if not os.path.exists(NVIM_DIR):
        os.makedirs(NVIM_DIR)
        logging.info(f"Created directory {NVIM_DIR}")

def update_symlink():
    """Update the symbolic link in /usr/bin for Neovim if necessary."""
    symlink_updated = False

    # Remove old symlink in /opt/nvim if it exists
    old_symlink = '/opt/nvim/nvim'
    if os.path.islink(old_symlink):
        os.unlink(old_symlink)
        logging.info(f"Removed old symlink: {old_symlink}")
        symlink_updated = True

    # Check if the symlink needs to be updated
    if not os.path.islink(SYMLINK_PATH) or os.readlink(SYMLINK_PATH) != APPRUN_PATH:
        if os.path.exists(SYMLINK_PATH):
            os.remove(SYMLINK_PATH)
        os.symlink(APPRUN_PATH, SYMLINK_PATH)
        logging.info(f"Updated symlink: {SYMLINK_PATH} -> {APPRUN_PATH}")
        symlink_updated = True

    if symlink_updated:
        refresh_shell_cache()
    else:
        logging.info("Symlink is already up to date")

def refresh_shell_cache():
    """Refresh the shell's command cache if using Bash or Zsh."""
    shell = os.environ.get('SHELL', '').lower()
    if 'bash' in shell or 'zsh' in shell:
        os.system("hash -r")
        logging.info("Refreshed shell's command cache with 'hash -r'")
    else:
        logging.info("Shell command cache refresh may be needed.")
        logging.info("If 'nvim' command doesn't work, you may need to restart your shell or run a shell-specific cache refresh command.")

def extract_appimage():
    """Extract the Neovim AppImage and setup symbolic links."""
    appimage_path = os.path.join(NVIM_DIR, 'nvim.appimage')
    extract_path = os.path.join(NVIM_DIR, 'squashfs-root')

    if os.path.exists(extract_path):
        logging.info("Removing old extracted AppImage directory")
        shutil.rmtree(extract_path)

    logging.info("Extracting AppImage")
    os.chdir(NVIM_DIR)
    with open(os.devnull, 'w') as FNULL:
        call([appimage_path, '--appimage-extract'], stdout=FNULL, stderr=FNULL)

    logging.info("Extraction complete")
    update_symlink()

def download_nvim():
    """Download and update the Neovim AppImage."""
    nvim_appimage_path = os.path.join(NVIM_DIR, 'nvim.appimage')
    logging.info("Attempting to download new version of Neovim AppImage")
    call(["curl", "-Lo", nvim_appimage_path, "https://github.com/neovim/neovim/releases/latest/download/nvim.appimage"])
    os.chmod(nvim_appimage_path, 0o755)  # Ensure the downloaded file is executable
    logging.info("Download complete and permissions set")
    extract_appimage()

def is_nvim_installed_correctly():
    """Check if Neovim is installed correctly."""
    return os.path.exists(os.path.join(NVIM_DIR, 'squashfs-root/AppRun'))

def setup_crontab():
    """Set up a crontab entry to run the update script nightly."""
    cron = CronTab(user=True)
    update_command = f"python3 {INSTALL_PATH}"

    # Check if the job already exists
    update_job = next((job for job in cron if job.command == update_command), None)

    if not update_job:
        update_job = cron.new(command=update_command)
        update_job.setall('0 2 * * *')  # Run at 2 AM every day
        cron.write()
        logging.info("Crontab entry added for nightly Neovim and config updates")
    else:
        logging.info("Crontab entry for nightly updates already exists")

def check_update():
    """Check for updates to Neovim and download if a newer version is found."""
    setup_directories()
    logging.info("Checking for new Neovim releases")
    current_version_url = "https://api.github.com/repos/neovim/neovim/releases/latest"
    response = requests.get(current_version_url)
    latest_version = response.json()['tag_name']
    version_file_path = os.path.join(NVIM_DIR, 'version.txt')

    if not os.path.exists(version_file_path):
        with open(version_file_path, 'w') as file:
            file.write("None")
        logging.info("Version file created")

    with open(version_file_path, 'r') as file:
        current_version = file.read().strip()

    if current_version != latest_version or not is_nvim_installed_correctly():
        logging.info(f"New version found: {latest_version}. Current version: {current_version}")
        download_nvim()
        with open(version_file_path, 'w') as file:
            file.write(latest_version)
        logging.info("Version updated")
    else:
        logging.info("No updates found")

    # Ensure symlink is correct even if no update was needed
    update_symlink()

def install_script():
    """Copy the script to /opt/nvim/update.py if it doesn't exist."""
    # Ensure the directory exists
    os.makedirs(os.path.dirname(INSTALL_PATH), exist_ok=True)

    if not os.path.exists(INSTALL_PATH):
        shutil.copy2(__file__, INSTALL_PATH)
        os.chmod(INSTALL_PATH, 0o755)  # Make the script executable
        logging.info(f"Script installed to {INSTALL_PATH}")
    else:
        logging.info(f"Script already installed at {INSTALL_PATH}")

def is_git_installed():
    """Check if git is installed on the system."""
    return shutil.which('git') is not None

def is_correct_git_repo(directory, expected_remote):
    """Check if the given directory is a git repo with the expected remote."""
    if not os.path.exists(os.path.join(directory, '.git')):
        return False

    result = run(['git', '-C', directory, 'remote', 'get-url', 'origin'], stdout=PIPE, stderr=PIPE, universal_newlines=True)
    return result.returncode == 0 and result.stdout.strip() == expected_remote

def clone_or_update_config_repo():
    """Clone the Neovim configuration repository or update if it exists."""
    if not is_git_installed():
        logging.error("Git is not installed. Please install git and run the script again.")
        sys.exit(1)

    if os.path.exists(CONFIG_DIR):
        if is_correct_git_repo(CONFIG_DIR, CONFIG_REPO):
            logging.info(f"Existing correct config repository found in {CONFIG_DIR}")
            update_config()
        else:
            logging.info(f"Removing existing incorrect config directory: {CONFIG_DIR}")
            shutil.rmtree(CONFIG_DIR)
            clone_config_repo()
    else:
        clone_config_repo()

def clone_config_repo():
    """Clone the Neovim configuration repository."""
    logging.info(f"Cloning Neovim config repository to {CONFIG_DIR}")
    result = run(['git', 'clone', CONFIG_REPO, CONFIG_DIR], stdout=PIPE, stderr=PIPE, universal_newlines=True)
    if result.returncode == 0:
        logging.info("Neovim config repository cloned successfully")
    else:
        logging.error(f"Failed to clone Neovim config repository: {result.stderr}")

def update_config():
    """Update the Neovim configuration repository, backing up local changes and resetting to the latest remote version."""
    logging.info("Updating Neovim config repository")
    os.chdir(CONFIG_DIR)

    # Check for local changes
    result = run(['git', 'status', '--porcelain'], stdout=PIPE, stderr=PIPE, universal_newlines=True)
    if result.stdout.strip():
        backup_dir = os.path.expanduser('~/nvim_config_backup/')
        os.makedirs(backup_dir, exist_ok=True)
        logging.warning("Local changes detected in Neovim config repository")

        # Backup modified files to ~/nvim_config_backup/
        logging.info(f"Backing up local changes to {backup_dir}")
        modified_files = result.stdout.strip().splitlines()
        for line in modified_files:
            file_path = line[3:]  # Remove the status characters from git status output
            abs_file_path = os.path.join(CONFIG_DIR, file_path)
            backup_file_path = os.path.join(backup_dir, file_path)

            if os.path.exists(abs_file_path):
                os.makedirs(os.path.dirname(backup_file_path), exist_ok=True)
                shutil.copy2(abs_file_path, backup_file_path)
                logging.info(f"Backed up {abs_file_path} to {backup_file_path}")

    # Force pull the latest changes by resetting the repository to the latest remote version
    result = run(['git', 'fetch', 'origin'], stdout=PIPE, stderr=PIPE, universal_newlines=True)
    if result.returncode == 0:
        run(['git', 'reset', '--hard', 'origin/master'], stdout=PIPE, stderr=PIPE)
        logging.info("Neovim config repository reset to latest remote commit")
    else:
        logging.error(f"Failed to fetch the latest remote changes: {result.stderr}")
        return

    logging.info("Neovim config repository updated successfully")


def create_update_alias():
    """Create an alias for instant config updates and reload shell configuration."""
    shell = os.environ.get('SHELL', '').lower()
    if 'bash' in shell:
        rc_file = os.path.expanduser('~/.bashrc')
        reload_command = f"source {rc_file}"
    elif 'zsh' in shell:
        rc_file = os.path.expanduser('~/.zshrc')
        reload_command = f"source {rc_file}"
    else:
        logging.warning("Unsupported shell. Unable to create alias.")
        return

    alias_line = f"\nalias update-nvim-config='python3 {INSTALL_PATH} --config'\n"

    alias_added = False
    with open(rc_file, 'a+') as f:
        f.seek(0)
        content = f.read()
        if 'alias update-nvim-config' not in content:
            f.write(alias_line)
            alias_added = True
            logging.info(f"Alias 'update-nvim-config' added to {rc_file}")
        else:
            logging.info("Alias 'update-nvim-config' already exists")

    if alias_added:
        # Attempt to reload the shell configuration
        try:
            os.system(reload_command)
            logging.info(f"Shell configuration reloaded. The 'update-nvim-config' alias should now be available.")
        except Exception as e:
            logging.warning(f"Failed to reload shell configuration: {e}")
            logging.info("Please run the following command to use the new alias in the current session:")
            logging.info(f"    {reload_command}")

    logging.info("To use the 'update-nvim-config' alias in new terminal sessions, no further action is needed.")
    logging.info("For the current session, you may need to run the following command if the alias is not working:")
    logging.info(f"    {reload_command}")

def uninstall():
    """Remove the crontab entries, symlink, /opt/nvim directory, and config directory."""
    # Remove crontab entries
    cron = CronTab(user=True)
    cron.remove_all(command=f"python3 {INSTALL_PATH}")
    cron.remove_all(command=f"python3 {INSTALL_PATH} --config")
    cron.write()
    logging.info("Removed crontab entries")

    # Remove symlink
    if os.path.islink(SYMLINK_PATH):
        os.unlink(SYMLINK_PATH)
        logging.info(f"Removed symlink from {SYMLINK_PATH}")

    # Remove /opt/nvim directory and config directory
    dirs_to_remove = [NVIM_DIR, CONFIG_DIR]
    if os.path.abspath(sys.argv[0]).startswith(os.path.abspath(NVIM_DIR)):
        logging.info(f"Script is running from {NVIM_DIR}. Will delete directories after script completion.")
        # Create a separate script to delete the directories
        delete_script = f'''
import shutil
import os

dirs_to_delete = {dirs_to_remove}
for dir in dirs_to_delete:
    if os.path.exists(dir):
        shutil.rmtree(dir)
        print(f"Removed directory {{dir}}")
os.remove(__file__)
'''
        with open('/tmp/delete_nvim.py', 'w') as f:
            f.write(delete_script)
        os.chmod('/tmp/delete_nvim.py', 0o755)
        # Schedule the delete script to run after this script exits
        os.system(f"(sleep 1 && python3 /tmp/delete_nvim.py)&")
    else:
        for dir in dirs_to_remove:
            if os.path.exists(dir):
                shutil.rmtree(dir)
                logging.info(f"Removed directory {dir}")

    logging.info("Uninstallation complete")

def main():
    if not is_git_installed():
        logging.error("Git is not installed. Please install git and run the script again.")
        sys.exit(1)

    if len(sys.argv) > 1:
        if sys.argv[1] == '--uninstall':
            uninstall()
        elif sys.argv[1] == '--config':
            clone_or_update_config_repo()
        else:
            logging.error(f"Unknown argument: {sys.argv[1]}")
    else:
        install_script()
        check_update()
        clone_or_update_config_repo()
        setup_crontab()
        create_update_alias()

        current_script_path = os.path.abspath(__file__)
        if current_script_path != INSTALL_PATH:
            logging.info("Initial setup complete.")
            logging.info(f"The script has been installed to {INSTALL_PATH}")
            if not current_script_path.startswith(NVIM_DIR):
                logging.info(f"You can safely delete this script at {current_script_path}")
            logging.info(f"Future updates will be handled by the installed script at {INSTALL_PATH}")
        else:
            logging.info("Update process complete.")
            logging.info(f"This script at {INSTALL_PATH} will handle future updates.")

        logging.info("Neovim has been installed/updated. You can now use the 'nvim' command.")
        logging.info("Your Neovim configuration has been set up.")
        logging.info("Both Neovim and its configuration will be updated nightly.")
        logging.info("The 'update-nvim-config' alias has been created for instant config updates.")
        logging.info("If the alias doesn't work immediately, please reload your shell configuration.")

if __name__ == '__main__':
    main()
