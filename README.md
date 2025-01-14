# Video Block Editor

A sophisticated video editing tool designed to split videos into labeled segments with customizable playback and export options. The tool is particularly useful for content creators who need to segment and categorize parts of longer videos.

## Features

- **Video Processing**
  - Automatic silence detection for block segmentation
  - FFmpeg integration for video processing and export
  - Maintains original video quality during exports

- **Block Management**
  - Splits videos into blocks based on silence detection
  - Visual timeline with color-coded blocks
  - Block navigation with keyboard shortcuts
  - Support for labeling and categorizing blocks

- **User Interface**
  - Customizable controls panel
  - Interactive timeline with zoom functionality
  - Preview mode for labeled segments
  - Label manager for custom categories
  - Progress tracking for block navigation

- **Export Capabilities**
  - Export blocks by label
  - Maintains original video quality
  - Automatic file naming based on labels
  - Support for multiple export formats

- **State Management**
  - Save/load functionality for block states
  - Persistent label configurations
  - Session recovery support

## Installation

1. System Requirements:
   - Python 3.8 or higher
   - FFmpeg installed and accessible from command line
   - System-level video codec support

2. Install FFmpeg:
   ```bash
   # Ubuntu/Debian
   sudo apt-get install ffmpeg

   # MacOS
   brew install ffmpeg

   # Windows
   # Download from https://ffmpeg.org/download.html
   ```

3. Install the package:
   ```bash
   pip install -r requirements.txt
   pip install .
   ```

## Usage

1. Start the application:
   ```bash
   block-editor
   ```

2. Controls and Shortcuts:
   - Space: Play/Pause video
   - Left/Right Arrow: Navigate between blocks
   - K: Quick label as "keep"
   - R: Quick label as "remove"
   - +/-: Zoom timeline view in/out
   - \: Open label manager
   - Tab: Toggle between read/write modes

## Configuration

- Labels are stored in ~/.config/video_editor/labels.json
- Project states can be saved and loaded for session recovery
- Custom labels can be created with unique colors and hotkeys

## Development

1. Clone the repository:
   ```bash
   git clone https://github.com/yourusername/block-editor.git
   cd block-editor
   ```

2. Install development dependencies:
   ```bash
   pip install -e ".[dev]"
   ```

3. Run tests:
   ```bash
   pytest
   ```

## Target Users

- Content creators
- Video editors
- Researchers working with video content
- Anyone needing to segment and categorize video content

## Use Cases

1. Content editing - Marking segments to keep or remove
2. Video analysis - Categorizing different types of content
3. Educational content - Segmenting lectures or tutorials
4. Research - Analyzing and categorizing video segments

## License

This project is licensed under the MIT License - see the LICENSE file for details.

## Contributing

1. Fork the repository
2. Create your feature branch (`git checkout -b feature/amazing-feature`)
3. Commit your changes (`git commit -m 'Add some amazing feature'`)
4. Push to the branch (`git push origin feature/amazing-feature`)
5. Open a Pull Request

## Acknowledgments

- FFmpeg for video processing capabilities
- Qt/PySide6 for the GUI framework
- All contributors who have helped shape this project
