from common import *
from collections import Counter,defaultdict
C=Counter();ex=defaultdict(list);ndist=Counter();filesby=defaultdict(set)
for y,m,f in files():
    L=open(D+f,'rb').read().decode('utf-8','replace').split('\r\n')
    for i,l in enumerate(L,1):
        s=l.rstrip('\t')
        if l.strip()=='' or l.count('\t')>=2 or re.fullmatch(r'PAGE (M-)?\d+',s): continue
        if re.match(r'\(NOTE',s,re.I): k='NOTE'
        elif re.match(r'PREVIEWS (\w+ (VOL\. |V)\d+ #\d+|ORDER FORM|\w+ \d{4})$',s) or re.match(r'ISSUE #\d+ \(VOL',s): k='ident'
        elif s.startswith('('): k='paren-other'
        elif re.search(r'[a-z]',s): k='has-lowercase'
        elif re.search(r'\d',s) : k='upper-with-digits'
        elif len(s)>60: k='long'
        else: k='heading-like'
        C[k]+=1; ndist[(k,s)]+=1; filesby[k].add(f)
        if len(ex[k])<3: ex[k].append((f,i,l))
print(C)
for k,v in ex.items(): print(k,len(filesby[k]),'files',v)
for k in ['NOTE','paren-other','has-lowercase','upper-with-digits','long']:
    print('---',k,len({s for (kk,s) in ndist if kk==k}),'distinct');
    print([ (s[:110],n) for (kk,s),n in ndist.most_common() if kk==k][:12])
hd=Counter();
for (k,s),n in ndist.items():
    if k=='heading-like': hd[s]+=n
print(len(hd),'distinct headings, total',sum(hd.values()));print(hd.most_common(25))
