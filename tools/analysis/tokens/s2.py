import pickle,collections,re
r=pickle.load(open('rows.pkl','rb'))
g=collections.Counter(); ex={}
for x in r:
    for m in re.findall(r'\([^()]*\)',x[3]):
        k=re.sub(r'\d','n',m)
        k=re.sub(r'\b[A-Z]{3}nnnnnn?\b','MMMYYSOL',k) if False else k
        g[k]+=1; ex.setdefault(k,m)
print(len(g))
for k,n in g.most_common(120): print(n,k)
print('lowercase non-Net:',collections.Counter(re.sub(r'[^a-z]','',w) for x in r for w in re.findall(r'\S*[a-z]\S*',x[3])).most_common(15))
