import pickle,re,collections as C
rows=pickle.load(open('rows.pkl','rb'))
SOLX=re.compile(r'^[A-Z]{3}\d\d \d{4}$')
MON='JAN FEB MAR APR MAY JUN JUL AUG SEP OCT NOV DEC'.split()
# non-item tab lines: sol-like?
items=[];non=[]
for fn,i,l,h in rows:
    f=l.split('\t')
    if len(f)>1 and re.match(r'^[A-Z]{3}\d\d ?\d{4}$',f[1].strip()): items.append((fn,i,l))
    else: non.append((fn,i,l))
print(len(items),len(non))
print('endings',C.Counter(re.sub(r'.*?((?: = \$)?[\t ]*\r?)$',r'\1',l) for fn,i,l in items).most_common(8))
print('no CR',sum(1 for x in items if not x[2].endswith('\r')))
# parse
P=[]
bad=[]
for fn,i,l in items:
    s=l[:-1] if l.endswith('\r') else l
    f=s.split('\t'); lay=None
    if f[-1]=='' : f=f[:-1]; tail_tab=True
    else: tail_tab=False
    # now expect: flag sol text date price ' = $'
    if len(f)==7 and f[2]=='': lay='extra_blank'; f=f[:2]+f[3:]
    elif len(f)==6: lay='std'
    elif len(f)==5: lay='nodate'; f=f[:3]+['']+f[3:]
    else: bad.append((fn,i,l)); continue
    P.append(dict(fn=fn,i=i,lay=lay,tt=tail_tab,f=f,raw=l))
print('bad',len(bad),bad[:5])
print(C.Counter((p['lay'],p['tt']) for p in P))
for key in [('std',False),('nodate',True),('extra_blank',True)]:
    c=C.Counter(p['fn'] for p in P if (p['lay'],p['tt'])==key); print(key,dict(c) if len(c)<12 else (len(c),'files'))
c=C.Counter(p['fn'] for p in P if p['lay']=='nodate'); print(c)
print('nodate f3 forms',C.Counter(re.sub(r'[\d.]+','N',p['f'][4]) for p in P if p['lay']=='nodate').most_common(5))
for p in P:
    if p['lay']=='nodate' and p['fn'] in('JUL11','JAN19'): print(p['fn'],p['i'],repr(p['raw'])[:200])
print('extra_blank files',C.Counter(p['fn'] for p in P if p['lay']=='extra_blank'))
print('tails',C.Counter(p['f'][5] for p in P))
print('std without tail tab files',sorted(set(p['fn'] for p in P if p['lay']=='std' and not p['tt'])))
pickle.dump(P,open('P.pkl','wb'))
