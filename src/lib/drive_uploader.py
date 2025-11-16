"""Google Drive upload abstraction with multiple implementation strategies.

This module implements the Strategy pattern for Google Drive uploads,
allowing flexible switching between different authentication methods:
- Service Account (via Google API client)
- rclone (command-line tool with OAuth)

Design Principles:
- Dependency Inversion: High-level code depends on abstractions, not concrete implementations
- Open/Closed: Easy to extend with new upload strategies without modifying existing code
- Single Responsibility: Each class has one clear purpose
- Interface Segregation: Minimal, focused interface for uploaders
"""
from __future__ import annotations
import os
import logging
import subprocess
from abc import ABC, abstractmethod
from typing import Optional, List

logger = logging.getLogger(__name__)


class DriveUploader(ABC):
    """Abstract base class for Google Drive upload strategies.

    This interface defines the contract that all concrete upload
    implementations must follow, enabling polymorphic usage.
    """

    @abstractmethod
    def upload_file(self, local_path: str, remote_folder: Optional[str] = None) -> str:
        """Upload a single file to Google Drive.

        Args:
            local_path: Path to the local file to upload
            remote_folder: Optional target folder identifier (folder ID or path)

        Returns:
            Identifier for the uploaded file (file ID, URL, or path)

        Raises:
            FileNotFoundError: If local_path doesn't exist
            RuntimeError: If upload fails
        """
        pass

    @abstractmethod
    def is_available(self) -> bool:
        """Check if this uploader is properly configured and ready to use.

        Returns:
            True if the uploader can be used, False otherwise
        """
        pass


class ServiceAccountUploader(DriveUploader):
    """Google Drive uploader using Service Account authentication.

    This implementation uses the official Google API client library
    with a service account JSON key file. Best for backend automation
    where server-to-server authentication is needed.

    Requirements:
        - google-api-python-client
        - google-auth
        - Service account JSON key file
        - Target folder shared with service account email
    """

    def __init__(self, service_account_file: str, scopes: Optional[List[str]] = None):
        """Initialize with service account credentials.

        Args:
            service_account_file: Path to service account JSON key file
            scopes: Optional list of OAuth scopes (defaults to drive.file)
        """
        self.service_account_file = service_account_file
        self.scopes = scopes or ["https://www.googleapis.com/auth/drive.file"]
        self._drive_service = None

    def _init_service(self):
        """Lazy initialization of Google Drive service."""
        if self._drive_service is not None:
            return

        try:
            from google.oauth2 import service_account
            from googleapiclient.discovery import build
        except ImportError as e:
            raise RuntimeError(
                "google-api-python-client not available. "
                "Install with: pip install google-api-python-client google-auth"
            ) from e

        if not os.path.exists(self.service_account_file):
            raise FileNotFoundError(f"Service account file not found: {self.service_account_file}")

        creds = service_account.Credentials.from_service_account_file(
            self.service_account_file, scopes=self.scopes
        )
        self._drive_service = build("drive", "v3", credentials=creds)

    def upload_file(self, local_path: str, remote_folder: Optional[str] = None) -> str:
        """Upload file using Google Drive API.

        Args:
            local_path: Path to local file
            remote_folder: Google Drive folder ID (e.g., "1a2b3c4d5e6f")

        Returns:
            Google Drive file ID
        """
        if not os.path.exists(local_path):
            raise FileNotFoundError(f"Local file not found: {local_path}")

        self._init_service()

        try:
            from googleapiclient.http import MediaFileUpload
        except ImportError as e:
            raise RuntimeError("googleapiclient not available") from e

        file_metadata = {"name": os.path.basename(local_path)}
        if remote_folder:
            file_metadata["parents"] = [remote_folder]

        media = MediaFileUpload(local_path, resumable=True)
        created = self._drive_service.files().create(
            body=file_metadata,
            media_body=media,
            fields="id"
        ).execute()

        file_id = created.get("id")
        logger.info(f"Uploaded via Service Account: {local_path} -> {file_id}")
        return file_id

    def is_available(self) -> bool:
        """Check if service account authentication is available."""
        try:
            import google.oauth2.service_account
            import googleapiclient.discovery
            return os.path.exists(self.service_account_file)
        except ImportError:
            return False


class RcloneUploader(DriveUploader):
    """Google Drive uploader using rclone command-line tool.

    This implementation delegates to rclone, which supports OAuth
    authentication for personal Google Drive accounts. Best for
    scenarios where you want to use your own Drive without service accounts.

    Requirements:
        - rclone installed and in PATH
        - rclone remote configured (typically named 'gdrive')
        - One-time OAuth authentication completed via 'rclone config'

    Setup:
        1. Install rclone: https://rclone.org/install/
        2. Run: rclone config
        3. Create remote named 'gdrive' with Google Drive
        4. Authenticate via browser
    """

    def __init__(self, remote_name: str = "gdrive"):
        """Initialize rclone uploader.

        Args:
            remote_name: Name of the rclone remote (default: 'gdrive')
        """
        self.remote_name = remote_name

    def upload_file(self, local_path: str, remote_folder: Optional[str] = None) -> str:
        """Upload file using rclone copy command.

        Args:
            local_path: Path to local file
            remote_folder: Remote path relative to Drive root (e.g., "backups/images")
                          If None, uploads to root

        Returns:
            Remote path in format "remote:path/to/file.jpg"

        Raises:
            FileNotFoundError: If local file doesn't exist
            RuntimeError: If rclone command fails
        """
        if not os.path.exists(local_path):
            raise FileNotFoundError(f"Local file not found: {local_path}")

        if not self.is_available():
            raise RuntimeError(
                f"rclone not available or remote '{self.remote_name}' not configured. "
                "Please install rclone and run 'rclone config'"
            )

        # Build remote path
        filename = os.path.basename(local_path)
        if remote_folder:
            # Ensure folder doesn't end with /
            remote_folder = remote_folder.rstrip("/")
            remote_path = f"{self.remote_name}:{remote_folder}"
        else:
            remote_path = f"{self.remote_name}:"

        # Execute rclone copy
        try:
            result = subprocess.run(
                ["rclone", "copy", local_path, remote_path, "-v"],
                check=True,
                capture_output=True,
                text=True,
                timeout=300  # 5 minutes timeout
            )

            final_path = f"{remote_path}/{filename}" if remote_folder else f"{self.remote_name}:{filename}"
            logger.info(f"Uploaded via rclone: {local_path} -> {final_path}")

            # Log rclone output for debugging
            if result.stderr:
                logger.debug(f"rclone stderr: {result.stderr}")

            return final_path

        except subprocess.CalledProcessError as e:
            error_msg = f"rclone upload failed: {e.stderr if e.stderr else str(e)}"
            logger.error(error_msg)
            raise RuntimeError(error_msg) from e
        except subprocess.TimeoutExpired as e:
            raise RuntimeError(f"rclone upload timeout after 300s") from e

    def is_available(self) -> bool:
        """Check if rclone is installed and remote is configured."""
        try:
            # Check if rclone is in PATH
            subprocess.run(
                ["rclone", "version"],
                check=True,
                capture_output=True,
                timeout=5
            )

            # Check if remote exists
            result = subprocess.run(
                ["rclone", "listremotes"],
                check=True,
                capture_output=True,
                text=True,
                timeout=5
            )

            # Remote names are listed with trailing colon
            remotes = [line.strip().rstrip(":") for line in result.stdout.split("\n") if line.strip()]
            return self.remote_name in remotes

        except (subprocess.CalledProcessError, FileNotFoundError, subprocess.TimeoutExpired):
            return False


def create_uploader(
    method: str = "service_account",
    service_account_file: Optional[str] = None,
    rclone_remote: str = "gdrive"
) -> DriveUploader:
    """Factory function to create appropriate DriveUploader instance.

    This factory implements the Factory pattern, encapsulating the
    logic for creating concrete uploader instances based on configuration.

    Args:
        method: Upload method - 'service_account' or 'rclone'
        service_account_file: Path to service account JSON (required for service_account)
        rclone_remote: Name of rclone remote (default: 'gdrive')

    Returns:
        Configured DriveUploader instance

    Raises:
        ValueError: If method is invalid or required parameters are missing
    """
    if method == "service_account":
        if not service_account_file:
            raise ValueError("service_account_file is required for service_account method")
        return ServiceAccountUploader(service_account_file)

    elif method == "rclone":
        return RcloneUploader(rclone_remote)

    else:
        raise ValueError(
            f"Unknown upload method: {method}. "
            "Valid options: 'service_account', 'rclone'"
        )


__all__ = [
    "DriveUploader",
    "ServiceAccountUploader",
    "RcloneUploader",
    "create_uploader",
]
