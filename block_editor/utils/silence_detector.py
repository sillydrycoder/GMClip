import subprocess
from ..core.audio_block import AudioBlock

class SilenceDetector:
    def __init__(self, input_file, silence_threshold=-40, min_silence_duration=0.1, non_silence_buffer=0.3):
        self.input_file = input_file
        self.silence_threshold = silence_threshold
        self.min_silence_duration = min_silence_duration
        self.non_silence_buffer = non_silence_buffer  # Buffer for non-silence blocks
        self.min_non_silence_duration = 0.5  # Minimum duration for non-silence blocks
        self.min_silence_gap = 0.5  # Minimum duration for silence gaps between non-silence blocks
        self.max_gap_to_bridge = 2.0  # Maximum gap to bridge between blocks

    def detect_blocks(self):
        print(f"[DEBUG] detect_blocks: Starting detection with threshold={self.silence_threshold}dB, duration={self.min_silence_duration}s")
        
        ffmpeg_cmd = [
            "ffmpeg",
            "-i", self.input_file,
            "-af", f"silencedetect=noise={self.silence_threshold}dB:d={self.min_silence_duration}",
            "-f", "null",
            "-"
        ]
        
        print(f"[DEBUG] detect_blocks: Running command: {' '.join(ffmpeg_cmd)}")
        result = subprocess.run(ffmpeg_cmd, capture_output=True, text=True)
        output = result.stderr
        
        if result.returncode != 0:
            print(f"[DEBUG] detect_blocks: FFmpeg error - {output}")
            raise Exception("FFmpeg failed to process the video")

        # Get video duration first
        duration_cmd = [
            "ffprobe",
            "-v", "error",
            "-show_entries", "format=duration",
            "-of", "default=noprint_wrappers=1:nokey=1",
            self.input_file
        ]
        duration_result = subprocess.run(duration_cmd, capture_output=True, text=True)
        try:
            duration = float(duration_result.stdout.strip())
            print(f"[DEBUG] Video duration: {duration:.3f}s")
        except ValueError as e:
            print(f"[DEBUG] detect_blocks: Error parsing duration - {e}")
            return []

        # Parse and sort silence points
        silence_ranges = []
        current_start = None
        
        for line in output.split('\n'):
            if "silence_start" in line:
                try:
                    time = float(line.split("silence_start: ")[1].split(" ")[0])
                    current_start = time
                    print(f"[DEBUG] Found silence start at {time:.3f}s")
                except (IndexError, ValueError) as e:
                    print(f"[DEBUG] detect_blocks: Error parsing silence_start - {e}")
                    continue
            elif "silence_end" in line and current_start is not None:
                try:
                    time = float(line.split("silence_end: ")[1].split(" ")[0])
                    if time > current_start:  # Ensure valid range
                        silence_ranges.append((current_start, time))
                        print(f"[DEBUG] Found silence end at {time:.3f}s")
                    current_start = None
                except (IndexError, ValueError) as e:
                    print(f"[DEBUG] detect_blocks: Error parsing silence_end - {e}")
                    continue

        # Sort silence ranges by start time
        silence_ranges.sort(key=lambda x: x[0])

        # Filter out short silence gaps
        filtered_ranges = []
        for i, (start, end) in enumerate(silence_ranges):
            # Check if this is a short silence between two non-silence regions
            if i > 0 and i < len(silence_ranges) - 1:
                prev_end = silence_ranges[i-1][1]
                next_start = silence_ranges[i+1][0]
                silence_duration = end - start
                if silence_duration < self.min_silence_gap:
                    print(f"[DEBUG] Removing short silence gap: {start:.3f}s - {end:.3f}s (duration: {silence_duration:.3f}s)")
                    continue
            filtered_ranges.append((start, end))

        # Create initial blocks
        blocks = []
        current_pos = 0.0

        for silence_start, silence_end in filtered_ranges:
            # Add non-silence block before silence if there's a gap
            if current_pos < silence_start:
                non_silence_start = current_pos
                non_silence_end = silence_start
                # Check minimum duration for non-silence block
                if non_silence_end - non_silence_start >= self.min_non_silence_duration:
                    blocks.append(AudioBlock(non_silence_start, non_silence_end, False))
                    print(f"[DEBUG] Created non-silence block: {non_silence_start:.3f}s - {non_silence_end:.3f}s")
                else:
                    print(f"[DEBUG] Skipping short non-silence block: {non_silence_start:.3f}s - {non_silence_end:.3f}s")
                    # Extend previous block if exists, otherwise extend to next silence end
                    if blocks and not blocks[-1].is_silence:
                        blocks[-1].end = silence_end
                        print(f"[DEBUG] Extended previous non-silence block to: {blocks[-1].start:.3f}s - {blocks[-1].end:.3f}s")
                    else:
                        current_pos = silence_end
                        continue

            # Add silence block
            blocks.append(AudioBlock(silence_start, silence_end, True))
            print(f"[DEBUG] Created silence block: {silence_start:.3f}s - {silence_end:.3f}s")
            current_pos = silence_end

        # Add final non-silence block if needed
        if current_pos < duration:
            final_duration = duration - current_pos
            if final_duration >= self.min_non_silence_duration:
                blocks.append(AudioBlock(current_pos, duration, False))
                print(f"[DEBUG] Created final non-silence block: {current_pos:.3f}s - {duration:.3f}s")
            else:
                print(f"[DEBUG] Skipping short final non-silence block: {current_pos:.3f}s - {duration:.3f}s")
                if blocks and not blocks[-1].is_silence:
                    blocks[-1].end = duration
                    print(f"[DEBUG] Extended last non-silence block to end: {blocks[-1].start:.3f}s - {duration:.3f}s")

        # Apply buffers to non-silence blocks while preventing overlaps
        buffered_blocks = []
        for i, block in enumerate(blocks):
            if not block.is_silence:
                # Calculate buffered boundaries
                buffered_start = max(0, block.start - self.non_silence_buffer)
                buffered_end = min(duration, block.end + self.non_silence_buffer)

                # Adjust for previous block
                if i > 0 and buffered_start < blocks[i-1].end:
                    buffered_start = blocks[i-1].end

                # Adjust for next block
                if i < len(blocks) - 1 and buffered_end > blocks[i+1].start:
                    buffered_end = blocks[i+1].start

                buffered_blocks.append(AudioBlock(buffered_start, buffered_end, False))
                print(f"[DEBUG] Created buffered non-silence block: {buffered_start:.3f}s - {buffered_end:.3f}s")
            else:
                buffered_blocks.append(block)
                print(f"[DEBUG] Kept silence block: {block.start:.3f}s - {block.end:.3f}s")

        # Final validation and gap filling
        validated_blocks = []
        for i, block in enumerate(buffered_blocks):
            if block.end <= block.start:
                print(f"[ERROR] Invalid block duration: {block.start:.3f}-{block.end:.3f}")
                continue

            if i > 0:
                prev_block = validated_blocks[-1]
                if block.start < prev_block.end:
                    print(f"[ERROR] Invalid block ordering detected: {prev_block.start:.3f}-{prev_block.end:.3f} and {block.start:.3f}-{block.end:.3f}")
                    # Adjust the current block to start after previous block
                    block.start = prev_block.end
                elif block.start > prev_block.end:
                    gap_size = block.start - prev_block.end
                    print(f"[DEBUG] Found gap between blocks: {prev_block.end:.3f}-{block.start:.3f} (size: {gap_size:.3f}s)")
                    
                    if gap_size <= self.max_gap_to_bridge:
                        # For small gaps, extend the previous block if it's non-silence
                        if not prev_block.is_silence:
                            prev_block.end = block.start
                            print(f"[DEBUG] Bridged small gap by extending previous block: {prev_block.start:.3f}-{prev_block.end:.3f}")
                        else:
                            # If previous block is silence, extend it to fill the gap
                            prev_block.end = block.start
                            print(f"[DEBUG] Extended silence block to fill gap: {prev_block.start:.3f}-{prev_block.end:.3f}")
                    else:
                        # For larger gaps, insert a silence block
                        silence_block = AudioBlock(prev_block.end, block.start, True)
                        validated_blocks.append(silence_block)
                        print(f"[DEBUG] Added silence block to fill gap: {silence_block.start:.3f}-{silence_block.end:.3f}")

            validated_blocks.append(block)
            print(f"[DEBUG] Final block {len(validated_blocks)-1}: {block.start:.3f}s - {block.end:.3f}s (type: {'silence' if block.is_silence else 'non-silence'})")

        if not validated_blocks:
            print("[ERROR] No valid blocks after validation")
            # Create a single block for the entire duration as fallback
            validated_blocks.append(AudioBlock(0, duration, False))
            print(f"[DEBUG] Created fallback block: 0.000s - {duration:.3f}s")

        return validated_blocks
