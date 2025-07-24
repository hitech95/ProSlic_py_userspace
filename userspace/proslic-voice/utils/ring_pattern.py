import re
import time

class RingPattern:
    def __init__(self, pattern_str):
        self.pattern_str = pattern_str
        self.total_duration = 0
        self.durations = []
        self._start_time_ms = None
        self._parse()

    def _parse(self):
        # Match pattern like 60(1/4) or 30(0.4/0.2/0.4/2)
        match = re.match(r"(\d+)\(([\d\./]+)\)", self.pattern_str)
        if not match:
            raise ValueError(f"Invalid pattern format: {self.pattern_str}")

        self.total_duration = int(match.group(1))
        # Split inside the parenthesis by '/'
        self.durations = [float(x) for x in match.group(2).split('/')]

        # Each complete ON/OFF cycle duration
        cycle_duration = sum(self.durations)
        if cycle_duration <= 0:
            raise ValueError("Cycle duration must be positive")

    def ton_toff_pairs(self):
        """Return list of (ton, toff) tuples"""
        if len(self.durations) % 2 != 0:
            raise ValueError("Pattern durations must alternate ON/OFF")
        return [(self.durations[i], self.durations[i + 1])
                for i in range(0, len(self.durations), 2)]
    
    def __iter__(self):
        return RingPatternIterator(self.total_duration, self.durations)   

    def reset(self):
        """Reset the iterator to reuse the pattern"""
        self._start_time_ms = None
        self._cycle_index = 0

    def __str__(self):
        return (f"RingPattern(total_duration={self.total_duration}s, "
                f"durations={self.durations}, repeats={self.repeats})")
    
class RingPatternIterator:
    def __init__(self, total_duration, durations):
        self.total_duration = total_duration
        self.durations = durations
        self._start_time_ms = int(time.time() * 1000)
        self._cycle_index = 0

    def __iter__(self):
        return self

    def __next__(self):
        now_ms = int(time.time() * 1000)
        elapsed_sec = (now_ms - self._start_time_ms) / 1000.0

        if elapsed_sec >= self.total_duration:
            raise StopIteration

        # Get current delay and truncate to remaining time
        delay = self.durations[self._cycle_index]
        remaining_sec = self.total_duration - elapsed_sec
        next_delay = min(delay, remaining_sec)

        # Advance index for next call
        self._cycle_index = (self._cycle_index + 1) % len(self.durations)

        return next_delay