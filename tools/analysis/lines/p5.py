exec(open('/private/tmp/claude-501/-Volumes-U34-Bolt-Personal-development-github-vibe-preview-parsing/961fccd7-e904-460f-abf8-159486acec47/scratchpad/lines/common.py').read())
from collections import Counter,defaultdict
FULL=['JANUARY','FEBRUARY','MARCH','APRIL','MAY','JUNE','JULY','AUGUST','SEPTEMBER','OCTOBER','NOVEMBER','DECEMBER']
def mon(s):
    for i,n in enumerate(FULL):
        if s==n or s==n[:3]: return i+1
res=[];vc=defaultdict(Counter)
for y,m,f in files():
    L=[l.rstrip('\t') for l in open(D+f,'rb').read().decode('utf-8','replace').split('\r\n')]
    nb=[(i+1,l) for i,l in enumerate(L) if l.strip()][:3]
    t=nb[0][1] if nb else ''
    t2=nb[1][1] if len(nb)>1 else ''
    var='none';mo=vo=io=yo=None;lines=[]
    if re.fullmatch(r'PREVIEWS (\w+) VOL\. (\d+) #(\d+)',t):
        a=re.fullmatch(r'PREVIEWS (\w+) VOL\. (\d+) #(\d+)',t); var='A:basic VOL.'; mo,vo,io=mon(a[1]),int(a[2]),int(a[3]);fmt='full' if len(a[1])>3 else 'abbr'; var+=' '+fmt
    elif re.fullmatch(r'PREVIEWS (\w+) V(\d+) #(\d+)',t):
        a=re.fullmatch(r'PREVIEWS (\w+) V(\d+) #(\d+)',t); var='B:Vnn'; mo,vo,io=mon(a[1]),int(a[2]),int(a[3]);var+=' '+('full' if len(a[1])>3 else 'abbr')
    elif t=='PREVIEWS ORDER FORM':
        a=re.fullmatch(r'(\w+) V(\d+) #(\d+)',t2); var='C:ORDER FORM terse'; mo,vo,io=mon(a[1]),int(a[2]),int(a[3])
    elif re.fullmatch(r'PREVIEWS (\w+) (\d{4})',t):
        a=re.fullmatch(r'PREVIEWS (\w+) (\d{4})',t); b=re.fullmatch(r'ISSUE #(\d+) \(VOL\. (\d+) #(\d+)\)',t2); var='D:two-line'; mo=mon(a[1]);yo=int(a[2]);ino=int(b[1]);vo=int(b[2]);io=int(b[3]);
        vc['issue'][(f,ino,(vo-1)*12+m+27)]+=1
    else: var='?? '+repr(t)
    res.append((f,y,m,var,mo,vo,io,yo))
    print(f,var,'|',mo,vo,io,yo,'| line',nb[0][0] if nb else None)
print('=====')
bad=0
for f,y,m,var,mo,vo,io,yo in res:
    if mo is None: continue
    probs=[]
    if mo!=m: probs.append(f'month {mo}!={m}')
    if io!=m: probs.append(f'issueInVol {io}!={m}')
    if vo!=y-1990: probs.append(f'vol {vo} vs y-1990={y-1990}')
    if yo is not None and yo!=y: probs.append(f'year {yo}!={y}')
    if probs: print(f,var,mo,vo,io,yo,probs)
print('vol by year:',{y:sorted({r[5] for r in res if r[1]==y and r[5]}) for y in range(2009,2021)})
print('D-variant issue formula:')
for k in vc['issue']:print(k)
