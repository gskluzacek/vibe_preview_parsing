exec(open('/private/tmp/claude-501/-Volumes-U34-Bolt-Personal-development-github-vibe-preview-parsing/961fccd7-e904-460f-abf8-159486acec47/scratchpad/lines/common.py').read())
from collections import Counter,defaultdict
byn=defaultdict(Counter)
for y,m,f in files():
    t=open(D+f,'rb').read().decode('utf-8',errors='replace')
    for i,l in enumerate(t.split('\r\n'),1):
        n=l.count('\t')
        byn[n][f]+=1
        if n in (1,2,3,4) or (n==5 and f[3:]!='09.txt' and f not in('MAR09.txt','FEB09.txt','JAN09.txt')): print(f,i,n,repr(l[:200]))
for n in byn: print(n,sum(byn[n].values()),len(byn[n]),sorted(byn[n].items(),key=lambda x:-x[1])[:12] if n!=6 and n!=0 else '')
