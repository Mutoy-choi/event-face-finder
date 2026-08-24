from __future__ import annotations

from pathlib import Path

import numpy as np
from PIL import Image

import app


def unit(index: int) -> np.ndarray:
    vector = np.zeros(128, dtype=np.float32)
    vector[index] = 1.0
    return vector


class FakeEngine:
    def query(self, _source):
        return app.DetectedFace(unit(0), (0, 0, 20, 20))

    def load(self, source):
        image = Image.open(source).convert("RGB")
        return app.LoadedImage(image, np.zeros((image.height, image.width, 3), dtype=np.uint8))

    def detect(self, bgr):
        index = 0 if bgr.shape[0] == 40 else 1
        return [app.DetectedFace(unit(index), (4, 4, 24, 24))]


def test_demo_builds() -> None:
    assert app.demo is not None


def test_search_ranks_matching_photo(tmp_path: Path) -> None:
    match = tmp_path / "match.jpg"
    other = tmp_path / "other.jpg"
    Image.new("RGB", (40, 40), "white").save(match)
    Image.new("RGB", (60, 60), "black").save(other)
    gallery, status = app.search_gallery(Image.new("RGB", (80, 80)), [str(other), str(match)], 0.45, 10, FakeEngine())
    assert len(gallery) == 1
    assert "match.jpg" in gallery[0][1]
    assert "유사 사진 **1장**" in status


def test_model_hashes_are_pinned() -> None:
    assert all(len(asset[2]) == 64 for asset in app.MODEL_ASSETS)
