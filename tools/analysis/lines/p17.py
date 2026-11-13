from common import *
import difflib,hashlib
print(open(D+'JAN09_original_txt','rb').read().split(b'\r\n')[5488])
fs={f[:5]:f for _,_,f in files()}
res=[]
from collections import Counter
cat=Counter()
for f in sorted(os.listdir(O)):
    mm=re.fullmatch(r'([A-Z]{3}\d\d)_COF\.txt',f)
    if not mm: continue
    k=mm[1]
    new=fs.get(k) 
    ob=open(O+f,'rb').read()
    if not new: print('no counterpart',f);continue
    nb=open(D+new,'rb').read()
    if ob==nb: c='identical';
    else:
        def n(b): return b.decode('latin-1' if False else 'utf-8','replace')
        ot=ob.decode('utf-8','replace');nt=nb.decode('utf-8','replace')
        eol=lambda s:s.replace('\r\n','\n').replace('\r','\n')
        if eol(ot)==eol(nt): c='eol-only'
        else:
            w=lambda s:'\n'.join(' '.join(l.split()) for l in eol(s).split('\n')).strip()
            if w(ot)==w(nt): c='whitespace-only'
            else:
                c='content'
    cat[c]+=1
    L1=ob.count(b'\r\n');L2=nb.count(b'\r\n');
    ols=ot=ob.decode('utf-8','replace').replace('\r\n','\n').split('\n'); nls=nb.decode('utf-8','replace').replace('\r\n','\n').split('\n')
    info=''
    if c!='identical':
        sm=difflib.SequenceMatcher(None,ols,nls,autojunk=False)
        ops=[(t,i2-i1,j2-j1) for t,i1,i2,j1,j2 in sm.get_opcodes() if t!='equal']
        info=(len(ob),len(nb),'old crlf/lf',ob.count(b'\r\n'),ob.count(b'\n')-ob.count(b'\r\n'),'ops',len(ops),'dellines',sum(o[1] for o in ops),'addlines',sum(o[2] for o in ops))
    print(f,c,info)
print(cat)
