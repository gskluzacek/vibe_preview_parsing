exec(open('/private/tmp/claude-501/-Volumes-U34-Bolt-Personal-development-github-vibe-preview-parsing/961fccd7-e904-460f-abf8-159486acec47/scratchpad/lines/common.py').read())
from collections import Counter
prev=None
for y,m,f in files():
    t=open(D+f,'rb').read().decode('utf-8',errors='replace')
    L=t.split('\r\n')
    c=Counter(l.count('\t') for l in L)
    # endings
    it=[l for l in L if l.count('\t')>=5]
    e=Counter(('endTab' if l.endswith('\t') else 'noEndTab') for l in it)
    h=Counter(('padhead' if (l.count('\t')==5 and l.endswith('\t\t\t\t\t')) else '') for l in L)
    nb=sum(1 for l in L if l.strip()=='' and l!='')  # whitespace-only
    sp=sum(1 for l in L if l!=l.rstrip() and l.count('\t')==0 and l.strip()!='')
    dts=Counter('mm/dd/yy' if re.search(r'\t\d\d/\d\d/\d\d\t',l) else 'other/none' if '\t' in l else '' for l in it)
    sig=(tuple(sorted(c.items())), tuple(sorted(e.items())))
    print(f, dict(sorted(c.items())), dict(e), 'padheads',h['padhead'],'wsonly',nb,'txt-trailing-sp',sp, dict(dts))
