import sys; sys.path.insert(0,".")
import pickle,collections,re
r=pickle.load(open('rows.pkl','rb'))
first={};cnt=collections.Counter()
def add(k,ym):
    cnt[k]+=1
    if k not in first: first[k]=ym
for x in r:
    ym=(x[0],x[1]); t=x[3]
    for w in set(re.findall(r"[A-Z0-9#&/\.\-:+]+",t)):
        w2=re.sub(r'\d','n',w) if re.search(r'#|\d',w) else w
        add('W:'+w2,ym)
    for g in set(re.findall(r'\([^()]*\)',t)):
        add('P:'+re.sub(r'\d','n',g),ym)
    for g in set(re.findall(r'\b(?:CVR|VAR|COVER) [A-Z]\b|\b[A-Z]+ (?:CVR|VAR)\b',t)): add('B:'+g,ym)
new=[(first[k],k,cnt[k]) for k in cnt if first[k]>=(2014,10) and cnt[k]>=25]
new.sort()
print(len(new))
for f,k,c in new: print(f'{f[0]}-{f[1]:02d}',k,c)
