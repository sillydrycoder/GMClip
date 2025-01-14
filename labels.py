import json
import os
from dataclasses import dataclass
from typing import Dict, Optional
from PySide6.QtGui import QColor

@dataclass
class Label:
    name: str
    color: QColor
    hotkey: str
    
    def to_dict(self):
        return {
            'name': self.name,
            'color': self.color.name(),
            'hotkey': self.hotkey
        }
    
    @classmethod
    def from_dict(cls, data):
        return cls(
            name=data['name'],
            color=QColor(data['color']),
            hotkey=data['hotkey']
        )

class LabelManager:
    def __init__(self):
        self.labels: Dict[str, Label] = {}
        self.selected_label: Optional[str] = None
        self._load_labels()
        
        # Create default labels if none exist
        if not self.labels:
            self.labels['keep'] = Label('keep', QColor('#00FF00'), 'c')  # Green
            self.labels['remove'] = Label('remove', QColor('#FF0000'), 'x')  # Red
            self._save_labels()
    
    def _get_labels_file(self):
        config_dir = os.path.expanduser('~/.config/video_block_editor')
        os.makedirs(config_dir, exist_ok=True)
        return os.path.join(config_dir, 'labels.json')
    
    def _load_labels(self):
        try:
            with open(self._get_labels_file(), 'r') as f:
                data = json.load(f)
                self.labels = {
                    name: Label.from_dict(label_data)
                    for name, label_data in data.items()
                }
        except (FileNotFoundError, json.JSONDecodeError):
            pass
    
    def _save_labels(self):
        with open(self._get_labels_file(), 'w') as f:
            json.dump({
                name: label.to_dict()
                for name, label in self.labels.items()
            }, f, indent=2)
    
    def add_label(self, name: str, color: QColor, hotkey: str):
        self.labels[name] = Label(name, color, hotkey)
        self._save_labels()
    
    def remove_label(self, name: str):
        if name in self.labels:
            del self.labels[name]
            if self.selected_label == name:
                self.selected_label = next(iter(self.labels), None)
            self._save_labels()
    
    def select_label(self, name: str):
        if name in self.labels:
            self.selected_label = name
            return True
        return False
    
    def get_label_by_hotkey(self, key: str) -> Optional[str]:
        for name, label in self.labels.items():
            if label.hotkey == key:
                return name
        return None
