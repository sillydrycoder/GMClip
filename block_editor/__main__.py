import sys
import os
import argparse
import subprocess
from PySide6.QtWidgets import QApplication
from block_editor.gui.video_player import VideoPlayer
from block_editor.utils.unix_ffbinary_manager import install_mac_binaries

def check_ffmpeg():
    try:
        subprocess.run(["ffmpeg", "-version"], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        return True
    except FileNotFoundError:
        if sys.platform == 'darwin':
            success = install_mac_binaries()
            if success:
                return True
            else:
                return False
        elif sys.platform == 'linux':
            pass
        else:
            return False

def main():
    parser = argparse.ArgumentParser(description='Video Block Editor')
    parser.add_argument('--debug', action='store_true', help='Enable debug logging')
    args = parser.parse_args()

    if not check_ffmpeg():
        print("Error: ffmpeg cannot be resolved.")
        print("Please install ffmpeg and ffprobe and ensure they are in your PATH.")
        return

    app = QApplication([])  # Don't pass sys.argv since we parsed it
    player = VideoPlayer(debug=args.debug)
    player.show()
    sys.exit(app.exec())

if __name__ == "__main__":
    main()