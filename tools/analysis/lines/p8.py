from common import *
from collections import Counter,defaultdict
cat=Counter();ex=defaultdict(list);big=[]
for y,m,f in files():
    L=open(D+f,'rb').read().decode('utf-8','replace').split('\r\n')
    prev=None;pm=None;nrs=0
    seq=[];mseq=[]
    for i,l in enumerate(L,1):
        s=l.rstrip('\t')
        a=re.fullmatch(r'PAGE (\d+)',s);b=re.fullmatch(r'PAGE M-(\d+)',s)
        if a:
            n=int(a[1]);
            if prev is not None:
                if n==prev: k='dup'
                elif n<prev and n<=6: k='reset-to-main(<=6)'; nrs+=1
                elif n<prev: k='backward>6'
                elif n-prev>20: k='jump>20'
                else: k=None
                if k: cat[k]+=1;ex[k].append((f,i,prev,n))
            prev=n; seq.append((i,n))
        if b:
            n=int(b[1]);
            if pm is not None and n<=pm: cat['M-nonincr']+=1;ex['M-nonincr'].append((f,i,pm,n))
            if pm is not None and n-pm>10: cat['M-jump>10']+=1; ex['M-jump>10'].append((f,i,pm,n))
            pm=n
    if nrs!=1: print('resets',f,nrs)
print(cat)
for k,v in ex.items():
    if k!='reset-to-main(<=6)': print(k,v)
