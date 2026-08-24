# Event Face Finder

Hugging Face Hub의 얼굴검색 모델을 실제로 실행하는 배포형 데모입니다.

- **GitHub Pages:** 공개 진입 페이지
- **Hugging Face Docker Space:** Python/OpenCV 얼굴검색 서버
- **GitHub Actions:** 테스트, Pages 배포, Space 동기화
- **탐지 모델:** `opencv/face_detection_yunet` (MIT)
- **임베딩 모델:** `opencv/face_recognition_sface` (Apache-2.0)

```text
GitHub Pages
https://mutoy-choi.github.io/event-face-finder/
        │ iframe
        ▼
Hugging Face Space
https://mutoy-event-face-finder.hf.space
        │
        ├─ YuNet 얼굴 탐지
        ├─ SFace 128차원 임베딩
        └─ cosine similarity Top-K
```

GitHub Pages 자체에서는 Python 서버를 실행할 수 없습니다. 이 저장소를 단일 원본으로 두고, `site/`는 GitHub Pages에, `space/`는 Hugging Face Docker Space에 자동 배포합니다.

## 최초 1회 설정

1. Hugging Face에서 **write 권한 토큰**을 생성합니다.
2. GitHub 저장소의 `Settings → Secrets and variables → Actions`에 `HF_TOKEN`으로 추가합니다.
3. GitHub `Settings → Pages → Source`를 **GitHub Actions**로 선택합니다.
4. Actions에서 `Sync Hugging Face Space`와 `Deploy GitHub Pages`를 다시 실행합니다.

기본 Space는 `mutoy/event-face-finder`입니다. 다른 Space를 쓰려면 Repository Variable `HF_SPACE_REPO`에 `계정/space-name`을 입력합니다.

## 로컬 실행

```bash
cd space
python -m venv .venv
source .venv/bin/activate       # Windows: .venv\\Scripts\\activate
pip install -r requirements.txt
python app.py --download-models
python app.py
```

## Docker 실행

```bash
docker build -t event-face-finder ./space
docker run --rm -p 7860:7860 event-face-finder
```

## 범위

이 앱은 사용자가 이번 요청에서 올린 후보 사진 묶음 안에서만 유사 얼굴을 찾습니다. 공개 웹·SNS 크롤링, 이름 검색, 감시용 인물 목록, 신원 확정은 지원하지 않습니다. 검색 결과는 동일인 확정이 아닌 유사 후보입니다.

## 라이선스 고지

애플리케이션은 MIT, YuNet은 MIT, SFace는 Apache-2.0입니다. 자세한 모델 파일과 체크섬은 [`THIRD_PARTY_NOTICES.md`](THIRD_PARTY_NOTICES.md)에 기록했습니다.
