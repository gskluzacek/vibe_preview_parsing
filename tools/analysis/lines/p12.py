exec(open('/private/tmp/claude-501/-Volumes-U34-Bolt-Personal-development-github-vibe-preview-parsing/961fccd7-e904-460f-abf8-159486acec47/scratchpad/lines/common.py').read())
from collections import Counter
for f in ['MAY14.txt','SEP16.txt','DEC16.txt','MAY17.txt','SEP17.txt']:
    L=open(D+f,'rb').read().decode('utf-8','replace').split('\r\n')
    for i,l in enumerate(L):
        if re.fullmatch(r'\d+\t*',l) and i<len(L)-8: print(f,i+1,[x[:50] for x in L[i-1:i+2]])
# non-ascii
ch=Counter();wh={}
for y,m,f in files():
    t=open(D+f,'rb').read().decode('utf-8')   # strict utf-8 check
    for i,l in enumerate(t.split('\r\n'),1):
        for c in l:
            if ord(c)>127: ch[c]+=1; wh.setdefault(c,[]).append((f,i,l[:90]))
print(ch)
for c,v in wh.items(): print(repr(c),hex(ord(c)),len(v),len({a for a,b,d in v}),'files',v[:2])
