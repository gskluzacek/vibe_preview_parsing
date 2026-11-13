import pickle,re,collections as C
rows=pickle.load(open('rows.pkl','rb'))
MON='JAN FEB MAR APR MAY JUN JUL AUG SEP OCT NOV DEC'.split()
def ym(fn): return (int(fn[3:])+ (1900 if int(fn[3:])>50 else 2000), MON.index(fn[:3]))
items=[]; odd=[]
for fn,i,l,h in rows:
    f=l.split('\t')
    if f[-1].strip()=='' : f=f[:-1]; 
    # now: 6 normal (flag,sol,text,date,price,tail); 
    n=len(f)
    if n==7 and f[2]=='': f=f[:2]+f[3:]; n=6; ext=1
    else: ext=0
    if n==5: f=f[:3]+['']+f[3:]; n=6; ext=2  # missing date
    if n!=6: odd.append((fn,i,l)); continue
    items.append((fn,i,h,ext,f))
print(len(items),'odd',len(odd),odd)
print('ext',C.Counter(x[3] for x in items))
# which 5->missing date: verify field3 looks like price
md=[x for x in items if x[3]==2]
print('missing-date by file',C.Counter(x[0] for x in md))
print(C.Counter(re.sub(r'[\d.,]+','N',x[4][3]) for x in md))
# ext==1 files
print('ext1 files',C.Counter(x[0] for x in items if x[3]==1) if True else 0)
# 8 field lines with nonblank f[2]?
print([ (fn,i) for fn,i,l,h in rows if len(l.split('\t'))==8 and l.split('\t')[2]!=''][:5])
# flag
fc=C.Counter(); first={}; last={}; hd=C.defaultdict(C.Counter)
for fn,i,h,e,f in items:
    k=f[0]; fc[k]+=1
    y=ym(fn); first[k]=min(first.get(k,y),y); last[k]=max(last.get(k,y),y)
    hd[k][h]+=1
def nm(y): return MON[y[1]]+str(y[0])[2:]
for k,v in fc.most_common():
    print(repr(k),v,nm(first[k]),nm(last[k]),hd[k].most_common(3),len(hd[k]))
pickle.dump(items,open('items.pkl','wb'))
