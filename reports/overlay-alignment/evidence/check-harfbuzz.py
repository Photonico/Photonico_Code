import argparse, json, subprocess, pathlib, shutil
from fontTools.ttLib import TTFont
from fontTools.pens.boundsPen import BoundsPen
parser=argparse.ArgumentParser(description='Verify the targeted geometric overlay alignment.')
parser.add_argument('before', type=pathlib.Path)
parser.add_argument('after', type=pathlib.Path)
parser.add_argument('--output', type=pathlib.Path, default=pathlib.Path('/tmp/photonico-overlay-results.json'))
args=parser.parse_args()
HB=shutil.which('hb-shape')
if not HB: raise SystemExit('hb-shape is required')
fonts={'before':args.before, 'after':args.after}
bases=['x','--','𝔼','◌']; marks=['\u0335','\u0336']
cases=[b+m for b in bases for m in marks]+[b+''.join(ms) for b in bases for ms in [marks,marks[::-1]]]
cases += ['x̵--̶𝔼̵◌̶','◌̶𝔼̵--̶x̵','x̶--̵𝔼̶◌̵','◌̵𝔼̶--̵x̶']
controls=['x -- 𝔼 ◌','x̂ x́ x̀ x̌ x̣ x̥','r̂ Λ̂ ϕ̂ œ̂','ḁ́ ḍ́ ẍ́','a==b a!=b <= >= -> => <-- --> <=>','<$> $> <$ $$ $','`` ``` ---- -- ---']
res={};errors=[]
for label,path in fonts.items():
 f=TTFont(path); gs=f.getGlyphSet(); bounds={}
 for g in f.getGlyphOrder():
  pen=BoundsPen(gs);gs[g].draw(pen);bounds[g]=pen.bounds
 def shape(texts,feat=None):
  args=[HB,str(path),'--shapers=ot','--output-format=json','--verify']
  if feat:args+=['--features='+feat]
  return [json.loads(line) for line in subprocess.check_output(args,input='\n'.join(texts).encode()).decode().splitlines()]
 def describe(s,row):
  cursor=0;items=[]
  for g in row:
   b=bounds[g['g']]
   ink=[b[0]+cursor+g['dx'],b[1]+g['dy'],b[2]+cursor+g['dx'],b[3]+g['dy']] if b else None
   items.append(dict(glyph=g['g'],ink=ink,centre=[(ink[0]+ink[2])/2,(ink[1]+ink[3])/2] if ink else None,dx=g['dx'],dy=g['dy'],advance=g['ax']))
   cursor+=g['ax']
  return dict(text=s,advance=cursor,glyphs=row,ink=items)
 res[label]={}
 for feat in ['default','calt=0']:
  samples=cases+controls
  rows=shape(samples,None if feat=='default' else feat)
  res[label][feat]=[describe(s,row) for s,row in zip(samples,rows)]
# Exact targeted single-run attachment expectations.
expected={'x':(-1200,-140,[600,480]),'--':(-1800,-20,[1200,600]),'𝔼':(-1205,30,[595,650]),'◌':(-1200,-20,[600,600])}
for feat in ['default','calt=0']:
 for i,(old,new) in enumerate(zip(res['before'][feat],res['after'][feat])):
  if old['advance']!=new['advance']:errors.append(['advance_changed',feat,new['text'],old['advance'],new['advance']])
  if i>=len(cases) and old['glyphs']!=new['glyphs']:errors.append(['control_changed',feat,new['text']])
 for rec in res['after'][feat][:8]:
  base=rec['text'][:-1]; last=rec['ink'][-1]; dx,dy,centre=expected[base]
  if feat=='calt=0' and base=='--':dx,dy,centre=-1200,-20,[1800,600]
  # Built uni0336 has an existing one-unit ink-centre shift from LSB/xMin rounding.
  if last['glyph']=='uni0336': centre=[centre[0]+1,centre[1]]
  if (last['dx'],last['dy'],last['centre'])!=(dx,dy,centre):errors.append(['target_mismatch',feat,rec['text'],last,[dx,dy,centre]])
  if rec['advance']!=1200*len(base):errors.append(['target_width',feat,rec])
# All mark order variants retain width; each zero-width overlay obeys the same base anchor.
for feat in ['default','calt=0']:
 for rec in res['after'][feat][8:16]:
  ink=[g for g in rec['ink'] if g['glyph'] in ['uni0335','uni0336']]
  if len(ink)!=2 or (ink[0]['dx'],ink[0]['dy'])!=(ink[1]['dx'],ink[1]['dy']):errors.append(['order_variant',feat,rec])
args.output.write_text(json.dumps({'results':res,'errors':errors},ensure_ascii=False,indent=2)+'\n')
print('target_cases',len(cases),'controls',len(controls),'feature_settings',2,'fonts',2,'errors',len(errors))
for x in errors:print(x)
for rec in res['after']['default'][:8]:print(rec['text'],rec['advance'],rec['ink'][-1]['dx'],rec['ink'][-1]['dy'],rec['ink'][-1]['centre'])

if errors: raise SystemExit(1)
