import os
from pathlib import Path
from backend.utils.zip_archive import ZipArchive


def test_zip_file() -> None:
    zip_filepath = "tests/files/zip_files.zip"
    image_path = "examples/palm_pixel_art.png"
    zip = ZipArchive(zip_filepath)
    zip.add_file(image_path, f"denoised/{Path(image_path).name}")
    out_path = zip.close()
    assert str(out_path) == zip_filepath
    assert os.path.exists(zip_filepath)
    # os.remove(zip_filepath)


def test_zip_bytes() -> None:
    zip_filepath = "tests/files/zip_bytes.zip"
    image_path = "examples/palm_pixel_art.png"
    with open(image_path, "rb") as f:
        data = f.read()
    zip = ZipArchive(zip_filepath)
    zip.add_bytes(f"denoised/{Path(image_path).name}", data)
    out_path = zip.close()
    assert str(out_path) == zip_filepath
    assert os.path.exists(zip_filepath)
    # os.remove(zip_filepath)
