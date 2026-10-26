# Preserved local sample workflow; private inputs excluded. See README.md.
from __future__ import annotations
import sys as _sample_sys
from pathlib import Path as _SamplePath
_sample_sys.path.insert(0,str(_SamplePath(__file__).resolve().parent))
from sample_runtime import sample
sample.configure()
import html
import json
from datetime import datetime
from pathlib import Path
ROOT = sample.input_path('input_0042')
PACKAGE = ROOT / 'wechat-output' / 'field_0010_field_0011_field_0043'
SKILL = ROOT / 'wechat-official-article-designer'
NOW = datetime.now().astimezone().isoformat(timespec='seconds')

def read_json(path: Path) -> dict:
    return json.loads(path.read_text(encoding='utf-8'))

def write_json(path: Path, data: dict) -> None:
    path.write_text(json.dumps(data, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')
package = read_json(PACKAGE / 'article-package.json')
manifest = read_json(PACKAGE / 'asset-manifest-generated.json')
photo_map = {item['id']: item for item in manifest['photos']}
manual_review_ids: list[str] = []
for asset in package['assets']:
    asset['wechat_ready'] = True
    asset_id = asset['id']
    if asset_id in photo_map:
        asset['portrait_review_required'] = True
        asset['source_reference'] = photo_map[asset_id]['source']
        asset['alt'] = photo_map[asset_id]['alt']
        manual_review_ids.append(asset_id)
    if asset_id == 'cover-main':
        asset['portrait_review_required'] = True
        manual_review_ids.append(asset_id)
    if asset_id == 'five-petal-bloom':
        asset['license'] = 'Original asset'
        asset['fallback'] = 'asset_0040.png'
        asset['semantic_motion'] = 'field_0183，field_0192'
    if asset_id == 'five-petal-bloom-poster':
        asset['license'] = 'Original asset'
    if asset_id == 'brand-strip':
        asset['logo_usage_review_required'] = True
        manual_review_ids.append(asset_id)
design_read = {'article_type': 'field_0193', 'audience': 'field_0194、field_0195、field_0196', 'action': 'field_0197、field_0198', 'emotion': 'field_0199、field_0200、field_0201', 'visual_family': 'field_0202 × field_0203', 'wechat_constraint': 'field_0204、field_0205；field_0206CSS、tablefield_0207bgcolor，field_0208SVG/Flex/Grid/field_0209/field_0210'}
controls = {'design_variance': 8, 'motion_intensity': 4, 'visual_density': 6}
components = ['field_0211', 'field_0212', 'field_0213', 'field_0214', 'field_0215', 'field_0216', 'field_0217', 'field_0218', 'field_0219']
package['design'] = {'track': 'field_0220', 'concept': 'field_0221，field_0222', 'mode': 'high-design', 'design_read': design_read, 'controls': controls, 'visual_concept': 'field_0223，field_0224，field_0225。', 'rhythm_families': ['editorial-longform', 'photo-journal', 'closing-manifesto'], 'palette': ['#183B56', '#2EAD72', '#D94135'], 'components': components}
package['publishing']['status'] = 'not_started'
package['publishing']['cover_asset_id'] = 'cover-main'
package['publishing']['wechat_client_final_preview_required'] = True
package['publishing']['portrait_authorization_required'] = True
write_json(PACKAGE / 'article-package.json', package)
article = read_json(PACKAGE / 'article.json')
article['goals'] = {'objective': 'field_0226、field_0227、field_0228', 'audience': 'field_0194、field_0195、field_0196', 'call_to_action': 'field_0229，field_0230', 'fact_risk': 'medium'}
article['content']['title_candidates'] = ['field_0010，field_0011｜“field_0012”field_0231', 'field_0076，field_0232｜“field_0012”field_0233', 'field_0234｜field_0016、13field_0235']
source_refs = ['chatgpt-conversation://6a705fca-ea78-83ee-9cfd-7d70c3d8373b', 'field_02365field_0237“field_0238”field_0239（field_0240）.xlsx#field_02415field_0237!A1:F17', 'Day1/Day3/Day4/Day5field_0242PPTfield_0243/field_0244/field_0245/field_0246PPT', 'workspace_summary/photo_audit.md']
for section in article['content']['sections']:
    section['source'] = {'kind': 'user-authorized-edit', 'source_refs': source_refs}
    for node in section['nodes']:
        node['provenance'] = {'kind': 'user-authorized-edit', 'source_refs': source_refs}
article['design'] = {'direction': 'field_0202；field_0247，field_0221、field_0248', 'mode': 'high-design', 'design_read': design_read, 'controls': controls, 'visual_concept': 'field_0223，field_0224，field_0225。', 'rhythm_families': ['editorial-longform', 'photo-journal', 'closing-manifesto'], 'quality_gates': {'source_integrity': 'all source blocks preserved in order', 'photo_truthfulness': 'alt/captions describe only visible content; no proxy images for unphotographed classes', 'wechat_compatibility': 'inline CSS and safe tags only; table/bgcolor fallbacks', 'minor_portrait_review': 'required before publication'}, 'tokens': {'palette': ['#183B56', '#2EAD72', '#D94135'], 'font_stack': '-apple-system, BlinkMacSystemFont, Segoe UI, PingFang SC, Microsoft YaHei, Arial, sans-serif', 'body_size': '15px', 'line_height': 1.95, 'spacing': '8/12/18/24/38/48px', 'radius': '14/18/20px'}, 'components': components}
article['assets'] = package['assets']
article['locks'] = {'document': False, 'title': False, 'node_ids': [], 'data_paths': ['metadata.title', 'metadata.summary', 'goals.objective'], 'asset_ids': []}
article['history'] = [item for item in article['history'] if item.get('version') != '1.0.0']
article['history'].append({'version': '1.0.0', 'timestamp': NOW, 'actor': 'Codex', 'changes': ['field_0249、field_0250、PPTfield_0207104field_0251', 'field_0252', 'field_025325field_0254']})
article['wechat'] = {'compatibility_level': 'strict', 'cover_asset_id': 'cover-main', 'fallbacks': [{'asset_id': 'five-petal-bloom', 'fallback_asset_id': 'five-petal-bloom-poster', 'reason': 'field_0255GIFfield_0256，field_0257PNG'}]}
article['copyright'] = {'status': 'review', 'manual_review_asset_ids': sorted(set(manual_review_ids))}
write_json(PACKAGE / 'article.json', article)
brief = {'schema_version': '2.0', 'title': article['metadata']['title'], 'track': 'field_0220', 'concept': 'field_0221，field_0222', 'design_read': design_read, 'controls': controls, 'palette': ['#183B56', '#2EAD72', '#D94135'], 'visual_concept': package['design']['visual_concept'], 'rhythm_families': package['design']['rhythm_families'], 'components': components, 'asset_direction': 'field_0258；field_0259、field_0260/field_0261；field_0262，field_0263。', 'wechat_rules': 'field_0264CSS；field_0265SVG、CSSfield_0266、Flex、Grid、field_0209、field_0267。', 'review_notes': ['field_0268、field_0269、AIfield_0270，field_0271，field_0272', 'Day3/Day4field_0273、field_0274，field_0275', 'field_0276']}
write_json(PACKAGE / 'design-brief.json', brief)
(PACKAGE / 'design-brief.md').write_text('# field_0277\n\n- field_0278：field_0193\n- field_0279：field_0221，field_0222\n- field_0280：field_0202 × field_0203\n- field_0281：field_0282 #183B56 / field_0283 #2EAD72 / field_0284 #D94135\n- field_0285：field_0286 8 / field_0287 4 / field_0288 6\n- field_0289：editorial-longform / photo-journal / closing-manifesto\n- field_0290：25field_0291 + field_0259 + field_0292GIFfield_0293PNGfield_0294 + field_0295。\n- field_0296：Day3/Day4field_0273、field_0297；field_0298。\n- field_0299：field_0300；field_0301。\n', encoding='utf-8')
matching_lines = ['# field_0302', '', '## field_0303', '', '1. field_0304 `preview.html`。', '2. field_0305“field_0306”。', '3. field_0307，field_0308。', '4. field_0309、field_0310；field_0311 `assets/cover-main.jpg`。', '5. field_0312GIFfield_0313，field_0314 `assets/five-petal-bloom.gif`；field_0315 `assets/five-petal-bloom-poster.png`。', '', '## field_0316', '', f'- field_0309：{article['metadata']['title']}', f'- field_0317：{article['metadata']['author']}', f'- field_0318：{article['metadata']['summary']}', '- field_0319：`assets/cover-main.jpg`（900×383）', '', '## field_0320', '', '- field_0321。', '- field_0322，field_0323‘field_0324’field_0325。', '- field_0326。', '- field_0327CDNfield_0328；field_0329。', '- field_0268、field_0330AIfield_0331。', '- field_0332《field_03337 field_0334.docx》field_0335。', '', '## field_0336', '']
for item in manifest['photos']:
    matching_lines.append(f'- `{item['local_path']}`｜{item['section']}｜{item['alt']}')
(PACKAGE / 'field_0302.md').write_text('\n'.join(matching_lines) + '\n', encoding='utf-8')
fragment = (PACKAGE / 'article-fragment.html').read_text(encoding='utf-8')
shell = (SKILL / 'assets' / 'preview-shell.html').read_text(encoding='utf-8')
warning = 'field_0337；field_0338。field_0339。'
preview = shell.replace('{{TITLE}}', html.escape(article['metadata']['title'])).replace('{{STYLE_SUMMARY}}', html.escape('field_0221，field_0222 · field_0220 · field_0340')).replace('{{ASSET_WARNING}}', html.escape(warning)).replace('{{ARTICLE_HTML}}', fragment)
(PACKAGE / 'preview.html').write_text(preview, encoding='utf-8')
print(json.dumps({'package': str(PACKAGE), 'assets': len(package['assets']), 'manual_review': len(set(manual_review_ids))}, ensure_ascii=False))
