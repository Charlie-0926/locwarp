"""Small cross-platform single-instance lock used by LocWarp entry points.

Windows is the primary target, so use a named mutex there. The fallback uses
an advisory file lock for development on POSIX systems. The lock must be kept
alive for the whole process lifetime; callers should retain the object and
release it during shutdown.
"""

from __future__ import annotations

import os
import tempfile
from pathlib import Path
from typing import Any, TextIO, cast


class SingleInstanceLock:
    """Acquire an inter-process lock and report whether this is the owner."""

    _WINDOWS_ALREADY_EXISTS = 183

    def __init__(self, name: str) -> None:
        self.name = name
        self._handle: Any = None
        self._file: TextIO | None = None
        self._acquired = False

    def acquire(self) -> bool:
        """Return ``False`` when another process already owns *name*."""
        if self._acquired:
            return True
        if os.name == "nt":
            return self._acquire_windows()
        return self._acquire_posix()

    def _acquire_windows(self) -> bool:
        import ctypes
        from ctypes import wintypes

        ctypes_api = cast(Any, ctypes)
        kernel32 = ctypes_api.WinDLL("kernel32", use_last_error=True)
        kernel32.CreateMutexW.argtypes = [
            wintypes.LPVOID,
            wintypes.BOOL,
            wintypes.LPCWSTR,
        ]
        kernel32.CreateMutexW.restype = wintypes.HANDLE
        kernel32.CloseHandle.argtypes = [wintypes.HANDLE]
        kernel32.CloseHandle.restype = wintypes.BOOL
        ctypes_api.set_last_error(0)
        handle = kernel32.CreateMutexW(None, False, self.name)
        if not handle:
            error = ctypes_api.get_last_error()
            raise OSError(error, f"CreateMutexW failed for {self.name!r}")

        if ctypes_api.get_last_error() == self._WINDOWS_ALREADY_EXISTS:
            kernel32.CloseHandle(handle)
            return False

        self._handle = handle
        self._acquired = True
        return True

    def _acquire_posix(self) -> bool:
        import fcntl

        fcntl_api = cast(Any, fcntl)
        filename = "locwarp-" + "".join(
            char if char.isalnum() else "-" for char in self.name
        ) + ".lock"
        path = Path(tempfile.gettempdir()) / filename
        self._file = path.open("a+")
        try:
            fcntl_api.flock(
                self._file.fileno(), fcntl_api.LOCK_EX | fcntl_api.LOCK_NB
            )
        except OSError:
            self._file.close()
            self._file = None
            return False

        self._acquired = True
        return True

    def release(self) -> None:
        """Release the lock. Safe to call more than once."""
        if not self._acquired:
            return

        if os.name == "nt":
            import ctypes
            from ctypes import wintypes

            if self._handle:
                ctypes_api = cast(Any, ctypes)
                kernel32 = ctypes_api.WinDLL("kernel32", use_last_error=True)
                kernel32.CloseHandle.argtypes = [wintypes.HANDLE]
                kernel32.CloseHandle.restype = wintypes.BOOL
                kernel32.CloseHandle(self._handle)
            self._handle = None
        else:
            import fcntl

            if self._file:
                fcntl_api = cast(Any, fcntl)
                try:
                    fcntl_api.flock(self._file.fileno(), fcntl_api.LOCK_UN)
                finally:
                    self._file.close()
            self._file = None

        self._acquired = False

    def __enter__(self) -> "SingleInstanceLock":
        if not self.acquire():
            raise RuntimeError(f"Another process already owns {self.name!r}")
        return self

    def __exit__(self, _exc_type: Any, _exc_value: Any, _traceback: Any) -> None:
        self.release()
