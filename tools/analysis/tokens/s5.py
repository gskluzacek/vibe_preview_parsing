import sys; sys.path.insert(0,".")
import pickle,collections,re,itertools
r=pickle.load(open('rows.pkl','rb'))
# positions of coarse classes
P={
'ISSUE':r'#[\w.#\-]+','ONESHOT':r'ONE[ -]SHOT','OFN':r'\( ?OF \d+\)','PT':r'\bPT ?\d+\b',
'PTG':r'\b\d+(?:ST|ND|RD|TH) (?:PTG|PRINTING)\b|\bNEW (?:PTG|PRINTING)\b|\bCURR PTG\b',
'CVR':r'\b(?:CVR|VAR|COVER)\b','SGN':r'\bSGN\b','VOL':r'\bVOL \d+\b','BOOK':r'\b(?:GN|TP|HC|SC|OMNIBUS)\b',
'ED':r'\b[A-Z0-9&]+ ED\b','PREVSOL':r'\([A-Z]{3}\d{6}\)|\(STAR\d+\)','CAUT':r'\(C: \d-\d-\d\)','NET':r'\(Net\)',
'ADV':r'\((?:MR|A)\)','SOL':r'\((?:O/A|RES)\)','TS':r'\bT/S\b'}
C={k:re.compile(v) for k,v in P.items()}
pair=collections.Counter(); last=collections.Counter(); lastnp=collections.Counter()
for x in r:
    t=x[3]; occ=[]
    for k,p in C.items():
        m=p.search(t)
        if m: occ.append((m.start(),k))
    occ.sort()
    ks=[k for _,k in occ]
    for a,b in itertools.combinations(ks,2): pair[(a,b)]+=1
    if ks: last[ks[-1]]+=1
    kn=[k for k in ks if k not in('CAUT','PREVSOL','NET','ADV','SOL')]
    if kn: lastnp[kn[-1]]+=1
print('last class overall',last.most_common())
print('last class excluding trailing meta paren',lastnp.most_common())
cl=list(P)
for a,b in itertools.combinations(cl,2):
    ab=pair[(a,b)];ba=pair[(b,a)]
    if ab+ba>=100: print(f'{a}<{b}:{ab}  {b}<{a}:{ba}  ({100*ab/(ab+ba):.0f}% first)')
