import pickle,re,collections as C
P=pickle.load(open('P.pkl','rb'))
sh=C.Counter();ex={};fl={}
def shape(x): return re.sub(r'\d+','N',x)
for p in P:
    pr=p['f'][4]; s=re.sub(r'\d','9',pr); s=re.sub(r'9+','9',s)
    sh[s]+=1; ex.setdefault(s,(p['fn'],p['i'],pr))
    fl.setdefault(s,C.Counter())[p['f'][0]]+=1
for s,n in sh.most_common(): print(repr(s),n,ex[s],dict(fl[s].most_common(3)))
R=re.compile(r'^(?:(?:SRP|MSRP): (?:\$\d+\.\d\d|PI|FREE)|\$\d+\.\d\d|\$|FREE|)$')
print('regex leftovers',[ (p['fn'],p['i'],p['f'][4]) for p in P if not R.match(p['f'][4])][:20])
print('blank price',sum(1 for p in P if p['f'][4]==''))
print('prefix by year', {k:dict(v) for k,v in {pre:C.Counter(p['fn'][3:] for p in P if p['f'][4].startswith(pre)) for pre in ['MSRP: $','SRP: $','SRP: PI','MSRP: PI']}.items()})
print('price first/last per kind')
