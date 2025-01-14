import json
from .audio_block import AudioBlock
from ..utils.silence_detector import SilenceDetector

class BlockManager:
    def __init__(self):
        self.blocks = []
        self.video_path = None

    def set_video_path(self, video_path):
        """Just set the video path without processing blocks"""
        self.video_path = video_path
        self.blocks = []

    def process_blocks(self, silence_settings=None):
        """Process the video to detect silence blocks"""
        if not self.video_path:
            print("[DEBUG] process_blocks: No video path set")
            return False
            
        try:
            if silence_settings:
                silence_detector = SilenceDetector(
                    self.video_path,
                    silence_threshold=silence_settings['threshold'],
                    min_silence_duration=silence_settings['duration'],
                    non_silence_buffer=silence_settings['buffer']
                )
            else:
                silence_detector = SilenceDetector(self.video_path)
            self.blocks = silence_detector.detect_blocks()
            print(f"[DEBUG] process_blocks: Successfully detected {len(self.blocks)} blocks")
            return True
        except Exception as e:
            print(f"[DEBUG] process_blocks: Error processing blocks - {str(e)}")
            return False

    def save_state(self, filepath):
        if not self.blocks:
            return False
        
        state = {
            'video_path': self.video_path,
            'blocks': [block.to_dict() for block in self.blocks]
        }
        
        try:
            with open(filepath, 'w') as f:
                json.dump(state, f)
            return True
        except Exception as e:
            print(f"Error saving state: {e}")
            return False

    def load_state(self, filepath):
        try:
            with open(filepath, 'r') as f:
                state = json.load(f)
            
            self.video_path = state['video_path']
            self.blocks = [AudioBlock.from_dict(block_data) for block_data in state['blocks']]
            # Get the duration from the last block's end time
            if self.blocks:
                self.duration = self.blocks[-1].end
            return True
        except Exception as e:
            print(f"Error loading state: {e}")
            return False

    def reset_blocks(self):
        for block in self.blocks:
            block.visited = False
            block.label = None
