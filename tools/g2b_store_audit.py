#!/usr/bin/env python3
import json,sys
from pathlib import Path
p=Path(sys.argv[1]); print(json.dumps({'status':'G2B_PREPARATION_ONLY','objects':len(list((p/'objects').rglob('*.twkv'))),'manifests':len(list((p/'manifests').glob('*.json'))),'load_operations':0},indent=2))
