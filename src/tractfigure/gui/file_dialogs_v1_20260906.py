from __future__ import annotations

import os
import subprocess
import sys
from collections.abc import Callable, Iterable
from pathlib import Path
from typing import Any

import nibabel as nib

from tractfigure.io import SUPPORTED_EXTENSIONS, tractogram_extension

PROJECT_ROOT = Path(__file__).resolve().parents[3]
ALL_FILES_FILETYPES = [("All files", "*.*")]


def _activate_process_frontmost() -> None:
    if sys.platform != "darwin":
        return

    try:
        subprocess.run(
            [
                "osascript",
                "-e",
                (
                    'tell application "System Events" to set frontmost of '
                    f"(first process whose unix id is {os.getpid()}) to true"
                ),
            ],
            check=False,
            capture_output=True,
            timeout=2,
        )
    except (OSError, subprocess.TimeoutExpired):
        pass


def _initial_directory(path: str | Path | None) -> str:
    if path is not None:
        candidate = Path(path).expanduser().resolve()
        directory = candidate if candidate.is_dir() else candidate.parent
        if directory.is_dir():
            return str(directory)

    return str(PROJECT_ROOT)


def _run_native_dialog(dialog: Callable[..., Any], **kwargs: Any) -> Any:
    import tkinter as tk

    _activate_process_frontmost()
    root = tk.Tk()
    root.withdraw()
    root.lift()
    root.attributes("-topmost", True)
    root.focus_force()

    try:
        return dialog(parent=root, **kwargs)
    finally:
        root.destroy()


def choose_image(current_path: str | Path | None = None) -> Path | None:
    from tkinter import filedialog

    selected = _run_native_dialog(
        filedialog.askopenfilename,
        title="Choose a 3D NIfTI reference image",
        initialdir=_initial_directory(current_path),
        filetypes=ALL_FILES_FILETYPES,
    )
    return Path(selected).expanduser().resolve() if selected else None


def choose_tractogram_files(
    current_path: str | Path | None = None,
) -> list[Path]:
    from tkinter import filedialog

    selected = _run_native_dialog(
        filedialog.askopenfilenames,
        title="Choose one or more tractogram files",
        initialdir=_initial_directory(current_path),
        filetypes=ALL_FILES_FILETYPES,
    )
    return [Path(value).expanduser().resolve() for value in selected]


def choose_tractogram_folder(
    current_path: str | Path | None = None,
) -> Path | None:
    from tkinter import filedialog

    selected = _run_native_dialog(
        filedialog.askdirectory,
        title="Choose a folder of tractograms",
        initialdir=_initial_directory(current_path),
        mustexist=True,
    )
    return Path(selected).expanduser().resolve() if selected else None


def validate_reference_image(path: str | Path) -> tuple[Path, tuple[int, int, int]]:
    resolved = Path(path).expanduser().resolve()
    if not resolved.is_file():
        raise FileNotFoundError(f"Reference image does not exist: {resolved}")

    if not resolved.name.lower().endswith((".nii", ".nii.gz")):
        raise ValueError(f"Reference image must be a NIfTI file: {resolved}")

    image = nib.as_closest_canonical(nib.load(str(resolved)))
    if len(image.shape) != 3:
        raise ValueError(f"Expected a 3D reference image; received {image.shape}")

    return resolved, tuple(int(value) for value in image.shape)


def expand_tractogram_entry(path: str | Path) -> list[Path]:
    resolved = Path(path).expanduser().resolve()

    if resolved.is_dir():
        matches = sorted(
            child.resolve()
            for child in resolved.iterdir()
            if child.is_file() and tractogram_extension(child) in SUPPORTED_EXTENSIONS
        )
        if matches:
            return matches

        supported = ", ".join(sorted(SUPPORTED_EXTENSIONS))
        raise ValueError(
            f"Folder has no supported tractogram files ({supported}): {resolved}"
        )

    if not resolved.is_file():
        raise FileNotFoundError(f"Tractogram does not exist: {resolved}")

    extension = tractogram_extension(resolved)
    if extension not in SUPPORTED_EXTENSIONS:
        supported = ", ".join(sorted(SUPPORTED_EXTENSIONS))
        raise ValueError(
            f"Unsupported tractogram extension {extension!r}; expected one of: {supported}"
        )

    return [resolved]


def expand_tractogram_entries(entries: Iterable[str | Path]) -> list[Path]:
    expanded: list[Path] = []
    seen: set[Path] = set()

    for entry in entries:
        for path in expand_tractogram_entry(entry):
            if path not in seen:
                expanded.append(path)
                seen.add(path)

    return expanded
