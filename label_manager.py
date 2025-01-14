import json
import os
from dataclasses import dataclass
from typing import Dict, Optional
from PySide6.QtGui import QColor, QKeySequence

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
        self.selected_label: Optional[Label] = None
        self.load_labels()
        
        # Create default labels if none exist
        if not self.labels:
            self.add_label(Label("keep", QColor("#00FF00"), "K"))
            self.add_label(Label("remove", QColor("#FF0000"), "R"))
            self.selected_label = self.labels["keep"]
    
    def add_label(self, label: Label) -> None:
        self.labels[label.name] = label
        
    def remove_label(self, name: str) -> None:
        if name in self.labels:
            del self.labels[name]
            
    def get_label(self, name: str) -> Optional[Label]:
        return self.labels.get(name)
        
    def save_labels(self) -> None:
        config_dir = os.path.expanduser("~/.config/video_editor")
        os.makedirs(config_dir, exist_ok=True)
        
        with open(os.path.join(config_dir, "labels.json"), "w") as f:
            json.dump({
                name: label.to_dict() 
                for name, label in self.labels.items()
            }, f)
            
    def load_labels(self) -> None:
        config_path = os.path.expanduser("~/.config/video_editor/labels.json")
        if os.path.exists(config_path):
            with open(config_path) as f:
                data = json.load(f)
                self.labels = {
                    name: Label.from_dict(label_data)
                    for name, label_data in data.items()
                }
