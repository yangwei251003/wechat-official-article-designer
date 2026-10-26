"""Exercise preserved local helper functions with newly generated geometric inputs."""
from __future__ import annotations
from pathlib import Path
import argparse,ast,csv,hashlib,html,json,math,shutil,subprocess,sys
import cv2
import numpy as np
from PIL import Image,ImageDraw,ImageFont,ImageOps,ImageFilter
from sample_runtime import sample

HERE=Path(__file__).resolve().parent

def load_functions(filename,workspace):
    """Reuse the reviewed public function bodies without running historical top-level I/O."""
    tree=ast.parse((HERE/filename).read_text(encoding='utf-8'))
    namespace={'__name__':'preserved_local_functions','Path':Path,'sample':sample,'Image':Image,'ImageDraw':ImageDraw,'ImageFont':ImageFont,'ImageOps':ImageOps,'ImageFilter':ImageFilter,'np':np,'cv2':cv2,'math':math,'hashlib':hashlib,'html':html,'json':json,'ASSETS':workspace/'outputs/article/assets'}
    def constant(node):
        if isinstance(node,ast.Name)and node.id in namespace:return namespace[node.id]
        if isinstance(node,ast.List):return[constant(n)for n in node.elts]
        if isinstance(node,ast.Tuple):return tuple(constant(n)for n in node.elts)
        if isinstance(node,ast.Dict):return{constant(k):constant(v)for k,v in zip(node.keys,node.values)}
        return ast.literal_eval(node)
    for node in tree.body:
        if isinstance(node,ast.Assign)and len(node.targets)==1 and isinstance(node.targets[0],ast.Name):
            try:namespace[node.targets[0].id]=constant(node.value)
            except(ValueError,TypeError):pass
        elif isinstance(node,ast.AnnAssign)and isinstance(node.target,ast.Name):
            try:namespace[node.target.id]=constant(node.value)
            except(ValueError,TypeError):pass
    definitions=[n for n in tree.body if isinstance(n,ast.FunctionDef)]
    module=ast.Module(body=[ast.ImportFrom(module='__future__',names=[ast.alias(name='annotations')],level=0),*definitions],type_ignores=[])
    ast.fix_missing_locations(module)
    exec(compile(module,filename,'exec'),namespace)
    return namespace

def main():
    parser=argparse.ArgumentParser(description='Synthetic geometric material only; no original photos/articles/course schedule.')
    parser.add_argument('--workspace',required=True,type=Path)
    args=parser.parse_args();w=args.workspace.resolve()
    if w.exists()and any(w.iterdir()):parser.error('Use a new empty workspace.')
    w.mkdir(parents=True,exist_ok=True)
    (w/'.wechat-synthetic-workspace.json').write_text(json.dumps({'synthetic':True}),encoding='utf-8')
    sample.root=w
    inputs=w/'inputs/photos';outputs=w/'outputs';assets=outputs/'article/assets';assets.mkdir(parents=True)
    for group in range(1,5):
        folder=inputs/f'group-{group}';folder.mkdir(parents=True)
        for index in range(1,4):
            path=folder/f'sample-{index:02d}.jpg'
            if group==4:
                shutil.copyfile(inputs/'group-1'/path.name,path);continue
            image=Image.new('RGB',(640,400),(235,241,230));draw=ImageDraw.Draw(image)
            draw.rounded_rectangle((35,30,605,370),radius=30,fill=(20+group*25,80+index*30,95))
            draw.ellipse((50+index*45,65,340+index*45,340),fill=(240,178+group*8,80))
            draw.rectangle((300,120,580,320),outline=(255,255,255),width=11)
            draw.text((50,40),f'SYNTHETIC GEOMETRY {group}-{index}',font=sample.font(24),fill='white')
            image.save(path,quality=93)
    source_hashes={p.relative_to(w).as_posix():hashlib.sha256(p.read_bytes()).hexdigest()for p in inputs.rglob('*.jpg')}
    result=subprocess.run([sys.executable,str(HERE/'build_photo_contact_sheets.py'),'--synthetic-demo','--workspace',str(w)],cwd=w,capture_output=True,text=True,encoding='utf-8')
    if result.returncode:raise RuntimeError('Historical contact-sheet program failed: '+result.stderr[-2400:])
    sheets=sorted((outputs/'contact-sheets').glob('*.jpg'));assert len(sheets)==4
    csv_files=sorted((outputs/'contact-sheets').glob('*.csv'));assert len(csv_files)==2
    csv_rows=[]
    for p in csv_files:
        text=p.read_text(encoding='utf-8-sig');assert str(w)not in text and 'C:\\Users'not in text
        with p.open(encoding='utf-8-sig',newline='')as handle:csv_rows.append(list(csv.DictReader(handle)))
    assert sorted(len(rows)for rows in csv_rows)==[12,15]
    candidates=next(rows for rows in csv_rows if rows and 'phash_distance'in rows[0])
    assert len({r['final_index']for r in candidates})==3
    for index in {r['final_index']for r in candidates}:
        assert any(r['final_index']==index and r['phash_distance']=='0'and r['dhash_distance']=='0'for r in candidates)
    contact=load_functions('build_photo_contact_sheets.py',w)
    original=Image.open(inputs/'group-1/sample-01.jpg').convert('RGB')
    duplicate=Image.open(inputs/'group-4/sample-01.jpg').convert('RGB')
    assert contact['phash'](original)==contact['phash'](duplicate)
    assert contact['dhash'](original)==contact['dhash'](duplicate)
    assert contact['blur_score'](original)>contact['blur_score'](original.filter(ImageFilter.GaussianBlur(12)))
    assert contact['exif_datetime'](original)==''
    photo=load_functions('build_wechat_assets.py',w)
    crop=photo['crop_to_ratio'](original,1.0,(0.5,0.5));assert crop.size==(400,400)
    crop.save(assets/'square-crop.png')
    photo['process_photo'](inputs/'group-1/sample-01.jpg',assets/'processed.jpg',(600,400))
    with Image.open(assets/'processed.jpg')as processed:assert processed.size==(600,400)and not processed.getexif()
    frame=photo['make_bloom_frame'](3);frame.save(assets/'synthetic-bloom.png')
    shutil.copyfile(sheets[0],assets/'contact-sheet.jpg')
    fragments=load_functions('build_wechat_fragment.py',w)
    body=fragments['paragraph']('SYNTHETIC DEMONSTRATION. All images are newly generated geometric material. No person, school, class, course venue or original article is included.','lead')
    body+=fragments['h2']('Reusable geometry and local image processing',0)
    body+=fragments['image_full']('processed.jpg','Synthetic geometric image','Actual output from the preserved process_photo function.')
    body+=fragments['image_pair'](('square-crop.png','Square crop','Center crop'),('synthetic-bloom.png','Generated petal diagram','Procedural pixels only'),'Actual preserved helper outputs; no real photographs.')
    body+=fragments['h3']('Synthetic material review',0)
    body+=fragments['fact_table'](['Inputs：12 new geometric JPEG images','Privacy：No original photographs or article data','Publishing：Local preview only'])
    body+=fragments['image_full']('contact-sheet.jpg','Synthetic contact sheet','Actual output from the complete historical contact-sheet program.')
    body+=fragments['paragraph']('This preview is local output. It does not demonstrate a WeChat draft submission or the original business workflow.','closing')
    assert fragments['esc']('<test & value>')=='&lt;test &amp; value&gt;'
    page='<!doctype html><html lang="en"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><title>Synthetic WeChat helper demonstration</title><style>body{margin:0;background:#f4f6f1;font-family:system-ui,sans-serif}main{max-width:720px;margin:auto;padding:clamp(16px,4vw,32px);overflow-wrap:anywhere}img{max-width:100%}table{table-layout:fixed}</style></head><body><main>'+body+'</main></body></html>'
    (outputs/'article/index.html').write_text(page,encoding='utf-8')
    finalize=load_functions('finalize_wechat_package.py',w)
    metadata=outputs/'synthetic-metadata.json';finalize['write_json'](metadata,{'synthetic':True,'private_inputs':False})
    assert finalize['read_json'](metadata)=={'synthetic':True,'private_inputs':False}
    for path,digest in source_hashes.items():assert hashlib.sha256((w/path).read_bytes()).hexdigest()==digest
    summary={'synthetic':True,'original_photos_articles_course_rows_read':False,'complete_contact_sheet_program_exit_code':0,'generated_input_images':12,'contact_sheets':len(sheets),'csv_record_counts':sorted(len(x)for x in csv_rows),'exact_duplicate_phash_dhash_equal':True,'blur_score_decreases_after_blur':True,'synthetic_input_exif_empty':True,'center_crop_dimensions':[400,400],'processed_dimensions':[600,400],'procedural_bloom_frame':list(frame.size),'html_escape_test':True,'actual_fragment_helper_functions':7,'json_helpers_round_trip':True,'input_files_unchanged':12,'WeChat_service_or_draft_submission_tested':False,'full_original_business_pipeline_tested':False}
    (w/'validation.json').write_text(json.dumps(summary,indent=2),encoding='utf-8')
    print(json.dumps(summary))

if __name__=='__main__':main()
