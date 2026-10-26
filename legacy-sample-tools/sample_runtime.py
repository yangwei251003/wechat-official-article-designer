"""Explicit synthetic-workspace boundary for historical local sample programs."""
from pathlib import Path
import argparse,json,sys
from PIL import ImageFont

class SampleRuntime:
    root=None
    def configure(self):
        if self.root is not None:return
        parser=argparse.ArgumentParser(description='Historical local example; real article and photographs excluded.')
        parser.add_argument('--synthetic-demo',action='store_true')
        parser.add_argument('--workspace',type=Path)
        args,rest=parser.parse_known_args()
        if not args.synthetic_demo or args.workspace is None:
            parser.exit(2,'SYNTHETIC_GUARD: use demo.py with a new workspace; historical programs require --synthetic-demo --workspace and a synthetic marker.\n')
        root=args.workspace.resolve();marker=root/'.wechat-synthetic-workspace.json'
        if not marker.is_file()or json.loads(marker.read_text(encoding='utf-8')).get('synthetic')is not True:
            parser.exit(2,'SYNTHETIC_GUARD: a synthetic=true workspace marker is required.\n')
        self.root=root;sys.argv=[sys.argv[0],*rest]
    def workspace(self):
        if self.root is None:raise RuntimeError('Sample runtime not configured')
        return self.root
    def project_root(self):return Path(__file__).resolve().parents[1]
    def input_path(self,name):return self.workspace()/'inputs'/name
    def photo_records(self):
        p=self.workspace()/'inputs/photos.json'
        return json.loads(p.read_text(encoding='utf-8'))if p.is_file()else[]
    def font(self,size):return ImageFont.load_default(size=int(size))

sample=SampleRuntime()
