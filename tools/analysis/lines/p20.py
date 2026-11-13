from common import *
from collections import Counter
d1=O+'originals/Archive 2/';c=Counter()
for f in sorted(os.listdir(d1)):
    a=open(d1+f,'rb').read();b=open(O+f,'rb').read()
    k=('crlf' if a.count(b'\r\n')==a.count(b'\n') else 'lf-or-mixed', 'ws-lines-eq' if [l.rstrip() for l in a.decode('latin-1').splitlines()]==[l.rstrip() for l in b.decode('latin-1').splitlines()] else 'content-diff')
    c[k]+=1
    if k[1]=='content-diff' and c[k]<4:
        import difflib
        x=a.decode('latin-1').splitlines();y=b.decode('latin-1').splitlines()
        print(f,len(x),len(y),[l[:80] for l in list(difflib.unified_diff(x,y,lineterm='',n=0))[:8]])
print(c)
