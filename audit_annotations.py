#!/usr/bin/env python3
import json, csv, argparse
from pathlib import Path
from collections import Counter

BASE=Path(__file__).resolve().parent
BOOK=json.loads((BASE/'annotation_taxonomy.json').read_text(encoding='utf8'))['levels']
ALLOWED={k:{v['tag'] for v in seq}|{'Unspecified'} for k,seq in BOOK.items()}
LEVELS=['ideological','syntactic','functional','discourse']

def audit(files,outdir):
 out=Path(outdir);out.mkdir(parents=True,exist_ok=True)
 freq={l:Counter() for l in LEVELS}
 places=[]; issues=[]; n=0
 for f in files:
  records=json.loads(Path(f).read_text(encoding='utf-8-sig'))
  if not isinstance(records,list):raise ValueError(f'Expected JSON list: {f}')
  for i,r in enumerate(records,1):
   n+=1; txt=r.get('paragraph','')
   for lv in LEVELS:
    e=r.get(lv+'_tags_en',[])
    a=r.get(lv+'_tags_ar',[])
    if not isinstance(e,list):issues.append([f,i,lv,'not_list',str(e)]) ; continue
    if not isinstance(a,list):a=[]
    if len(e)!=len(a):issues.append([f,i,lv,'misaligned_bilingual_pairs',f'{len(e)} != {len(a)}'])
    for j,t in enumerate(e):
     freq[lv][t]+=1
     places.append([Path(f).name,i,lv,t,a[j] if j<len(a) else '',txt])
     if t not in ALLOWED[lv]:issues.append([f,i,lv,'out_of_taxonomy',t])
 total=sum(sum(c.values()) for c in freq.values())
 totals=[];counts=[]
 for lv in LEVELS:
  level_total=sum(freq[lv].values())
  totals.append([lv,level_total,freq[lv]['Unspecified'],round(level_total/total*100,2) if total else 0])
  for t,c in freq[lv].most_common():counts.append([lv,t,c,round(100*c/level_total,2) if level_total else 0,round(100*c/total,2) if total else 0])
 def write(name,header,rows):
  with open(out/name,'w',newline='',encoding='utf-8-sig') as f:
   w=csv.writer(f);w.writerow(header);w.writerows(rows)
 write('levels.csv',['level','n_assignments','n_unspecified','percent_all'],totals)
 write('tags.csv',['level','tag','count','percent_level','percent_all'],counts)
 write('locations_PRIVATE.csv',['source','paragraph_index','level','tag_en','tag_ar','paragraph'],places)
 write('schema_issues.csv',['source','paragraph_index','level','issue','value'],issues)
 print(json.dumps({'paragraphs':n,'tag_assignments':total,'levels':totals,'out_of_schema':sum(x[3]=='out_of_taxonomy' for x in issues)},ensure_ascii=False,indent=2))

if __name__=='__main__':
 ap=argparse.ArgumentParser();ap.add_argument('--files',required=True,nargs='+');ap.add_argument('--out',default='outputs/audit');a=ap.parse_args();audit(a.files,a.out)
