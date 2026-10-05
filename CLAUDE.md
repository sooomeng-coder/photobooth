# 포토부스 웹앱 (photobooth)

행사용 그린스크린 포토부스 웹앱. 아이패드 사파리에서 전체화면으로 띄워두고, 4명이 카메라 앞에 서서 프레임 구멍에 얼굴을 맞춰 찍는 방식.

- 배포: GitHub Pages — `https://sooomeng-coder.github.io/photobooth/`
- 저장소: `sooomeng-coder/photobooth` (main 브랜치 루트의 `index.html`이 서비스됨)
- 사용 기기: 아이패드 사파리 (홈 화면에 추가해서 전체화면으로 사용)

## 현재 상태 (v3)

이미지는 base64가 아니라 별도 파일로 분리되어 있고, `index.html`이 상대경로로 불러옴.

```
index.html               앱 전체 (HTML/CSS/JS)
assets/start.jpg         시작 이미지 (START 글자 있는 버전)
frames/frames.json       프레임 목록 (선택 화면에 이 순서대로 표시)
frames/frame1.png        그린스크린 프레임 원본 (저장 해상도 = 이 파일 해상도)
frames/thumbs/frame1.jpg 선택 화면용 썸네일 (가로 600px JPEG)
```

### 화면 흐름
1. **시작 화면** — 시작 이미지를 화면에 맞춰 표시. START 글자 위에 투명 버튼이 있고(초록 glow pulse), 화면 아무 곳을 눌러도 다음으로 넘어감. 이때 카메라 권한도 미리 요청.
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
- `CONFIG` — `COUNTDOWN`(5), `MAX_RETAKE`(1), `FILE_PREFIX`
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
- 현재 프레임 5종 (frame1~5). frame1은 펭귄 탈 4구멍(원본 5661×3894 → 가로 2400px), frame2~5는 업로드된 `Group 7~10.png`를 변환한 것(1~2구멍).
- 업로드된 원본은 RGB로 변환(가장자리 반투명 1px 제거), 가로 2400px 초과면 줄임, 파일명은 `frameN.png`로 정리.
- 선택 화면 카드의 썸네일 영역은 4:3 고정(`object-fit: contain`)이라 프레임 비율이 달라도 카드 크기가 같음.
- 시작 이미지는 같은 그림에 START 글자가 있는 버전 (START 위치: 가로 24~76%, 세로 64~86% 부근).

### 프레임 추가 방법
1. 그린스크린 PNG를 가로 2400px 정도로 리사이즈해서 `frames/frame2.png` 등으로 넣기
2. (선택) 가로 600px JPEG 썸네일을 `frames/thumbs/frame2.jpg`로 넣기 — 없으면 원본을 썸네일로 씀(선택 화면 로딩이 느려짐)
3. `frames/frames.json`에 한 줄 추가:
   `{ "name": "FRAME 2", "src": "frames/frame2.png", "thumb": "frames/thumbs/frame2.jpg" }`
- 썸네일 만들기 예: `python3 -c "from PIL import Image; im=Image.open('frames/frame2.png').convert('RGB'); im.thumbnail((600,600)); im.save('frames/thumbs/frame2.jpg', quality=82)"`
- 크로마키 처리(`getImageData`) 때문에 프레임 이미지는 **같은 출처(이 저장소)** 에 있어야 함. 외부 URL 쓰지 말 것.

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
