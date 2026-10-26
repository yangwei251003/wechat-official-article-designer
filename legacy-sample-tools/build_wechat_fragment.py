# Preserved local sample workflow; private inputs excluded. See README.md.
from __future__ import annotations
import sys as _sample_sys
from pathlib import Path as _SamplePath
_sample_sys.path.insert(0,str(_SamplePath(__file__).resolve().parent))
from sample_runtime import sample
sample.configure()
import html
import sys
from pathlib import Path
ROOT = sample.input_path('input_0042')
PACKAGE = ROOT / 'wechat-output' / 'field_0010_field_0011_field_0043'
SOURCE = PACKAGE / 'source.md'
FRAGMENT = PACKAGE / 'article-fragment.html'
SKILL_SCRIPTS = ROOT / 'wechat-official-article-designer' / 'scripts'
sys.path.insert(0, str(sample.project_root() / 'scripts'))
from common import markdown_blocks, read_text
INK = '#183B56'
GREEN = '#2EAD72'
RED = '#D94135'
PAPER = '#F7F2E8'
MUTED = '#607479'

def esc(text: str) -> str:
    return html.escape(text, quote=True)

def image_full(src: str, alt: str, caption: str, margin: str='24px 0 28px') -> str:
    return f'<section data-component="photo-full" data-visual-role="documentary-photo" style="margin:{margin};"><img src="assets/{esc(src)}" alt="{esc(alt)}" style="display:block;width:100%;height:auto;margin:0;border-radius:16px;" /><p style="margin:9px 4px 0;color:#748386;font-size:12px;line-height:1.65;text-align:center;letter-spacing:.04em;">{esc(caption)}</p></section>'

def image_pair(left: tuple[str, str, str], right: tuple[str, str, str], caption: str) -> str:
    return f'<section data-component="photo-pair" data-visual-role="photo-dialogue" style="margin:24px 0 28px;"><table width="100%" cellspacing="0" cellpadding="0" role="presentation" style="width:100%;border-collapse:separate;border-spacing:7px 0;"><tbody><tr><td width="50%" valign="top" style="width:50%;padding:0;"><img src="assets/{esc(left[0])}" alt="{esc(left[1])}" style="display:block;width:100%;height:auto;margin:0;border-radius:14px;" /><p style="margin:8px 2px 0;color:#748386;font-size:11px;line-height:1.55;text-align:center;">{esc(left[2])}</p></td><td width="50%" valign="top" style="width:50%;padding:0;"><img src="assets/{esc(right[0])}" alt="{esc(right[1])}" style="display:block;width:100%;height:auto;margin:0;border-radius:14px;" /><p style="margin:8px 2px 0;color:#748386;font-size:11px;line-height:1.55;text-align:center;">{esc(right[2])}</p></td></tr></tbody></table><p style="margin:9px 4px 0;color:#748386;font-size:12px;line-height:1.65;text-align:center;letter-spacing:.04em;">{esc(caption)}</p></section>'

def h2(title: str, index: int) -> str:
    nums = ['01', '02', '03', '04', '05', '06']
    number = nums[min(index, len(nums) - 1)]
    return f'<section data-component="chapter-heading" data-visual-role="chapter-marker" style="margin:48px 0 24px;"><table width="100%" cellspacing="0" cellpadding="0" role="presentation" style="width:100%;border-collapse:collapse;"><tbody><tr><td width="54" valign="middle" style="width:54px;padding:0 12px 0 0;color:{RED};font-size:13px;font-weight:700;letter-spacing:.14em;">{number}</td><td valign="middle" style="padding:0 0 0 14px;border-left:4px solid {GREEN};"><p style="margin:0;color:{INK};font-size:22px;font-weight:800;line-height:1.45;letter-spacing:.02em;">{esc(title)}</p></td></tr></tbody></table></section>'
DAY_COLORS = [INK, '#177A55', '#B92F27', '#177A55', INK]

def h3(title: str, day_index: int) -> str:
    accent = DAY_COLORS[day_index]
    day_no = f'0{day_index + 1}'
    return f'<section data-component="day-heading" data-visual-role="petal-marker" style="margin:38px 0 20px;"><table width="100%" cellspacing="0" cellpadding="0" role="presentation" bgcolor="#FFFFFF" style="width:100%;border-collapse:collapse;background-color:#FFFFFF;border:1px solid #E1E8E4;border-radius:18px;"><tbody><tr><td width="72" valign="middle" bgcolor="{accent}" style="width:72px;padding:19px 9px;background-color:{accent};color:#FFFFFF;text-align:center;border-radius:18px 0 0 18px;"><p style="margin:0;font-size:12px;line-height:1.2;letter-spacing:.12em;">PETAL</p><p style="margin:4px 0 0;font-size:30px;font-weight:800;line-height:1;">{day_no}</p></td><td valign="middle" style="padding:18px 18px 18px 20px;"><p style="margin:0;color:{INK};font-size:19px;font-weight:800;line-height:1.55;">{esc(title)}</p></td></tr></tbody></table></section>'

def paragraph(text: str, special: str='') -> str:
    if special == 'lead':
        return f'<p style="margin:0 0 20px;color:{INK};font-size:17px;line-height:2.05;letter-spacing:.035em;font-weight:600;">{esc(text)}</p>'
    if special == 'impact':
        return f'<blockquote data-component="impact-quote" data-visual-role="pull-quote" style="margin:26px 0;padding:21px 20px 20px;border-left:5px solid {RED};background-color:#FFF2EE;border-radius:0 16px 16px 0;"><p style="margin:0;color:{INK};font-size:16px;line-height:1.95;font-weight:700;">{esc(text)}</p></blockquote>'
    if special == 'closing':
        return f'<section data-component="closing-manifesto" data-visual-role="manifesto" bgcolor="{INK}" style="margin:26px 0;padding:26px 22px;background-color:{INK};border-radius:20px;"><p style="margin:0;color:#FFFFFF;font-size:17px;line-height:2.05;font-weight:700;letter-spacing:.025em;">{esc(text)}</p></section>'
    if special == 'thanks':
        return f'<p style="margin:26px 0 8px;padding:18px 16px;color:{RED};font-size:15px;line-height:1.9;text-align:center;font-weight:700;border-top:1px solid #D7E2DC;border-bottom:1px solid #D7E2DC;">{esc(text)}</p>'
    return f'<p style="margin:0 0 18px;color:#284752;font-size:15px;line-height:1.95;letter-spacing:.025em;text-align:justify;">{esc(text)}</p>'

def fact_table(facts: list[str]) -> str:
    rows = []
    for item in facts:
        label, value = item.split('：', 1)
        rows.append(f'<tr><td width="30%" valign="top" style="width:30%;padding:10px 8px;color:{MUTED};font-size:13px;line-height:1.6;border-bottom:1px solid #E7ECE9;">{esc(label)}：</td><td valign="top" style="padding:10px 8px;color:{INK};font-size:14px;line-height:1.6;font-weight:700;border-bottom:1px solid #E7ECE9;">{esc(value)}</td></tr>')
    return '<section data-component="fact-card" data-visual-role="fact-anchor" bgcolor="#FFFFFF" style="margin:16px 0 24px;padding:8px 16px 12px;background-color:#FFFFFF;border:1px solid #DCE6E1;border-radius:18px;"><table width="100%" cellspacing="0" cellpadding="0" role="presentation" style="width:100%;border-collapse:collapse;"><tbody>' + ''.join(rows) + '</tbody></table></section>'
INSERTIONS: dict[str, str] = {'2026field_00447field_004527field_004631field_0047': image_full('asset_0074.jpg', 'field_0075', 'field_0076，field_0077。'), 'field_0048': image_full('asset_0078.jpg', 'field_0079', 'field_0080。') + image_full('asset_0081.jpg', 'field_0082', 'field_0083、field_0084，field_0085。', '18px 24px 30px'), 'field_0049': image_full('asset_0086.jpg', 'field_0087', 'field_0088，field_0089。'), 'field_0050': image_pair(('asset_0090.jpg', 'field_0091', 'field_0092'), ('asset_0093.jpg', 'field_0094', 'field_0095，field_0096'), 'field_0097，field_0098。'), 'field_0051，field_0052': image_pair(('asset_0099.jpg', 'field_0100', 'field_0101'), ('asset_0102.jpg', 'field_0103', 'field_0104'), 'field_0105，field_0106。'), 'field_0053，field_0054“field_0055”': image_full('asset_0107.jpg', 'field_0108', 'field_0109，field_0110。'), 'field_0056、field_0057、field_0058': image_full('asset_0111.jpg', 'field_0112', 'field_0113，field_0114。'), 'field_0051，field_0059': image_pair(('asset_0115.jpg', 'field_0116', 'field_0117'), ('asset_0118.jpg', 'field_0119', 'field_0120，field_0121'), 'field_0122，field_0123。'), 'field_0060，field_0061': image_pair(('asset_0124.jpg', 'field_0125', 'field_0126，field_0127'), ('asset_0128.jpg', 'field_0129', 'field_0130，field_0131'), 'field_0132，field_0133。') + image_full('asset_0134.jpg', 'field_0135', 'field_0136，field_0137。'), 'field_0051，field_0062': image_full('asset_0138.jpg', 'field_0139', 'field_0140、field_0141、field_0142，field_0143。'), 'field_0063《field_0064》': image_pair(('asset_0144.jpg', 'field_0145、field_0146', 'field_0147'), ('asset_0148.jpg', 'field_0149', 'field_0150，field_0151'), 'field_0152，field_0153。'), 'field_0065，“field_0066”field_0067': image_full('asset_0154.jpg', 'field_0155', 'field_0156，field_0157。'), 'field_0068': image_full('asset_0158.jpg', 'field_0159', 'field_0160，field_0161。'), 'field_0069，field_0070': image_pair(('asset_0162.jpg', 'field_0163', 'field_0164，field_0165'), ('asset_0166.jpg', 'field_0167', 'field_0168，field_0169'), 'field_0170，field_0171。'), 'field_0071，field_0072': image_full('asset_0172.jpg', 'field_0173', 'field_0174，field_0175。'), 'field_0073': image_full('asset_0176.jpg', 'field_0177', 'field_0178。') + image_full('asset_0179.jpg', 'field_0180', '“field_0012”field_0181。', '18px 0 28px')}

def main() -> None:
    blocks = markdown_blocks(read_text(SOURCE))
    output = [f'<table width="100%" cellspacing="0" cellpadding="0" role="presentation" bgcolor="{PAPER}" style="width:100%;border-collapse:collapse;background-color:{PAPER};">', f'<tbody><tr><td bgcolor="{PAPER}" style="padding:0;background-color:{PAPER};">', f"""<section data-rhythm="editorial-longform" data-visual-role="article-root" data-component="five-petal-story" style="max-width:677px;margin:0 auto;padding:18px 15px 36px;font-family:-apple-system,BlinkMacSystemFont,'Segoe UI','PingFang SC','Microsoft YaHei',Arial,sans-serif;color:{INK};background-color:{PAPER};">""", '<img src="assets/brand-strip.png" alt="field_0182" style="display:block;width:100%;height:auto;margin:0 0 22px;border-radius:14px;" />', f'<p style="margin:0 0 12px;color:{RED};font-size:12px;line-height:1.5;text-align:center;font-weight:700;letter-spacing:.18em;">YOUTH PRACTICE JOURNAL · 2026</p>']
    fact_items: list[str] = []
    in_facts = False
    h2_index = 0
    day_index = 0
    para_index = 0
    for block in blocks:
        kind = block['type']
        text = block['text']
        if kind == 'heading' and block.get('level') == '1':
            output.append(f'<p data-component="hero-title" data-visual-role="headline" style="margin:0 0 22px;color:{INK};font-size:30px;font-weight:900;line-height:1.45;text-align:center;letter-spacing:.015em;">{esc(text)}</p>')
            output.append(f'<p style="margin:0 auto 25px;width:56px;border-bottom:5px solid {GREEN};line-height:0;">&nbsp;</p>')
            continue
        if kind == 'heading' and block.get('level') == '2':
            if in_facts:
                output.append(fact_table(fact_items))
                output.append('<section data-rhythm="photo-journal" data-component="five-day-map" data-visual-role="semantic-motion" style="margin:24px 0 34px;"><img src="assets/five-petal-bloom.gif" alt="field_0183，field_0184、field_0019、field_0020、field_0185" style="display:block;width:100%;height:auto;margin:0;border-radius:18px;" /><p style="margin:9px 4px 0;color:#748386;font-size:12px;line-height:1.65;text-align:center;">field_0186，field_0187。</p></section>')
                in_facts = False
                fact_items = []
            output.append(h2(text, h2_index))
            h2_index += 1
            if text == 'field_0188':
                in_facts = True
            continue
        if kind == 'heading' and block.get('level') == '3':
            output.append(h3(text, day_index))
            day_index += 1
            continue
        if kind == 'paragraph' and in_facts:
            fact_items.append(text)
            continue
        if kind == 'paragraph':
            special = ''
            if para_index == 0:
                special = 'lead'
            elif text.startswith('field_0189'):
                special = 'impact'
            elif text.startswith('field_0011，field_0190'):
                special = 'closing'
            elif text.startswith('field_0191'):
                special = 'thanks'
            output.append(paragraph(text, special))
            para_index += 1
            for prefix, insertion in INSERTIONS.items():
                if text.startswith(prefix):
                    output.append(insertion)
                    break
    if in_facts:
        output.append(fact_table(fact_items))
    output.extend([f'<p style="margin:30px 0 0;color:{MUTED};font-size:12px;line-height:1.8;text-align:center;letter-spacing:.08em;">— END · field_0010，field_0011 —</p>', '</section>', '</td></tr></tbody></table>'])
    FRAGMENT.write_text('\n'.join(output) + '\n', encoding='utf-8')
    print(FRAGMENT)
if __name__ == '__main__':
    main()
