import config
import pickle,collections,re,csv
from config import COF_DIR as P
files,out=pickle.load(open('rec.pkl','rb'))
# raw whitespace features of HDG lines
feat=collections.Counter()
for f in files:
    t=open(P+f,'rb').read().decode('cp1252',errors='replace').replace('\r\n','\n').split('\n')
    for l in t:
        s=l.rstrip('\r')
        if s.strip() and '\t' not in s.strip('\t') and not s.startswith('\t') and not re.match(r'^PAGE',s):
            feat[('lead_ws',s!=s.lstrip(' '))]+=1; feat[('trail_ws',s!=s.rstrip(' \t'))]+=1
print(feat)
# signals over all HDG occurrences
tot=0;followed_page=0;prev_page=0;prev_blank=0;prevhdg=0;upper=0;digit=0
for f in files:
    o=out[f]
    for i,(k,s) in enumerate(o):
        if k!='HDG':continue
        tot+=1
        nk=o[i+1][0] if i+1<len(o) else None;pk=o[i-1][0] if i>0 else None
        followed_page+=nk=='PAGE';prev_page+=pk=='PAGE';prev_blank+=pk=='BLANK';prevhdg+=pk=='HDG'
        upper+= s==s.upper()
        digit+=bool(re.fullmatch(r'[\d\s]+',s))
print(dict(tot=tot,followed_page=followed_page,prev_page=prev_page,prev_blank=prev_blank,prev_hdg=prevhdg,upper=upper,numeric=digit))
# noise candidates
bad=collections.Counter()
for f in files:
    for k,s in out[f]:
        if k=='HDG':
            if re.fullmatch(r'[\d\s]+',s): bad['numeric']+=1
            elif s.startswith('['): bad['bracket']+=1
            elif re.search(r'V\d+ #\d+|PREVIEWS ORDER FORM|CUSTOMER ORDER',s): bad['ident-like']+=1
            elif s!=s.upper(): bad['has-lower']+=1
            elif not re.search(r'[A-Z]',s): bad['no-letters']+=1
print(bad)
print('ident-like examples',collections.Counter(s for f in files for k,s in out[f] if k=='HDG' and re.search(r'V\d+ #\d+|ORDER FORM',s)).most_common(5))
# JAN09 eval
ex=list(csv.reader(open(config.HEADING_EXTRACT,encoding='utf-8'),delimiter='\t',quoting=csv.QUOTE_NONE))[1:]
gold=collections.Counter(x[8].strip().strip('"').replace('É','…') for x in ex)
def rule(s):
    return s==s.upper() and bool(re.search(r'[A-Z]',s)) and not s.startswith('[') and not re.fullmatch(r'[\d\s]+',s) 
for name,fn in [('all non-item/page/note lines',lambda s:True),('+caps+has-letter+not bracket/numeric',rule)]:
    pred=collections.Counter(s for k,s in out['JAN09.txt'] if k=='HDG' and fn(s))
    tp=sum((pred&gold).values());print(name,'pred',sum(pred.values()),'gold',sum(gold.values()),'tp',tp,'prec',round(tp/sum(pred.values()),4),'rec',round(tp/sum(gold.values()),4))
# frequency signal on whole corpus: noise lines in 1 file
print([ (s,f) for f in files for k,s in out[f] if k=='HDG' and re.fullmatch(r'[\d\s]+',s)][:8])
