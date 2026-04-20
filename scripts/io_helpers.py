"""
I/O helpers for the voter map pipeline.

Side-effectful wrappers around network and filesystem operations. These
are intentionally thin so that tests can mock them. Pure transformation
logic lives in transforms.py instead.
"""

import json
import os
import subprocess
import sys
import urllib.request
import zipfile


def pip_install(package):
    """Install a pip package via subprocess."""
    subprocess.check_call([sys.executable, "-m", "pip", "install", package, "-q"])


def download(url, label):
    """HTTP GET with a browser User-Agent header. Returns response bytes.

    Uses a 120-second timeout. Prints a one-line progress message.
    """
    print(f"  Downloading {label}...")
    req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0"})
    return urllib.request.urlopen(req, timeout=120).read()


def read_or_download(local_path, url, label):
    """Return bytes from ``local_path`` if it exists, else download and cache.

    If the file at ``local_path`` exists, its contents are returned directly.
    Otherwise, ``download(url, label)`` is called and the result is written
    to ``local_path`` before being returned.
    """
    if os.path.exists(local_path):
        with open(local_path, "rb") as f:
            return f.read()
    data = download(url, label)
    os.makedirs(os.path.dirname(local_path) or ".", exist_ok=True)
    with open(local_path, "wb") as f:
        f.write(data)
    return data


def read_zip_shapefile(zip_bytes, shp_base=None):
    """Extract (shp, dbf, shx) byte triples from a ZIP archive.

    If ``shp_base`` is provided, reads ``{shp_base}.shp``, ``.dbf``, ``.shx``
    from the archive. Otherwise auto-discovers the shapefile: finds the first
    entry ending in ``.shp`` (case-insensitive) and pairs it with its ``.dbf``
    and ``.shx`` siblings (also case-insensitive).

    Raises :class:`FileNotFoundError` if no matching shapefile is found.
    """
    import io as _io
    with zipfile.ZipFile(_io.BytesIO(zip_bytes)) as z:
        names = z.namelist()
        if shp_base is not None:
            shp_name = f"{shp_base}.shp"
            dbf_name = f"{shp_base}.dbf"
            shx_name = f"{shp_base}.shx"
        else:
            shp_name = next(
                (n for n in names if n.lower().endswith(".shp")),
                None,
            )
            if shp_name is None:
                raise FileNotFoundError("No .shp file found in ZIP archive")
            base = shp_name[:-4]
            dbf_name = next(
                (n for n in names if n.lower() == f"{base.lower()}.dbf"),
                None,
            )
            shx_name = next(
                (n for n in names if n.lower() == f"{base.lower()}.shx"),
                None,
            )
            if dbf_name is None or shx_name is None:
                raise FileNotFoundError(
                    f"Missing .dbf or .shx sibling for {shp_name} in ZIP"
                )
        return z.read(shp_name), z.read(dbf_name), z.read(shx_name)


def write_json(path, data, indent=None):
    """Write ``data`` as JSON to ``path``, creating parent dirs as needed."""
    os.makedirs(os.path.dirname(path) or ".", exist_ok=True)
    with open(path, "w") as f:
        json.dump(data, f, indent=indent)
