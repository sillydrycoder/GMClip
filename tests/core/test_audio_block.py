import pytest
from block_editor.core.audio_block import AudioBlock

def test_audio_block_creation():
    block = AudioBlock(start=0.0, end=1.0, is_silence=False)
    assert block.start == 0.0
    assert block.end == 1.0
    assert block.is_silence == False
    assert block.label is None
    assert block.include == True
    assert block.visited == False

def test_audio_block_to_dict():
    block = AudioBlock(start=0.0, end=1.0, is_silence=False)
    block.label = "test_label"
    block.visited = True
    
    block_dict = block.to_dict()
    assert block_dict == {
        'start': 0.0,
        'end': 1.0,
        'is_silence': False,
        'label': "test_label",
        'visited': True
    }

def test_audio_block_from_dict():
    data = {
        'start': 0.0,
        'end': 1.0,
        'is_silence': False,
        'label': "test_label",
        'visited': True
    }
    
    block = AudioBlock.from_dict(data)
    assert block.start == 0.0
    assert block.end == 1.0
    assert block.is_silence == False
    assert block.label == "test_label"
    assert block.visited == True