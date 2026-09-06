from __future__ import annotations

from pathlib import Path

import pytest

from tractfigure.morphology_niimath_v1_20260905 import (
    NIIMATH_ENV_VAR,
    NiimathError,
    SurfaceMorpher,
    describe_offset,
    find_niimath,
    offset_tag,
)

NIIMATH_LOG = (
    "intensity range 0..15.4433, isolevel 3.41159\n"
    "bubbles=1 isolevel=3.41159 preSmooth=1 quality=1 smooth=0 reduction=0.25\n"
)


class RecordingRunner:
    """Stand-in for niimath that records its arguments and writes the surface."""

    def __init__(self, *, write_output: bool = True) -> None:
        self.calls: list[list[str]] = []
        self.write_output = write_output

    def __call__(self, arguments: list[str]) -> str:
        self.calls.append(list(arguments))

        if self.write_output:
            Path(arguments[-1]).write_text("surface", encoding="utf-8")

        return NIIMATH_LOG


def make_morpher(
    tmp_path: Path,
    runner: RecordingRunner,
) -> SurfaceMorpher:
    image_path = tmp_path / "template0.nii.gz"
    image_path.write_bytes(b"reference volume")

    return SurfaceMorpher(
        image_path,
        tmp_path / "outputs" / "surface_cache",
        runner=runner,
    )


def test_offset_formatting() -> None:
    assert offset_tag(0) == "source"
    assert offset_tag(2) == "erode_2mm"
    assert offset_tag(-3) == "dilate_3mm"

    assert describe_offset(0) == "unmodified"
    assert describe_offset(2) == "eroded 2 mm"
    assert describe_offset(-3) == "diffused 3 mm"


def test_erode_and_dilate_pipelines_reuse_the_probed_isolevel(tmp_path: Path) -> None:
    runner = RecordingRunner()
    morpher = make_morpher(tmp_path, runner)

    eroded = morpher.mesh_for_offset(2)
    assert eroded.is_file()
    assert eroded.name == "erode_2mm.gii"

    # The first non-zero offset probes the unmodified surface for its isolevel.
    probe, erode = runner.calls
    assert probe[1:] == ["-mesh", "-b", "1", str(morpher.mesh_for_offset(0))]
    assert erode[1:-1] == [
        "-erode",
        "3.41159",
        "2",
        "-mesh",
        "-i",
        "3.41159",
        "-b",
        "1",
    ]

    diffused = morpher.mesh_for_offset(-1)
    assert diffused.name == "dilate_1mm.gii"
    assert runner.calls[-1][1:-1] == [
        "-dilate",
        "3.41159",
        "1",
        "-mesh",
        "-i",
        "3.41159",
        "-b",
        "1",
    ]


def test_generated_surfaces_are_cached_on_disk(tmp_path: Path) -> None:
    runner = RecordingRunner()
    morpher = make_morpher(tmp_path, runner)

    first = morpher.mesh_for_offset(1)
    call_count = len(runner.calls)

    assert morpher.mesh_for_offset(1) == first
    assert len(runner.calls) == call_count

    # A fresh morpher recovers the isolevel from the cache instead of re-probing.
    reopened = SurfaceMorpher(
        morpher.image_path,
        morpher.cache_directory,
        runner=runner,
    )
    assert reopened.isosurface_level() == pytest.approx(3.41159)
    assert len(runner.calls) == call_count


def test_missing_output_is_reported(tmp_path: Path) -> None:
    morpher = make_morpher(tmp_path, RecordingRunner(write_output=False))

    with pytest.raises(NiimathError, match="did not write the surface"):
        morpher.mesh_for_offset(0)


def test_missing_executable_is_reported(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setenv(NIIMATH_ENV_VAR, str(tmp_path / "absent" / "niimath"))
    assert find_niimath() is None

    image_path = tmp_path / "template0.nii.gz"
    image_path.write_bytes(b"reference volume")
    morpher = SurfaceMorpher(image_path, tmp_path / "cache")

    with pytest.raises(NiimathError, match="niimath was not found"):
        morpher.mesh_for_offset(0)


def test_environment_override_locates_the_executable(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    executable = tmp_path / "niimath"
    executable.write_text("#!/bin/sh\n", encoding="utf-8")
    monkeypatch.setenv(NIIMATH_ENV_VAR, str(executable))

    assert find_niimath() == executable
