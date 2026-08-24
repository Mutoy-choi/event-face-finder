from __future__ import annotations

import argparse
import hashlib
import math
import os
import shutil
import threading
import time
from dataclasses import dataclass
from functools import lru_cache
from pathlib import Path

import cv2
import gradio as gr
import numpy as np
from huggingface_hub import hf_hub_download
from PIL import Image, ImageDraw, ImageFont, ImageOps

ROOT = Path(__file__).resolve().parent
MODEL_DIR = ROOT / "models"
MODEL_ASSETS = (
    (
        "opencv/face_detection_yunet",
        "face_detection_yunet_2023mar.onnx",
        "8f2383e4dd3cfbb4553ea8718107fc0423210dc964f9f4280604804ed2552fa4",
    ),
    (
        "opencv/face_recognition_sface",
        "face_recognition_sface_2021dec.onnx",
        "0ba9fbfa01b5270c96627c4ef784da859931e02f04419c829e83484087c34e79",
    ),
)
MAX_FILES = 60
MAX_FILE_BYTES = 12 * 1024 * 1024
MAX_PIXELS = 60_000_000


class FaceSearchError(RuntimeError):
    pass


@dataclass(frozen=True)
class DetectedFace:
    embedding: np.ndarray
    bbox: tuple[int, int, int, int]


@dataclass(frozen=True)
class LoadedImage:
    pil: Image.Image
    bgr: np.ndarray


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def download_models() -> None:
    MODEL_DIR.mkdir(parents=True, exist_ok=True)
    for repo_id, filename, expected in MODEL_ASSETS:
        destination = MODEL_DIR / filename
        if destination.is_file() and sha256_file(destination) == expected:
            print(f"verified: {filename}")
            continue
        cached = Path(hf_hub_download(repo_id=repo_id, filename=filename, revision="main"))
        actual = sha256_file(cached)
        if actual != expected:
            raise RuntimeError(f"checksum mismatch for {repo_id}/{filename}: {actual}")
        shutil.copyfile(cached, destination)
        print(f"downloaded: {repo_id}/{filename}")


class FaceEngine:
    def __init__(self) -> None:
        detector_path = MODEL_DIR / MODEL_ASSETS[0][1]
        recognizer_path = MODEL_DIR / MODEL_ASSETS[1][1]
        if not detector_path.is_file() or not recognizer_path.is_file():
            raise FaceSearchError("얼굴 모델이 없습니다. Space 빌드 로그를 확인해 주세요.")
        try:
            self.detector = cv2.FaceDetectorYN.create(
                str(detector_path), "", (320, 320), float(os.getenv("DETECTOR_THRESHOLD", "0.80")), 0.30, 5000
            )
            self.recognizer = cv2.FaceRecognizerSF.create(str(recognizer_path), "")
        except cv2.error as exc:
            raise FaceSearchError("OpenCV 얼굴 모델 초기화에 실패했습니다.") from exc
        self.min_face_size = int(os.getenv("MIN_FACE_SIZE", "44"))
        self.max_side = int(os.getenv("MAX_IMAGE_SIDE", "1920"))
        self.lock = threading.Lock()

    def load(self, source: str | Path | Image.Image) -> LoadedImage:
        if isinstance(source, Image.Image):
            image = source.copy()
        else:
            path = Path(source)
            if not path.is_file() or path.stat().st_size > MAX_FILE_BYTES:
                raise FaceSearchError("읽을 수 없거나 12MB를 초과한 이미지가 있습니다.")
            with Image.open(path) as opened:
                image = opened.copy()
        image = ImageOps.exif_transpose(image).convert("RGB")
        width, height = image.size
        if width < 32 or height < 32 or width * height > MAX_PIXELS:
            raise FaceSearchError("이미지 해상도가 허용 범위를 벗어났습니다.")
        if max(width, height) > self.max_side:
            scale = self.max_side / max(width, height)
            image = image.resize((round(width * scale), round(height * scale)), Image.Resampling.LANCZOS)
        rgb = np.asarray(image, dtype=np.uint8)
        return LoadedImage(image, cv2.cvtColor(rgb, cv2.COLOR_RGB2BGR))

    def detect(self, bgr: np.ndarray) -> list[DetectedFace]:
        height, width = bgr.shape[:2]
        with self.lock:
            self.detector.setInputSize((width, height))
            _retval, faces = self.detector.detect(bgr)
            if faces is None:
                return []
            found: list[DetectedFace] = []
            for face in faces:
                x, y, w, h = [int(round(float(v))) for v in face[:4]]
                if min(w, h) < self.min_face_size:
                    continue
                try:
                    aligned = self.recognizer.alignCrop(bgr, face)
                    vector = np.asarray(self.recognizer.feature(aligned), dtype=np.float32).reshape(-1)
                except cv2.error:
                    continue
                norm = float(np.linalg.norm(vector))
                if vector.size == 128 and math.isfinite(norm) and norm > 1e-12:
                    found.append(DetectedFace(vector / norm, (max(0, x), max(0, y), max(0, w), max(0, h))))
            return found

    def query(self, source: Image.Image) -> DetectedFace:
        faces = self.detect(self.load(source).bgr)
        if not faces:
            raise FaceSearchError("검색 사진에서 얼굴을 찾지 못했습니다. 밝고 선명한 정면 사진을 사용해 주세요.")
        if len(faces) != 1:
            raise FaceSearchError("검색 사진에는 한 사람의 얼굴만 있어야 합니다.")
        return faces[0]


@lru_cache(maxsize=1)
def get_engine() -> FaceEngine:
    return FaceEngine()


def confidence(score: float) -> str:
    if score >= 0.64:
        return "매우 높은 유사도"
    if score >= 0.55:
        return "높은 유사도"
    return "유사 후보"


def annotate(image: Image.Image, bbox: tuple[int, int, int, int], score: float) -> Image.Image:
    output = image.copy()
    draw = ImageDraw.Draw(output)
    x, y, w, h = bbox
    line = max(3, round(max(output.size) / 300))
    draw.rectangle((x, y, x + w, y + h), outline=(88, 101, 242), width=line)
    label = f"MATCH {score:.3f}"
    font = ImageFont.load_default()
    box = draw.textbbox((0, 0), label, font=font)
    tw, th = box[2] - box[0], box[3] - box[1]
    ly = max(0, y - th - 12)
    draw.rounded_rectangle((x, ly, x + tw + 16, ly + th + 10), radius=6, fill=(29, 35, 58))
    draw.text((x + 8, ly + 4), label, fill="white", font=font)
    return output


def search_gallery(
    query_image: Image.Image | None,
    gallery_paths: list[str] | None,
    threshold: float,
    top_k: int,
    engine: FaceEngine | None = None,
) -> tuple[list[tuple[Image.Image, str]], str]:
    if query_image is None:
        raise FaceSearchError("검색할 얼굴 사진을 올려 주세요.")
    if not gallery_paths:
        raise FaceSearchError("찾아볼 후보 사진을 한 장 이상 올려 주세요.")
    if len(gallery_paths) > MAX_FILES:
        raise FaceSearchError(f"한 번에 최대 {MAX_FILES}장까지 검색할 수 있습니다.")
    if not math.isfinite(threshold) or not 0.30 <= threshold <= 0.70:
        raise FaceSearchError("유사도 기준값이 올바르지 않습니다.")
    top_k = max(1, min(int(top_k), 30))
    engine = engine or get_engine()
    query = engine.query(query_image)
    started = time.perf_counter()
    matches: list[tuple[float, Path, Image.Image, tuple[int, int, int, int]]] = []
    skipped = total_faces = 0
    for raw in gallery_paths:
        path = Path(raw)
        try:
            loaded = engine.load(path)
            faces = engine.detect(loaded.bgr)
        except Exception:
            skipped += 1
            continue
        if not faces:
            skipped += 1
            continue
        total_faces += len(faces)
        scores = [float(face.embedding @ query.embedding) for face in faces]
        index = int(np.argmax(scores))
        if scores[index] >= threshold:
            matches.append((scores[index], path, loaded.pil, faces[index].bbox))
    matches.sort(key=lambda item: item[0], reverse=True)
    chosen = matches[:top_k]
    output = [(annotate(image, bbox, score), f"{path.name} · {confidence(score)}") for score, path, image, bbox in chosen]
    elapsed = time.perf_counter() - started
    if chosen:
        status = f"### 검색 완료\n후보 **{len(gallery_paths)}장**의 얼굴 **{total_faces}개**를 비교해 유사 사진 **{len(matches)}장**을 찾았습니다. 처리 시간 **{elapsed:.1f}초**."
    else:
        status = f"### 일치 후보 없음\n얼굴 **{total_faces}개**를 비교했지만 기준값 `{threshold:.2f}` 이상의 후보가 없었습니다."
    if skipped:
        status += f"\n\n얼굴이 없거나 읽지 못한 사진 **{skipped}장**은 제외했습니다."
    status += "\n\n> 결과는 동일인 확정이 아니라 얼굴 특징이 가까운 유사 후보입니다."
    return output, status


def run_search(query, gallery, threshold, top_k, consent):
    if not consent:
        raise gr.Error("본인 사진 또는 적법하게 처리할 수 있는 사진만 사용한다는 확인이 필요합니다.")
    try:
        return search_gallery(query, gallery, float(threshold), int(top_k))
    except FaceSearchError as exc:
        raise gr.Error(str(exc)) from exc
    except Exception as exc:
        raise gr.Error("이미지를 처리하지 못했습니다. 파일 형식과 크기를 확인해 주세요.") from exc


CSS = """
.gradio-container{max-width:1180px!important}.hero{padding:28px 30px;margin-bottom:18px;border:1px solid #dfe3ff;border-radius:28px;background:radial-gradient(circle at top right,#dfe3ff,transparent 36%),linear-gradient(135deg,#fff,#f5f7ff)}.hero h1{font-size:clamp(30px,5vw,50px);line-height:1.05;margin:0 0 8px}.hero p{color:#525b73;margin:0}.privacy{padding:14px 16px;border:1px solid #bbebca;border-radius:18px;background:#f0fdf4}.primary-button{min-height:50px;font-weight:800!important}
"""
HEAD = '<meta name="description" content="셀피로 직접 올린 행사 사진 묶음 안의 유사 얼굴을 찾는 데모">'


def build_demo() -> gr.Blocks:
    with gr.Blocks(title="Event Face Finder", delete_cache=(1800, 1800), fill_width=True) as demo:
        gr.HTML('<section class="hero"><h1>행사 사진에서<br>내 얼굴 찾기</h1><p>YuNet + SFace가 직접 업로드한 후보 사진 안에서 유사 얼굴을 찾습니다.</p></section>')
        gr.HTML('<div class="privacy"><strong>요청 범위 안에서만 검색합니다.</strong><br>공개 웹·SNS를 검색하거나 별도 얼굴 데이터베이스를 만들지 않습니다.</div>')
        with gr.Row(equal_height=False):
            query = gr.Image(type="pil", sources=["upload", "webcam", "clipboard"], label="1. 검색할 얼굴", height=330)
            gallery = gr.File(file_count="multiple", file_types=["image"], type="filepath", label="2. 찾아볼 행사 사진", height=330)
        with gr.Accordion("검색 설정", open=False):
            with gr.Row():
                threshold = gr.Slider(0.30, 0.70, value=0.45, step=0.01, label="유사도 기준")
                top_k = gr.Slider(1, 30, value=20, step=1, label="최대 결과 수")
        consent = gr.Checkbox(label="본인 사진 또는 적법하게 처리할 수 있는 사진만 사용하며, 결과가 신원 확정이 아닌 유사 후보임을 이해합니다.")
        with gr.Row():
            button = gr.Button("유사 사진 검색", variant="primary", elem_classes="primary-button")
            gr.ClearButton([query, gallery, consent], value="초기화")
        status = gr.Markdown("검색할 셀피와 후보 사진을 올려 주세요.")
        results = gr.Gallery(label="검색 결과", columns=3, rows=3, height="auto", object_fit="contain", allow_preview=True, buttons=["download", "fullscreen"])
        button.click(run_search, [query, gallery, threshold, top_k, consent], [results, status], api_name="search", concurrency_limit=1)
        gr.Markdown("Models: [YuNet](https://huggingface.co/opencv/face_detection_yunet) · [SFace](https://huggingface.co/opencv/face_recognition_sface) · [Source](https://github.com/Mutoy-choi/event-face-finder)")
    return demo


demo = build_demo().queue(default_concurrency_limit=1, max_size=20)


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--download-models", action="store_true")
    args = parser.parse_args()
    if args.download_models:
        download_models()
        return
    demo.launch(
        server_name="0.0.0.0",
        server_port=int(os.getenv("PORT", "7860")),
        show_error=False,
        max_file_size="12mb",
        footer_links=["api"],
        strict_cors=True,
        css=CSS,
        head=HEAD,
    )


if __name__ == "__main__":
    main()
