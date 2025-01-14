import pytest
import subprocess
from unittest.mock import patch, MagicMock
from block_editor.utils.silence_detector import SilenceDetector

@pytest.fixture
def silence_detector():
    return SilenceDetector("test_video.mp4")

@pytest.fixture
def mock_ffmpeg_output():
    return """
    [silencedetect @ 0x7f8a1c0] silence_start: 1.5
    [silencedetect @ 0x7f8a1c0] silence_end: 2.5 | silence_duration: 1.00
    [silencedetect @ 0x7f8a1c0] silence_start: 4.0
    [silencedetect @ 0x7f8a1c0] silence_end: 5.0 | silence_duration: 1.00
    """

@pytest.fixture
def mock_duration_output():
    return "10.0\n"

def test_silence_detector_initialization(silence_detector):
    assert silence_detector.input_file == "test_video.mp4"
    assert silence_detector.silence_threshold == -40
    assert silence_detector.min_silence_duration == 0.1

@patch('subprocess.run')
def test_detect_blocks(mock_run, silence_detector, mock_ffmpeg_output, mock_duration_output):
    # Create mock processes with proper attributes
    mock_ffmpeg_process = MagicMock()
    mock_ffmpeg_process.returncode = 0
    mock_ffmpeg_process.stderr = mock_ffmpeg_output
    mock_ffmpeg_process.stdout = ""
    
    mock_duration_process = MagicMock()
    mock_duration_process.returncode = 0
    mock_duration_process.stdout = mock_duration_output
    mock_duration_process.stderr = ""
    
    def mock_run_side_effect(*args, **kwargs):
        if '-af' in args[0]:  # FFmpeg silence detection command
            return mock_ffmpeg_process
        elif 'ffprobe' in args[0]:  # FFprobe duration command
            return mock_duration_process
        return MagicMock()
    
    mock_run.side_effect = mock_run_side_effect
    
    blocks = silence_detector.detect_blocks()
    
    # We should have 5 blocks:
    # 1. 0.0 -> 1.5 (non-silence)
    # 2. 1.5 -> 2.5 (silence)
    # 3. 2.5 -> 4.0 (non-silence)
    # 4. 4.0 -> 5.0 (silence)
    # 5. 5.0 -> 10.0 (non-silence)
    assert len(blocks) == 5
    
    # Check first non-silence block
    assert blocks[0].start == 0.0
    assert blocks[0].end == 1.5
    assert not blocks[0].is_silence
    
    # Check first silence block
    assert blocks[1].start == 1.5
    assert blocks[1].end == 2.5
    assert blocks[1].is_silence
    
    # Check middle non-silence block
    assert blocks[2].start == 2.5
    assert blocks[2].end == 4.0
    assert not blocks[2].is_silence
    
    # Check second silence block
    assert blocks[3].start == 4.0
    assert blocks[3].end == 5.0
    assert blocks[3].is_silence
    
    # Check final non-silence block
    assert blocks[4].start == 5.0
    assert blocks[4].end == 10.0
    assert not blocks[4].is_silence

@patch('subprocess.run')
def test_detect_blocks_ffmpeg_error(mock_run, silence_detector):
    mock_process = MagicMock()
    mock_process.returncode = 1
    mock_process.stderr = "FFmpeg error"
    mock_run.return_value = mock_process
    
    with pytest.raises(Exception, match="FFmpeg failed to process the video"):
        silence_detector.detect_blocks()
