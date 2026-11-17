#!/usr/bin/env python3
# Reconstructed reproducible implementation. Not a copy of an archived historical script.
import os, json, argparse, hashlib, time
from datetime import datetime, timezone
from pathlib import Path
from docx import Document
from openai import OpenAI

BASE = Path(__file__).resolve().parent
TAXONOMY = json.loads((BASE/'annotation_taxonomy.json').read_text(encoding='utf-8'))['levels']
LEVELS = ('ideological','syntactic','functional','discourse')
ALLOWED = {level:{item['tag'] for item in items}|{'Unspecified'} for level,items in TAXONOMY.items()}
AR = {lv:{r['tag']:r.get('label_ar') or r.get('description_ar','') for r in items} for lv,items in TAXONOMY.items()}

# Human-readable labels of observed common tags; default to the authored Arabic descriptions in the codebook.
OVERRIDES = {'Positive_Self':'تمجيد الذات','Negative_Other':'تشويه الآخر','Victimization':'تصوير الذات/الآخر كضحية',
'Crisis_Framing':'تأطير الأزمة','Passive_Voice':'المبني للمجهول','Nominalization':'الاسمية',
'Act_Justification':'تبرير','Act_Call_to_Action':'دعوة إلى الفعل','Argument':'عرض الحجة','Assertive':'التأكيد'}

def parse_args():
 ap=argparse.ArgumentParser()
 ap.add_argument('--input',nargs='+',required=True,help='DOCX files')
 ap.add_argument('--model',default='gpt-4o',help='Explicit API model alias or fixed snapshot ID')
 ap.add_argument('--output',default='outputs/labeled.json')
 ap.add_argument('--temperature',type=float,default=0.2)
 ap.add_argument('--max-tokens',type=int,default=4000)
 ap.add_argument('--retry',type=int,default=3)
 return ap.parse_args()

def check_tags(obj):
 if not isinstance(obj,dict):raise ValueError('Output is not a JSON object')
 for level in LEVELS:
  key=f'{level}_tags_en';tags=obj.get(key)
  if not isinstance(tags,list) or not tags:raise ValueError(f'missing/non-list {key}')
  if not all(isinstance(t,str) and t in ALLOWED[level] for t in tags):
   raise ValueError(f'out-of-taxonomy tags: {key}: {tags}')
  if len(tags)!=len(set(tags)):raise ValueError(f'repeated tags in {key}')
  if 'Unspecified' in tags and len(tags)>1:raise ValueError(f'Unspecified mixed with labels in {key}')

def main():
 args=parse_args()
 if not os.environ.get('OPENAI_API_KEY'):raise SystemExit('Please set OPENAI_API_KEY in environment')
 client=OpenAI()
 out=Path(args.output);out.parent.mkdir(parents=True,exist_ok=True)
 saved=[]
 if out.exists():
  saved=json.loads(out.read_text(encoding='utf-8'))
  if not isinstance(saved,list):raise ValueError('Existing output must be an array')
 done={r['item_uid'] for r in saved if isinstance(r,dict) and 'item_uid' in r}
 system=(BASE/'prompt_ar.md').read_text(encoding='utf-8')+'\nAllowed tags by level:\n'+json.dumps({k:sorted(v) for k,v in ALLOWED.items()},ensure_ascii=False)
 for fn in args.input:
  p=Path(fn)
  if p.suffix.lower()!='.docx':raise ValueError(f'Only .docx is supported: {p}')
  doc=Document(p)
  paragraphs=[x.text.strip() for x in doc.paragraphs if x.text.strip()]
  for pos,text in enumerate(paragraphs,1):
   uid=hashlib.sha256((p.name+'\n'+str(pos)+'\n'+text).encode('utf8')).hexdigest()
   if uid in done:continue
   last_error=None
   for trial in range(args.retry):
    try:
     response=client.chat.completions.create(
      model=args.model,temperature=args.temperature,max_tokens=args.max_tokens,
      messages=[{'role':'system','content':system},
                {'role':'user','content':'حلل الفقرة التالية بإسناد الوسوم للمستويات الأربعة، وأعد كائن JSON فقط:\n'+text}],
      response_format={'type':'json_object'})
     completion=response.choices[0]
     if completion.finish_reason=='length':raise ValueError('Truncated output')
     decoded=json.loads(completion.message.content)
     check_tags(decoded)
     record={'source_file':p.name,'paragraph_index':pos,'item_uid':uid,'paragraph':text,
             'model_requested':args.model,'model_returned':response.model,
             'response_id':response.id,'run_at_utc':datetime.now(timezone.utc).isoformat(),
             'temperature':args.temperature,'max_tokens':args.max_tokens}
     for level in LEVELS:
      tags=decoded[level+'_tags_en']
      record[level+'_tags_en']=tags
      record[level+'_tags_ar']=['غير محدد' if t=='Unspecified' else OVERRIDES.get(t,AR[level].get(t,t)) for t in tags]
     saved.append(record)
     tmp=out.with_suffix('.tmp')
     tmp.write_text(json.dumps(saved,ensure_ascii=False,indent=2),encoding='utf-8')
     tmp.replace(out)
     done.add(uid)
     print(f'{p.name}: {pos}/{len(paragraphs)} accepted',flush=True)
     break
    except Exception as e:
     last_error=e
     print(f'{p.name}: paragraph {pos} attempt {trial+1} error: {e}',flush=True)
     time.sleep(min(2**trial,8))
   else:
    raise RuntimeError(f'Failed paragraph {pos} in {p.name}; earlier paragraphs preserved; retry after fixing: {last_error}')
 print(f'Completed {len(saved)} paragraphs: {out}')

if __name__=='__main__':main()
