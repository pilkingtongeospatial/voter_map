"""Tests for scripts/io_helpers.py using mocks and synthetic ZIPs."""

import io
import json
import zipfile
from unittest.mock import patch

import pytest

from io_helpers import read_or_download, read_zip_shapefile, write_json


# ── read_or_download ──────────────────────────────────────────────────────────

def test_read_or_download_uses_cache(tmp_path):
    cache = tmp_path / "cached.bin"
    cache.write_bytes(b"cached content")

    with patch("io_helpers.download") as mock_dl:
        result = read_or_download(str(cache), "http://example.com/x", "x")

    assert result == b"cached content"
    mock_dl.assert_not_called()


def test_read_or_download_fetches_when_missing(tmp_path):
    cache = tmp_path / "new.bin"
    assert not cache.exists()

    with patch("io_helpers.download", return_value=b"fresh bytes") as mock_dl:
        result = read_or_download(str(cache), "http://example.com/x", "x")

    assert result == b"fresh bytes"
    mock_dl.assert_called_once_with("http://example.com/x", "x")
    # Bytes were cached to disk
    assert cache.read_bytes() == b"fresh bytes"


def test_read_or_download_creates_parent_dir(tmp_path):
    cache = tmp_path / "nested" / "sub" / "file.bin"

    with patch("io_helpers.download", return_value=b"data"):
        read_or_download(str(cache), "http://example.com/x", "x")

    assert cache.exists()


# ── read_zip_shapefile ────────────────────────────────────────────────────────

def _make_zip(entries):
    """Build a ZIP in memory from {name: bytes} entries."""
    buf = io.BytesIO()
    with zipfile.ZipFile(buf, "w") as z:
        for name, data in entries.items():
            z.writestr(name, data)
    return buf.getvalue()


def test_read_zip_shapefile_explicit_base():
    zip_bytes = _make_zip({
        "foo.shp": b"SHP",
        "foo.dbf": b"DBF",
        "foo.shx": b"SHX",
        "foo.prj": b"PRJ",
    })
    shp, dbf, shx = read_zip_shapefile(zip_bytes, shp_base="foo")
    assert shp == b"SHP"
    assert dbf == b"DBF"
    assert shx == b"SHX"


def test_read_zip_shapefile_auto_discovers():
    zip_bytes = _make_zip({
        "nested/CD_2025.SHP": b"SHP",
        "nested/CD_2025.DBF": b"DBF",
        "nested/CD_2025.SHX": b"SHX",
    })
    shp, dbf, shx = read_zip_shapefile(zip_bytes)
    assert (shp, dbf, shx) == (b"SHP", b"DBF", b"SHX")


def test_read_zip_shapefile_auto_discovers_mixed_case():
    # pyshp-style where shp is lowercase but dbf is uppercase
    zip_bytes = _make_zip({
        "x.shp": b"shp-bytes",
        "x.DBF": b"dbf-bytes",
        "x.ShX": b"shx-bytes",
    })
    shp, dbf, shx = read_zip_shapefile(zip_bytes)
    assert shp == b"shp-bytes"
    assert dbf == b"dbf-bytes"
    assert shx == b"shx-bytes"


def test_read_zip_shapefile_missing_shp_raises():
    zip_bytes = _make_zip({"foo.dbf": b"DBF"})
    with pytest.raises(FileNotFoundError):
        read_zip_shapefile(zip_bytes)


def test_read_zip_shapefile_missing_sibling_raises():
    zip_bytes = _make_zip({"foo.shp": b"SHP"})  # no .dbf, no .shx
    with pytest.raises(FileNotFoundError):
        read_zip_shapefile(zip_bytes)


# ── write_json ────────────────────────────────────────────────────────────────

def test_write_json_writes_valid_json(tmp_path):
    path = tmp_path / "out.json"
    write_json(str(path), {"a": 1, "b": [2, 3]})
    loaded = json.loads(path.read_text())
    assert loaded == {"a": 1, "b": [2, 3]}


def test_write_json_respects_indent(tmp_path):
    path = tmp_path / "out.json"
    write_json(str(path), {"a": 1}, indent=2)
    content = path.read_text()
    assert "\n" in content  # indented output has newlines


def test_write_json_creates_parent_dir(tmp_path):
    path = tmp_path / "a" / "b" / "c.json"
    write_json(str(path), {"x": 1})
    assert path.exists()
