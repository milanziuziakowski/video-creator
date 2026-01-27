"""Custom exceptions for video creator."""


class VideoCreatorError(Exception):
    """Base exception for video creator errors."""
    pass


class ValidationError(VideoCreatorError):
    """Raised when validation fails."""
    pass


class MCPServerError(VideoCreatorError):
    """Raised when MCP server communication fails."""
    pass


class SegmentGenerationError(VideoCreatorError):
    """Raised when segment generation fails."""
    
    def __init__(self, segment_index: int, message: str):
        self.segment_index = segment_index
        super().__init__(f"Segment {segment_index}: {message}")


class FinalizationError(VideoCreatorError):
    """Raised when video finalization fails."""
    pass


class StorageError(VideoCreatorError):
    """Raised when storage operations fail."""
    pass
