import pickle,re,collections as C
rows=pickle.load(open('rows.pkl','rb'))
def show(fn,l,i=None): return f'{fn}:{i} '+repr(l)[:200]
# layouts
lay=C.defaultdict(list)
for fn,i,l,h in rows:
    f=l.split('\t')
    n=len(f)
    if n==7: continue
    lay[(n)].append((fn,i,l))
for n,v in lay.items():
    print('NF',n,len(v),sorted(C.Counter(x[0] for x in v).items(),key=lambda x:(x[0][3:],x[0]))[:60])
    for x in v[:2]+v[-1:]: print('  ',show(x[0],x[2],x[1]))
# 7-field tails
print(C.Counter((l.split('\t')[5],l.split('\t')[6]) for fn,i,l,h in rows if len(l.split('\t'))==7))
