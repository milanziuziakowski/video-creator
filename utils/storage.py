"""Storage abstraction layer for local filesystem."""

from abc import ABC, abstractmethod
from pathlib import Path
from typing import Optional


class StorageBackend(ABC):
    """Abstract base class for storage backends."""
    
    @abstractmethod
    async def upload_file(self, local_path: str, remote_path: str) -> str:
        """Upload a file and return the URL/path."""
        pass
    
    @abstractmethod
    async def download_file(self, remote_path: str, local_path: str) -> None:
        """Download a file from remote storage."""
        pass
    
    @abstractmethod
    async def delete_file(self, remote_path: str) -> None:
        """Delete a file from remote storage."""
        pass
    
    @abstractmethod
    async def get_file_url(self, remote_path: str) -> str:
        """Get a public/signed URL for a file."""
        pass
    
    @abstractmethod
    async def exists(self, remote_path: str) -> bool:
        """Check if a file exists in remote storage."""
        pass


class LocalStorage(StorageBackend):
    """Local filesystem storage backend."""
    
    def __init__(self, base_path: str = "./storage"):
        self.base_path = Path(base_path)
        self.base_path.mkdir(parents=True, exist_ok=True)
    
    async def upload_file(self, local_path: str, remote_path: str) -> str:
        """Copy file to local storage directory."""
        source = Path(local_path)
        dest = self.base_path / remote_path
        dest.parent.mkdir(parents=True, exist_ok=True)
        
        with open(source, "rb") as src_file:
            with open(dest, "wb") as dst_file:
                dst_file.write(src_file.read())
        
        return str(dest)
    
    async def download_file(self, remote_path: str, local_path: str) -> None:
        """Copy file from local storage directory."""
        source = self.base_path / remote_path
        dest = Path(local_path)
        dest.parent.mkdir(parents=True, exist_ok=True)
        
        with open(source, "rb") as src_file:
            with open(dest, "wb") as dst_file:
                dst_file.write(src_file.read())
    
    async def delete_file(self, remote_path: str) -> None:
        """Delete file from local storage."""
        file_path = self.base_path / remote_path
        if file_path.exists():
            file_path.unlink()
    
    async def get_file_url(self, remote_path: str) -> str:
        """Return local file path as URL."""
        return str(self.base_path / remote_path)
    
    async def exists(self, remote_path: str) -> bool:
        """Check if file exists locally."""
        return (self.base_path / remote_path).exists()


def get_storage_path(project_id: str = None, subfolder: str = None, base_path: str = "./storage") -> Path:
    """
    Get storage path for a project and optional subfolder.
    
    Args:
        project_id: Project identifier (optional)
        subfolder: Subfolder within project (e.g., 'frames', 'videos', 'audio')
        base_path: Base storage directory
    
    Returns:
        Path object for the storage location
    
    Examples:
        >>> get_storage_path()  # Base storage path
        PosixPath('storage')
        >>> get_storage_path('proj_001')  # Project directory
        PosixPath('storage/projects/proj_001')
        >>> get_storage_path('proj_001', 'frames')  # Project subfolder
        PosixPath('storage/projects/proj_001/frames')
    """
    base = Path(base_path)
    
    if project_id is None:
        path = base
    elif subfolder is None:
        path = base / "projects" / project_id
    else:
        path = base / "projects" / project_id / subfolder
    
    # Create directory if it doesn't exist
    path.mkdir(parents=True, exist_ok=True)
    
    return path


def get_storage_client(base_path: str = "./storage") -> LocalStorage:
    """
    Factory function to get local storage client.
    
    Args:
        base_path: Base directory for storage
    
    Returns:
        LocalStorage instance
    """
    return LocalStorage(base_path=base_path)
