import pytest
import json
from pathlib import Path
from block_editor.core.block_manager import BlockManager
from block_editor.core.audio_block import AudioBlock

@pytest.fixture
def block_manager():
    return BlockManager()

@pytest.fixture
def sample_blocks():
    return [
        AudioBlock(0.0, 1.0, False),
        AudioBlock(1.0, 2.0, True),
        AudioBlock(2.0, 3.0, False)
    ]

@pytest.fixture
def temp_state_file(tmp_path):
    return tmp_path / "test_state.json"

def test_block_manager_initialization(block_manager):
    assert block_manager.blocks == []
    assert block_manager.video_path is None

def test_set_video_path(block_manager):
    test_path = "test_video.mp4"
    block_manager.set_video_path(test_path)
    assert block_manager.video_path == test_path
    assert block_manager.blocks == []

def test_reset_blocks(block_manager, sample_blocks):
    block_manager.blocks = sample_blocks
    # Mark some blocks as visited and labeled
    block_manager.blocks[0].visited = True
    block_manager.blocks[0].label = "test"
    block_manager.blocks[2].visited = True
    block_manager.blocks[2].label = "test"
    
    block_manager.reset_blocks()
    
    for block in block_manager.blocks:
        assert block.visited == False
        assert block.label is None

def test_save_state(block_manager, sample_blocks, temp_state_file):
    block_manager.video_path = "test_video.mp4"
    block_manager.blocks = sample_blocks
    block_manager.blocks[0].label = "test"
    block_manager.blocks[0].visited = True
    
    assert block_manager.save_state(temp_state_file) == True
    
    # Verify the saved state
    with open(temp_state_file, 'r') as f:
        state = json.load(f)
        assert state['video_path'] == "test_video.mp4"
        assert len(state['blocks']) == 3
        assert state['blocks'][0]['visited'] == True
        assert state['blocks'][0]['label'] == "test"

def test_load_state(block_manager, sample_blocks, temp_state_file):
    # First save a state
    block_manager.video_path = "test_video.mp4"
    block_manager.blocks = sample_blocks
    block_manager.blocks[0].label = "test"
    block_manager.blocks[0].visited = True
    block_manager.save_state(temp_state_file)
    
    # Create a new block manager and load the state
    new_manager = BlockManager()
    assert new_manager.load_state(temp_state_file) == True
    
    assert new_manager.video_path == "test_video.mp4"
    assert len(new_manager.blocks) == 3
    assert new_manager.blocks[0].visited == True
    assert new_manager.blocks[0].label == "test"
    assert new_manager.blocks[1].is_silence == True

def test_save_state_no_blocks(block_manager, temp_state_file):
    assert block_manager.save_state(temp_state_file) == False

def test_load_state_invalid_file(block_manager, temp_state_file):
    assert block_manager.load_state("nonexistent_file.json") == False

def test_process_blocks_no_video_path(block_manager):
    assert block_manager.process_blocks() == False