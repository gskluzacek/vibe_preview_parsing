exec(open('/private/tmp/claude-501/-Volumes-U34-Bolt-Personal-development-github-vibe-preview-parsing/961fccd7-e904-460f-abf8-159486acec47/scratchpad/lines/common.py').read())
from collections import Counter,defaultdict
g=defaultdict(list)
for y,m,f in files():
    L=open(D+f,'rb').read().decode('utf-8','replace').split('\r\n')
    # find first non-blank lines up to first PAGE
    pre=[]
    for i,l in enumerate(L):
        if re.match(r'PAGE\b',l): first=i;break
        pre.append(l)
    nb=[l.rstrip('\t') for l in pre if l.strip()]
    key=re.sub(r'\d+','N',' | '.join(nb)) 
    print(f,'firstPAGE@',first+1,'blankbefore',len(pre)-len(nb),nb[:4], L[first])
