import pickle,collections,json
files,out=pickle.load(open('rec.pkl','rb'))
r=json.load(open('hdg_lvls.json'));L1=set(x[4] for x in r if x[1]==1)|{'DIAMOND SELECT TOYS & COLLECTIBLES','WIZARD ENTERTAINMENT','PREMIERE COLLECTIBLES'}
BM={'BOOKS','MAGAZINES','BOOKS & MAGAZINES'}
tot=collections.Counter();yr=collections.defaultdict(collections.Counter)
subc=collections.Counter()
for f in files:
    cur=None
    for k,s in out[f]:
        if k=='HDG' and s in L1:
            if s=='COMICS' and cur in BM|{'(COMICS-in-BM)'}: cur='(COMICS under BOOKS/MAG)';continue
            if s=='COMICS' and cur=='COMICS': subc['COMICS twice']+=1
            if s in BM or s!='COMICS' : cur=s
            else: cur=s
        elif k=='ITEM':tot[cur]+=1;yr[2000+int(f[3:5])][cur]+=1
print(tot.most_common(8))
for y in (2009,2013,2017,2018,2019): print(y,yr[y].most_common(3), yr[y]['(COMICS under BOOKS/MAG)'])
# repeated PREVIEWS PUBLICATIONS context
for f in files:
    hs=[(i,s) for i,(k,s) in enumerate(out[f]) if k=='HDG' and s=='PREVIEWS PUBLICATIONS']
    if len(hs)>1:
        print(f,[i for i,_ in hs]); i=hs[1][0]; print('   ',[ (k,s[:30]) for k,s in out[f][i-3:i+3]])
        break
# repeated DESIGNER TOYS ctx
n=0
for f in files:
    hs=[i for i,(k,s) in enumerate(out[f]) if k=='HDG' and s=='DESIGNER TOYS']
    if len(hs)>1:
        i=hs[1]; print(f,hs,[ (k,s[:25]) for k,s in out[f][i-6:i+3]]);n+=1
        if n>1:break
# L1 repeated counts: which files have PREVIEWS PUBLICATIONS (141 occ in 135 files)
print([ (f,len([1 for k,s in out[f] if k=='HDG' and s=='PREVIEWS PUBLICATIONS'])) for f in files if len([1 for k,s in out[f] if k=='HDG' and s=='PREVIEWS PUBLICATIONS'])>1])
