exec(open('/private/tmp/claude-501/-Volumes-U34-Bolt-Personal-development-github-vibe-preview-parsing/961fccd7-e904-460f-abf8-159486acec47/scratchpad/lines/common.py').read())
import difflib,filecmp
from collections import Counter
fs={f[:5]:f for _,_,f in files()}
cnt=Counter();rem=[]
def norm(t):
    L=t.split('\r\n')
    L=[l.rstrip() for l in L]   # strip trailing ws/tabs
    L=[l for l in L if l and not re.match(r'PREVIEWS (\w+ (VOL\.? |V)\d+ #\d+|ORDER FORM)$',l) and not re.fullmatch(r'\w+ V\d+ #\d+',l)]
    return L
ids=Counter()
for f in sorted(os.listdir(O)):
    mm=re.fullmatch(r'([A-Z]{3}\d\d)_COF\.txt',f)
    if not mm: continue
    ob=open(O+f,'rb').read();nb=open(D+fs[mm[1]],'rb').read()
    o=ob.decode('cp1252',errors='replace');n=nb.decode('utf-8')
    if '�' in o: cnt['old has undecodable cp1252']+=1
    a=norm(o);b=norm(n)
    if a==b: cnt['equal after: cp1252->utf8, strip trailing ws, drop ident+blank']+=1
    else:
        cnt['still differ']+=1
        for t,i1,i2,j1,j2 in difflib.SequenceMatcher(None,a,b,autojunk=False).get_opcodes():
            if t!='equal': rem.append((mm[1],a[i1:i2][:2],b[j1:j2][:2]))
    # blank/ws
    ol=ob.split(b'\r\n');nl=nb.split(b'\r\n')
    ids['trailing-ws old items w/o final tab']+=sum(1 for l in ol if l.count(b'\t')>=5 and not l.endswith(b'\t'))
    ids['same line count']+= (len(ol)==len(nl))
print(cnt,ids);print(rem[:20])
# whitespace-only diffs between files (strict)
import subprocess
d1=O+'originals/Archive 2/'
same=sum(1 for f in os.listdir(d1) if os.path.exists(O+f) and open(d1+f,'rb').read()==open(O+f,'rb').read())
print('originals/Archive 2 identical to main old files:',same,'of',len(os.listdir(d1)))
