import sys
import os
import argparse
import subprocess
from PySide6.QtWidgets import QApplication
from block_editor.gui.video_player import VideoPlayer

if not hasattr(sys, 'frozen'):
    sys.stdout = open(os.devnull, 'w')
    sys.stderr = open(os.devnull, 'w')

def check_ffmpeg():
    try:
        subprocess.run(["ffmpeg", "-version"], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        return True
    except FileNotFoundError:
        return False

def main():
    parser = argparse.ArgumentParser(description='Video Block Editor')
    parser.add_argument('--debug', action='store_true', help='Enable debug logging')
    args = parser.parse_args()

    if not check_ffmpeg():
        print("Error: ffmpeg is not installed or not found in the system PATH.")
        print("Please install ffmpeg and make sure it's accessible from the command line.")
        return

    app = QApplication([])  # Don't pass sys.argv since we parsed it
    player = VideoPlayer(debug=args.debug)
    player.show()
    sys.exit(app.exec())

if __name__ == "__main__":
    main()