#!/usr/bin/env python3
"""frames/ 폴더에 새로 올라온 이미지를 정리해서 frames.json에 등록한다.

- frames.json에 없는 이미지(png/jpg/jpeg/webp)를 찾아 frameN.png로 이름을 바꾼다
- 긴 변이 MAX_SIDE보다 크면 줄인다
- 투명한 부분이 있으면 RGBA 그대로 두고(투명 = 카메라가 보이는 자리),
  가장자리 1px에만 반투명이 있으면(내보내기 찌꺼기) RGB로 바꾼다
- 썸네일(frames/thumbs/frameN.jpg)을 만들고 frames.json 끝에 추가한다
- 썸네일이 빠진 기존 프레임도 썸네일을 만들어 준다

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
MAX_SIDE = 2400
THUMB_SIZE = 600
EXTS = {'.png', '.jpg', '.jpeg', '.webp'}
# 이런 파일명은 카드 이름으로 쓰지 않고 FRAME N으로 붙임
GENERIC = re.compile(r'^(group|frame|image|img|untitled|제목\s*없음|그룹)[\s_-]*\d*$', re.I)


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


def make_thumb(im, dest):
    t = im.convert('RGBA')
    bg = Image.new('RGBA', t.size, (17, 17, 17, 255))  # 선택 화면 카드 배경색
    bg.alpha_composite(t)
    bg = bg.convert('RGB')
    bg.thumbnail((THUMB_SIZE, THUMB_SIZE))
    dest.parent.mkdir(exist_ok=True)
    bg.save(dest, quality=82, optimize=True)


def main():
    frames = json.loads(LIST.read_text(encoding='utf-8')) if LIST.exists() else []
    known = {f['src'] for f in frames}
    used = {int(m.group(1)) for f in frames if (m := re.search(r'frame(\d+)\.png$', f['src']))}
    used |= {int(m.group(1)) for p in FRAMES.glob('frame*.png') if (m := re.fullmatch(r'frame(\d+)\.png', p.name))}
    next_no = max(used, default=0) + 1

    new_files = sorted(
        (p for p in FRAMES.iterdir()
         if p.is_file() and p.suffix.lower() in EXTS and f'frames/{p.name}' not in known),
        key=natural_key)

    changed = False
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
        label = p.stem if not GENERIC.match(p.stem.strip()) else f'FRAME {next_no}'
        frames.append({'name': label, 'src': f'frames/{name}', 'thumb': f'frames/thumbs/frame{next_no}.jpg'})
        if p != dest:
            p.unlink()
        print(f'{p.name} -> {name} {im.size} {"RGBA(투명 유지)" if alpha else "RGB"} "{label}"')
        next_no += 1
        changed = True

    for f in frames:
        src = ROOT / f['src']
        thumb = f.get('thumb')
        if src.exists() and thumb and not (ROOT / thumb).exists():
            make_thumb(Image.open(src), ROOT / thumb)
            print(f'썸네일 생성: {thumb}')
            changed = True

    if changed:
        LIST.write_text('[\n' + ',\n'.join('  ' + json.dumps(f, ensure_ascii=False) for f in frames) + '\n]\n',
                        encoding='utf-8')
    else:
        print('새 프레임 없음')


if __name__ == '__main__':
    main()
