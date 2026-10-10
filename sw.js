/* 오프라인 대비 (v4.4)
 * - 인터넷이 되면 항상 최신 파일을 받아 쓰고(네트워크 우선), 받은 파일은 아이패드에 저장해 둠
 * - 인터넷이 끊기면 저장해 둔 파일로 앱이 그대로 돌아감
 * - 앱을 열 때마다 프레임·컷·얼굴인식 파일 중 아직 저장 안 된 것만 조용히 받아 둠
 *   → 행사 전에 와이파이에서 앱을 한 번 열어 두고, 버전 옆에 "오프라인 준비됨"이 뜨면 끝
 */
const CACHE = 'photobooth-offline-v1';
const CORE = [
  './',
  'index.html',
  'frames/frames.json',
  'cuts/cuts.json',
  'assets/ui/manifest.json',
  'assets/start-bg.jpg',
  'assets/pick-bg.jpg',
  'assets/pick-bg-land.jpg',
  'vendor/mediapipe/vision_bundle.mjs',
  'vendor/mediapipe/wasm/vision_wasm_internal.js',
  'vendor/mediapipe/wasm/vision_wasm_internal.wasm',
  'vendor/mediapipe/wasm/vision_wasm_nosimd_internal.js',
  'vendor/mediapipe/wasm/vision_wasm_nosimd_internal.wasm',
  'vendor/mediapipe/models/blaze_face_full_range.tflite',
  'vendor/mediapipe/models/blaze_face_short_range.tflite',
  'vendor/mediapipe/models/selfie_segmenter.tflite',
];

self.addEventListener('install', e => {
  self.skipWaiting();
  e.waitUntil(caches.open(CACHE).then(c => Promise.all(CORE.map(u => c.add(u).catch(() => {})))));
});

self.addEventListener('activate', e => {
  e.waitUntil((async () => {
    const keys = await caches.keys();
    await Promise.all(keys.filter(k => k.startsWith('photobooth-offline-') && k !== CACHE).map(k => caches.delete(k)));
    await self.clients.claim();
  })());
});

self.addEventListener('fetch', e => {
  const req = e.request;
  if (req.method !== 'GET') return;
  const url = new URL(req.url);
  if (url.origin !== self.location.origin) return;
  e.respondWith((async () => {
    try {
      const res = await fetch(req);
      if (res && res.ok && res.type === 'basic') {
        const copy = res.clone();
        caches.open(CACHE).then(c => c.put(req, copy)).catch(() => {});
      }
      return res;
    } catch (err) {
      const c = await caches.open(CACHE);
      const hit = (await c.match(req)) || (await c.match(req, { ignoreSearch: true }));
      if (hit) return hit;
      if (req.mode === 'navigate') {
        const page = (await c.match('index.html')) || (await c.match('./'));
        if (page) return page;
      }
      throw err;
    }
  })());
});

/* 앱이 'warm'을 보내면: 목록에 있는 파일 중 저장 안 된 것만 받아 두고, 끝나면 몇 개 준비됐는지 알려줌 */
async function listAll() {
  const urls = new Set(CORE);
  const read = async (path) => {
    try { const r = await fetch(path, { cache: 'no-cache' }); return r.ok ? await r.json() : null; } catch (e) { return null; }
  };
  const [frames, cuts, ui] = await Promise.all([read('frames/frames.json'), read('cuts/cuts.json'), read('assets/ui/manifest.json')]);
  const walk = (v) => {
    if (typeof v === 'string') { if (/\.(png|jpe?g|webp|gif)(\?|$)/i.test(v)) urls.add(v); }
    else if (Array.isArray(v)) v.forEach(walk);
    else if (v && typeof v === 'object') Object.values(v).forEach(walk);
  };
  walk(frames);
  walk(cuts);
  if (ui && typeof ui === 'object') for (const v of Object.values(ui)) if (typeof v === 'string') urls.add(v);
  return [...urls];
}

self.addEventListener('message', e => {
  if (e.data !== 'warm') return;
  const port = e.source;
  e.waitUntil((async () => {
    const c = await caches.open(CACHE);
    const urls = await listAll();
    let ok = 0;
    for (const u of urls) {
      if (await c.match(u)) { ok++; continue; }
      try { const r = await fetch(u); if (r.ok) { await c.put(u, r); ok++; } } catch (err) {}
    }
    if (port) port.postMessage({ type: 'offline-status', ok, total: urls.length });
  })());
});
