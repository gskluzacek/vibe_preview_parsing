from common import *
import difflib
from collections import Counter
fs={f[:5]:f for _,_,f in files()}
cls=Counter();allh=[]
for f in sorted(os.listdir(O)):
    mm=re.fullmatch(r'([A-Z]{3}\d\d)_COF\.txt',f)
    if not mm: continue
    ob=open(O+f,'rb').read();nb=open(D+fs[mm[1]],'rb').read()
    ols=ob.decode('latin-1').split('\r\n');nls=nb.decode('latin-1').split('\r\n')
    sm=difflib.SequenceMatcher(None,ols,nls,autojunk=False)
    for t,i1,i2,j1,j2 in sm.get_opcodes():
        if t=='equal':continue
        o=ols[i1:i2];n=nls[j1:j2]
        allh.append((mm[1],i1+1,o,n))
for h in allh: print(h[0],h[1],[x[:90] for x in h[2]],'=>',[x[:90] for x in h[3]])
