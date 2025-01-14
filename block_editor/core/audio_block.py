class AudioBlock:
    def __init__(self, start, end, is_silence):
        self.start = start
        self.end = end
        self.is_silence = is_silence
        self.label = None  # Store the label name instead of just include flag
        self.include = True  # Default to including the block
        self.visited = False  # Track if playhead has visited this block

    def to_dict(self):
        return {
            'start': self.start,
            'end': self.end,
            'is_silence': self.is_silence,
            'label': self.label,
            'visited': self.visited
        }

    @classmethod
    def from_dict(cls, data):
        block = cls(data['start'], data['end'], data['is_silence'])
        block.label = data.get('label')  # Use get() to handle old state files
        block.visited = data['visited']
        return block