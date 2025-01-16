import os
import requests
import shutil
import tempfile
import subprocess

# Example usage
mac_binary_urls = [
    "https://evermeet.cx/ffmpeg/ffmpeg-118273-g251de1791e.7z",
    "https://evermeet.cx/ffmpeg/ffprobe-118273-g251de1791e.7z"
]

def install_mac_binaries():
    dest_dir = "/usr/local/bin"
    success = True

    # Ensure destination directory exists
    if not os.path.exists(dest_dir):
        print(f"Destination directory '{dest_dir}' does not exist.")
        return False

    for url in mac_binary_urls:
        try:
            print(f"Processing {url}...")
            # Create a temporary file for downloading
            with tempfile.TemporaryDirectory() as tmp_dir:
                file_name = os.path.join(tmp_dir, os.path.basename(url))

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
                subprocess.run(["7z", "x", file_name, f"-o{extract_dir}"], check=True)

                # Move the binaries to the destination directory
                for root, _, files in os.walk(extract_dir):
                    for file in files:
                        source_path = os.path.join(root, file)
                        dest_path = os.path.join(dest_dir, file)
                        print(f"Moving {source_path} to {dest_path}...")
                        shutil.move(source_path, dest_path)

                print(f"Installed binaries from {url}.")

        except Exception as e:
            print(f"Failed to process {url}: {e}")
            success = False

    return success
