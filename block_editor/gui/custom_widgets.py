from PySide6.QtWidgets import QSlider, QWidget
from PySide6.QtCore import Qt
from PySide6.QtGui import QPainter, QColor, QFont

class CustomSlider(QSlider):
    def __init__(self, orientation, parent=None):
        super().__init__(orientation, parent)
        self._destroyed = False
        
    def isDestroyed(self):
        return self._destroyed
        
    def deleteLater(self):
        self._destroyed = True
        super().deleteLater()
        self.setStyleSheet("""
            QSlider::groove:horizontal {
                border: 1px solid #999999;
                height: 8px;
                background: qlineargradient(x1:0, y1:0, x2:0, y2:1, stop:0 #B1B1B1, stop:1 #c4c4c4);
                margin: 2px 0;
            }
            QSlider::handle:horizontal {
                background: qlineargradient(x1:0, y1:0, x2:1, y2:1, stop:0 #b4b4b4, stop:1 #8f8f8f);
                border: 1px solid #5c5c5c;
                width: 18px;
                margin: -2px 0;
                border-radius: 3px;
            }
        """)

class BlockTimeline(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.blocks = []
        self.current_position = 0
        self.visible_blocks = 200
        self.setMinimumHeight(60)
        self.total_duration = 0
        self.video_player = parent

    def setBlocks(self, blocks, total_duration):
        self.blocks = blocks
        self.total_duration = total_duration
        self.update()

    def setCurrentPosition(self, position):
        self.current_position = position
        self.update()

    def setVisibleBlocks(self, visible_blocks):
        self.visible_blocks = visible_blocks
        self.update()

    def mousePressEvent(self, event):
        if not self.blocks or self.total_duration == 0:
            return
            
        # Get current visible time range
        current_block_index = next((i for i, block in enumerate(self.blocks) if block.start <= self.current_position <= block.end), 0)
        start_index = max(0, current_block_index - self.visible_blocks // 2)
        end_index = min(len(self.blocks), start_index + self.visible_blocks)
        visible_blocks = self.blocks[start_index:end_index]
        
        time_start = visible_blocks[0].start
        time_end = visible_blocks[-1].end
        time_range = time_end - time_start
        
        # Convert click position to time
        click_x = event.position().x()
        click_time = time_start + (click_x / self.width()) * time_range
        
        # Find clicked block
        clicked_block_index = next((i for i, block in enumerate(self.blocks) 
                                  if block.start <= click_time <= block.end), None)
        
        if clicked_block_index is not None:
            # Update position in media player
            self.video_player.media_player.setPosition(int(self.blocks[clicked_block_index].start * 1000))
            self.video_player.current_block_index = clicked_block_index

    def paintEvent(self, event):
        if not self.blocks or self.total_duration == 0:
            return

        painter = QPainter(self)
        width = self.width()
        height = self.height()

        # Find the current block
        current_block_index = next((i for i, block in enumerate(self.blocks) if block.start <= self.current_position <= block.end), 0)

        # Calculate the range of blocks to display
        start_index = max(0, current_block_index - self.visible_blocks // 2)
        end_index = min(len(self.blocks), start_index + self.visible_blocks)

        # Adjust start_index if we're near the end of the list
        if end_index - start_index < self.visible_blocks:
            start_index = max(0, end_index - self.visible_blocks)

        visible_blocks = self.blocks[start_index:end_index]

        # Calculate the time range for the visible blocks
        time_start = visible_blocks[0].start
        time_end = visible_blocks[-1].end
        time_range = time_end - time_start

        for block in visible_blocks:
            start_x = int(((block.start - time_start) / time_range) * width)
            end_x = int(((block.end - time_start) / time_range) * width)
            
            if block.is_silence:
                color = QColor(200, 200, 200, 100)  # Light gray for silence
            elif block.visited:  # Only color visited blocks
                if block.label:
                    # Use the label's color if one is assigned
                    label = self.video_player.label_manager.get_label(block.label)
                    if label:
                        color = label.color
                        color.setAlpha(100)
                    else:
                        color = QColor(150, 150, 150, 100)
                else:
                    color = QColor(150, 150, 150, 100)  # Neutral color for unlabeled blocks
            else:
                color = QColor(150, 150, 150, 100)  # Neutral color for unvisited blocks

            painter.fillRect(start_x, 0, end_x - start_x, height - 20, color)

        # Draw a marker for the current position
        painter.setPen(Qt.blue)
        position_x = int(((self.current_position - time_start) / time_range) * width)
        painter.drawLine(position_x, 0, position_x, height - 20)

        # Draw zoom level indicator
        painter.setPen(Qt.black)
        painter.setFont(QFont("Arial", 10))
        painter.drawText(0, height - 20, width, 20, Qt.AlignRight, f"Zoom: {self.visible_blocks} blocks")