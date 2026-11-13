import pickle,re,collections as C
P=pickle.load(open('P.pkl','rb'))
MON='JAN FEB MAR APR MAY JUN JUL AUG SEP OCT NOV DEC'.split()
S=re.compile(r'^([A-Z]{3})(\d\d) (\d{4})$')
# sol
nm=0;mm=[];bad=[];nosp=[]
byfile=C.defaultdict(list)
for p in P:
    s=p['f'][1]; m=S.match(s)
    if not m: bad.append(p); continue
    if m.group(1)+m.group(2)!=p['fn']: mm.append(p)
    byfile[p['fn']].append((p['i'],int(m.group(3)),p))
print('sol nonconf',len(bad),[(p['fn'],p['i'],p['f'][1]) for p in bad])
print('sol month != file',len(mm),[(p['fn'],p['i'],p['f'][1]) for p in mm][:12])
dup=0;nonseq=0;files_dup=[];gaps={};nonmono=[];start=C.Counter()
for fn,v in byfile.items():
    nums=[n for _,n,_ in v]
    c=C.Counter(nums); d=sum(k-1 for k in c.values() if k>1)
    if d: dup+=d; files_dup.append((fn,d,[n for n,k in c.items() if k>1][:3]))
    start[min(nums)]+=1
    if nums!=sorted(nums): nonmono.append((fn,sum(1 for a,b in zip(nums,nums[1:]) if b<a)))
    s=sorted(set(nums)); g=(max(s)-min(s)+1)-len(s)
    if g: gaps[fn]=g
print('files',len(byfile),'dups',dup,files_dup[:15],len(files_dup))
print('nonmonotone files',len(nonmono),nonmono[:10])
print('files with gaps',len(gaps),sum(gaps.values()),'min starts',start.most_common(4))
print('max per file',max(max(n for _,n,_ in v) for v in byfile.values()))
print('sol numeric 4 digits; starts with 0000?',sum(1 for p in P if p['f'][1].endswith(' 0000')))
# flags set, first/last, check text patterns
def key(fn): y=int(fn[3:]);return (y,MON.index(fn[:3]))
fl=C.defaultdict(list)
for p in P: fl[p['f'][0]].append(p)
for k,v in sorted(fl.items(),key=lambda x:-len(x[1])):
    ks=[key(p['fn']) for p in v]
    f=lambda t:MON[t[1]]+str(t[0])
    n=len(v)
    par=sum(1 for p in v if re.search(r'\([A-Z]{3}\d{6}\)',p['f'][2]))
    oa=sum(1 for p in v if '(O/A)' in p['f'][2])
    ci=sum(1 for p in v if re.search(r'\(C: ?\d-\d-\d\)',p['f'][2]))
    print(repr(k),n,f(min(ks)),f(max(ks)),'prevsol(XXXNNNNNN)',par,'(O/A)',oa,'(C:..)',ci)
