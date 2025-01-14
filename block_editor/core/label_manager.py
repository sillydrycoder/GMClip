import json
import os
from pathlib import Path
from PySide6.QtGui import QColor

class Label:
    def __init__(self, name, color, hotkey):
        self.name = name
        self.color = color if isinstance(color, QColor) else QColor(color)
        self.hotkey = hotkey

    def to_dict(self):
        return {
            'name': self.name,
            'color': self.color.name(),
            'hotkey': self.hotkey
        }

    @classmethod
    def from_dict(cls, data):
        return cls(data['name'], data['color'], data['hotkey'])

class LabelManager:
    def __init__(self):
        self.labels = {}
        self.selected_label = None
        self.config_dir = os.path.expanduser("~/.config/video_editor")
        self.config_file = os.path.join(self.config_dir, "labels.json")
        self.load_labels()
        
        # Create default labels if none exist
        if not self.labels:
            self.create_default_labels()

    def create_default_labels(self):
        keep_label = Label("keep", QColor("#00FF00"), "k")  # Green
        remove_label = Label("remove", QColor("#FF0000"), "r")  # Red
        self.add_label(keep_label)
        self.add_label(remove_label)
        self.save_labels()

    def add_label(self, label):
        self.labels[label.name] = label

    def remove_label(self, name):
        if name in self.labels:
            del self.labels[name]

    def get_label(self, name):
        return self.labels.get(name)

    def save_labels(self):
        os.makedirs(self.config_dir, exist_ok=True)
        with open(self.config_file, 'w') as f:
            json.dump({name: label.to_dict() for name, label in self.labels.items()}, f)

    def load_labels(self):
        try:
            if os.path.exists(self.config_file):
                with open(self.config_file, 'r') as f:
                    data = json.load(f)
                    self.labels = {name: Label.from_dict(label_data) for name, label_data in data.items()}
        except Exception as e:
            print(f"Error loading labels: {e}")
            self.labels = {}