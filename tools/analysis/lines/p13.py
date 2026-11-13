exec(open('/private/tmp/claude-501/-Volumes-U34-Bolt-Personal-development-github-vibe-preview-parsing/961fccd7-e904-460f-abf8-159486acec47/scratchpad/lines/common.py').read())
from collections import Counter
agree=Counter();dis=[];tot=0;solshape=Counter();solcol=Counter()
for y,m,f in files():
    L=open(D+f,'rb').read().decode('utf-8').split('\r\n')
    for i,l in enumerate(L,1):
        fl=l.split('\t')
        A=l.count('\t')>=2
        B=sum(1 for x in fl if x.strip())>=3
        sol=fl[1].strip() if len(fl)>1 else ''
        C=sol!=''
        Cs=bool(re.fullmatch(r'[A-Z]{3}\d\d \d{4}',sol))
        if A: solshape[(Cs,)]+=1
        key=(A,B,C,Cs)
        agree[key]+=1
        if len({A,B,C})>1 or (A and not Cs): 
            dis.append((f,i,key,l[:120]))
print('A=>=2tabs,B=>=3 nonempty fields,C=nonempty col1,Cs=col1 matches AAA99 9999')
print(agree)
print(len(dis))
c2=Counter((k) for _,_,k,_ in dis);print(c2)
for k in c2:
    print(k,[d for d in dis if d[2]==k][:3])
