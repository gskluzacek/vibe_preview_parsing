from common import *
from collections import Counter
tl=Counter();lt=Counter();ex=[];ib=Counter()
for y,m,f in files():
    L=open(D+f,'rb').read().decode('utf-8','replace').split('\r\n')
    # trailing: after final split '' due to final CRLF
    assert L[-1]==''
    L=L[:-1]
    idx=[i for i,l in enumerate(L) if l.strip()]
    last=idx[-1]; nb=len(L)-1-last
    t='item' if L[last].count('\t')>=2 else 'PAGE' if L[last].startswith('PAGE') else 'other'
    # last item index
    li=max(i for i,l in enumerate(L) if l.count('\t')>=2)
    after=[(i+1,L[i]) for i in range(li+1,len(L)) if L[i].strip()]
    tl[nb]+=1; lt[t]+=1
    if after: ex.append((f,after[:3],len(after)))
    # blank lines in the middle: runs
    runs=0;cur=0
    for l in L[:last]:
        if l.strip()=='': cur+=1
        else:
            if cur: ib[cur]+=1
            cur=0
print('trailing blank lines dist',sorted(tl.items()));print('last nonblank type',lt)
print('files w/ nonblank after last item:',len(ex));
for e in ex[:80]: print(e)
print('interior blank-run lengths',sorted(ib.items()))
