import pickle,re,collections as C
rows=pickle.load(open('rows.pkl','rb'))
SOL=re.compile(r'^[A-Z]{3}\d\d \d{4}$')
MON='JAN FEB MAR APR MAY JUN JUL AUG SEP OCT NOV DEC'.split()
def ymk(fn): y=int(fn[3:]); return (y+(1900 if y>50 else 2000),MON.index(fn[:3]))
nm=lambda y:MON[y[1]]+str(y[0])[2:]
items=[];non=[]
for fn,i,l,h in rows:
    f=l.split('\t')
    if len(f)<2 or not SOL.match(f[1]): non.append((fn,i,l));continue
    items.append((fn,i,l,f))
print('items',len(items),'nonitem tab lines',len(non))
print(C.Counter(x[0] for x in non))
print(C.Counter(re.sub(r'[^\t]','x',x[2]) for x in non).most_common(5))
for x in non[:2]+[y for y in non if y[0] not in('JAN13','JUL13')]: print(x[0],x[1],repr(x[2])[:150])
# raw field count by file-group
lay=C.defaultdict(C.Counter)
for fn,i,l,f in items: lay[fn][len(f)]+=1
byera=C.defaultdict(C.Counter)
for fn,c in lay.items():
    for n,k in c.items(): byera[fn[3:]][n]+=k
print({y:dict(c) for y,c in sorted(byera.items())})
print({fn:dict(c) for fn,c in lay.items() if len(c)>1 or 7 not in c})
# 6 field other than MAR09 APR09
for fn,i,l,f in items:
    if len(f)==6 and fn not in('MAR09','APR09'): print(fn,i,repr(l)[:200])
for fn,i,l,f in items:
    if len(f)==8 and fn=='SEP15': print(fn,i,repr(l)[:200])
pickle.dump(items,open('items2.pkl','wb'))
