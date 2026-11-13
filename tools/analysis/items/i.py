import pickle,re,collections as C,datetime
P=pickle.load(open('P.pkl','rb'))
# dates
def shape(d): return re.sub(r'\d','9',d)
byera=C.defaultdict(C.Counter); ex={}
for p in P:
    d=p['f'][3]; sh=shape(d); y=p['fn'][3:]
    byera[sh][y]+=1; ex.setdefault(sh,(p['fn'],p['i'],d))
for sh,c in byera.items(): print(repr(sh),sum(c.values()),dict(sorted(c.items())),ex[sh])
# unparseable calendar
badc=[]
for p in P:
    d=p['f'][3]
    m=re.match(r'^(\d{1,2})/(\d{1,2})/(\d{2}|\d{4})$',d)
    if m:
        a,b,y=map(int,m.groups()); y=y+2000 if y<100 else y
        try: datetime.date(y,a,b)
        except: badc.append((p['fn'],p['i'],d))
print('invalid calendar',len(badc),badc[:5])
blank=C.Counter(p['fn'] for p in P if p['f'][3]=='' )
print('blank date by file',len(blank),blank.most_common(8),sum(blank.values()))
print('blank date by lay',C.Counter(p['lay'] for p in P if p['f'][3]==''))
# leading/trailing space in date
print('date ws',sum(1 for p in P if p['f'][3]!=p['f'][3].strip()))
# mm/dd/yy by year consistency: first/last file for 4-digit year
fy=sorted({p['fn'] for p in P if len(p['f'][3])in(8,9,10) and re.match(r'^\d{1,2}/\d{1,2}/\d{4}$',p['f'][3])},key=lambda f:(f[3:],f))
print('4-digit-year files',fy)
sd=sorted({p['fn'] for p in P if re.match(r'^\d/\d/\d\d$|^\d/\d\d/\d\d$|^\d\d/\d/\d\d$',p['f'][3])}); print('non-padded 2-digit files',sd[:10],len(sd))
# unpadded in 'mm/dd/yy' era?
print('single-digit parts, 2-digit year',C.Counter(p['fn'][3:] for p in P if re.match(r'^(\d/|\d\d/\d/)\d\d?/?\d\d$',p['f'][3]) and len(p['f'][3])<8))
# release year vs file: sanity
