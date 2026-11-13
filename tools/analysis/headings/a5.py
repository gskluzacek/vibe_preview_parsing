import pickle,collections,json
files,out=pickle.load(open('rec.pkl','rb'))
r=json.load(open('hdg_lvls.json'));L1=set(x[4] for x in r if x[1]==1)|{'DIAMOND SELECT TOYS & COLLECTIBLES','WIZARD ENTERTAINMENT','PREMIERE COLLECTIBLES'}
for f in files:
    if f[3:5] not in('17','18') : continue
    cur=None;c=collections.Counter();order=[]
    for k,s in out[f]:
        if k=='HDG' and s in L1:cur=s;order.append(s)
        elif k=='ITEM':c[cur]+=1
    hs={s for k,s in out[f] if k=='HDG'}
    print(f,dict(c.most_common(3)),'DH' if 'DARK HORSE' in hs else '','DHC' if 'DARK HORSE COMICS' in hs else '','DYN' if 'DYNAMITE ENTERTAINMENT' in hs else '','DED' if 'D. E./DYNAMITE ENTERTAINMENT' in hs else '','COMICS' if 'COMICS' in hs else '')
