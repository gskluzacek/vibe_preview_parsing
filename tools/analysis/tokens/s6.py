import sys; sys.path.insert(0,".")
import pickle,collections,re
r=pickle.load(open('rows.pkl','rb'))
META=re.compile(r'\((?:C: \d-\d-\d|MR|A|O/A|RES|Net|NOTE PRICE|[A-Z]{3}\d{6}|STAR\d+| ?OF \d+)\)')
# unclassified paren groups
og=collections.Counter()
for x in r:
    for g in re.findall(r'\([^()]*\)',x[3]):
        if not META.fullmatch(g): og[g]+=1
print('distinct non-meta paren groups',len(og),'total',sum(og.values()))
print(og.most_common(60))
# trailing words after stripping metas
tw=collections.Counter();tb=collections.Counter();tt=collections.Counter()
for x in r:
    t=META.sub('',x[3]); t=re.sub(r'\s+',' ',t).strip()
    w=t.split()
    if w: tw[w[-1]]+=1
    if len(w)>1: tb[' '.join(w[-2:])]+=1
    if len(w)>2: tt[' '.join(w[-3:])]+=1
print('LAST WORD',tw.most_common(70))
print('LAST BIGRAM',tb.most_common(60))
print('LAST TRIGRAM',tt.most_common(30))
