import pickle,collections,re
files,out=pickle.load(open('rec.pkl','rb'))
yr=lambda f:2000+int(f[3:5])
H=collections.defaultdict(set)
cnt=collections.Counter()
for f in files:
    for k,s in out[f]:
        if k=='HDG': H[s].add(f); cnt[s]+=1
print('distinct',len(H),'occ',sum(cnt.values()))
y=collections.defaultdict(set)
for s,fs in H.items():
    for f in fs:y[yr(f)].add(s)
print({k:len(v) for k,v in sorted(y.items())})
nf=collections.Counter(len(v) for v in H.values())
print('one file',nf[1],'2-5',sum(v for k,v in nf.items() if 2<=k<=5),'6-50',sum(v for k,v in nf.items() if 6<=k<=50),'>50',sum(v for k,v in nf.items() if k>50),'all135',nf[135])
print('per file hdg lines mean',sum(cnt.values())/135)
# only-one-file samples
one=[s for s,v in H.items() if len(v)==1]
import random;random.seed(2);print(random.sample(one,25))
print('lower-case headings',sum(1 for s in H if s!=s.upper()),[s for s in H if s!=s.upper()][:25])
print('long >60',[s for s in H if len(s)>60][:10])
# non-hdg unusual
print([ (f,s) for f in files for k,s in out[f] if k=='NOTE'][:5])
print('ident first-lines',collections.Counter(k for f in files for k,s in out[f][:1]))
print('first nonblank non-page types',collections.Counter(next(k for k,s in out[f] if k!='BLANK') for f in files))
print('items with <3 fields',sum(1 for f in files for k,s in out[f] if k=='ITEM' and s.count('\t')<2))
