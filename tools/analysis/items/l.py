import pickle,re,collections as C
P=pickle.load(open('P.pkl','rb'))
ss=[p for p in P if p['f'][0]=='SS']
cl=C.Counter()
ex={}
for p in ss:
    t=p['f'][2]
    m=re.findall(r'\(([A-Z]{3}\d{6}|STAR\d+|[A-Z]{3}\d{5}|[A-Z0-9]{5,10})\)',t)
    k='MMMYYNNNN' if any(re.fullmatch(r'[A-Z]{3}\d{6}',x) for x in m) else ('STAR' if any(x.startswith('STAR') for x in m) else ('other-paren' if m else 'none'))
    cl[k]+=1; ex.setdefault(k,(p['fn'],p['i'],t[:90]))
print(cl,ex)
print('STAR any flag',C.Counter(p['f'][0] for p in P if 'STAR' in p['f'][2] and re.search(r'\(STAR\d+\)',p['f'][2])), 'files',len({p['fn'] for p in P if re.search(r'\(STAR\d+\)',p['f'][2])}))
print('SS none sample',[ (p['fn'],p['f'][2][:70]) for p in ss if not re.search(r'\([A-Z0-9]{5,10}\)',p['f'][2])][:5])
print('blank-date flags',C.Counter(p['f'][0] for p in P if p['f'][3]=='').most_common(6))
print('blank-date price',C.Counter(re.sub(r'[\d.]+','N',p['f'][4]) for p in P if p['f'][3]=='').most_common(4))
print('blank date with (C:',sum('(C:' in p['f'][2] for p in P if p['f'][3]==''),'of',sum(1 for p in P if p['f'][3]==''))
print('JAN09 flags',C.Counter(p['f'][0] for p in P if p['fn']=='JAN09').most_common(6))
# flag multiword order
print('flag combos',sorted({p['f'][0] for p in P}))
# GEM text sample
print([p['f'][2][:50] for p in P if p['f'][0]=='GEM'][:3])
# nonpadded 4 SOL within MAR09 'ext'? percent items with flag by era
