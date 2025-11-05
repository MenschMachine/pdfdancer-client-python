import hashlib
import locale
import os
import platform
import socket
import uuid
from datetime import datetime
from pathlib import Path


class Fingerprint:
    """Generates a fingerprint hash for API request identification."""

    _SALT_FILE = Path.home() / ".pdfdancer" / "fingerprint.salt"

    @classmethod
    def generate(cls) -> str:
        """Generate X-Fingerprint header value.

        Returns:
            SHA256 hash of fingerprint components
        """
        ip_hash = cls._get_local_ip()
        uid_hash = cls._get_uid()
        os_type = platform.system()
        sdk_language = "python"
        timezone = cls._get_timezone()
        locale_str = cls._get_locale()
        domain_hash = cls._get_hostname()
        install_salt = cls._get_or_create_salt()

        fingerprint_data = (
            ip_hash
            + uid_hash
            + os_type
            + sdk_language
            + timezone
            + locale_str
            + domain_hash
            + install_salt
        )

        return cls._hash(fingerprint_data)

    @classmethod
    def _get_local_ip(cls) -> str:
        """Get local IP address."""
        try:
            return socket.gethostbyname(socket.gethostname())
        except Exception:
            return "unknown"

    @classmethod
    def _get_uid(cls) -> str:
        """Get user login name."""
        try:
            return os.getlogin()
        except Exception:
            return "unknown"

    @classmethod
    def _get_timezone(cls) -> str:
        """Get timezone name."""
        try:
            tz = datetime.now().astimezone().tzinfo
            timezone_name = getattr(tz, "key", str(tz))
            return timezone_name
        except Exception:
            return "unknown"

    @classmethod
    def _get_locale(cls) -> str:
        """Get default locale."""
        try:
            loc = locale.getlocale()[0]
            return loc if loc else "en_US"
        except Exception:
            return "unknown"

    @classmethod
    def _get_hostname(cls) -> str:
        """Get local hostname."""
        try:
            return socket.gethostname()
        except Exception:
            return "unknown"

    @classmethod
    def _get_or_create_salt(cls) -> str:
        """Get or create persistent install salt.

        Returns:
            UUID string used as install salt
        """
        if cls._SALT_FILE.exists():
            try:
                return cls._SALT_FILE.read_text().strip()
            except Exception:
                pass

        # Create salt file
        salt = str(uuid.uuid4())
        try:
            cls._SALT_FILE.parent.mkdir(parents=True, exist_ok=True)
            cls._SALT_FILE.write_text(salt)
        except Exception:
            pass

        return salt

    @classmethod
    def _hash(cls, value: str) -> str:
        """Generate SHA256 hash of value.

        Args:
            value: String to hash

        Returns:
            Hexadecimal SHA256 hash
        """
        return hashlib.sha256(value.encode("utf-8")).hexdigest()
