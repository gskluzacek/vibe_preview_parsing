import sys
import pickle,collections,random,sys
from cls import CR
r=pickle.load(open('rows.pkl','rb'))
random.seed(1)
yrs=list(range(2009,2021))
tot=collections.Counter(x[0] for x in r)
sub=sys.argv[1] if len(sys.argv)>1 else 'all'
if sub=='premier': r=[x for x in r if x[4]=='premier']; tot=collections.Counter(x[0] for x in r)
res={}
for n,p in CR:
    hits=[x for x in r if p.search(x[3])]
    by=collections.Counter(x[0] for x in hits)
    ex=random.sample([x[3] for x in hits],min(3,len(hits)))
    res[n]=(len(hits),by,ex)
print('total',len(r),' years items:',dict(sorted(tot.items())))
print('class,N,pct,per-year % (2009..2020)')
for n,(c,by,ex) in res.items():
    print(f"{n}\t{c}\t{100*c/len(r):.2f}\t"+' '.join(f"{100*by[y]/tot[y]:.1f}" for y in yrs)+'\t'+' | '.join(ex))
