import pickle,re,collections as C
P=pickle.load(open('P.pkl','rb'))
S=re.compile(r'^([A-Z]{3})(\d\d) (\d{4})$')
byfile=C.defaultdict(list)
for p in P:
    m=S.match(p['f'][1])
    if m: byfile[p['fn']].append((p['i'],int(m.group(3)),p))
# dup detail
for fn in('DEC18','NOV16','SEP16'):
    c=C.Counter(n for _,n,_ in byfile[fn]); d=[n for n,k in c.items() if k>1][0]
    for i,n,p in byfile[fn]:
        if n==d: print(fn,i,repr(p['raw'])[:160])
for fn in('JUN17','NOV13','AUG19','JAN19','MAY18'):
    v=byfile[fn]
    for (i1,n1,p1),(i2,n2,p2) in zip(v,v[1:]):
        if n2<n1: print(fn,'drop',i1,n1,'->',i2,n2, p2['f'][1], p2['f'][2][:40])
# ranges
big=C.Counter(); 
for fn,v in byfile.items():
    nums=sorted(n for _,n,_ in v)
    hi=[n for n in nums if n>=5000]
    main=[n for n in nums if n<5000]
    g=(max(main)-min(main)+1)-len(set(main))
    big[fn]=(len(hi),g,min(main),max(main))
tot_hi=sum(1 for v in byfile.values() for _,n,_ in v if n>=5000)
print('codes>=5000',tot_hi,'files with any',sum(1 for x in big.values() if x[0]))
print('files with zero gaps in <5000 block',sum(1 for x in big.values() if x[1]==0),'of',len(big))
print('max main gap ex',sorted(((x[1],f) for f,x in big.items()),reverse=True)[:5])
print('main block min start',C.Counter(x[2] for x in big.values()).most_common(5))
hi=C.Counter(p['f'][1][7:9] for fn,v in byfile.items() for _,n,p in v if n>=5000)
print('>=5000 first 2 digits',sorted(hi.items())[:20])
print('where >=5000 position: ', [ (fn,x[0]) for fn,x in list(big.items()) if x[0]][:8])
# are >=5000 at end of file?
