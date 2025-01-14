import pytest
import os
import json
from pathlib import Path
from PySide6.QtGui import QColor
from block_editor.core.label_manager import LabelManager, Label

@pytest.fixture
def temp_config_dir(tmp_path):
    """Create a temporary config directory for testing"""
    config_dir = tmp_path / ".config" / "video_editor"
    config_dir.mkdir(parents=True)
    return config_dir

@pytest.fixture
def label_manager(temp_config_dir, monkeypatch):
    """Create a LabelManager instance with temporary config directory"""
    monkeypatch.setattr(os.path, 'expanduser', lambda x: str(temp_config_dir.parent.parent))
    return LabelManager()

def test_label_creation():
    label = Label("test", QColor("#FF0000"), "t")
    assert label.name == "test"
    assert label.color.name() == "#ff0000"
    assert label.hotkey == "t"

def test_label_to_dict():
    label = Label("test", QColor("#FF0000"), "t")
    label_dict = label.to_dict()
    assert label_dict == {
        'name': "test",
        'color': "#ff0000",
        'hotkey': "t"
    }

def test_label_from_dict():
    data = {
        'name': "test",
        'color': "#FF0000",
        'hotkey': "t"
    }
    label = Label.from_dict(data)
    assert label.name == "test"
    assert label.color.name() == "#ff0000"
    assert label.hotkey == "t"

def test_label_manager_default_labels(label_manager):
    # Check if default labels are created
    assert "keep" in label_manager.labels
    assert "remove" in label_manager.labels
    
    keep_label = label_manager.labels["keep"]
    assert keep_label.name == "keep"
    assert keep_label.color.name() == "#00ff00"
    assert keep_label.hotkey == "k"
    
    remove_label = label_manager.labels["remove"]
    assert remove_label.name == "remove"
    assert remove_label.color.name() == "#ff0000"
    assert remove_label.hotkey == "r"

def test_label_manager_add_remove_label(label_manager):
    new_label = Label("test", QColor("#0000FF"), "t")
    label_manager.add_label(new_label)
    assert "test" in label_manager.labels
    
    label_manager.remove_label("test")
    assert "test" not in label_manager.labels

def test_label_manager_save_load(label_manager, temp_config_dir):
    # Add a custom label
    new_label = Label("test", QColor("#0000FF"), "t")
    label_manager.add_label(new_label)
    
    # Save labels
    label_manager.save_labels()
    
    # Create a new label manager instance to test loading
    new_manager = LabelManager()
    
    # Check if labels were loaded correctly
    assert "test" in new_manager.labels
    loaded_label = new_manager.labels["test"]
    assert loaded_label.name == "test"
    assert loaded_label.color.name() == "#0000ff"
    assert loaded_label.hotkey == "t"

def test_label_manager_get_label(label_manager):
    label = label_manager.get_label("keep")
    assert label is not None
    assert label.name == "keep"
    
    non_existent = label_manager.get_label("non_existent")
    assert non_existent is None