#!/usr/bin/env python3
"""
PDFDancer Python Client Release Tool

A tool to bump version and upload to PyPI.
"""

import argparse
import glob
import re
import subprocess
import sys
from pathlib import Path
from typing import List


class ReleaseError(Exception):
    """Base exception for release operations."""
    pass


class VersionBumper:
    """Handles version bumping in pyproject.toml."""

    def __init__(self, pyproject_path: Path = Path("pyproject.toml")):
        self.pyproject_path = pyproject_path
        if not self.pyproject_path.exists():
            raise ReleaseError(f"pyproject.toml not found at {pyproject_path}")

    def get_current_version(self) -> str:
        """Get the current version from pyproject.toml."""
        content = self.pyproject_path.read_text()
        match = re.search(r'^version\s*=\s*"([^"]+)"', content, re.MULTILINE)
        if not match:
            raise ReleaseError("Version not found in pyproject.toml")
        return match.group(1)

    def set_version(self, new_version: str) -> None:
        """Set a new version in pyproject.toml."""
        content = self.pyproject_path.read_text()
        new_content = re.sub(
            r'^version\s*=\s*"[^"]+"',
            f'version = "{new_version}"',
            content,
            flags=re.MULTILINE
        )
        if content == new_content:
            raise ReleaseError("Failed to update version in pyproject.toml")
        self.pyproject_path.write_text(new_content)

    def bump_version(self, bump_type: str) -> str:
        """Bump version by type (major, minor, patch)."""
        current = self.get_current_version()
        parts = current.split(".")

        if len(parts) != 3:
            raise ReleaseError(f"Invalid version format: {current}")

        try:
            major, minor, patch = map(int, parts)
        except ValueError:
            raise ReleaseError(f"Invalid version format: {current}")

        if bump_type == "major":
            major += 1
            minor = 0
            patch = 0
        elif bump_type == "minor":
            minor += 1
            patch = 0
        elif bump_type == "patch":
            patch += 1
        else:
            raise ReleaseError(f"Invalid bump type: {bump_type}")

        new_version = f"{major}.{minor}.{patch}"
        self.set_version(new_version)
        return new_version


class PyPIUploader:
    """Handles PyPI upload operations."""

    def __init__(self, venv_path: Path = Path("venv")):
        self.venv_path = venv_path
        self.python_exe = self._get_python_executable()

    def _get_python_executable(self) -> Path:
        """Get the Python executable from the virtual environment."""
        if sys.platform == "win32":
            python_exe = self.venv_path / "Scripts" / "python.exe"
        else:
            python_exe = self.venv_path / "bin" / "python"

        if not python_exe.exists():
            raise ReleaseError(f"Python executable not found at {python_exe}")
        return python_exe

    def run_command(self, cmd: List[str], check: bool = True) -> subprocess.CompletedProcess:
        """Run a command and return the result."""
        print(f"Running: {' '.join(cmd)}")
        result = subprocess.run(cmd, capture_output=True, text=True)

        if check and result.returncode != 0:
            print(f"Command failed with exit code {result.returncode}")
            print(f"STDOUT: {result.stdout}")
            print(f"STDERR: {result.stderr}")
            raise ReleaseError(f"Command failed: {' '.join(cmd)}")

        return result

    def clean_dist(self) -> None:
        """Clean the dist directory."""
        dist_path = Path("dist")
        if dist_path.exists():
            import shutil
            shutil.rmtree(dist_path)
            print("Cleaned dist directory")

    def build_package(self) -> None:
        """Build the package."""
        self.run_command([str(self.python_exe), "-m", "build"])
        print("Package built successfully")

    def check_package(self) -> None:
        """Check the built package."""
        self.run_command([str(self.python_exe), "-m", "twine", "check", "dist/*"])
        print("Package validation passed")

    def upload_to_pypi(self, test: bool = False) -> None:
        """Upload to PyPI or test PyPI."""
        cmd = [str(self.python_exe), "-m", "twine", "upload"]
        if test:
            cmd.extend(["--repository", "testpypi"])
        cmd.append("dist/*")

        self.run_command(cmd)
        repo_name = "Test PyPI" if test else "PyPI"
        print(f"Package uploaded to {repo_name} successfully")

    def run_tests(self, include_e2e: bool = False) -> None:
        """Run the test suite."""
        if include_e2e:
            test_path = "tests/"
        else:
            # Collect all test files except those in e2e/
            test_files = [
                f for f in glob.glob("tests/**/*.py", recursive=True)
                if "e2e" not in f
            ]
            test_path = " ".join(test_files)

        self.run_command([str(self.python_exe), "-m", "pytest"] + test_path.split() + ["-v"])
        print("All tests passed")


def main():
    """Main entry point."""
    parser = argparse.ArgumentParser(description="PDFDancer Python Client Release Tool")
    parser.add_argument(
        "action",
        choices=["bump", "upload", "release"],
        help="Action to perform: bump (version only), upload (build+upload), release (bump+test+build+upload)"
    )
    parser.add_argument(
        "--bump-type",
        choices=["major", "minor", "patch"],
        default="patch",
        help="Type of version bump (default: patch)"
    )
    parser.add_argument(
        "--version",
        help="Specific version to set (overrides --bump-type)"
    )
    parser.add_argument(
        "--test",
        action="store_true",
        help="Upload to test PyPI instead of production PyPI"
    )
    parser.add_argument(
        "--skip-tests",
        action="store_true",
        help="Skip running tests before release"
    )
    parser.add_argument(
        "--include-e2e",
        action="store_true",
        help="Include E2E tests (requires PDFDancer server and token)"
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Show what would be done without actually doing it"
    )

    args = parser.parse_args()

    try:
        version_bumper = VersionBumper()
        uploader = PyPIUploader()

        if args.dry_run:
            print("DRY RUN MODE - No changes will be made")

        if args.action in ["bump", "release"]:
            current_version = version_bumper.get_current_version()
            print(f"Current version: {current_version}")

            if args.version:
                new_version = args.version
                if not args.dry_run:
                    version_bumper.set_version(new_version)
            else:
                if not args.dry_run:
                    new_version = version_bumper.bump_version(args.bump_type)
                else:
                    # Calculate what the new version would be for dry run
                    parts = current_version.split(".")
                    major, minor, patch = map(int, parts)
                    if args.bump_type == "major":
                        major += 1
                        minor = 0
                        patch = 0
                    elif args.bump_type == "minor":
                        minor += 1
                        patch = 0
                    elif args.bump_type == "patch":
                        patch += 1
                    new_version = f"{major}.{minor}.{patch}"

            print(f"New version: {new_version}")

        if args.action in ["upload", "release"]:
            if args.action == "release" and not args.skip_tests:
                if not args.dry_run:
                    print("Running tests...")
                    uploader.run_tests(include_e2e=args.include_e2e)
                else:
                    test_type = "all tests (including E2E)" if args.include_e2e else "unit tests only"
                    print(f"Would run {test_type}")

            if not args.dry_run:
                print("Cleaning dist directory...")
                uploader.clean_dist()

                print("Building package...")
                uploader.build_package()

                print("Checking package...")
                uploader.check_package()

                print("Uploading to PyPI...")
                uploader.upload_to_pypi(test=args.test)
            else:
                print("Would clean dist directory")
                print("Would build package")
                print("Would check package")
                repo_name = "Test PyPI" if args.test else "PyPI"
                print(f"Would upload to {repo_name}")

        print("Release process completed successfully!")

    except ReleaseError as e:
        print(f"Error: {e}", file=sys.stderr)
        sys.exit(1)
    except KeyboardInterrupt:
        print("\nOperation cancelled by user", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()
