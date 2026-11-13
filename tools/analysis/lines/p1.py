exec(open('/private/tmp/claude-501/-Volumes-U34-Bolt-Personal-development-github-vibe-preview-parsing/961fccd7-e904-460f-abf8-159486acec47/scratchpad/lines/common.py').read())
from collections import Counter,defaultdict
fs=files();print(len(fs))
tabs=defaultdict(Counter)
for y,m,f in fs:
    b=open(D+f,'rb').read()
    crlf=b.count(b'\r\n');lf=b.count(b'\n')-crlf;cr=b.count(b'\r')-crlf
    bom=b[:3]==b'\xef\xbb\xbf'
    na=Counter(c for c in b if c>127)
    endnl=b.endswith(b'\n')
    kind='CRLF' if lf==0 and cr==0 else 'LF' if crlf==0 and cr==0 else 'MIXED'
    ls=b.split(b'\n')
    tw=sum(1 for l in ls if re.search(rb'[ \t]+\r?$',l)); 
    print(f,kind,crlf,lf,cr,'BOM' if bom else '', dict(na) if na else '', 'endNL' if endnl else 'noEndNL','trail',tw, 'ctrl',[c for c in set(b) if c<32 and c not in(9,10,13)])
    for l in ls:
        l=l.rstrip(b'\r');tabs[y][l.count(b'\t')]+=1
for y in sorted(tabs):print(y,sorted(tabs[y].items()))
