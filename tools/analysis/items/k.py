import pickle,re,collections as C
P=pickle.load(open('P.pkl','rb'))
bare=[p for p in P if re.match(r'^\$',p['f'][4])]
print('bare$ by file',C.Counter(p['fn'] for p in bare).most_common(8))
print('zero price',sum(1 for p in P if re.search(r'\$0\.00$',p['f'][4])),'max',max(float(re.search(r'\$([\d.]+)',p['f'][4]).group(1)) for p in P if '$' in p['f'][4]))
print('SRP:PI',[ (p['fn'],p['i'],p['raw'][:120]) for p in P if p['f'][4]=='SRP:PI'])
print('FREE',[ (p['fn'],p['i'],p['raw'][:140]) for p in P if 'FREE' in p['f'][4]])
print('MSRP PI',[ (p['fn'],p['i'],p['raw'][:140]) for p in P if p['f'][4]=='MSRP: PI'])
# text
t=[p['f'][2] for p in P]
print('empty text',[(p['fn'],p['i']) for p in P if p['f'][2]==''][:5],sum(1 for x in t if x==''))
print('text ws-trailing',sum(1 for x in t if x!=x.rstrip()),'leading',sum(1 for x in t if x!=x.lstrip()),'double space',sum(1 for x in t if '  ' in x))
for p in P:
    if p['f'][2]!=p['f'][2].rstrip() or p['f'][2]!=p['f'][2].lstrip(): print(p['fn'],p['i'],repr(p['f'][2])[:100]); break
print('trailing ws files',C.Counter(p['fn'] for p in P if p['f'][2]!=p['f'][2].rstrip()).most_common(6))
print('nonascii',sum(1 for x in t if re.search(r'[^\x20-\x7e]',x)), C.Counter(c for x in t for c in x if not (' '<=c<='~')).most_common(8))
print('len max',max(map(len,t)))
# flags field whitespace
print('flag ws',sum(1 for p in P if p['f'][0]!=p['f'][0].strip()), 'price ws',sum(1 for p in P if p['f'][4]!=p['f'][4].strip()))
# SS: prev code
ss=[p for p in P if p['f'][0]=='SS']
pc=[re.search(r'\(([A-Z]{3}\d{6})\)',p['f'][2]) for p in ss]
print('SS with (MMMYYNNNN)',sum(1 for m in pc if m),len(ss))
print('SS w/o', [ (p['fn'],p['f'][2][:60]) for p,m in zip(ss,pc) if not m][:5])
print('SS pattern last paren',C.Counter(bool(re.search(r'\([A-Z]{3}\d{6}\)(?: \(.*\))*$',p['f'][2])) for p in ss))
# non-SS having prev code
ns=[p for p in P if 'SS' not in p['f'][0].split() and re.search(r'\([A-Z]{3}\d{6}\)',p['f'][2])]
print('non-SS flag with prevcode',len(ns),C.Counter(p['f'][0] for p in ns))
# sol codes in text, forms
print('prevcode forms',C.Counter(re.sub(r'\d','9',m) for p in P for m in re.findall(r'\(([A-Z]{3}\d{5,7}[A-Z]?)\)',p['f'][2])).most_common(6))
# O/A
oa=[p for p in P if 'OA' in p['f'][0].split()]
print('OA flag with (O/A)',sum('(O/A)' in p['f'][2] for p in oa),len(oa),'no OA flag but (O/A)',sum(1 for p in P if 'OA' not in p['f'][0].split() and '(O/A)' in p['f'][2]))
print('FI/KIDS/SPOT/GEM text tokens:')
for k in ['FI','KIDS','SPOT','GEM']:
    v=[p for p in P if k in p['f'][0].split()]
    print(k,len(v),'(Net)',sum('(Net)' in p['f'][2] for p in v),'(C:',sum('(C:' in p['f'][2] for p in v),'(MR)',sum('(MR)' in p['f'][2] for p in v),'(Net) overall',)
# cases flag & non-default: star codes? '(C:' share by era
