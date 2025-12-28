"""
Error Analyzer Module for SelfAI Error Correction System

This module provides functionality to:
- Scan log files for errors
- Parse and classify errors
- Extract error context (file, line, traceback)
- Identify error patterns
- Generate error statistics
"""

import re
import json
from pathlib import Path
from dataclasses import dataclass, field, asdict
from datetime import datetime
from typing import List, Dict, Optional, Any
from enum import Enum


class ErrorSeverity(Enum):
    """Error severity classification"""
    CRITICAL = "critical"  # System crashes, data loss
    ERROR = "error"        # Feature broken, exception raised
    WARNING = "warning"    # Potential issues, deprecated
    INFO = "info"          # Informational, performance


@dataclass
class ErrorEntry:
    """Represents a single error found in logs"""
    error_type: str                    # Exception type (e.g., "AttributeError")
    message: str                       # Error message
    file_path: Optional[str] = None    # File where error occurred
    line_number: Optional[int] = None  # Line number
    traceback: List[str] = field(default_factory=list)  # Full traceback
    timestamp: Optional[str] = None    # When error occurred
    severity: ErrorSeverity = ErrorSeverity.ERROR
    context: Dict[str, Any] = field(default_factory=dict)  # Additional context
    occurrences: int = 1               # Number of times this error occurred

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for JSON serialization"""
        data = asdict(self)
        data['severity'] = self.severity.value
        return data

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'ErrorEntry':
        """Create from dictionary"""
        if 'severity' in data and isinstance(data['severity'], str):
            data['severity'] = ErrorSeverity(data['severity'])
        return cls(**data)


@dataclass
class ErrorPattern:
    """Represents a pattern of recurring errors"""
    pattern_id: str
    error_type: str
    pattern_signature: str  # Unique signature for grouping
    occurrences: int
    first_seen: str
    last_seen: str
    examples: List[ErrorEntry] = field(default_factory=list)
    root_cause: Optional[str] = None
    suggested_fixes: List[str] = field(default_factory=list)


class ErrorAnalyzer:
    """
    Analyzes log files to extract and classify errors.

    Features:
    - Scans multiple log file formats
    - Parses Python tracebacks
    - Groups similar errors
    - Classifies by severity
    - Extracts context information
    """

    # Regex patterns for error detection
    PYTHON_EXCEPTION_PATTERN = re.compile(
        r'(?P<type>\w+Error|Exception):\s*(?P<message>.*?)(?:\n|$)',
        re.MULTILINE
    )

    TRACEBACK_START_PATTERN = re.compile(r'Traceback \(most recent call last\):')

    FILE_LINE_PATTERN = re.compile(
        r'File\s+"(?P<file>[^"]+)",\s+line\s+(?P<line>\d+)'
    )

    TIMESTAMP_PATTERN = re.compile(
        r'(?P<timestamp>\d{4}-\d{2}-\d{2}[T\s]\d{2}:\d{2}:\d{2})'
    )

    def __init__(self, log_dir: Path):
        """
        Initialize error analyzer.

        Args:
            log_dir: Directory containing log files to analyze
        """
        self.log_dir = Path(log_dir)
        self.errors: List[ErrorEntry] = []
        self.patterns: List[ErrorPattern] = []

    def scan_logs(self, pattern: str = "*.log") -> List[ErrorEntry]:
        """
        Scan all log files matching pattern.

        Args:
            pattern: Glob pattern for log files (default: "*.log")

        Returns:
            List of ErrorEntry objects found in logs
        """
        self.errors.clear()

        if not self.log_dir.exists():
            return self.errors

        log_files = list(self.log_dir.glob(pattern))

        for log_file in log_files:
            try:
                self._parse_log_file(log_file)
            except Exception as e:
                # Don't fail if one log file is corrupted
                print(f"Warning: Could not parse {log_file}: {e}")
                continue

        # Group similar errors
        self._group_errors()

        return self.errors

    def _parse_log_file(self, log_file: Path) -> None:
        """
        Parse a single log file for errors.

        Args:
            log_file: Path to log file
        """
        try:
            content = log_file.read_text(encoding='utf-8', errors='ignore')
        except Exception:
            return

        # Find all Python exceptions
        lines = content.split('\n')
        i = 0

        while i < len(lines):
            line = lines[i]

            # Check for traceback start
            if self.TRACEBACK_START_PATTERN.search(line):
                error = self._parse_traceback(lines, i)
                if error:
                    error.context['log_file'] = str(log_file.name)
                    self.errors.append(error)
                    i += len(error.traceback) + 2  # Skip parsed lines
                    continue

            # Check for inline errors (without full traceback)
            exception_match = self.PYTHON_EXCEPTION_PATTERN.search(line)
            if exception_match:
                error = ErrorEntry(
                    error_type=exception_match.group('type'),
                    message=exception_match.group('message').strip(),
                    severity=self._classify_severity(exception_match.group('type')),
                    context={'log_file': str(log_file.name), 'line_in_log': i}
                )

                # Try to extract timestamp
                timestamp_match = self.TIMESTAMP_PATTERN.search(line)
                if timestamp_match:
                    error.timestamp = timestamp_match.group('timestamp')

                self.errors.append(error)

            i += 1

    def _parse_traceback(self, lines: List[str], start_idx: int) -> Optional[ErrorEntry]:
        """
        Parse a Python traceback from log lines.

        Args:
            lines: All log lines
            start_idx: Index where traceback starts

        Returns:
            ErrorEntry if successfully parsed, None otherwise
        """
        traceback_lines = [lines[start_idx]]
        i = start_idx + 1

        # Collect traceback lines
        while i < len(lines):
            line = lines[i]

            # Traceback ends with exception line
            exception_match = self.PYTHON_EXCEPTION_PATTERN.search(line)
            if exception_match:
                traceback_lines.append(line)

                # Extract file and line from traceback
                file_path = None
                line_number = None

                for tb_line in traceback_lines:
                    file_match = self.FILE_LINE_PATTERN.search(tb_line)
                    if file_match:
                        file_path = file_match.group('file')
                        line_number = int(file_match.group('line'))
                        # Use last occurrence (actual error location)

                error = ErrorEntry(
                    error_type=exception_match.group('type'),
                    message=exception_match.group('message').strip(),
                    file_path=file_path,
                    line_number=line_number,
                    traceback=traceback_lines,
                    severity=self._classify_severity(exception_match.group('type'))
                )

                # Try to extract timestamp from context
                for j in range(max(0, start_idx - 5), start_idx):
                    timestamp_match = self.TIMESTAMP_PATTERN.search(lines[j])
                    if timestamp_match:
                        error.timestamp = timestamp_match.group('timestamp')
                        break

                return error

            # Continue if looks like traceback line
            if line.strip().startswith('File ') or line.strip().startswith('  '):
                traceback_lines.append(line)
                i += 1
            else:
                break

        return None

    def _classify_severity(self, error_type: str) -> ErrorSeverity:
        """
        Classify error severity based on error type.

        Args:
            error_type: Exception type name

        Returns:
            ErrorSeverity enum value
        """
        critical_errors = {
            'SystemExit', 'KeyboardInterrupt', 'MemoryError',
            'RecursionError', 'SystemError'
        }

        warnings = {
            'DeprecationWarning', 'FutureWarning', 'PendingDeprecationWarning',
            'UserWarning', 'ResourceWarning'
        }

        if error_type in critical_errors:
            return ErrorSeverity.CRITICAL
        elif 'Warning' in error_type or error_type in warnings:
            return ErrorSeverity.WARNING
        else:
            return ErrorSeverity.ERROR

    def _group_errors(self) -> None:
        """
        Group similar errors into patterns.

        Groups errors by:
        - Error type
        - File location
        - Message similarity
        """
        error_groups: Dict[str, List[ErrorEntry]] = {}

        for error in self.errors:
            # Create signature for grouping
            signature = self._create_error_signature(error)

            if signature not in error_groups:
                error_groups[signature] = []

            error_groups[signature].append(error)

        # Create patterns from groups
        self.patterns.clear()

        for signature, group in error_groups.items():
            if not group:
                continue

            # Sort by timestamp
            sorted_group = sorted(
                group,
                key=lambda e: e.timestamp or '',
                reverse=True
            )

            pattern = ErrorPattern(
                pattern_id=signature[:8],
                error_type=group[0].error_type,
                pattern_signature=signature,
                occurrences=len(group),
                first_seen=sorted_group[-1].timestamp or 'unknown',
                last_seen=sorted_group[0].timestamp or 'unknown',
                examples=sorted_group[:3]  # Keep top 3 examples
            )

            self.patterns.append(pattern)

        # Sort patterns by occurrence count
        self.patterns.sort(key=lambda p: p.occurrences, reverse=True)

    def _create_error_signature(self, error: ErrorEntry) -> str:
        """
        Create unique signature for error grouping.

        Args:
            error: ErrorEntry to create signature for

        Returns:
            Unique signature string
        """
        parts = [
            error.error_type,
            error.file_path or 'unknown',
            str(error.line_number or 0)
        ]

        # Normalize message (remove variable parts)
        normalized_msg = re.sub(r'\d+', 'N', error.message)
        normalized_msg = re.sub(r"'[^']*'", "'VAR'", normalized_msg)
        parts.append(normalized_msg[:50])

        return '|'.join(parts)

    def get_top_errors(self, limit: int = 10) -> List[ErrorPattern]:
        """
        Get most frequent error patterns.

        Args:
            limit: Maximum number of patterns to return

        Returns:
            List of ErrorPattern objects, sorted by frequency
        """
        return self.patterns[:limit]

    def get_errors_by_severity(self, severity: ErrorSeverity) -> List[ErrorEntry]:
        """
        Filter errors by severity.

        Args:
            severity: ErrorSeverity to filter by

        Returns:
            List of errors matching severity
        """
        return [e for e in self.errors if e.severity == severity]

    def get_error_stats(self) -> Dict[str, Any]:
        """
        Get statistical summary of errors.

        Returns:
            Dictionary with error statistics
        """
        stats = {
            'total_errors': len(self.errors),
            'unique_patterns': len(self.patterns),
            'by_severity': {
                'critical': len(self.get_errors_by_severity(ErrorSeverity.CRITICAL)),
                'error': len(self.get_errors_by_severity(ErrorSeverity.ERROR)),
                'warning': len(self.get_errors_by_severity(ErrorSeverity.WARNING)),
                'info': len(self.get_errors_by_severity(ErrorSeverity.INFO))
            },
            'top_error_types': {}
        }

        # Count by error type
        type_counts: Dict[str, int] = {}
        for error in self.errors:
            type_counts[error.error_type] = type_counts.get(error.error_type, 0) + 1

        stats['top_error_types'] = dict(
            sorted(type_counts.items(), key=lambda x: x[1], reverse=True)[:5]
        )

        return stats

    def export_to_json(self, output_file: Path) -> None:
        """
        Export analysis results to JSON file.

        Args:
            output_file: Path to output JSON file
        """
        data = {
            'timestamp': datetime.now().isoformat(),
            'stats': self.get_error_stats(),
            'patterns': [
                {
                    'pattern_id': p.pattern_id,
                    'error_type': p.error_type,
                    'occurrences': p.occurrences,
                    'first_seen': p.first_seen,
                    'last_seen': p.last_seen,
                    'examples': [e.to_dict() for e in p.examples]
                }
                for p in self.patterns
            ]
        }

        output_file.write_text(
            json.dumps(data, indent=2, ensure_ascii=False),
            encoding='utf-8'
        )
