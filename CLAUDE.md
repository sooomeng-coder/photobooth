# 포토부스 웹앱 (photobooth)

행사용 그린스크린 포토부스 웹앱. 아이패드 사파리에서 전체화면으로 띄워두고, 4명이 카메라 앞에 서서 프레임 구멍에 얼굴을 맞춰 찍는 방식.

- 배포: GitHub Pages — `https://sooomeng-coder.github.io/photobooth/`
- 저장소: `sooomeng-coder/photobooth` (main 브랜치 루트의 `index.html`이 서비스됨)
- 사용 기기: 아이패드 사파리 (홈 화면에 추가해서 전체화면으로 사용)

## 현재 상태 (v4.1) — 버전 기록·되돌리기는 `CHANGELOG.md`

이미지는 base64가 아니라 별도 파일로 분리되어 있고, `index.html`이 상대경로로 불러옴.

```
index.html               앱 전체 (HTML/CSS/JS)
assets/start.jpg         시작 이미지 (START 글자 있는 버전)
frames/frames.json       프레임 목록 (선택 화면에 이 순서대로 표시)
frames/frame1.png        그린스크린 프레임 원본 (저장 해상도 = 이 파일 해상도)
frames/thumbs/frame1.jpg 선택 화면용 썸네일 (가로 600px JPEG)
cuts/cuts.json           4컷/9컷용 컷 프레임 목록 (3:4, 708×944, cutN.png)
assets/sheet-*.png       (선택) 시트 디자인 배경 2400×3600
templates/               인화 시트 가이드·좌표 (디자인용)
CHANGELOG.md             버전 기록 + 되돌리는 방법
```

### 화면 흐름
1. **시작 화면** — 시작 이미지를 화면에 맞춰 표시. START 글자 위에 투명 버튼이 있고(초록 glow pulse), 화면 아무 곳을 눌러도 다음으로 넘어감. 이때 카메라 권한도 미리 요청.
1-1. **모드 선택** (`#modeScreen`) — 4컷 / 9컷 / 1장. 1장이면 아래 2번(기존 흐름), 4컷·9컷이면 1-2번
1-2. **컷 프레임 고르기** (`#pickScreen`, 4컷·9컷) — 위에 빈 칸 N개, 아래 컷 프레임 목록. 누르면 다음 칸에 들어감(중복 가능),
   칸을 누르면 빠짐, 랜덤 채우기/비우기. 다 채우면 촬영 시작 → 연속 촬영(아래 `#cutBar`에 "N / 9 번째 사진" + 모든 컷 미리보기,
   찍은 컷은 ✓와 사진) → 시트 결과(컷을 눌러 1번 다시 찍기) → SAVE
2. **프레임 선택 화면** — `frames/frames.json`의 프레임을 카드로 보여줌(번호 + 썸네일 + 이름). 누르면 촬영 화면으로.
3. **촬영 화면** — 카메라 한 화면을 프레임 전체 뒤에 cover 방식으로 깔고, 초록색 영역을 투명하게 뚫어서 보이게 함. 거울처럼 좌우반전. 셔터 → 5,4,3,2,1 카운트다운 → 플래시 → 촬영. 왼쪽 위 ← 버튼은 프레임 선택으로 돌아감.
4. **결과 화면** — 합성 결과를 보여줌. SAVE(PNG 다운로드) / RETAKE(다시 찍기, 1회만). 왼쪽 위 ⌂ 버튼은 시작 화면으로 돌아감.

### 확정된 결정사항
- 카메라는 **1개 화면**으로 프레임 전체 뒤에 깔린다 (구멍마다 따로 넣지 않음). 4명이 한 카메라로 같이 찍는 방식.
- 다시 찍기는 1회만 가능. 횟수는 **시작 화면으로 돌아갈 때만** 초기화됨 (프레임 선택으로 돌아갔다 와도 초기화 안 됨).
- 화면 맞춤은 비율 유지하며 화면에 최대한 크게 표시(contain). 맨 왼쪽 구멍이 프레임 가장자리에 있어서 cover로 하면 잘림.
- 결과 PNG는 프레임 원본 해상도로 저장. 파일명 `photobooth_YYYYMMDD_HHMMSS.png`.
- 키보드: 스페이스/엔터로 시작·촬영.

### 핵심 코드 구조 (index.html 안의 script)
- `APP_VERSION` — 모드 선택 화면 오른쪽 아래에 표시. 버전 올릴 때 `CHANGELOG.md`도 같이
- `CONFIG` — `COUNTDOWN`(5), `CUT_COUNTDOWN`(3), `MAX_RETAKE`(1), `FILE_PREFIX`
- `IMG_START` — 시작 이미지 경로 (`assets/start.jpg`)
- `loadFrames()` — `frames/frames.json`을 fetch해서 `FRAMES`(`[{ name, src, thumb }]`)를 채움. 실패하면 `FALLBACK_FRAMES`(frame1) 사용
- `buildFrameList()` — 카드 생성. `thumb`가 없거나 깨지면 원본 `src`를 썸네일로 사용
- `buildOverlay(img)` — 크로마키 처리. `diff = g - max(r,b)` 기준으로 `HI=110` 이상은 완전 투명, `LO=40~110`은 부드럽게 반투명 + 초록 번짐 제거(despill). 프레임별로 `overlayCache`에 캐시
- `drawMirroredCover()` — 영상을 영역에 cover + 좌우반전으로 그림
- `compose(ctx, W, H)` — 검정 배경 → 카메라 → 오버레이 순서로 합성. 라이브 미리보기와 최종 저장에 같이 사용
- `selectFrame(i)` — 프레임 원본 로드/캐시(로딩 중 중복 터치 무시), 촬영·결과 화면의 `--ar`(비율) CSS 변수 설정
- 화면 전환은 `show(name)`, `.screen.active` 클래스로 처리

### 아이패드 관련 주의사항
- 카메라(getUserMedia)는 **https에서만** 동작. 파일 앱 미리보기, 카카오톡 인앱 브라우저, `file://`로 열면 안 됨.
- iOS 사파리는 `display:none`인 video의 프레임을 갱신하지 않음 → video를 2px·opacity 0.01로 숨겨둠. **display:none으로 바꾸지 말 것.**
- video에 `playsinline webkit-playsinline muted autoplay` 필수.
- 구글 앱스크립트 웹앱 배포는 iframe 때문에 카메라/다운로드가 막혀서 쓰지 않기로 함.

### 프레임 이미지 규칙
- 얼굴이 들어갈 자리를 순수 초록(#00FF00 계열)으로 칠한 이미지.
- 현재 프레임 8종 (frame1~7 + 반응형 `눈물`). frame7은 투명 PNG(투명 사각형 창 + 반투명 자막 바).
- frame1~5: frame1은 펭귄 탈 4구멍(원본 5661×3894 → 가로 2400px), frame2~5는 업로드된 `Group 7~10.png`를 변환한 것(1~2구멍).
- 업로드된 원본은 RGB로 변환(가장자리 반투명 1px 제거), 가로 2400px 초과면 줄임, 파일명은 `frameN.png`로 정리.
- 선택 화면 카드의 썸네일 영역은 4:3 고정(`object-fit: contain`)이라 프레임 비율이 달라도 카드 크기가 같음.
- 시작 이미지는 같은 그림에 START 글자가 있는 버전 (START 위치: 가로 24~76%, 세로 64~86% 부근).

### 프레임 추가 방법 (자동)
**`main` 브랜치의 `frames/` 폴더에 이미지를 올리기만 하면 됨.** GitHub Actions(`.github/workflows/frames.yml`)가
`tools/process_frames.py`를 돌려서 자동으로 정리하고 `main`에 커밋 → Pages 재배포.
- `frames.json`에 없는 이미지(png/jpg/webp)를 `frameN.png`로 이름 변경, 긴 변 2400px 초과면 축소
- 썸네일 `frames/thumbs/frameN.jpg` 생성, `frames.json` 끝에 등록
- 카드 이름: 파일명(예: `토마토.png` → "토마토"). `Group 11` 같은 기본 이름이면 `FRAME N`. 이름은 `frames.json`에서 바꾸면 됨
- 로컬에서 직접 돌리기: `python3 tools/process_frames.py` (Pillow 필요)
- 크로마키 처리(`getImageData`) 때문에 프레임 이미지는 **같은 출처(이 저장소)** 에 있어야 함. 외부 URL 쓰지 말 것.

### 투명 PNG 프레임
- 투명한 부분 = 카메라가 보이는 자리 (초록과 같은 역할). 반투명 = 카메라 위에 반투명하게 겹침(자막 바 등)
- 초록 구멍과 투명 구멍을 한 프레임에 섞어 써도 됨
- 반드시 PNG로 올릴 것(JPG는 투명도가 사라짐). 처리 스크립트는 투명도가 있으면 RGBA 그대로 유지하고,
  가장자리 1px에만 반투명이 있으면(내보내기 찌꺼기) RGB로 바꿈
- `buildOverlay`는 초록 판정 투명도를 원래 알파에 곱함

### 반응형(LIVE) 프레임 — 얼굴 인식으로 움직이는 스티커
`frames/` 안의 **하위 폴더 하나 = 프레임 하나** (폴더 이름 = 카드 이름, 카드에 LIVE 배지). 예: `frames/눈물/`
- `background.*` — 사람 뒤에 깔리는 배경. 있으면 카메라에서 **사람만 오려서** 배경 위에 올림(구멍 필요 없음).
  처리 스크립트가 아이패드 비율(세로 1640×2360, 가로 2360×1640, `frame.png`가 있으면 그 크기)로 꽉 차게 잘라 `background.jpg`로 저장
- `frame.png` — (선택) 맨 위에 덮는 고정 프레임. 초록/투명 구멍 규칙 동일. 배경이 없으면 지금처럼 카메라 전체 + 이 프레임
- 스티커 PNG — **파일 이름 = 붙는 위치**. 각 사람 얼굴을 따라 움직이고 크기·기울기도 따라감. 4명이면 4명 모두에 붙음
  - 기준 길이 d = 두 눈 사이 거리. 아래 "PNG 가로"는 d의 배수
  | 파일 | 붙는 점 | PNG 가로 | PNG의 어느 점을 맞추나 |
  |---|---|---|---|
  | `eye.png` (또는 `eye-left/right.png`) | 눈동자 중심 | 1d | 맨 위 가운데 |
  | `cheek.png` (또는 `cheek-left/right.png`) | 눈 아래 0.75d, 바깥 0.15d | 1d | 가운데 |
  | `nose.png` | 코끝 | 1d | 가운데 |
  | `mouth.png` | 입 | 1d | 가운데 |
  | `face.png` | 코끝 | 2.2d | 가운데 |
  | `head.png` | 두 눈 가운데에서 위로 0.9d | 2.2d | 맨 아래 가운데 |
  - left/right는 **화면 기준**(보는 사람 기준) 왼쪽/오른쪽
- 코드: `index.html`의 `VISION`(설정), `ANCHORS`(위치 규칙), `loadVision()`, `infer()`, `updateMask()`, `updateTracks()`, `drawStickers()`, `prepareLive()`
  - MediaPipe `FaceDetector`(full-range 모델, 눈·코·입 키포인트) + `ImageSegmenter`(selfie_segmenter). `vendor/mediapipe/`에 자체 호스팅
  - 인식은 영상을 가로 640px로 줄여 45ms 간격으로, 화면은 매 프레임. 얼굴 위치는 부드럽게(SMOOTH) + 잠깐 놓쳐도 400ms 유지
  - GPU 사용 실패 시 CPU로 자동 전환
- 지금 프레임: `눈물` — 하늘 배경(`2.jpg` 9:16 → 1640×2360 크롭) + 눈물 도트(`eye-left/right.png`, Claude가 그림, 레퍼런스: 눈 아래로 하늘색 도트 두 줄)
- 테스트: Chromium `--use-file-for-fake-video-capture=파일.y4m`로 얼굴이 나오는 영상을 가짜 카메라로 쓸 수 있음

### 업로드 폴더 (사용자가 GitHub 웹에서 올리는 곳) — 저장소 첫 화면 `README.md`에 표로 정리
- `cuts/` 컷 프레임, `frames/` 1장 프레임, `디자인/<용도>/` 디자인 이미지(용도별 폴더에 한 장)
  - `디자인/9컷_시트배경`·`4컷_시트배경` → `assets/sheet-9cut.png`·`sheet-4cut.png` (2400×3600)
  - `디자인/모드카드_4컷`·`_9컷`·`_1장` → `assets/mode-4cut.png`·`mode-9cut.png`·`mode-single.png` (600×900)
  - `process_design()`이 이름순 마지막 이미지를 cover로 잘라 크기 맞춤. 폴더가 비면 assets 파일 삭제(=기본 모양)
  - `assets/sheet-*`, `assets/mode-*`는 자동 생성물 → 직접 올리지 말고 `디자인/`에
- 폴더마다 `README.md`(올리기 링크·크기 안내)가 있어서 빈 폴더도 유지됨

### 4×6 인화 시트 (4컷 / 9컷)
- 4×6인치 세로 한 장에 3×3 = 9컷. 컷 = **반명함판 3×4cm (비율 3:4)**
- 1x(300dpi): 시트 1200×1800, 컷 354×472, 여백 45, 간격 24, 아래 띠 1110×222 / 디자인은 2x(컷 708×944) 권장
- 템플릿·좌표: `templates/` (`sheet_4x6_9cut.json`, 가이드 PNG, `README.md`). `frames/`에 넣지 말 것(자동 등록됨)
- 4컷: 2×6인치 띠 2줄(가운데 자름), 띠마다 같은 4컷. 컷 276×368 @1x (비율 3:4 동일 → 컷 프레임 공유), 아래 띠 540×168
- 코드: `SHEET`(SCALE 2 → 저장 2400×3600), `CUT`(708×944), `LAYOUTS`(4/9 좌표), `session`(mode, picks, shots, idx, retakeLeft, retakeIdx),
  `chooseMode()`, `renderPick()`, `startCutSession()`, `enterCut()`, `renderCutBar()`, `onCutShot()`, `composeSheet()`, `finishSheet()`, `retakeCut()`
- `shoot()`는 1장/컷 공용. 컷이면 `onCutShot()`으로 넘어감. 카운트다운: 첫 컷 `COUNTDOWN`(5), 이후 `CUT_COUNTDOWN`(3), 다시 찍기는 5
- 다시 찍기: 시트당 1번(`MAX_RETAKE`), 결과 화면에서 컷을 누름(`#retakeLayer`)
- 시트 디자인(`assets/sheet-4cut.png`/`sheet-9cut.png`, 2400×3600)은 맨 아래에 깔리고 컷이 위에 올라감. 없으면 흰 배경 + 날짜(4컷은 가운데 자르는 점선)
- 컷 고르기 화면: 작은 카드 그리드(`#cutList`, 약 200개 대비, 목록만 스크롤), 번호 `#N` = `cuts.json` 순서(+1).
  숫자는 위아래 헷갈리지 않게 **항상 밑줄**(`.no`). 컷 썸네일 240px(`CUT_THUMB`), `loading="lazy"`
  (프레임을 지우면 뒤 번호가 당겨짐)
- 컷 프레임 자동 등록: `cuts/`에 올리면 `process_frames.py`가 3:4로 맞춤(비율 다르면 초록/투명 구멍 기준으로 자름) → `cutN.png`, `cuts/cuts.json`
- PNG 저장 후 프린트. 파일명 `photobooth_9cut_…png` / `photobooth_4cut_…png`

## 다음 할 일 (디벨롭)
1. ~~이미지 파일 분리~~ (완료)
2. ~~프레임 여러 개 지원 (`frames.json`)~~ (완료) → 실제 프레임 이미지 추가만 하면 됨
3. (아이디어) 프레임별 시작 이미지/설명, 프린터 출력, 촬영 기록 등은 필요 시 결정.

## 테스트 방법
- 로컬: `python3 -m http.server 8000` → `http://localhost:8000` (localhost는 카메라 허용됨). `frames.json`을 fetch하므로 `file://`로 열면 안 됨
- 자동 테스트: Playwright + Chromium `--use-fake-ui-for-media-stream --use-fake-device-for-media-stream` 으로 가짜 카메라 사용 가능
- 실제 확인은 꼭 아이패드 사파리 + https(GitHub Pages)에서

## 배포
변경 후 `main`에 push하면 1~2분 뒤 GitHub Pages에 반영. 아이패드에서 예전 화면이 보이면 새로고침.
