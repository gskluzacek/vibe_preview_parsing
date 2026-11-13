exec(open('/private/tmp/claude-501/-Volumes-U34-Bolt-Personal-development-github-vibe-preview-parsing/961fccd7-e904-460f-abf8-159486acec47/scratchpad/lines/common.py').read())
from collections import Counter,defaultdict
forms=Counter();ex=defaultdict(list);fp=Counter();res=[]
dec=[];dups=Counter();padp=Counter();after=[];pg_in_item=[];nonstart=[]
for y,m,f in files():
    L=open(D+f,'rb').read().decode('utf-8','replace').split('\r\n')
    nums=[];first=None;lastpage=None
    for i,l in enumerate(L,1):
        s=l.rstrip('\t')
        if l.count('\t')>=2 and re.search(r'\bPAGE\b',l): pg_in_item.append((f,i,l[:100]))
        if l.count('\t')<2 and re.search(r'PAGE',l) and not l.startswith('PAGE'): nonstart.append((f,i,l))
        if l.startswith('PAGE') and l.count('\t')<2 or l.startswith('PAGE'):
            k='PAGE n' if re.fullmatch(r'PAGE \d+',s) else 'PAGE M-n' if re.fullmatch(r'PAGE \d+-\d+',s) else 'OTHER'
            if k=='PAGE n' and s!=l: padp[f]+=1
            forms[k]+=1
            if len(ex[k])<4: ex[k].append((f,i,l))
            if k=='OTHER': continue
            n=int(re.findall(r'\d+',s)[-1])
            if first is None: first=(i,n)
            if nums and n<nums[-1]: dec.append((f,i,nums[-1],n))
            if nums and n==nums[-1]: dups[f]+=1
            nums.append(n); lastpage=i
    nonblank_after=[l for l in L[lastpage:] if l.strip()] if lastpage else []
    res.append((f,first,len(nums),nums[-1],len([1 for l in L[:first[0]-1] if l.strip()])))
print(forms);print(dict(ex));print('padded PAGE lines files',dict(padp))
print('first-page line position dist',Counter(r[1][0] for r in res))
print('lines before first PAGE nonblank count dist',Counter(r[4] for r in res))
print('first page num dist',sorted(Counter(r[1][1] for r in res).items()))
print('decreasing',dec)
print('dups',dict(dups))
print('PAGE in item lines',pg_in_item[:5],len(pg_in_item))
print('PAGE non-start',nonstart[:10],len(nonstart))
for r in res: 
    if r[1][0]>5 or r[4]>1: print(r)
