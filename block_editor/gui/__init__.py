"""
GUI components for the Video Block Editor.
"""

from .video_player import VideoPlayer
from .custom_widgets import CustomSlider, BlockTimeline
from .dialogs import LabelDialog, PreviewDialog

__all__ = [
    'VideoPlayer',
    'CustomSlider',
    'BlockTimeline',
    'LabelDialog',
    'PreviewDialog'
]
