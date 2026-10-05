# MediaPipe (반응형 프레임용)

- `vision_bundle.mjs`, `wasm/` — npm `@mediapipe/tasks-vision` 1.0.1 (Apache-2.0)
- `models/blaze_face_full_range.tflite` — 얼굴 인식 (멀리 선 여러 명용)
- `models/blaze_face_short_range.tflite` — 얼굴 인식 (가까운 거리용, 예비)
- `models/selfie_segmenter.tflite` — 사람 오려내기
  (모델 출처: https://storage.googleapis.com/mediapipe-models/)

행사장 네트워크에 덜 의존하도록 CDN 대신 저장소에 같이 둠. 반응형 프레임을 고를 때만 내려받음.
