from common import *
from collections import Counter,defaultdict
sh=Counter();ex={};files_by=defaultdict(set)
for y,m,f in files():
    L=open(D+f,'rb').read().decode('utf-8','replace').split('\r\n')
    for i,l in enumerate(L,1):
        s=l.rstrip('\t')
        if l.startswith('PAGE') and not re.fullmatch(r'PAGE \d+',s):
            k=re.sub(r'\d+','N',s); sh[k]+=1; ex.setdefault(k,(f,i,l)); files_by[k].add(f)
        if re.match(r'GE \d',l) or (re.search(r'PAGE',l) and not l.startswith('PAGE') and l.count('\t')<2): print('weird',f,i,repr(l))
print(sh); print({k:(v,len(files_by[k])) for k,v in ex.items()}); 
for k in files_by: print(k,sorted(files_by[k])[:30])
