import hashlib
import tempfile
from pathlib import Path
from unittest.mock import patch

from pdfdancer.fingerprint import Fingerprint


class TestFingerprint:
    """Tests for fingerprint generation."""

    def test_generate_returns_sha256_hash(self):
        """Fingerprint should return a SHA256 hash."""
        fingerprint = Fingerprint.generate()
        assert len(fingerprint) == 64
        assert all(c in "0123456789abcdef" for c in fingerprint)

    def test_generate_is_deterministic_with_same_salt(self):
        """Multiple calls should return the same fingerprint with same salt."""
        with tempfile.TemporaryDirectory() as tmpdir:
            salt_file = Path(tmpdir) / "fingerprint.salt"
            with patch.object(Fingerprint, "_SALT_FILE", salt_file):
                fp1 = Fingerprint.generate()
                fp2 = Fingerprint.generate()
                assert fp1 == fp2

    def test_generate_creates_salt_file(self):
        """First call should create salt file."""
        with tempfile.TemporaryDirectory() as tmpdir:
            salt_file = Path(tmpdir) / "fingerprint.salt"
            with patch.object(Fingerprint, "_SALT_FILE", salt_file):
                assert not salt_file.exists()
                Fingerprint.generate()
                assert salt_file.exists()
                salt_content = salt_file.read_text().strip()
                assert len(salt_content) == 36  # UUID format

    def test_generate_reuses_existing_salt(self):
        """Should reuse existing salt file."""
        with tempfile.TemporaryDirectory() as tmpdir:
            salt_file = Path(tmpdir) / "fingerprint.salt"
            expected_salt = "test-salt-value"
            salt_file.write_text(expected_salt)

            with patch.object(Fingerprint, "_SALT_FILE", salt_file):
                salt = Fingerprint._get_or_create_salt()
                assert salt == expected_salt

    def test_get_local_ip_fallback(self):
        """Should fallback to 127.0.0.1 on error."""
        with patch("socket.gethostbyname", side_effect=Exception("Network error")):
            ip = Fingerprint._get_local_ip()
            assert ip == "unknown"

    def test_get_uid_fallback(self):
        """Should fallback to 'unknown' on error."""
        with patch("os.getlogin", side_effect=Exception("No login")):
            uid = Fingerprint._get_uid()
            assert uid == "unknown"

    def test_get_timezone_fallback(self):
        """Should fallback to 'UTC' on error."""
        with patch("pdfdancer.fingerprint.datetime") as mock_dt:
            mock_dt.now.side_effect = Exception("Timezone error")
            tz = Fingerprint._get_timezone()
            assert tz == "unknown"

    def test_get_locale_fallback(self):
        """Should fallback to 'unknown' on error."""
        with patch("locale.getlocale", side_effect=Exception("Locale error")):
            loc = Fingerprint._get_locale()
            assert loc == "unknown"

    def test_get_hostname_fallback(self):
        """Should fallback to 'unknown' on error."""
        with patch("socket.gethostname", side_effect=Exception("Hostname error")):
            hostname = Fingerprint._get_hostname()
            assert hostname == "unknown"

    def test_hash_produces_sha256(self):
        """Hash method should produce SHA256."""
        value = "test-value"
        expected = hashlib.sha256(value.encode("utf-8")).hexdigest()
        assert Fingerprint._hash(value) == expected

    def test_fingerprint_includes_all_components(self):
        """Fingerprint should include all required components."""
        with tempfile.TemporaryDirectory() as tmpdir:
            salt_file = Path(tmpdir) / "fingerprint.salt"
            test_salt = "test-salt-123"
            salt_file.write_text(test_salt)

            with patch.object(Fingerprint, "_SALT_FILE", salt_file):
                with patch("socket.gethostbyname", return_value="192.168.1.1"):
                    with patch("os.getlogin", return_value="testuser"):
                        with patch("platform.system", return_value="Linux"):
                            with patch("socket.gethostname", return_value="testhost"):
                                with patch.object(
                                    Fingerprint, "_get_timezone", return_value="UTC"
                                ):
                                    with patch.object(
                                        Fingerprint, "_get_locale", return_value="en_US"
                                    ):
                                        fingerprint = Fingerprint.generate()

                                        # Verify it's a valid SHA256 hash
                                        assert len(fingerprint) == 64
                                        assert all(
                                            c in "0123456789abcdef" for c in fingerprint
                                        )

    def test_salt_file_creates_parent_directory(self):
        """Salt file creation should create parent directory."""
        with tempfile.TemporaryDirectory() as tmpdir:
            salt_file = Path(tmpdir) / "subdir" / "fingerprint.salt"
            with patch.object(Fingerprint, "_SALT_FILE", salt_file):
                assert not salt_file.parent.exists()
                Fingerprint._get_or_create_salt()
                assert salt_file.parent.exists()
                assert salt_file.exists()
