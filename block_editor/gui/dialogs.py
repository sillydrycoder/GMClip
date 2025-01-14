from PySide6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QFormLayout, QLabel, 
    QPushButton, QLineEdit, QListWidget, QListWidgetItem,
    QColorDialog, QMessageBox, QGroupBox, QCheckBox, QProgressDialog,
    QFileDialog, QDoubleSpinBox, QWidget, QSizePolicy
)
from PySide6.QtCore import Signal, Qt, QTimer
from PySide6.QtGui import QColor
from .custom_widgets import CustomSlider
from ..core.label_manager import Label
import subprocess
import os

class LabelDialog(QDialog):
    labels_changed = Signal()
    
    def __init__(self, label_manager, parent=None):
        super().__init__(parent)
        self.label_manager = label_manager
        self.setWindowTitle("Label Manager")
        self.setModal(True)
        
        layout = QVBoxLayout(self)
        
        # Label list
        self.label_list = QListWidget()
        self.update_label_list()
        layout.addWidget(self.label_list)
        
        # Form for adding/editing labels
        form = QFormLayout()
        self.name_edit = QLineEdit()
        self.hotkey_edit = QLineEdit()
        self.color_button = QPushButton("Choose Color")
        self.color_button.clicked.connect(self.choose_color)
        self.current_color = QColor("#FFFFFF")
        
        form.addRow("Name:", self.name_edit)
        form.addRow("Hotkey:", self.hotkey_edit)
        form.addRow("Color:", self.color_button)
        layout.addLayout(form)
        
        # Buttons
        button_layout = QHBoxLayout()
        add_button = QPushButton("Add Label")
        add_button.clicked.connect(self.add_label)
        remove_button = QPushButton("Remove Selected")
        remove_button.clicked.connect(self.remove_label)
        
        button_layout.addWidget(add_button)
        button_layout.addWidget(remove_button)
        layout.addLayout(button_layout)
        
    def update_label_list(self):
        self.label_list.clear()
        for name, label in self.label_manager.labels.items():
            self.label_list.addItem(f"{name} ({label.hotkey})")
            
    def choose_color(self):
        color = QColorDialog.getColor(self.current_color, self)
        if color.isValid():
            self.current_color = color
            self.color_button.setStyleSheet(f"background-color: {color.name()}")
            
    def add_label(self):
        name = self.name_edit.text().strip()
        hotkey = self.hotkey_edit.text().strip()
        if name and hotkey:
            label = Label(name, self.current_color, hotkey)
            self.label_manager.add_label(label)
            self.label_manager.save_labels()
            self.update_label_list()
            self.labels_changed.emit()
            self.name_edit.clear()
            self.hotkey_edit.clear()
            
    def remove_label(self):
        current_item = self.label_list.currentItem()
        if current_item:
            name = current_item.text().split(" (")[0]
            self.label_manager.remove_label(name)
            self.label_manager.save_labels()
            self.update_label_list()
            self.labels_changed.emit()

class SilenceSettingsDialog(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Silence Detection Settings")
        self.setModal(True)
        
        layout = QVBoxLayout(self)
        
        form = QFormLayout()
        
        # Threshold spinbox
        self.threshold_spin = QDoubleSpinBox()
        self.threshold_spin.setRange(-100, 0)
        self.threshold_spin.setValue(-40)
        self.threshold_spin.setSuffix(" dB")
        form.addRow("Silence Threshold:", self.threshold_spin)
        
        # Duration spinbox
        self.duration_spin = QDoubleSpinBox()
        self.duration_spin.setRange(0.01, 10.0)
        self.duration_spin.setValue(0.1)
        self.duration_spin.setSuffix(" seconds")
        form.addRow("Min Silence Duration:", self.duration_spin)
        
        # Buffer spinbox
        self.buffer_spin = QDoubleSpinBox()
        self.buffer_spin.setRange(0.0, 2.0)
        self.buffer_spin.setValue(0.3)
        self.buffer_spin.setSuffix(" seconds")
        form.addRow("Non-silence Buffer:", self.buffer_spin)
        
        layout.addLayout(form)
        
        # Buttons
        button_box = QHBoxLayout()
        ok_button = QPushButton("OK")
        ok_button.clicked.connect(self.accept)
        cancel_button = QPushButton("Cancel")
        cancel_button.clicked.connect(self.reject)
        
        button_box.addWidget(ok_button)
        button_box.addWidget(cancel_button)
        layout.addLayout(button_box)
    
    def get_settings(self):
        return {
            'threshold': self.threshold_spin.value(),
            'duration': self.duration_spin.value(),
            'buffer': self.buffer_spin.value()
        }

class PreviewDialog(QDialog):
    def __init__(self, block_manager, label_manager, parent=None):
        super().__init__(parent)
        self.block_manager = block_manager
        self.label_manager = label_manager
        self.setWindowTitle("Preview Blocks by Label")
        self.setModal(False)
        self.resize(300, 400)
        
        # Position dialog to the right of the parent window
        if parent:
            parent_geo = parent.geometry()
            self.move(parent_geo.right() + 10, parent_geo.top())
        
        layout = QVBoxLayout(self)
        
        # Label selection with checkboxes
        label_group = QGroupBox("Select Labels")
        label_group_layout = QVBoxLayout()
        self.label_checkboxes = {}
        for name, label in self.label_manager.labels.items():
            checkbox = QCheckBox(name)
            checkbox.stateChanged.connect(self.update_block_list)
            self.label_checkboxes[name] = checkbox
            label_group_layout.addWidget(checkbox)
        label_group.setLayout(label_group_layout)
        layout.addWidget(label_group)
        
        # Block list and preview controls
        list_preview_layout = QHBoxLayout()
        
        # Block list
        list_layout = QVBoxLayout()
        self.block_list = QListWidget()
        self.block_list.itemDoubleClicked.connect(self.jump_to_block)
        list_layout.addWidget(self.block_list)
        list_preview_layout.addLayout(list_layout)
        
        # Preview and Export controls
        controls_layout = QVBoxLayout()
        
        self.preview_button = QPushButton("Preview Selected")
        self.preview_button.setCheckable(True)
        self.preview_button.clicked.connect(self.toggle_preview)
        controls_layout.addWidget(self.preview_button)
        
        self.stop_preview_button = QPushButton("Stop")
        self.stop_preview_button.clicked.connect(self.stop_preview)
        self.stop_preview_button.setEnabled(False)
        controls_layout.addWidget(self.stop_preview_button)
        
        self.export_button = QPushButton("Export Selected Labels")
        self.export_button.clicked.connect(self.export_selected)
        controls_layout.addWidget(self.export_button)
        
        controls_layout.addStretch()
        list_preview_layout.addLayout(controls_layout)
        
        layout.addLayout(list_preview_layout)
        
        # Preview state
        self.preview_blocks = []
        self.current_preview_index = 0
        self.preview_timer = QTimer()
        self.preview_timer.timeout.connect(self.check_preview_position)
        
        # Initial update
        self.update_block_list()

    def update_block_list(self):
        self.block_list.clear()
        selected_labels = [name for name, cb in self.label_checkboxes.items() if cb.isChecked()]
        
        for i, block in enumerate(self.block_manager.blocks):
            if not block.is_silence and block.visited:
                if not selected_labels or (block.label and block.label in selected_labels):
                    duration = block.end - block.start
                    label_text = block.label if block.label else "No Label"
                    item_text = f"Block {i}: {duration:.2f}s - {label_text}"
                    item = QListWidgetItem(item_text)
                    item.setData(Qt.UserRole, i)  # Store block index
                    self.block_list.addItem(item)

    def jump_to_block(self, item):
        block_index = item.data(Qt.UserRole)
        if 0 <= block_index < len(self.block_manager.blocks):
            block = self.block_manager.blocks[block_index]
            parent = self.parent()
            if parent:
                parent.media_player.setPosition(int(block.start * 1000))
                parent.current_block_index = block_index

    def toggle_preview(self, checked):
        if checked:
            self.start_preview()
        else:
            self.stop_preview()

    def start_preview(self):
        # Get blocks for selected labels
        selected_labels = [name for name, cb in self.label_checkboxes.items() if cb.isChecked()]
        self.preview_blocks = []
        
        for i, block in enumerate(self.block_manager.blocks):
            if not block.is_silence and block.visited:
                if not selected_labels or (block.label and block.label in selected_labels):
                    self.preview_blocks.append((i, block))
        
        if not self.preview_blocks:
            self.preview_button.setChecked(False)
            return
            
        self.current_preview_index = 0
        self.stop_preview_button.setEnabled(True)
        
        # Store current UI state and hide elements
        parent = self.parent()
        if parent:
            # Only hide the button container
            parent.button_container.hide()
            parent.toggle_controls_button.hide()
            
            # Start playback
            block_index, block = self.preview_blocks[0]
            parent.media_player.setPosition(int(block.start * 1000))
            parent.current_block_index = block_index
            parent.media_player.play()
            
            # Start checking position
            self.preview_timer.start(100)
            
            # Add return button
            self.return_button = QPushButton("Return to Editor", parent)
            self.return_button.clicked.connect(self.stop_preview)
            self.return_button.setStyleSheet("""
                QPushButton {
                    background-color: rgba(0, 0, 0, 100);
                    color: white;
                    border: none;
                    padding: 10px;
                    border-radius: 5px;
                }
                QPushButton:hover {
                    background-color: rgba(0, 0, 0, 150);
                }
            """)
            self.return_button.show()
            self.return_button.raise_()
            # Position button at bottom center
            self.return_button.move(
                (parent.width() - self.return_button.width()) // 2,
                parent.height() - self.return_button.height() - 20
            )

    def stop_preview(self):
        self.preview_button.setChecked(False)
        self.stop_preview_button.setEnabled(False)
        self.preview_timer.stop()
        
        parent = self.parent()
        if parent:
            # Pause playback first
            parent.media_player.pause()
            
            # Remove return button if it exists
            if hasattr(self, 'return_button'):
                self.return_button.deleteLater()
                delattr(self, 'return_button')
            
            # Only restore visibility of button container
            parent.button_container.show()
            parent.toggle_controls_button.show()
            
            # Ensure timeline slider is properly recreated if needed
            if not hasattr(parent, 'timeline_slider') or parent.timeline_slider.isDestroyed():
                parent.timeline_slider = CustomSlider(Qt.Horizontal)
                parent.timeline_slider.sliderMoved.connect(parent.set_position)
                parent.timeline_slider.setFixedHeight(20)
                parent.timeline_slider.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Minimum)
                # Add to layout in the correct position
                timeline_container = parent.findChild(QWidget, "timeline_container")
                if timeline_container and timeline_container.layout():
                    timeline_container.layout().insertWidget(0, parent.timeline_slider)
            
        # Clear highlight
        for i in range(self.block_list.count()):
            item = self.block_list.item(i)
            item.setBackground(Qt.transparent)

    def check_preview_position(self):
        parent = self.parent()
        if not parent or not self.preview_blocks:
            return
            
        current_position = parent.media_player.position() / 1000.0
        _, current_block = self.preview_blocks[self.current_preview_index]
        
        # If we've reached the end of current block
        if current_position >= current_block.end:
            self.current_preview_index += 1
            
            # If there are more blocks to play
            if self.current_preview_index < len(self.preview_blocks):
                block_index, next_block = self.preview_blocks[self.current_preview_index]
                parent.media_player.setPosition(int(next_block.start * 1000))
                parent.current_block_index = block_index
                self.highlight_playing_block(self.current_preview_index)
            else:
                # End of preview
                self.stop_preview()

    def highlight_playing_block(self, preview_index):
        # Clear previous highlights
        for i in range(self.block_list.count()):
            item = self.block_list.item(i)
            item.setBackground(Qt.transparent)
            
        # Highlight current block
        if 0 <= preview_index < self.block_list.count():
            item = self.block_list.item(preview_index)
            item.setBackground(QColor(200, 200, 255))

    def export_selected(self):
        if not self.block_manager.video_path or not self.block_manager.blocks:
            return

        selected_labels = [name for name, cb in self.label_checkboxes.items() if cb.isChecked()]
        if not selected_labels:
            QMessageBox.warning(self, "Export Error", "Please select at least one label to export!")
            return

        try:
            output_dir = QFileDialog.getExistingDirectory(self, "Select Output Directory")
            if not output_dir:
                return

            props = self.parent().get_video_properties(self.block_manager.video_path)
            
            # Create temporary directory for segments
            temp_dir = os.path.abspath("temp_segments")
            os.makedirs(temp_dir, exist_ok=True)

            for label_name in selected_labels:
                # Get blocks for this label and sort them by start time
                label_blocks = [(i, block) for i, block in enumerate(self.block_manager.blocks) 
                              if block.label == label_name]
                label_blocks.sort(key=lambda x: x[1].start)  # Sort by block start time
                
                if not label_blocks:
                    print(f"[DEBUG] No blocks found for label: {label_name}")
                    continue

                # Create segments list file for this label
                segments_file = os.path.join(temp_dir, f"segments_{label_name}.txt")
                with open(segments_file, "w") as f:
                    buffer_duration = 0.3  # Buffer duration in seconds
                    
                    for idx, (_, block) in enumerate(label_blocks):
                        # Extract segment
                        segment_name = f"segment_{label_name}_{idx}.mp4"
                        segment_path = os.path.join(temp_dir, segment_name)
                        
                        # Calculate buffered start and end times
                        buffered_start = max(0, block.start - buffer_duration)
                        buffered_end = block.end + buffer_duration
                        
                        # Adjust for overlaps with previous block
                        if idx > 0:
                            prev_block = label_blocks[idx-1][1]
                            prev_end = prev_block.end + buffer_duration
                            if buffered_start < prev_end:
                                # Find midpoint between blocks for clean separation
                                midpoint = (prev_block.end + block.start) / 2
                                buffered_start = midpoint
                        
                        # Adjust for overlaps with next block
                        if idx < len(label_blocks) - 1:
                            next_block = label_blocks[idx+1][1]
                            if buffered_end > next_block.start - buffer_duration:
                                # Find midpoint between blocks for clean separation
                                midpoint = (block.end + next_block.start) / 2
                                buffered_end = midpoint
                        
                        # Calculate final duration
                        duration = buffered_end - buffered_start
                        if duration < 0.1:  # Ensure minimum duration
                            print(f"[DEBUG] Warning: Block {idx} duration too short ({duration}s), adjusting to 0.1s")
                            duration = 0.1
                            buffered_end = buffered_start + duration
                        
                        start_time = str(round(buffered_start, 3))
                        duration_str = str(round(duration, 3))
                        
                        print(f"[DEBUG] Extracting segment {idx} for {label_name}:")
                        print(f"[DEBUG]   Original: {str(round(block.start, 3))}s to {str(round(block.end, 3))}s")
                        print(f"[DEBUG]   Buffered: {start_time}s to {str(round(buffered_end, 3))}s")
                        
                        # Cut segment using ffmpeg
                        subprocess.run([
                            "ffmpeg", "-y",
                            "-ss", start_time,
                            "-t", duration_str,
                            "-i", self.block_manager.video_path,
                            "-c:v", props['video_codec'],
                            "-c:a", props['audio_codec'],
                            "-copyts",
                            "-avoid_negative_ts", "make_zero",
                            segment_path
                        ], check=True)
                        
                        # Write absolute path to segments file
                        f.write(f"file '{os.path.abspath(segment_path)}'\n")

                # Concatenate segments for this label
                output_path = os.path.join(output_dir, f"{label_name}_blocks.mp4")
                subprocess.run([
                    "ffmpeg", "-y",
                    "-f", "concat",
                    "-safe", "0",
                    "-i", segments_file,
                    "-c:v", props['video_codec'],
                    "-c:a", props['audio_codec'],
                    output_path
                ], check=True)

            QMessageBox.information(self, "Export Complete", "Selected labels have been exported successfully!")

        except Exception as e:
            QMessageBox.critical(self, "Export Error", f"An error occurred during export: {e}")
            print(f"[DEBUG] Export error: {str(e)}")
        finally:
            # Clean up temporary files
            if os.path.exists(temp_dir):
                for file in os.listdir(temp_dir):
                    try:
                        os.remove(os.path.join(temp_dir, file))
                    except Exception as e:
                        print(f"[DEBUG] Error removing temp file {file}: {e}")
                try:
                    os.rmdir(temp_dir)
                except Exception as e:
                    print(f"[DEBUG] Error removing temp directory: {e}")
