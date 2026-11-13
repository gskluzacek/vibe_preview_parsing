import pickle,re,collections
r=pickle.load(open('rows.pkl','rb'))
MON='JAN FEB MAR APR MAY JUN JUL AUG SEP OCT NOV DEC'.split()
# caution digits
c=collections.Counter()
for x in r:
    for m in re.finditer(r'\(C: (\d)-(\d)-(\d)\)',x[3]): c[m.groups()]+=1
d=[collections.Counter(k[i] for k in c.elements() ) for i in range(3)]
pos=[collections.Counter() for _ in range(3)]
for k,v in c.items():
    for i in range(3): pos[i][k[i]]+=v
print('caution digit dist per position',[dict(sorted(p.items())) for p in pos]); print(c.most_common(8))
# caution presence by scope / flags
# prev sol lag
lag=collections.Counter(); badm=0; n=0; star=collections.Counter(); sy=collections.Counter()
mm=0
for x in r:
    m=re.search(r'\(([A-Z]{3})(\d\d)(\d{4})\)',x[3])
    if m:
        n+=1
        py=2000+int(m.group(2)); pm=MON.index(m.group(1))+1
        # file code = x[2] like 'JAN09 0047' — cof month is the order month; compare
        cm=MON.index(x[2][:3])+1; cy=2000+int(x[2][3:5])
        l=(cy*12+cm)-(py*12+pm); lag[min(max(l,-3),24)]+=1
        if m.group(3)==x[2][6:]: mm+=1
    ms=re.search(r'\(STAR(\d+)\)',x[3])
    if ms: star[len(ms.group(1))]+=1
print('prevsol n',n,'lag months (current order month - prev month)',sorted(lag.items()),'same-4digit-as-current',mm)
print('STAR digit lengths',star)
# sol code year vs file year
mis=sum(1 for x in r if int(x[2][3:5])+2000!=x[0] and True)
print('sol-code-year != file year',mis, 'sample',[ (x[0],x[1],x[2]) for x in r if int(x[2][3:5])+2000!=x[0]][:3])
# flags
fl=collections.Counter(); 
for x in r:
    f=' '.join(x[5]).strip()
    t=x[3]
    fl[(f,'prevsol' if re.search(r'\([A-Z]{3}\d{6}\)|\(STAR',t) else '-', 'O/A' if '(O/A)' in t else '-','RES' if '(RES)' in t else '-')]+=1
agg=collections.defaultdict(collections.Counter)
for (f,p,o,s),v in fl.items():
    agg[f]['n']+=v; agg[f]['prevsol']+=v*(p!='-'); agg[f]['O/A']+=v*(o!='-'); agg[f]['RES']+=v*(s!='-')
for f,a in agg.items(): print(repr(f),dict(a))
# Net by scope, caution by scope
sc=collections.defaultdict(collections.Counter)
for x in r:
    sc[x[4]]['n']+=1; sc[x[4]]['caut']+= '(C:' in x[3]; sc[x[4]]['net']+='(Net)' in x[3]
print({k:dict(v) for k,v in sc.items()})
# caution dup months
dm=collections.Counter()
for x in r:
    if len(re.findall(r'\(C: ',x[3]))>1: dm[(x[0],x[1])]+=1
print('dup caution months',sorted(dm.items()))
# MR and A together
print('MR&A both',sum(1 for x in r if '(MR)' in x[3] and '(A)' in x[3]))
print('MR with caution vs not', sum(1 for x in r if '(MR)' in x[3] and '(C:' in x[3]),sum(1 for x in r if '(MR)' in x[3]))
print('weird (C:',[x[3] for x in r if re.search(r'\(C:(?! \d-\d-\d\))',x[3])])
