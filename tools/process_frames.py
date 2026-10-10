#!/usr/bin/env python3
"""frames/ 폴더에 새로 올라온 이미지를 정리해서 frames.json에 등록한다.

- frames.json에 없는 이미지(png/jpg/jpeg/webp)를 찾아 frameN.png로 이름을 바꾼다
- 긴 변이 MAX_SIDE보다 크면 줄인다
- 투명한 부분이 있으면 RGBA 그대로 두고(투명 = 카메라가 보이는 자리),
  가장자리 1px에만 반투명이 있으면(내보내기 찌꺼기) RGB로 바꾼다
- 썸네일(frames/thumbs/frameN.jpg)을 만들고 frames.json 끝에 추가한다
- 썸네일이 빠진 기존 프레임도 썸네일을 만들어 준다

반응형(라이브) 프레임: frames/ 안의 하위 폴더 하나 = 프레임 하나 (폴더 이름 = 카드 이름)
- background.*  사람 뒤에 깔리는 배경. 있으면 카메라에서 사람만 오려서 그 위에 올림.
                아이패드 비율(세로 1640x2360 / 가로 2360x1640, frame.png가 있으면 그 크기)로 꽉 차게 잘라 background.jpg로 저장
- frame.png     맨 위에 덮는 고정 프레임 (초록/투명 구멍 규칙 동일)
- 스티커 PNG    파일 이름 = 붙는 위치 (STICKERS 참고). 얼굴을 따라 움직임

컷 프레임 (4컷/9컷 시트용): cuts/ 폴더
- 새 이미지를 cutN.png로 바꾸고 3:4(708x944)로 맞춤. 비율이 다르면 초록/투명 구멍이 가운데 오도록 잘라냄
- 썸네일 cuts/thumbs/cutN.jpg, 목록 cuts/cuts.json

디자인 이미지: 디자인/ 아래 용도별 폴더(DESIGN_TARGETS)에 아무 이름으로 한 장 올리면 크기를 맞춰 assets/로 복사하고
assets/ui/manifest.json에 목록을 씀. 앱은 이 목록에 있는 것만 바꿔 씀(없으면 기본 모양)

사용: python3 tools/process_frames.py   (저장소 루트에서 실행, Pillow 필요)
"""
import json
import re
from pathlib import Path

from PIL import Image

ROOT = Path(__file__).resolve().parent.parent
FRAMES = ROOT / 'frames'
THUMBS = FRAMES / 'thumbs'
LIST = FRAMES / 'frames.json'
CUTS = ROOT / 'cuts'
CUT_LIST = CUTS / 'cuts.json'
CUT_SIZE = (708, 944)  # 반명함판 3x4cm @600dpi
CUT_THUMB = 240        # 컷 고르기 화면은 카드가 작고 200개쯤 들어가서 썸네일도 작게
MAX_SIDE = 2400
THUMB_SIZE = 600
EXTS = {'.png', '.jpg', '.jpeg', '.webp'}
STICKERS = ['eye', 'eye-left', 'eye-right', 'cheek', 'cheek-left', 'cheek-right', 'nose', 'mouth', 'face', 'head']
LIVE_SIZE = {'portrait': (1640, 2360), 'landscape': (2360, 1640)}  # 아이패드 10세대/Air 11" 해상도
# 이런 파일명은 카드 이름으로 쓰지 않고 FRAME N으로 붙임
GENERIC = re.compile(r'^(group|frame|image|img|untitled|제목\s*없음|그룹)[\s_-]*\d*$', re.I)
# 해시처럼 생긴 이름이나 편집 앱/스크린샷 기본 이름도 FRAME N으로
GENERIC_PARTS = re.compile(r'[0-9a-f]{12,}|photoroom|screenshot|스크린샷|^img[_-]|^dsc|^kakaotalk', re.I)


def natural_key(p):
    return [int(t) if t.isdigit() else t.lower() for t in re.split(r'(\d+)', p.name)]


def has_real_alpha(im):
    """가장자리 1px을 뺀 안쪽에 투명/반투명 픽셀이 있는지."""
    if im.mode != 'RGBA':
        return False
    w, h = im.size
    if w <= 2 or h <= 2:
        return False
    inner = im.getchannel('A').crop((1, 1, w - 1, h - 1))
    return inner.getextrema()[0] < 250


def make_thumb(im, dest, size=THUMB_SIZE):
    t = im.convert('RGBA')
    bg = Image.new('RGBA', t.size, (17, 17, 17, 255))  # 선택 화면 카드 배경색
    bg.alpha_composite(t)
    bg = bg.convert('RGB')
    bg.thumbnail((size, size))
    dest.parent.mkdir(exist_ok=True)
    bg.save(dest, quality=82, optimize=True)


def hole_center(im):
    """초록/투명 구멍의 무게중심 (0~1). 구멍이 없으면 가운데."""
    t = im.convert('RGBA').copy()
    t.thumbnail((300, 300))
    px = t.load()
    sx = sy = n = 0
    for y in range(t.height):
        for x in range(t.width):
            r, g, b, a = px[x, y]
            if a < 128 or g - max(r, b) >= 110:
                sx += x; sy += y; n += 1
    return (sx / n / t.width, sy / n / t.height) if n else (.5, .5)


def fit_cut(im):
    """3:4로 꽉 차게 자르고(구멍이 가운데 오도록) CUT_SIZE로 맞춤."""
    W, H = CUT_SIZE
    s = max(W / im.width, H / im.height)
    im = im.resize((max(W, round(im.width * s)), max(H, round(im.height * s))), Image.LANCZOS)
    cx, cy = hole_center(im)
    x = min(max(round(cx * im.width - W / 2), 0), im.width - W)
    y = min(max(round(cy * im.height - H / 2), 0), im.height - H)
    return im.crop((x, y, x + W, y + H))


def write_list(path, items):
    path.write_text('[\n' + ',\n'.join('  ' + json.dumps(f, ensure_ascii=False) for f in items) + '\n]\n',
                    encoding='utf-8')


def process_cuts():
    if not CUTS.exists():
        return
    cuts = json.loads(CUT_LIST.read_text(encoding='utf-8')) if CUT_LIST.exists() else []
    known = {f.get('src') for f in cuts}
    used = {int(m.group(1)) for f in cuts if (m := re.search(r'cut(\d+)\.png$', f.get('src', '')))}
    used |= {int(m.group(1)) for p in CUTS.glob('cut*.png') if (m := re.fullmatch(r'cut(\d+)\.png', p.name))}
    no = max(used, default=0) + 1
    changed = False
    for p in sorted((p for p in CUTS.iterdir() if p.is_file() and p.suffix.lower() in EXTS
                     and f'cuts/{p.name}' not in known), key=natural_key):
        im = Image.open(p)
        im.load()
        im = fit_cut(im.convert('RGBA'))
        alpha = has_real_alpha(im)
        if not alpha:
            im = im.convert('RGB')
        dest = CUTS / f'cut{no}.png'
        im.save(dest, optimize=True)
        make_thumb(im, CUTS / 'thumbs' / f'cut{no}.jpg', CUT_THUMB)
        stem = p.stem.strip()
        label = f'CUT {no}' if GENERIC.match(stem) or GENERIC_PARTS.search(stem) else stem
        cuts.append({'name': label, 'src': f'cuts/cut{no}.png', 'thumb': f'cuts/thumbs/cut{no}.jpg'})
        if p != dest:
            p.unlink()
        print(f'컷 프레임: {p.name} -> {dest.name} "{label}"')
        no += 1
        changed = True
    for f in cuts:
        t = ROOT / f.get('thumb', '')
        if not f.get('thumb') or not (ROOT / f['src']).exists():
            continue
        if not t.exists() or max(Image.open(t).size) > CUT_THUMB:
            make_thumb(Image.open(ROOT / f['src']), t, CUT_THUMB)
            print(f'컷 썸네일: {f["thumb"]}')
            changed = True
    if changed:
        write_list(CUT_LIST, cuts)


DESIGN = ROOT / '디자인'
UI_MANIFEST = ROOT / 'assets' / 'ui' / 'manifest.json'
FONT_EXTS = {'.ttf', '.otf', '.woff', '.woff2'}
# 폴더 이름: (앱에서 쓰는 이름, 만들 파일, 크기, 맞추는 방식)
#   cover  = 비율 맞춰 가운데 기준으로 잘라 정확히 그 크기
#   inside = 비율 그대로, 그 크기 안에 들어가게만 줄임 (버튼·글자 이미지)
#   font   = 글꼴 파일 그대로 복사
DESIGN_TARGETS = {
    '시작화면':           ('bgStart',    'assets/ui/bg-start.jpg',    (1640, 2360), 'cover'),
    '모드카드_4컷':        ('mode4',      'assets/mode-4cut.png',      (600, 900),   'cover'),
    '모드카드_9컷':        ('mode9',      'assets/mode-9cut.png',      (600, 900),   'cover'),
    '모드카드_1장':        ('modeSingle', 'assets/mode-single.png',    (600, 900),   'cover'),
    '9컷_시트배경':        ('sheet9',     'assets/sheet-9cut.png',     (2400, 3600), 'cover'),
    '4컷_시트배경':        ('sheet4',     'assets/sheet-4cut.png',     (2400, 3600), 'cover'),
    '배경_메뉴화면':       ('bgMenu',     'assets/ui/bg-menu.jpg',     (1640, 2360), 'cover'),
    '제목_모드선택':       ('titleMode',  'assets/ui/title-mode.png',  (1200, 240),  'inside'),
    '제목_컷프레임고르기':  ('titlePick',  'assets/ui/title-pick.png',  (1200, 240),  'inside'),
    '제목_1장프레임고르기': ('titleFrame', 'assets/ui/title-frame.png', (1200, 240),  'inside'),
    '버튼_셔터':          ('shutter',    'assets/ui/shutter.png',     (240, 240),   'inside'),
    '버튼_처음으로':       ('home',       'assets/ui/home.png',        (120, 120),   'inside'),
    '버튼_뒤로':          ('back',       'assets/ui/back.png',        (120, 120),   'inside'),
    '버튼_촬영시작':       ('pickGo',     'assets/ui/btn-start.png',   (480, 160),   'inside'),
    '버튼_랜덤채우기':     ('pickRandom', 'assets/ui/btn-random.png',  (480, 160),   'inside'),
    '버튼_비우기':         ('pickClear',  'assets/ui/btn-clear.png',   (480, 160),   'inside'),
    '버튼_SAVE':          ('save',       'assets/ui/btn-save.png',    (480, 160),   'inside'),
    '버튼_RETAKE':        ('retake',     'assets/ui/btn-retake.png',  (480, 160),   'inside'),
    '카운트다운_5':        ('count5',     'assets/ui/count-5.png',     (600, 600),   'inside'),
    '카운트다운_4':        ('count4',     'assets/ui/count-4.png',     (600, 600),   'inside'),
    '카운트다운_3':        ('count3',     'assets/ui/count-3.png',     (600, 600),   'inside'),
    '카운트다운_2':        ('count2',     'assets/ui/count-2.png',     (600, 600),   'inside'),
    '카운트다운_1':        ('count1',     'assets/ui/count-1.png',     (600, 600),   'inside'),
    '글꼴':               ('font',       'assets/ui/font',            None,         'font'),
}


def process_design():
    """디자인/<용도> 폴더의 파일을 크기 맞춰 assets/로 복사하고 assets/ui/manifest.json에 목록을 씀.
    폴더가 비면 만든 파일도 지움(= 앱 기본 모양)."""
    import hashlib
    manifest = {}
    for folder, (key, target, size, mode) in DESIGN_TARGETS.items():
        d = DESIGN / folder
        exts = FONT_EXTS if mode == 'font' else EXTS
        files = sorted((p for p in d.iterdir() if p.is_file() and p.suffix.lower() in exts), key=natural_key) if d.exists() else []
        if mode == 'font':
            olds = [p for p in (ROOT / 'assets' / 'ui').glob('font.*')] if (ROOT / 'assets' / 'ui').exists() else []
            if not files:
                for o in olds:
                    o.unlink(); print(f'디자인: {folder} 비어 있음 → {o.name} 삭제')
                continue
            src = files[-1]
            out = ROOT / (target + src.suffix.lower())
            for o in olds:
                if o != out:
                    o.unlink()
            out.parent.mkdir(parents=True, exist_ok=True)
            if not out.exists() or out.read_bytes() != src.read_bytes():
                out.write_bytes(src.read_bytes()); print(f'디자인: {folder}/{src.name} → {out.relative_to(ROOT)}')
        else:
            out = ROOT / target
            if not files:
                if out.exists() and mode != 'start':
                    out.unlink(); print(f'디자인: {folder} 비어 있음 → {target} 삭제')
                if not out.exists():
                    continue
            else:
                if len(files) > 1:
                    print(f'디자인: {folder}에 이미지가 {len(files)}개 → 이름순 마지막 {files[-1].name} 사용')
                im = Image.open(files[-1]); im.load(); im = im.convert('RGBA')
                if mode == 'cover':
                    im = cover_crop(im, size)
                else:  # inside / start: 비율 유지, 크기 안으로만 줄임
                    im.thumbnail(size, Image.LANCZOS)
                if out.suffix == '.jpg' or not has_real_alpha(im):
                    flat = Image.new('RGB', im.size, (0, 0, 0)) if out.suffix == '.jpg' else None
                    if flat:
                        flat.paste(im, mask=im.getchannel('A')); im = flat
                    else:
                        im = im.convert('RGB')
                old = out.read_bytes() if out.exists() else None
                out.parent.mkdir(parents=True, exist_ok=True)
                if out.suffix == '.jpg':
                    im.save(out, quality=90, optimize=True)
                else:
                    im.save(out, optimize=True)
                if out.read_bytes() != old:
                    print(f'디자인: {folder}/{files[-1].name} → {target} {im.size}')
        # 같은 이름으로 바꿔 올려도 아이패드가 예전 그림을 안 쓰도록 내용 해시를 붙임
        h = hashlib.md5(out.read_bytes()).hexdigest()[:8]
        manifest[key] = f'{out.relative_to(ROOT).as_posix()}?v={h}'
    UI_MANIFEST.parent.mkdir(parents=True, exist_ok=True)
    text = json.dumps(manifest, ensure_ascii=False, indent=1) + '\n'
    if not UI_MANIFEST.exists() or UI_MANIFEST.read_text(encoding='utf-8') != text:
        UI_MANIFEST.write_text(text, encoding='utf-8'); print('디자인 목록:', ', '.join(manifest) or '(없음)')


def find(folder, stem):
    for ext in ('.png', '.jpg', '.jpeg', '.webp'):
        for p in folder.iterdir():
            if p.is_file() and p.stem.lower() == stem and p.suffix.lower() == ext:
                return p
    return None


def cover_crop(im, size):
    """비율 유지하며 size를 꽉 채우도록 가운데 기준으로 자르고 맞춤."""
    W, H = size
    s = max(W / im.width, H / im.height)
    im = im.resize((max(W, round(im.width * s)), max(H, round(im.height * s))), Image.LANCZOS)
    x, y = (im.width - W) // 2, (im.height - H) // 2
    return im.crop((x, y, x + W, y + H))


def process_live(folder, old):
    rel = lambda p: p.relative_to(ROOT).as_posix()
    entry = {'name': (old or {}).get('name', folder.name), 'live': True}
    size = None

    fr = find(folder, 'frame')
    if fr:
        im = Image.open(fr).convert('RGBA')
        if max(im.size) > MAX_SIDE:
            s = MAX_SIDE / max(im.size)
            im = im.resize((round(im.width * s), round(im.height * s)), Image.LANCZOS)
        if not has_real_alpha(im):
            im = im.convert('RGB')
        dest = folder / 'frame.png'
        im.save(dest, optimize=True)
        if fr != dest:
            fr.unlink()
        entry['src'] = rel(dest)
        size = im.size

    bg = find(folder, 'background') or find(folder, 'bg')
    if bg:
        im = Image.open(bg)
        im.load()
        if size is None:
            size = LIVE_SIZE['landscape' if im.width > im.height else 'portrait']
        dest = folder / 'background.jpg'
        if im.size != size or bg != dest:
            flat = Image.new('RGB', im.size, (0, 0, 0))
            flat.paste(im.convert('RGBA'), mask=im.convert('RGBA').getchannel('A'))
            cover_crop(flat, size).save(dest, quality=90, optimize=True)
            if bg != dest:
                bg.unlink()
        entry['background'] = rel(dest)

    entry['width'], entry['height'] = size or LIVE_SIZE['portrait']
    stickers = {}
    for k in STICKERS:
        p = find(folder, k)
        if p:
            stickers[k] = rel(p)
    if stickers:
        entry['stickers'] = stickers

    # 썸네일: 배경 + 프레임 (스티커는 얼굴이 있어야 해서 생략)
    base = Image.new('RGBA', (entry['width'], entry['height']), (17, 17, 17, 255))
    if bg:
        base.alpha_composite(Image.open(ROOT / entry['background']).convert('RGBA'))
    if fr:
        base.alpha_composite(Image.open(ROOT / entry['src']).convert('RGBA'))
    thumb = THUMBS / f'{folder.name}.jpg'
    make_thumb(base, thumb)
    entry['thumb'] = rel(thumb)
    return entry


def main():
    frames = json.loads(LIST.read_text(encoding='utf-8')) if LIST.exists() else []
    known = {f.get('src') for f in frames}
    used = {int(m.group(1)) for f in frames if (m := re.search(r'frame(\d+)\.png$', f.get('src', '')))}
    used |= {int(m.group(1)) for p in FRAMES.glob('frame*.png') if (m := re.fullmatch(r'frame(\d+)\.png', p.name))}
    next_no = max(used, default=0) + 1

    new_files = sorted(
        (p for p in FRAMES.iterdir()
         if p.is_file() and p.suffix.lower() in EXTS and f'frames/{p.name}' not in known),
        key=natural_key)

    changed = False
    # 반응형 프레임 폴더: 매번 다시 훑어서 새 파일/교체된 파일을 반영 (이름과 순서는 유지)
    for folder in sorted((d for d in FRAMES.iterdir() if d.is_dir() and d.name != 'thumbs'), key=natural_key):
        key = f'frames/{folder.name}'
        idx = next((i for i, f in enumerate(frames) if f.get('dir') == key), None)
        old = frames[idx] if idx is not None else None
        entry = process_live(folder, old)
        entry = {'name': entry.pop('name'), 'dir': key, **entry}
        if entry != old:
            if idx is None:
                frames.append(entry)
            else:
                frames[idx] = entry
            print(f'반응형 프레임: {folder.name} {entry.get("stickers", {})}')
            changed = True

    for p in new_files:
        im = Image.open(p)
        im.load()
        im = im.convert('RGBA')
        if max(im.size) > MAX_SIDE:
            s = MAX_SIDE / max(im.size)
            im = im.resize((round(im.width * s), round(im.height * s)), Image.LANCZOS)
        alpha = has_real_alpha(im)
        if not alpha:
            im = im.convert('RGB')

        name = f'frame{next_no}.png'
        dest = FRAMES / name
        im.save(dest, optimize=True)
        make_thumb(im, THUMBS / f'frame{next_no}.jpg')
        stem = p.stem.strip()
        label = f'FRAME {next_no}' if GENERIC.match(stem) or GENERIC_PARTS.search(stem) else stem
        frames.append({'name': label, 'src': f'frames/{name}', 'thumb': f'frames/thumbs/frame{next_no}.jpg'})
        if p != dest:
            p.unlink()
        print(f'{p.name} -> {name} {im.size} {"RGBA(투명 유지)" if alpha else "RGB"} "{label}"')
        next_no += 1
        changed = True

    for f in frames:
        if f.get('live'):
            continue
        src = ROOT / f['src']
        thumb = f.get('thumb')
        if src.exists() and thumb and not (ROOT / thumb).exists():
            make_thumb(Image.open(src), ROOT / thumb)
            print(f'썸네일 생성: {thumb}')
            changed = True

    if changed:
        write_list(LIST, frames)
    else:
        print('새 프레임 없음')
    process_cuts()
    process_design()


if __name__ == '__main__':
    main()
