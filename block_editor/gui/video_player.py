import sys
import os
import subprocess
import json
from PySide6.QtWidgets import (
    QMainWindow, QWidget, QVBoxLayout, QHBoxLayout, 
    QSlider, QPushButton, QFileDialog, QLabel, QMessageBox, QProgressBar,
    QGroupBox, QProgressDialog, QSizePolicy, QScrollArea, QDialog, QApplication
)
from PySide6.QtGui import QShortcut, QKeySequence
from PySide6.QtCore import Qt, QTimer, QUrl
from PySide6.QtMultimedia import QMediaPlayer, QAudioOutput
from PySide6.QtMultimediaWidgets import QVideoWidget

from ..core.block_manager import BlockManager
from ..core.label_manager import LabelManager
from .custom_widgets import CustomSlider, BlockTimeline
from .dialogs import LabelDialog, PreviewDialog, SilenceSettingsDialog

class VideoPlayer(QMainWindow):
    def __init__(self, debug=False):
        super().__init__()
        self.debug = debug
        self.block_manager = BlockManager()
        self.current_block_index = 0
        self.last_jumped_block_index = 0
        self.label_manager = LabelManager()
        self.label_buttons = {}
        self.label_shortcuts = {}

        # Initialize UI components to None
        self.media_player = None
        self.audio_output = None
        self.video_widget = None
        self.timeline_slider = None
        self.block_timeline = None
        self.progress_bar = None
        self.mode_label = None
        self.skip_timer = None

        # Initialize control buttons to None
        self.toggle_controls_button = None
        self.button_container = None
        self.play_pause_button = None
        self.prev_block_button = None
        self.next_block_button = None
        self.open_file_button = None
        self.save_state_button = None
        self.load_state_button = None
        self.reset_blocks_button = None
        self.export_button = None
        self.preview_button = None
        self.zoom_in_button = None
        self.zoom_out_button = None
        self.help_button = None

        # Initialize UI
        self.init_ui()
        self.setup_shortcuts()
        self.set_initial_button_states()
        self.show_welcome_screen()

    def set_initial_button_states(self):
        """Disable buttons that require a video to be loaded"""
        buttons_requiring_video = [
            self.play_pause_button,
            self.prev_block_button,
            self.next_block_button,
            self.save_state_button,
            self.export_button,
            self.preview_button,
            self.zoom_in_button,
            self.zoom_out_button,
            self.reset_blocks_button
        ]
        
        for button in buttons_requiring_video:
            if button is not None:  # Check if button exists
                button.setEnabled(False)

    def toggle_controls(self):
        if self.toggle_controls_button.isChecked():
            self.button_container.show()
            self.toggle_controls_button.setText("Hide Controls")
        else:
            self.button_container.hide()
            self.toggle_controls_button.setText("Show Controls")
        
        # Force layout update
        if self.centralWidget() and self.centralWidget().layout():
            self.centralWidget().layout().update()
        QApplication.processEvents()

    def load_video(self, video_path):
        """Load a video file and initialize the player."""
        if not video_path:
            return False

        try:
            if self.debug:
                print(f"[DEBUG] load_video: Loading video from {video_path}")
                
            self.media_player.setSource(QUrl.fromLocalFile(video_path))
            self.block_manager.set_video_path(video_path)
            
            # Show processing dialog
            dialog = self.show_processing_dialog()
            
            # Show silence settings dialog
            settings_dialog = SilenceSettingsDialog(self)
            if settings_dialog.exec():
                settings = settings_dialog.get_settings()
                success = self.block_manager.process_blocks(settings)
            else:
                dialog.close()
                return False
            dialog.close()
            
            if success:
                if self.debug:
                    print(f"[DEBUG] load_video: Successfully processed {len(self.block_manager.blocks)} blocks")
                    
                self.current_block_index = 0
                self.last_jumped_block_index = 0
                self.block_timeline.setBlocks(self.block_manager.blocks, self.media_player.duration() / 1000.0)
                self.enable_controls()
                
                # Ensure audio is enabled and unmuted
                self.audio_output.setMuted(False)
                self.audio_output.setVolume(1.0)
                
                if self.debug:
                    print("[DEBUG] load_video: Setup complete")
                    
                return True
            else:
                if self.debug:
                    print("[DEBUG] load_video: Failed to process blocks")
                QMessageBox.warning(self, "Error", "Failed to process blocks!")
                return False
                
        except Exception as e:
            if self.debug:
                print(f"[DEBUG] load_video: Error loading video: {str(e)}")
            QMessageBox.critical(self, "Error", f"Failed to load video: {str(e)}")
            return False
            
    def open_file(self):
        if self.debug:
            print("[DEBUG] open_file: Starting file selection")
            
        file_dialog = QFileDialog(self)
        video_path, _ = file_dialog.getOpenFileName(self, "Open Video File", "", "Video Files (*.mp4 *.avi *.mov)")
        
        if video_path:
            self.load_video(video_path)

    def init_ui(self):
        self.setWindowTitle("Video Player with Block Editor")
        self.setGeometry(100, 100, 400, 800)  # Taller, narrower initial window

        # Create a scroll area as the central widget
        scroll_area = QScrollArea(self)
        self.setCentralWidget(scroll_area)
        scroll_area.setWidgetResizable(True)
        scroll_area.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        scroll_area.setVerticalScrollBarPolicy(Qt.ScrollBarAsNeeded)

        # Main container inside scroll area
        main_container = QWidget()
        scroll_area.setWidget(main_container)
        
        # Main layout
        main_layout = QVBoxLayout(main_container)
        main_layout.setContentsMargins(10, 10, 10, 10)
        main_layout.setSpacing(5)

        self.setup_controls(main_layout)
        self.setup_video_widget(main_layout)
        self.setup_timeline(main_layout)
        self.setup_progress_bar(main_layout)
        self.setup_mode_label(main_layout)
        self.setup_label_controls(main_layout)

        # Media player setup
        self.media_player = QMediaPlayer()
        self.audio_output = QAudioOutput()
        self.media_player.setAudioOutput(self.audio_output)
        self.media_player.setVideoOutput(self.video_widget)

        # Connect media player signals
        self.media_player.positionChanged.connect(self.position_changed)
        self.media_player.durationChanged.connect(self.duration_changed)

        # Timer for skipping silences
        self.skip_timer = QTimer(self)
        self.skip_timer.timeout.connect(self.skip_silence)

    def setup_controls(self, main_layout):
        # Toggle button for showing/hiding controls
        self.toggle_controls_button = QPushButton("Show Controls")
        self.toggle_controls_button.setCheckable(True)
        self.toggle_controls_button.clicked.connect(self.toggle_controls)
        main_layout.addWidget(self.toggle_controls_button)

        # Button container at the top (hidden by default)
        self.button_container = QWidget()
        self.button_container.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Minimum)
        button_layout = QVBoxLayout(self.button_container)
        button_layout.setSpacing(2)
        self.button_container.hide()
        main_layout.addWidget(self.button_container)

        # Create control groups
        self.create_file_group(button_layout)
        self.create_playback_group(button_layout)
        self.create_block_group(button_layout)
        self.create_view_group(button_layout)

    def create_file_group(self, parent_layout):
        file_group = QGroupBox("File")
        file_layout = QVBoxLayout(file_group)
        
        self.open_file_button = QPushButton("Open Video")
        self.open_file_button.clicked.connect(self.open_file)
        self.save_state_button = QPushButton("Save State")
        self.save_state_button.clicked.connect(self.save_state)
        self.load_state_button = QPushButton("Load State")
        self.load_state_button.clicked.connect(self.load_state)
        
        file_layout.addWidget(self.open_file_button)
        file_layout.addWidget(self.save_state_button)
        file_layout.addWidget(self.load_state_button)
        parent_layout.addWidget(file_group)

    def create_playback_group(self, parent_layout):
        playback_group = QGroupBox("Playback")
        playback_layout = QVBoxLayout(playback_group)
        
        self.play_pause_button = QPushButton("Play")
        self.play_pause_button.clicked.connect(self.play_pause)
        self.prev_block_button = QPushButton("Previous")
        self.prev_block_button.clicked.connect(self.goto_previous_block)
        self.next_block_button = QPushButton("Next")
        self.next_block_button.clicked.connect(self.goto_next_block)
        
        playback_layout.addWidget(self.play_pause_button)
        playback_layout.addWidget(self.prev_block_button)
        playback_layout.addWidget(self.next_block_button)
        parent_layout.addWidget(playback_group)

    def create_block_group(self, parent_layout):
        block_group = QGroupBox("Blocks")
        block_layout = QVBoxLayout(block_group)
        
        self.reset_blocks_button = QPushButton("Reset")
        self.reset_blocks_button.clicked.connect(self.reset_blocks)
        self.export_button = QPushButton("Preview/Export Labels")
        self.export_button.clicked.connect(self.show_preview)
        self.export_button.setEnabled(False)
        self.preview_button = QPushButton("Preview Labels")
        self.preview_button.clicked.connect(self.show_preview)
        self.preview_button.setEnabled(False)
        
        block_layout.addWidget(self.reset_blocks_button)
        block_layout.addWidget(self.export_button)
        block_layout.addWidget(self.preview_button)
        parent_layout.addWidget(block_group)

    def create_view_group(self, parent_layout):
        view_group = QGroupBox("View")
        view_layout = QVBoxLayout(view_group)
        
        self.zoom_in_button = QPushButton("Zoom In")
        self.zoom_in_button.clicked.connect(self.zoom_in)
        self.zoom_out_button = QPushButton("Zoom Out")
        self.zoom_out_button.clicked.connect(self.zoom_out)
        self.help_button = QPushButton("Help")
        self.help_button.clicked.connect(self.show_help)
        label_manager_button = QPushButton("Label Manager")
        label_manager_button.clicked.connect(self.show_label_manager)
        
        view_layout.addWidget(self.zoom_in_button)
        view_layout.addWidget(self.zoom_out_button)
        view_layout.addWidget(self.help_button)
        view_layout.addWidget(label_manager_button)
        parent_layout.addWidget(view_group)

    def setup_video_widget(self, main_layout):
        """Setup the video widget"""
        self.video_widget = QVideoWidget()
        self.video_widget.setStyleSheet("background-color: #1a1a1a;")
        self.video_widget.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
        self.video_widget.setMinimumHeight(300)  # Ensure minimum height for visibility
        main_layout.addWidget(self.video_widget, 10)  # Higher stretch factor for video

    def setup_timeline(self, main_layout):
        """Setup the timeline widgets"""
        timeline_container = QWidget()
        timeline_container.setObjectName("timeline_container")
        timeline_layout = QVBoxLayout(timeline_container)
        timeline_layout.setSpacing(5)
        main_layout.addWidget(timeline_container)

        # Timeline slider with improved style
        self.timeline_slider = CustomSlider(Qt.Horizontal)
        self.timeline_slider.sliderMoved.connect(self.set_position)
        self.timeline_slider.setFixedHeight(20)
        self.timeline_slider.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Minimum)
        timeline_layout.addWidget(self.timeline_slider)

        # Block timeline
        self.block_timeline = BlockTimeline(self)
        self.block_timeline.setFixedHeight(60)
        self.block_timeline.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Minimum)
        timeline_layout.addWidget(self.block_timeline)

    def setup_progress_bar(self, main_layout):
        """Setup the progress bar"""
        self.progress_bar = QProgressBar()
        self.progress_bar.setRange(0, 100)
        main_layout.addWidget(self.progress_bar)

    def setup_mode_label(self, main_layout):
        self.mode_label = QLabel()
        self.update_mode_label()
        main_layout.addWidget(self.mode_label)

    def setup_label_controls(self, main_layout):
        """Setup the label controls"""
        label_group = QGroupBox("Labels")
        label_group.setObjectName("Labels")
        label_layout = QHBoxLayout(label_group)
        self.label_buttons = {}
        
        for label in self.label_manager.labels.values():
            btn = QPushButton(f"{label.name} ({label.hotkey})")
            btn.setStyleSheet(f"background-color: {label.color.name()}; color: black;")
            btn.clicked.connect(lambda checked, l=label: self.select_label(l))
            self.label_buttons[label.name] = btn
            label_layout.addWidget(btn)
            
        main_layout.addWidget(label_group)

    def setup_shortcuts(self):
        """Setup keyboard shortcuts"""
        # Navigation shortcuts
        self.shortcut_left = QShortcut(QKeySequence(Qt.Key_Left), self)
        self.shortcut_left.activated.connect(self.goto_previous_block)
        self.shortcut_right = QShortcut(QKeySequence(Qt.Key_Right), self)
        self.shortcut_right.activated.connect(self.goto_next_block)
        self.shortcut_space = QShortcut(QKeySequence(Qt.Key_Space), self)
        self.shortcut_space.activated.connect(self.play_pause)
        
        # Zoom shortcuts
        self.shortcut_zoom_in = QShortcut(QKeySequence(Qt.Key_Equal), self)
        self.shortcut_zoom_in.activated.connect(self.zoom_in)
        self.shortcut_zoom_out = QShortcut(QKeySequence(Qt.Key_Minus), self)
        self.shortcut_zoom_out.activated.connect(self.zoom_out)
        
        # Label manager shortcut
        self.shortcut_label_manager = QShortcut(QKeySequence("\\"), self)
        self.shortcut_label_manager.activated.connect(self.show_label_manager)

        # Set up label shortcuts
        self.label_shortcuts = {}
        for label in self.label_manager.labels.values():
            shortcut = QShortcut(QKeySequence(label.hotkey), self)
            shortcut.activated.connect(lambda l=label: self.select_label(l))
            self.label_shortcuts[label.name] = shortcut

    def set_position(self, position):
        """Set the media player position when the slider is moved"""
        self.media_player.setPosition(position)

    def position_changed(self, position):
        """Handle media player position changes"""
        if not self.block_manager.blocks:
            return
            
        current_position = position / 1000.0  # Convert to seconds
        
        # Only update UI elements if they exist and we're not in preview mode
        if hasattr(self, 'timeline_slider') and self.timeline_slider and not self.timeline_slider.isDestroyed():
            self.timeline_slider.setValue(position)
            self.block_timeline.setCurrentPosition(current_position)
            
        # Update current block index based on position
        new_block_index = next((i for i, block in enumerate(self.block_manager.blocks) 
                            if block.start <= current_position <= block.end), 0)
        
        if new_block_index < len(self.block_manager.blocks):
            current_block = self.block_manager.blocks[new_block_index]
            
            # Only log for non-silence blocks or when transitioning blocks
            if not current_block.is_silence or self.current_block_index != new_block_index:
                if self.debug:
                    print(f"[DEBUG] Position {current_position:.3f}s - Block {new_block_index}")
                    if not current_block.is_silence:
                        print(f"[DEBUG] Non-silence block: {current_block.start:.3f}s - {current_block.end:.3f}s")
            
            # Mark non-silence blocks as visited and apply selected label
            if not current_block.is_silence:
                current_block.visited = True
                if self.label_manager.selected_label:
                    current_block.label = self.label_manager.selected_label.name
                
            # Update current block index
            if self.current_block_index != new_block_index:
                self.current_block_index = new_block_index
            
        self.block_timeline.update()
        self.update_progress_bar()

    def duration_changed(self, duration):
        """Handle media player duration changes"""
        self.timeline_slider.setRange(0, duration)
        self.block_timeline.setBlocks(self.block_manager.blocks, duration / 1000.0)

    def update_progress_bar(self):
        """Update the progress bar based on current position"""
        if self.media_player.duration() > 0:
            progress = (self.media_player.position() / self.media_player.duration()) * 100
            self.progress_bar.setValue(int(progress))

    def show_processing_dialog(self):
        """Show a progress dialog while processing blocks."""
        dialog = QProgressDialog("Processing video blocks...", None, 0, 0, self)
        dialog.setWindowTitle("Processing")
        dialog.setWindowModality(Qt.WindowModal)
        dialog.setMinimumDuration(0)
        dialog.setValue(0)
        dialog.show()
        QApplication.processEvents()
        return dialog

    def show_welcome_screen(self):
        """Show welcome screen with quick actions"""
        welcome = QDialog(self)
        welcome.setWindowTitle("Welcome")
        layout = QVBoxLayout(welcome)
        
        label = QLabel("Welcome to Video Block Editor")
        label.setStyleSheet("font-size: 18px; font-weight: bold;")
        layout.addWidget(label)
        
        open_btn = QPushButton("Open Video")
        open_btn.clicked.connect(lambda: (welcome.accept(), self.open_file()))
        layout.addWidget(open_btn)
        
        load_btn = QPushButton("Load Previous Session")
        load_btn.clicked.connect(lambda: (welcome.accept(), self.load_state()))
        layout.addWidget(load_btn)
        
        welcome.exec()

    def update_label_buttons(self):
        """Update the label buttons and shortcuts to match current labels"""
        if self.debug:
            print("[DEBUG] update_label_buttons: Starting update")
            print(f"[DEBUG] update_label_buttons: Current labels: {list(self.label_manager.labels.keys())}")
            print(f"[DEBUG] update_label_buttons: Current buttons: {list(self.label_buttons.keys())}")
        
        # Remove existing buttons and shortcuts
        for btn in self.label_buttons.values():
            if self.debug:
                print(f"[DEBUG] update_label_buttons: Removing button {btn.text()}")
            btn.setParent(None)
        self.label_buttons.clear()
        
        # Remove existing shortcuts
        if hasattr(self, 'label_shortcuts'):
            for shortcut in self.label_shortcuts.values():
                shortcut.setParent(None)
            self.label_shortcuts.clear()
        else:
            self.label_shortcuts = {}
        
        # Find the label group and recreate buttons
        label_group = self.findChild(QGroupBox, "Labels")
        if self.debug:
            print(f"[DEBUG] update_label_buttons: Label groups found: {[obj.objectName() for obj in self.findChildren(QGroupBox)]}")
        if label_group:
            if self.debug:
                print("[DEBUG] update_label_buttons: Found label group")
            label_layout = label_group.layout()
            if not label_layout:
                if self.debug:
                    print("[DEBUG] update_label_buttons: Creating new layout for label group")
                label_layout = QHBoxLayout(label_group)
            
            for label in self.label_manager.labels.values():
                if self.debug:
                    print(f"[DEBUG] update_label_buttons: Creating button for {label.name}")
                btn = QPushButton(f"{label.name} ({label.hotkey})")
                btn.setStyleSheet(f"background-color: {label.color.name()}; color: black;")
                if self.label_manager.selected_label and self.label_manager.selected_label.name == label.name:
                    btn.setStyleSheet(f"background-color: {label.color.name()}; color: black; border: 5px solid yellow;")
                btn.clicked.connect(lambda checked, l=label: self.select_label(l))
                self.label_buttons[label.name] = btn
                label_layout.addWidget(btn)
                
                # Create shortcut for this label
                shortcut = QShortcut(QKeySequence(label.hotkey), self)
                shortcut.activated.connect(lambda l=label: self.select_label(l))
                self.label_shortcuts[label.name] = shortcut
                if self.debug:
                    print(f"[DEBUG] update_label_buttons: Added button {label.name} to layout")
        else:
            if self.debug:
                print("[DEBUG] update_label_buttons: ERROR - Label group not found!")

    def play_pause(self):
        if self.media_player.playbackState() == QMediaPlayer.PlayingState:
            self.media_player.pause()
            self.play_pause_button.setText("Play")
            self.skip_timer.stop()
        else:
            self.media_player.play()
            self.play_pause_button.setText("Pause")
            self.skip_timer.start(100)

    def goto_previous_block(self):
        if self.debug:
            print(f"[DEBUG] goto_previous_block: Starting from index {self.current_block_index}")
        next_index = self.find_next_non_silence_block(self.current_block_index, forward=False)
        
        if next_index is not None:
            was_playing = self.media_player.playbackState() == QMediaPlayer.PlayingState
            if self.debug:
                print(f"[DEBUG] goto_previous_block: Found next block at index {next_index}, was_playing={was_playing}")
            
            self.current_block_index = next_index
            target_position = int(self.block_manager.blocks[next_index].start * 1000)
            if self.debug:
                print(f"[DEBUG] goto_previous_block: Setting position to {target_position}ms")
            
            self.media_player.setPosition(target_position)
            
            if was_playing:
                if self.debug:
                    print("[DEBUG] goto_previous_block: Resuming playback")
                self.media_player.play()
        else:
            if self.debug:
                print("[DEBUG] goto_previous_block: No previous non-silence block found")

    def goto_next_block(self):
        if self.debug:
            print(f"[DEBUG] goto_next_block: Starting from index {self.current_block_index}")
        next_index = self.find_next_non_silence_block(self.current_block_index, forward=True)
        
        if next_index is not None:
            was_playing = self.media_player.playbackState() == QMediaPlayer.PlayingState
            if self.debug:
                print(f"[DEBUG] goto_next_block: Found next block at index {next_index}, was_playing={was_playing}")
            
            self.current_block_index = next_index
            target_position = int(self.block_manager.blocks[next_index].start * 1000)
            if self.debug:
                print(f"[DEBUG] goto_next_block: Setting position to {target_position}ms")
            
            self.media_player.setPosition(target_position)
            
            if was_playing:
                if self.debug:
                    print("[DEBUG] goto_next_block: Resuming playback")
                self.media_player.play()
        else:
            if self.debug:
                print("[DEBUG] goto_next_block: No next non-silence block found")

    def find_next_non_silence_block(self, start_index, forward=True):
        blocks = self.block_manager.blocks
        if forward:
            for i in range(start_index + 1, len(blocks)):
                if not blocks[i].is_silence:
                    return i
        else:
            for i in range(start_index - 1, -1, -1):
                if not blocks[i].is_silence:
                    return i
        return None

    def reset_blocks(self):
        if not self.block_manager.blocks:
            return
        
        self.block_manager.reset_blocks()
        self.block_timeline.update()

    def zoom_in(self):
        self.block_timeline.setVisibleBlocks(max(1, self.block_timeline.visible_blocks // 2))

    def zoom_out(self):
        self.block_timeline.setVisibleBlocks(min(len(self.block_manager.blocks), self.block_timeline.visible_blocks * 2))

    def show_label_manager(self):
        dialog = LabelDialog(self.label_manager, self)
        dialog.labels_changed.connect(self.update_label_buttons)
        dialog.exec()

    def show_preview(self):
        dialog = PreviewDialog(self.block_manager, self.label_manager, self)
        dialog.exec()

    def show_help(self):
        help_text = """
        Hotkeys:
        - Space: Play/Pause
        - Left Arrow: Go to Previous Block
        - Right Arrow: Go to Next Block
        - =: Zoom In
        - -: Zoom Out
        - Label Hotkeys: Press the assigned key to apply a label to the current block

        Buttons:
        - Open Video: Open a video file
        - Play/Pause: Control video playback
        - Previous Block: Move to the previous block
        - Next Block: Move to the next block
        - Save State: Save current block states to a file
        - Load State: Load previously saved block states
        - Reset Blocks: Reset all blocks to unvisited state
        - Export Blocks: Export a new video with blocks by label
        - Zoom In: Increase the number of visible blocks
        - Zoom Out: Decrease the number of visible blocks
        - Label Manager: Create and manage labels and their hotkeys
        """
        QMessageBox.information(self, "Help", help_text)

    def skip_silence(self):
        if not self.block_manager.blocks:
            if self.debug:
                print("[DEBUG] skip_silence: No blocks available")
            return
            
        current_position = self.media_player.position() / 1000.0
        if self.debug:
            print(f"[DEBUG] skip_silence: Current position {current_position:.3f}s")
        
        if self.current_block_index >= len(self.block_manager.blocks):
            if self.debug:
                print(f"[DEBUG] skip_silence: Adjusting index from {self.current_block_index} to {len(self.block_manager.blocks) - 1}")
            self.current_block_index = len(self.block_manager.blocks) - 1
            
        current_block = self.block_manager.blocks[self.current_block_index]
        
        # Check if we're near the end of the current block
        time_in_block = current_position - current_block.start
        time_remaining = current_block.end - current_position
        
        if self.debug:
            print(f"[DEBUG] skip_silence: Current block - Index: {self.current_block_index}, Start: {current_block.start:.3f}s, End: {current_block.end:.3f}s, Is Silence: {current_block.is_silence}")
            print(f"[DEBUG] skip_silence: Time in block: {time_in_block:.3f}s, Time remaining: {time_remaining:.3f}s")

        # Skip if we're in a silence block or near the end of any block
        should_skip = current_block.is_silence or time_remaining < 0.1
            
        if should_skip:
            # Find the next suitable non-silence block
            next_block_index = self.current_block_index + 1
            min_block_duration = 0.3  # Increased minimum duration for stability
            
            while next_block_index < len(self.block_manager.blocks):
                next_block = self.block_manager.blocks[next_block_index]
                block_duration = next_block.end - next_block.start
                
                # Skip silence blocks and blocks that are too short
                if not next_block.is_silence and block_duration >= min_block_duration:
                    if self.debug:
                        print(f"[DEBUG] skip_silence: Found suitable block {next_block_index} with duration {block_duration:.3f}s")
                    break
                    
                if self.debug and next_block.is_silence:
                    print(f"[DEBUG] skip_silence: Skipping silence block {next_block_index}")
                elif self.debug:
                    print(f"[DEBUG] skip_silence: Skipping short block {next_block_index} ({block_duration:.3f}s)")
                    
                next_block_index += 1
                
            if next_block_index < len(self.block_manager.blocks):
                next_block = self.block_manager.blocks[next_block_index]
                # Add a small offset to avoid boundary issues
                target_position = next_block.start + 0.05
                if self.debug:
                    print(f"[DEBUG] skip_silence: Skipping to next suitable block at {target_position:.3f}s")
                self.media_player.setPosition(int(target_position * 1000))
                self.current_block_index = next_block_index
            else:
                # If no more suitable blocks, stop playback
                if self.debug:
                    print("[DEBUG] skip_silence: No more suitable blocks, stopping playback")
                self.media_player.stop()
                return
            
            playback_state = self.media_player.playbackState()
            if self.debug:
                print(f"[DEBUG] skip_silence: Playback state is {playback_state}")
            
            if playback_state != QMediaPlayer.PlayingState:
                if self.debug:
                    print("[DEBUG] skip_silence: Resuming playback")
                self.media_player.play()

    def save_state(self):
        if not self.block_manager.blocks:
            QMessageBox.warning(self, "Warning", "No blocks to save!")
            return

        filepath, _ = QFileDialog.getSaveFileName(
            self, "Save Block State", "", "JSON Files (*.json)"
        )
        if filepath:
            if self.block_manager.save_state(filepath):
                QMessageBox.information(self, "Success", "State saved successfully!")
            else:
                QMessageBox.warning(self, "Error", "Failed to save state!")

    def load_state(self):
        filepath, _ = QFileDialog.getOpenFileName(
            self, "Load Block State", "", "JSON Files (*.json)"
        )
        if filepath:
            if self.block_manager.load_state(filepath):
                # Update UI with loaded state
                self.media_player.setSource(QUrl.fromLocalFile(self.block_manager.video_path))
                self.current_block_index = 0
                self.last_jumped_block_index = 0
                
                # Wait for media player to load and get duration
                def on_duration_changed(duration):
                    self.block_timeline.setBlocks(self.block_manager.blocks, duration / 1000.0)
                    self.media_player.durationChanged.disconnect(on_duration_changed)
                
                self.media_player.durationChanged.connect(on_duration_changed)
                self.enable_controls()
                QMessageBox.information(self, "Success", "State loaded successfully!")
            else:
                QMessageBox.warning(self, "Error", "Failed to load state!")

    def get_video_properties(self, video_path):
        """Get video properties using ffprobe"""
        cmd = [
            "ffprobe",
            "-v", "error",
            "-select_streams", "v:0",
            "-show_entries", "stream=r_frame_rate,codec_name",
            "-of", "json",
            video_path
        ]
        video_info = json.loads(subprocess.check_output(cmd).decode())
        
        cmd = [
            "ffprobe",
            "-v", "error",
            "-select_streams", "a:0",
            "-show_entries", "stream=codec_name,bit_rate",
            "-of", "json",
            video_path
        ]
        audio_info = json.loads(subprocess.check_output(cmd).decode())
        
        # Parse frame rate fraction
        num, den = map(int, video_info['streams'][0]['r_frame_rate'].split('/'))
        frame_rate = num/den
        
        return {
            'video_codec': video_info['streams'][0]['codec_name'],
            'audio_codec': audio_info['streams'][0]['codec_name'],
            'frame_rate': frame_rate,
            'audio_bitrate': audio_info['streams'][0].get('bit_rate', '192k')
        }


    def update_mode_label(self):
        # Hide the mode label since we're showing selection via border
        self.mode_label.hide()

    def select_label(self, label):
        self.label_manager.selected_label = label
        if self.current_block_index < len(self.block_manager.blocks):
            current_block = self.block_manager.blocks[self.current_block_index]
            if not current_block.is_silence:
                current_block.label = label.name
                current_block.visited = True
                self.block_timeline.update()
        
        # Update all button styles
        for name, btn in self.label_buttons.items():
            if name == label.name:
                btn.setStyleSheet(f"background-color: {label.color.name()}; color: black; border: 5px solid yellow;")
            else:
                other_label = self.label_manager.get_label(name)
                btn.setStyleSheet(f"background-color: {other_label.color.name()}; color: black;")
        
        self.update_mode_label()

    def enable_controls(self):
        """Enable all control buttons after video is loaded"""
        self.play_pause_button.setEnabled(True)
        self.prev_block_button.setEnabled(True)
        self.next_block_button.setEnabled(True)
        self.zoom_in_button.setEnabled(True)
        self.zoom_out_button.setEnabled(True)
        self.export_button.setEnabled(True)
        self.preview_button.setEnabled(True)
        self.save_state_button.setEnabled(True)
