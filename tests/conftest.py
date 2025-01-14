import pytest
from PySide6.QtWidgets import QApplication
from block_editor.core.label_manager import LabelManager
from block_editor.core.audio_block import AudioBlock

@pytest.fixture(scope="session")
def qapp():
    """Create a QApplication instance that can be reused for all tests."""
    app = QApplication.instance()
    if app is None:
        app = QApplication([])
    yield app

@pytest.fixture
def label_manager():
    """Create a fresh LabelManager instance for each test."""
    return LabelManager()

@pytest.fixture
def sample_blocks():
    """Create a list of sample AudioBlocks for testing."""
    return [
        AudioBlock(0.0, 1.0, False),
        AudioBlock(1.0, 2.0, True),
        AudioBlock(2.0, 3.0, False)
    ]

@pytest.fixture
def temp_config_dir(tmp_path):
    """Create a temporary config directory for testing."""
    config_dir = tmp_path / ".config" / "video_editor"
    config_dir.mkdir(parents=True)
    return config_dir

@pytest.fixture
def mock_ffmpeg_output():
    """Sample FFmpeg silence detection output."""
    return """
    [silencedetect @ 0x7f8a1c0] silence_start: 1.5
    [silencedetect @ 0x7f8a1c0] silence_end: 2.5 | silence_duration: 1.00
    [silencedetect @ 0x7f8a1c0] silence_start: 4.0
    [silencedetect @ 0x7f8a1c0] silence_end: 5.0 | silence_duration: 1.00
    """

@pytest.fixture
def mock_duration_output():
    """Sample FFprobe duration output."""
    return "10.0"