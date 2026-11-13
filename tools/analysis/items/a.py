import re,glob,os,collections as C
from config import COF_DIR as D
MON='JAN FEB MAR APR MAY JUN JUL AUG SEP OCT NOV DEC'.split()
rows=[]
for p in sorted(glob.glob(D+'*.txt')):
    fn=os.path.basename(p)[:-4]
    raw=open(p,'rb').read()
    txt=raw.decode('latin-1')
    hd=None
    for i,l in enumerate(txt.split('\n')):
        l=l.rstrip('\r') if False else l
        if '\t' in l:
            rows.append((fn,i+1,l,hd))
        elif l.strip() and not l.startswith('PAGE'): hd=l.strip()
print(len(rows))
import pickle;pickle.dump(rows,open('rows.pkl','wb'))
# tab line stats
c=C.Counter()
for fn,i,l,h in rows:
    f=l.split('\t'); c[(fn[3:],len(f))]+=1
yr=C.defaultdict(C.Counter)
for (y,n),k in c.items(): yr[y][n]+=k
for y in sorted(yr): print(y,dict(sorted(yr[y].items())))
