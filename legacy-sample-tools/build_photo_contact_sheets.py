# Preserved local sample workflow; private inputs excluded. See README.md.
from __future__ import annotations
import sys as _sample_sys
from pathlib import Path as _SamplePath
_sample_sys.path.insert(0,str(_SamplePath(__file__).resolve().parent))
from sample_runtime import sample
sample.configure()
import csv
import hashlib
import math
from pathlib import Path
import cv2
import numpy as np
from PIL import Image, ImageDraw, ImageFont, ImageOps
BASE = sample.workspace() / 'inputs/photos'
OUT = sample.workspace() / 'outputs/contact-sheets'
GROUPS = ['group-1', 'group-2', 'group-3', 'group-4']
FONT_PATH = sample.input_path('input_0003')

def phash(image: Image.Image) -> str:
    gray = np.asarray(image.convert('L').resize((32, 32), Image.Resampling.LANCZOS), dtype=np.float32)
    coeff = cv2.dct(gray)[:8, :8]
    flat = coeff.flatten()
    median = np.median(flat[1:])
    bits = flat > median
    return f'{sum((int(bit) << 63 - i for i, bit in enumerate(bits))):016x}'

def dhash(image: Image.Image) -> str:
    gray = np.asarray(image.convert('L').resize((9, 8), Image.Resampling.LANCZOS))
    bits = gray[:, 1:] > gray[:, :-1]
    return f'{sum((int(bit) << 63 - i for i, bit in enumerate(bits.flatten()))):016x}'

def blur_score(image: Image.Image) -> float:
    gray = np.asarray(image.convert('L'))
    max_side = max(gray.shape)
    if max_side > 1600:
        ratio = 1600 / max_side
        gray = cv2.resize(gray, None, fx=ratio, fy=ratio, interpolation=cv2.INTER_AREA)
    return float(cv2.Laplacian(gray, cv2.CV_64F).var())

def exif_datetime(raw: Image.Image) -> str:
    exif = raw.getexif()
    return str(exif.get(36867) or exif.get(306) or '')

def sheet_label(group: str, idx: int, path: Path) -> str:
    if group == 'group-1':
        return f'{idx:02d}  {path.stem}'
    return f'{idx:02d}  {path.stem[:12]}'

def main() -> None:
    OUT.mkdir(parents=True, exist_ok=True)
    records: list[dict[str, object]] = []
    font = sample.font(23)
    small = sample.font(18)
    for group in GROUPS:
        paths = sorted((BASE / group).rglob('*.jpg'), key=lambda p: p.name)
        thumbs: list[tuple[Path, Image.Image, str]] = []
        for idx, path in enumerate(paths, 1):
            data = path.read_bytes()
            with Image.open(path) as raw:
                original_size = raw.size
                dt = exif_datetime(raw)
                image = ImageOps.exif_transpose(raw).convert('RGB')
            records.append({'group': group, 'index': idx, 'filename': path.name, 'path': str(path.relative_to(BASE)), 'width': image.width, 'height': image.height, 'raw_width': original_size[0], 'raw_height': original_size[1], 'orientation': 'landscape' if image.width > image.height else 'portrait' if image.height > image.width else 'square', 'bytes': len(data), 'md5': hashlib.md5(data).hexdigest(), 'phash': phash(image), 'dhash': dhash(image), 'blur_score': round(blur_score(image), 2), 'exif_datetime': dt})
            thumb = ImageOps.contain(image, (330, 235), Image.Resampling.LANCZOS)
            thumbs.append((path, thumb, sheet_label(group, idx, path)))
        cols, rows = (3, 3)
        cell_w, cell_h = (420, 330)
        page_size = cols * rows
        for page_idx in range(math.ceil(len(thumbs) / page_size)):
            page = Image.new('RGB', (cols * cell_w, rows * cell_h + 70), '#f4f4f2')
            draw = ImageDraw.Draw(page)
            draw.text((22, 18), f'{group} — field_0004 {page_idx + 1}/{math.ceil(len(thumbs) / page_size)}', font=font, fill='#111111')
            for offset, (path, thumb, label) in enumerate(thumbs[page_idx * page_size:(page_idx + 1) * page_size]):
                row, col = divmod(offset, cols)
                x, y = (col * cell_w, row * cell_h + 70)
                draw.rounded_rectangle((x + 8, y + 8, x + cell_w - 8, y + cell_h - 8), 12, fill='white', outline='#cccccc', width=2)
                ix = x + (cell_w - thumb.width) // 2
                iy = y + 18 + (235 - thumb.height) // 2
                page.paste(thumb, (ix, iy))
                clipped = label if len(label) <= 28 else label[:27] + '…'
                draw.text((x + 18, y + 265), clipped, font=small, fill='#111111')
                rec = records[page_idx * page_size + offset + sum((len(sorted((BASE / g).rglob('*.jpg'), key=lambda p: p.name)) for g in GROUPS[:GROUPS.index(group)]))]
                draw.text((x + 18, y + 296), f'{rec['width']}×{rec['height']}  field_0005{rec['blur_score']}', font=small, fill='#666666')
            page.save(OUT / f'contact_{GROUPS.index(group) + 1}_{group}_{page_idx + 1}.jpg', quality=92)
    fields = list(records[0].keys())
    with (OUT / 'photo_metadata.csv').open('w', encoding='utf-8-sig', newline='') as handle:
        writer = csv.DictWriter(handle, fieldnames=fields)
        writer.writeheader()
        writer.writerows(records)

    def hamming(hex_a: str, hex_b: str) -> int:
        return (int(hex_a, 16) ^ int(hex_b, 16)).bit_count()
    finals = [r for r in records if r['group'] == 'group-1']
    originals = [r for r in records if r['group'] != 'group-1']
    with (OUT / 'photo_nearest_matches.csv').open('w', encoding='utf-8-sig', newline='') as handle:
        fields2 = ['final_index', 'final_filename', 'source_group', 'source_index', 'source_filename', 'phash_distance', 'dhash_distance']
        writer = csv.DictWriter(handle, fieldnames=fields2)
        writer.writeheader()
        for final in finals:
            ranked = sorted(originals, key=lambda other: (hamming(str(final['phash']), str(other['phash'])), hamming(str(final['dhash']), str(other['dhash']))))[:5]
            for other in ranked:
                writer.writerow({'final_index': final['index'], 'final_filename': final['filename'], 'source_group': other['group'], 'source_index': other['index'], 'source_filename': other['filename'], 'phash_distance': hamming(str(final['phash']), str(other['phash'])), 'dhash_distance': hamming(str(final['dhash']), str(other['dhash']))})
if __name__ == '__main__':
    main()
