import pickle,collections,json,csv
files,out=pickle.load(open('rec.pkl','rb'))
r=json.load(open('hdg_lvls.json'))
L1=set(x[4] for x in r if x[1]==1)
ex=list(csv.reader(open('/Volumes/U34-Bolt/Personal/development/github/previews_parsing/headings_hrch_extract_2.txt',encoding='utf-8'),delimiter='\t',quoting=csv.QUOTE_NONE))[1:]
exL1=set(x[8].strip() for x in ex if x[6]=='1'); print('extract L1 not in dump L1',exL1-L1,'dump L1 not in extract',L1-exL1)
allh=collections.Counter(s for f in files for k,s in out[f] if k=='HDG')
print({n:allh[n] for n in sorted(L1|exL1)})
print([ (s,c) for s,c in allh.items() if 'FREE COMIC' in s][:5], [(s,c) for s,c in allh.items() if s in('PREVIEWS PUBLICATIONS','PREMIER PUBLISHERS','COMICS')])
# sequences of L1
seqs=collections.Counter(); itemsec=collections.Counter(); itemyr=collections.defaultdict(collections.Counter)
rep=collections.Counter(); nfiles_rep=collections.Counter()
allL1=L1|exL1
tot=0
firsts=collections.Counter()
for f in files:
    cur='(before any L1)';seq=[]
    for k,s in out[f]:
        if k=='HDG' and s in allL1:
            seq.append(s);cur=s
        elif k=='ITEM':
            itemsec[cur]+=1;itemyr[2000+int(f[3:5])][cur]+=1;tot+=1
    c=collections.Counter(seq)
    for s,v in c.items():
        if v>1: rep[s]+=1
    seqs[tuple(seq)]+=1
    firsts[seq[0] if seq else None]+=1
print('items',tot);print(itemsec.most_common())
print('firsts',firsts)
print('distinct L1 seqs',len(seqs))
for s,c in seqs.most_common(4): print(c,s)
print('files with repeated L1',rep)
# collapsed order: first-occurrence order consensus
pos=collections.defaultdict(list)
for sq in seqs.elements():
    for i,s in enumerate(dict.fromkeys(sq)): pos[s].append(i)
print('avg first-occ idx',{s:round(sum(v)/len(v),1) for s,v in sorted(pos.items(),key=lambda x:sum(x[1])/len(x[1]))}, )
print('files containing',{s:len(v) for s,v in pos.items()})
for y in sorted(itemyr): print(y,sum(itemyr[y].values()),itemyr[y].most_common(3))
