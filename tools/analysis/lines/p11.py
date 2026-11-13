exec(open('/private/tmp/claude-501/-Volumes-U34-Bolt-Personal-development-github-vibe-preview-parsing/961fccd7-e904-460f-abf8-159486acec47/scratchpad/lines/common.py').read())
from collections import Counter
numonly=Counter();tr=[];allnum=[]
for y,m,f in files():
    L=open(D+f,'rb').read().decode('utf-8','replace').split('\r\n')[:-1]
    for i,l in enumerate(L,1):
        if re.fullmatch(r'\d+\t*',l): numonly[f]+=1; allnum.append((f,i,l))
    idx=[i for i,l in enumerate(L) if l.strip()]
    nb=len(L)-1-idx[-1]
    if nb!=6: tr.append((f,nb,L[idx[-1]]))
    last=L[idx[-1]]
    if not re.fullmatch(r'\d+',last): print('last not numeric',f,repr(last))
print('files with number-only lines',len(numonly),'total',sum(numonly.values()),'files with >1:',[(f,n) for f,n in numonly.items() if n>1])
print(tr)
print([ (f,i,l) for f,i,l in allnum if not f.startswith('XXX')][:0])
# context for tail of 3 files
for f in ['JAN09.txt','MAR20.txt','DEC15.txt']:
    L=open(D+f,'rb').read().decode('utf-8','replace').split('\r\n')
    print(f,[l[:60] for l in L[-12:]])
