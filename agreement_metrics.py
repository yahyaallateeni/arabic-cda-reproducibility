#!/usr/bin/env python3
"""Nominal multi-label agreement with transparent denominators. Input is LONG CSV with labels as JSON list.
Cohen kappa and Krippendorff alpha are computed per tag (binary inclusion), never confused with exact set match.
"""
import csv,json,argparse,itertools,math
from pathlib import Path
from collections import defaultdict
from sklearn.metrics import cohen_kappa_score
import krippendorff

def main(path,outdir):
 rows=list(csv.DictReader(open(path,encoding='utf-8-sig',newline='')))
 required={'item_id','level','reviewer','labels'}
 if not rows or not required.issubset(rows[0]):raise ValueError('Required CSV columns: item_id,level,reviewer,labels')
 by=defaultdict(dict)
 for r in rows:
  key=(r['level'],r['item_id']); person=r['reviewer'];tags=json.loads(r['labels'])
  if not isinstance(tags,list):raise ValueError('labels must be a JSON list')
  if person in by[key]:raise ValueError(f'Duplicate annotation for {key} {person}')
  by[key][person]=frozenset(tags)
 levels=sorted({k[0] for k in by});persons=sorted({p for pmap in by.values() for p in pmap})
 results=[]
 for lv in levels:
  items={item:annotations for (level,item),annotations in by.items() if level==lv}
  tags=sorted(set().union(*(set(labels) for v in items.values() for labels in v.values())))
  for a,b in itertools.combinations(persons,2):
   shared=[v for v in items.values() if a in v and b in v]
   if not shared:continue
   exact=sum(v[a]==v[b] for v in shared)/len(shared)
   results.append([lv,f'{a} vs {b}',len(shared),'set_exact_match',round(exact,6),''])
   for tag in tags:
    va=[int(tag in v[a]) for v in shared];vb=[int(tag in v[b]) for v in shared]
    k=cohen_kappa_score(va,vb) if len(set(va)|set(vb))>1 else float('nan')
    results.append([lv,f'{a} vs {b}',len(shared),f'kappa: {tag}',round(k,6) if not math.isnan(k) else '', 'binary-per-label'])
  humans=[p for p in persons if p!='AUTO']
  for tag in tags:
   rel=[]
   for p in humans:
    rel.append([float(int(tag in v[p])) if p in v else float('nan') for v in items.values()])
   if len(humans)<2:continue
   try:
    alpha=krippendorff.alpha(reliability_data=rel,level_of_measurement='nominal')
   except (ValueError,ZeroDivisionError):alpha=float('nan')
   results.append([lv,'ALL HUMAN',len(items),f'krippendorff_alpha: {tag}',round(float(alpha),6) if not math.isnan(alpha) else '', 'binary-per-label'])
 out=Path(outdir);out.mkdir(parents=True,exist_ok=True)
 with open(out/'agreement.csv','w',encoding='utf-8-sig',newline='') as f:
  w=csv.writer(f);w.writerow(['level','comparison','shared_items','metric','value','note']);w.writerows(results)
 print('Results:',out/'agreement.csv','comparisons:',len(results))

if __name__=='__main__':
 ap=argparse.ArgumentParser();ap.add_argument('--input',required=True);ap.add_argument('--out',default='outputs/agreement');a=ap.parse_args();main(a.input,a.out)
