import pickle,collections,json,re
files,out=pickle.load(open('rec.pkl','rb'))
idx={f:i for i,f in enumerate(files)}
H=collections.defaultdict(lambda:{'f':[], 'items':0})
for f in files:
    cur=None;seen=set()
    for k,s in out[f]:
        if k=='HDG':
            cur=s
            if s not in seen: H[s]['f'].append(idx[f]);seen.add(s)
        elif k=='ITEM' and cur: H[cur]['items']+=1
def isnoise(s): return bool(re.fullmatch(r'[\d\s]+',s)) or s.startswith('[')
rows=[]
for s,d in H.items():
    if isnoise(s):continue
    fl=d['f'];rows.append((s,files[fl[0]],files[fl[-1]],len(fl),d['items'],fl[-1]-fl[0]+1))
print('noise headings',sum(1 for s in H if isnoise(s)))
rows.sort(key=lambda r:-r[4])
print('--- top by items, not full-span (first!=JAN09 or last!=MAR20)')
n=0
for r in rows:
    if r[1]!='JAN09.txt' or r[2]!='MAR20.txt':
        print(r);n+=1
        if n>=40:break
# L1 presence per year
L1=['PREMIER PUBLISHERS','COMICS','BOOKS','MAGAZINES','BOOKS & MAGAZINES','CALENDARS','INTERNATIONAL','WIZARD ENTERTAINMENT','PREMIERE COLLECTIBLES','OTHER IMPORT TOYS & MODELS','STATUES & MODELS','DVDS & DIGITAL MEDIA','TOYS','DIAMOND SELECT TOYS & COLLECTIBLES','DESIGNER TOYS','OTHER APPAREL']
print('--- L1 first/last/nfiles'); 
for s in L1:
    d=H[s];print(s,files[d['f'][0]],files[d['f'][-1]],len(d['f']))
# distinct heading count per file by index - detect jumps
cnt=[(f,len({s for k,s in out[f] if k=='HDG'})) for f in files]
print(cnt)
