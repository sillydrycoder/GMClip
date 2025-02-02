import os
import requests
import shutil
import tempfile
import py7zr
import subprocess

# Example usage
mac_binary_urls = [
    "https://evermeet.cx/ffmpeg/ffmpeg-118273-g251de1791e.7z",
    "https://evermeet.cx/ffmpeg/ffprobe-118273-g251de1791e.7z"
]

def sanitize_filename(url):
    """
    Extracts a clean filename from a URL.
    """
    return os.path.basename(url.split("?")[0])

def install_7z():
    """
    Installs 7z using Homebrew if not already installed.
    """
    try:
        print("Checking if 7z is installed...")
        subprocess.run(["7z", "--help"], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, check=True)
        print("7z is already installed.")
    except FileNotFoundError:
        print("7z not found. Installing via Homebrew...")
        subprocess.run(["brew", "install", "p7zip"], check=True)
        print("7z installed successfully.")

def install_unix_binaries():
    dest_dir = "/usr/local/bin"
    success = True

    # Ensure destination directory exists
    if not os.path.exists(dest_dir):
        print(f"Destination directory '{dest_dir}' does not exist.")
        return False

    # Ensure 7z is installed
    install_7z()

    for url in mac_binary_urls:
        try:
            print(f"Processing {url}...")
            # Create a temporary file for downloading
            with tempfile.TemporaryDirectory() as tmp_dir:
                file_name = os.path.join(tmp_dir, sanitize_filename(url))

                # Download the file
                print(f"Downloading {url}...")
                response = requests.get(url, stream=True)
                response.raise_for_status()

                with open(file_name, 'wb') as f:
                    shutil.copyfileobj(response.raw, f)
                print(f"Downloaded to {file_name}")

                # Extract the file
                print(f"Extracting {file_name}...")
                extract_dir = os.path.join(tmp_dir, "extracted")
                os.makedirs(extract_dir, exist_ok=True)

                # Try py7zr first
                try:
                    with py7zr.SevenZipFile(file_name, mode='r') as archive:
                        archive.extractall(path=extract_dir)
                except Exception as e:
                    print(f"py7zr extraction failed: {e}. Falling back to system '7z'.")
                    # Fallback to system 7z command
                    subprocess.run(["7z", "x", file_name, f"-o{extract_dir}"], check=True)

                # Move the binaries to the destination directory using sudo cp
                for root, _, files in os.walk(extract_dir):
                    for file in files:
                        source_path = os.path.join(root, file)
                        dest_path = os.path.join(dest_dir, file)
                        print(f"Copying {source_path} to {dest_path} using sudo cp...")
                        # for sudo approach.
                        subprocess.run(["sudo", "cp", source_path, dest_path], check=True)

                print(f"Installed binaries from {url}.")

        except Exception as e:
            print(f"Failed to process {url}: {e}")
            success = False

    return success
