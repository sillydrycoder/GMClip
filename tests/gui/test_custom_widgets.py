import pytest
from PySide6.QtCore import Qt
from block_editor.gui.custom_widgets import CustomSlider, BlockTimeline
from block_editor.core.audio_block import AudioBlock

@pytest.fixture
def sample_blocks():
    return [
        AudioBlock(0.0, 1.0, False),
        AudioBlock(1.0, 2.0, True),
        AudioBlock(2.0, 3.0, False)
    ]

def test_custom_slider_initialization(qapp):
    slider = CustomSlider(Qt.Horizontal)
    assert slider.orientation() == Qt.Horizontal
    assert not slider.isDestroyed()

def test_custom_slider_delete_later(qapp):
    slider = CustomSlider(Qt.Horizontal)
    slider.deleteLater()
    assert slider.isDestroyed()

def test_block_timeline_initialization(qapp):
    timeline = BlockTimeline()
    assert timeline.blocks == []
    assert timeline.current_position == 0
    assert timeline.visible_blocks == 200
    assert timeline.total_duration == 0
    assert timeline.minimumHeight() == 60

def test_block_timeline_set_blocks(qapp, sample_blocks):
    timeline = BlockTimeline()
    timeline.setBlocks(sample_blocks, 3.0)
    assert timeline.blocks == sample_blocks
    assert timeline.total_duration == 3.0

def test_block_timeline_set_current_position(qapp):
    timeline = BlockTimeline()
    timeline.setCurrentPosition(1.5)
    assert timeline.current_position == 1.5

def test_block_timeline_set_visible_blocks(qapp):
    timeline = BlockTimeline()
    timeline.setVisibleBlocks(100)
    assert timeline.visible_blocks == 100
