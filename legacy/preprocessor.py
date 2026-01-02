"""
Data preprocessor for logistics traces.
Handles cleaning, normalization, and key event extraction.
"""
import re
from typing import List, Dict, Optional, Tuple
from dataclasses import dataclass
from datetime import datetime


@dataclass
class TraceEvent:
    """A single event in a logistics trace."""
    timestamp: Optional[str]
    location: Optional[str]
    message: str
    raw_line: str


@dataclass
class ProcessedTrace:
    """A processed logistics trace."""
    tracking_number: Optional[str]
    carrier: Optional[str]
    route: Optional[str]  # e.g., "China->USA"
    events: List[TraceEvent]
    raw_text: str
    cleaned_text: str
    key_events_text: str  # Compressed version with key events only


class TracePreprocessor:
    """Preprocessor for logistics trace data."""
    
    # Patterns to remove (noise)
    NOISE_PATTERNS = [
        r'={5,}',  # Separator lines
        r'Powered by .*',  # Attribution
        r'www\.track123\.com',
        r'^\s*$',  # Empty lines
    ]
    
    # Patterns to extract metadata
    TRACKING_PATTERN = r'单号[：:]\s*([A-Za-z0-9]+)'
    CARRIER_PATTERN = r'物流商[：:]\s*(.+?)(?:\n|$)'
    ROUTE_PATTERN = r'国家[：:]\s*(.+?)\s*->\s*(.+?)(?:\n|$)'
    
    # Timestamp patterns (various formats)
    TIMESTAMP_PATTERNS = [
        r'(\d{4}-\d{2}-\d{2}\s+\d{2}:\d{2}(?::\d{2})?)',  # 2025-12-16 22:35:00
        r'(\d{4}-\d{2}-\d{2}\s+\d{2}:\d{2})',  # 2025-12-16 22:35
    ]
    
    # Key event keywords (for compression)
    KEY_EVENT_KEYWORDS = [
        # Delivery related
        'delivered', 'signed', 'received', '签收', '妥投', '已投递',
        # Out for delivery
        'out for delivery', '派送中', '正在派送',
        # Arrival
        'arrived', 'arrival', '到达', '抵达',
        # Departure
        'departed', 'departure', '离开', '发出', '起飞',
        # Customs
        'customs', 'clearance', '清关', '海关', '放行',
        # Exception
        'failed', 'exception', 'returned', 'refused', '失败', '异常', '拒收', '退回',
        # Pickup
        'picked up', 'pickup', '揽收', '已取件',
        # Airport/airline
        'airport', 'airline', 'flight', '机场', '航空', '航班',
    ]
    
    def __init__(self, max_events_for_compression: int = 10):
        self.max_events_for_compression = max_events_for_compression
        self._compile_patterns()
    
    def _compile_patterns(self):
        """Compile regex patterns."""
        self.noise_regex = [re.compile(p, re.IGNORECASE) for p in self.NOISE_PATTERNS]
        self.tracking_regex = re.compile(self.TRACKING_PATTERN)
        self.carrier_regex = re.compile(self.CARRIER_PATTERN)
        self.route_regex = re.compile(self.ROUTE_PATTERN)
        self.timestamp_regexes = [re.compile(p) for p in self.TIMESTAMP_PATTERNS]
        self.key_event_regex = re.compile(
            '|'.join(self.KEY_EVENT_KEYWORDS), 
            re.IGNORECASE
        )
    
    def clean_text(self, text: str) -> str:
        """Remove noise from trace text."""
        lines = text.split('\n')
        cleaned_lines = []
        
        for line in lines:
            line = line.strip()
            if not line:
                continue
            
            # Check if line matches any noise pattern
            is_noise = False
            for pattern in self.noise_regex:
                if pattern.search(line):
                    is_noise = True
                    break
            
            if not is_noise:
                cleaned_lines.append(line)
        
        return '\n'.join(cleaned_lines)
    
    def extract_metadata(self, text: str) -> Tuple[Optional[str], Optional[str], Optional[str]]:
        """Extract tracking number, carrier, and route from text."""
        tracking_number = None
        carrier = None
        route = None
        
        # Extract tracking number
        match = self.tracking_regex.search(text)
        if match:
            tracking_number = match.group(1)
        
        # Extract carrier
        match = self.carrier_regex.search(text)
        if match:
            carrier = match.group(1).strip()
        
        # Extract route
        match = self.route_regex.search(text)
        if match:
            route = f"{match.group(1).strip()}->{match.group(2).strip()}"
        
        return tracking_number, carrier, route
    
    def parse_events(self, text: str) -> List[TraceEvent]:
        """Parse trace text into individual events."""
        events = []
        lines = text.split('\n')
        
        for line in lines:
            line = line.strip()
            if not line:
                continue
            
            # Skip metadata lines
            if any(p in line for p in ['单号', '物流商', '国家']):
                continue
            
            # Try to extract timestamp
            timestamp = None
            for pattern in self.timestamp_regexes:
                match = pattern.search(line)
                if match:
                    timestamp = match.group(1)
                    break
            
            # Extract location (often at the end after the message)
            location = None
            # Common pattern: message LOCATION or message, LOCATION
            location_match = re.search(r'[,\s]([A-Z]{2,}(?:\s*,\s*[A-Z]{2,})?)\s*$', line)
            if location_match:
                location = location_match.group(1)
            
            # The message is the main content
            message = line
            if timestamp:
                message = message.replace(timestamp, '').strip()
            
            events.append(TraceEvent(
                timestamp=timestamp,
                location=location,
                message=message,
                raw_line=line
            ))
        
        return events
    
    def extract_key_events(self, events: List[TraceEvent]) -> List[TraceEvent]:
        """Extract key events for compression."""
        if len(events) <= self.max_events_for_compression:
            return events
        
        key_events = []
        
        # Always include first and last events
        if events:
            key_events.append(events[0])
        
        # Find events with key keywords
        for event in events[1:-1]:
            if self.key_event_regex.search(event.message):
                key_events.append(event)
        
        # Always include last event
        if len(events) > 1:
            key_events.append(events[-1])
        
        # Remove duplicates while preserving order
        seen = set()
        unique_events = []
        for event in key_events:
            if event.raw_line not in seen:
                seen.add(event.raw_line)
                unique_events.append(event)
        
        # If still too many, take most recent ones
        if len(unique_events) > self.max_events_for_compression:
            unique_events = unique_events[-self.max_events_for_compression:]
        
        return unique_events
    
    def process(self, raw_text: str) -> ProcessedTrace:
        """Process a raw trace text into a structured format."""
        # Clean the text
        cleaned_text = self.clean_text(raw_text)
        
        # Extract metadata
        tracking_number, carrier, route = self.extract_metadata(raw_text)
        
        # Parse events
        events = self.parse_events(cleaned_text)
        
        # Extract key events for compression
        key_events = self.extract_key_events(events)
        key_events_text = '\n'.join(e.raw_line for e in key_events)
        
        return ProcessedTrace(
            tracking_number=tracking_number,
            carrier=carrier,
            route=route,
            events=events,
            raw_text=raw_text,
            cleaned_text=cleaned_text,
            key_events_text=key_events_text
        )
    
    def format_for_prompt(self, trace: ProcessedTrace, use_compressed: bool = False) -> str:
        """Format a processed trace for use in a prompt."""
        lines = []
        
        if trace.tracking_number:
            lines.append(f"Tracking Number: {trace.tracking_number}")
        if trace.carrier:
            lines.append(f"Carrier: {trace.carrier}")
        if trace.route:
            lines.append(f"Route: {trace.route}")
        
        if lines:
            lines.append("")
        
        lines.append("Tracking Events:")
        if use_compressed:
            lines.append(trace.key_events_text)
        else:
            lines.append(trace.cleaned_text)
        
        return '\n'.join(lines)
