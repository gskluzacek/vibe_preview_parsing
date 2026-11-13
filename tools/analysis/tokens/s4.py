import sys; sys.path.insert(0,".")
import pickle,collections,re,itertools
r=pickle.load(open('rows.pkl','rb'))
def pc(g):
    if re.fullmatch(r'\(C: \d-\d-\d\)',g): return 'CAUT'
    if g in('(MR)','(A)'): return 'ADV'
    if g in('(O/A)','(RES)'): return 'SOL'
    if g=='(Net)': return 'NET'
    if g=='(NOTE PRICE)': return 'NOTEPRICE'
    if g=='(PD)': return 'PD'
    if g=='(OSW)': return 'OSW'
    if re.fullmatch(r'\([A-Z]{3}\d{6}\)|\(STAR\d+\)',g): return 'PREVSOL'
    if re.fullmatch(r'\( ?OF \d+\)',g): return 'OFN'
    if re.fullmatch(r'\((?:NEW|CURR|\d+(?:ST|ND|RD|TH)) (?:PTG|PRINTING)\)|\(NEW PRINTING\)',g): return 'PTG'
    return 'OTHER'
seqs=collections.Counter(); first=collections.defaultdict(list)
n=0;withp=0
lastc=collections.Counter(); posttext=collections.Counter()
pair=collections.Counter()
for x in r:
    t=x[3]
    gs=[(m.start(),m.group()) for m in re.finditer(r'\([^()]*\)',t)]
    if not gs: seqs[()]+=1; continue
    cl=[pc(g) for _,g in gs]
    seqs[tuple(cl)]+=1
    if 'CAUT' in cl:
        i=cl.index('CAUT'); 
        lastc['caut_is_last_paren' if i==len(cl)-1 else 'caut_not_last']+=1
        end=gs[i][0]+len(gs[i][1])
        lastc['caut_ends_string' if t[end:].strip()=='' else 'text_after_caut']+=1
        if i!=len(cl)-1 and len(first['cn'])<8: first['cn'].append(t)
        if t[end:].strip()!='' and len(first['ta'])<8: first['ta'].append(t)
    for a,b in itertools.combinations(range(len(cl)),2):
        pair[(cl[a],cl[b])]+=1
    # text after last paren
    last=gs[-1]; tail=t[last[0]+len(last[1]):].strip()
    posttext['tail_text' if tail else 'ends_with_paren']+=1
print(lastc);print(posttext)
print('top seqs');
for k,v in seqs.most_common(45): print(v,k)
print('pair order (first,second)')
cls=['ADV','SOL','NET','NOTEPRICE','PD','OSW','PREVSOL','OFN','PTG','OTHER','CAUT']
for a,b in itertools.combinations(cls,2):
    ab=pair[(a,b)];ba=pair[(b,a)]
    if ab+ba>=20: print(f'{a}->{b}:{ab}  {b}->{a}:{ba}')
for a in cls:
    for b in [a]:
        if pair[(a,a)]: print('same-class pair',a,pair[(a,a)])
print(first)
# MR+A both
