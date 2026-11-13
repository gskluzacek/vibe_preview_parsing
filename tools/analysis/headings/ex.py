import re,glob,os,collections,pickle
from config import COF_DIR as P
files=sorted([f for f in os.listdir(P) if re.fullmatch(r'[A-Z]{3}\d\d\.txt',f)],key=lambda f:(f[3:5],['JAN','FEB','MAR','APR','MAY','JUN','JUL','AUG','SEP','OCT','NOV','DEC'].index(f[:3])))
print(len(files))
PAGE=re.compile(r'^PAGE\s+(M-?|S-?)?\d+\s*$',re.I)
out={}
cls=collections.Counter()
other=collections.Counter()
for f in files:
    raw=open(P+f,'rb').read()
    try: t=raw.decode('utf-8')
    except: t=raw.decode('cp1252',errors='replace')
    L=t.replace('\r\n','\n').replace('\r','\n').split('\n')
    rec=[]
    for i,l in enumerate(L):
        s=l.rstrip('\t \r')
        if not s.strip(): k='BLANK'
        elif PAGE.match(s): k='PAGE'
        elif '\t' in s.strip('\t') or s.startswith('\t'): k='ITEM'
        elif re.match(r'^\(NOTE',s): k='NOTE'
        elif re.match(r'^PREVIEWS\b.*(VOL|#\d|ISSUE|20\d\d)',s) and i<8: k='IDENT'
        else: k='HDG'
        rec.append((k,s.strip()))
        cls[k]+=1
    out[f]=rec
pickle.dump((files,out),open('rec.pkl','wb'))
print(cls)
