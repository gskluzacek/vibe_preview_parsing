import re,glob,os,pickle,collections
D='/Volumes/U34-Bolt/Personal/development/github/previews_parsing/cof_files/'
MON='JAN FEB MAR APR MAY JUN JUL AUG SEP OCT NOV DEC'.split()
def ym(fn):
    b=os.path.basename(fn)[:-4]; return (1900+int(b[3:]) if int(b[3:])>50 else 2000+int(b[3:]), MON.index(b[:3])+1)
rows=[];heads=collections.Counter()
for fn in sorted(glob.glob(D+'*.txt'),key=ym):
    y,m=ym(fn)
    sec=[];scope='pre'
    for ln in open(fn,encoding='latin-1',newline='').read().split('\n'):
        ln=ln.rstrip('\r')
        f=ln.split('\t')
        code=None
        for i,x in enumerate(f[:3]):
            if re.fullmatch(r'[A-Z]{3}\d\d \d{4}',x): code=i;break
        if code is None:
            h=ln.strip()
            if h and not h.startswith('PAGE '):
                heads[h]+=1; sec.append(h)
                if h=='PREMIER PUBLISHERS': scope='premier'
                elif scope=='premier' and h.startswith('COMICS'): scope='comicsblk'
                elif scope in('comicsblk',) and re.match(r'(APPAREL|TOYS|TRADING CARDS|COLLECTIBLES|GAMES$|PREMIERE COLL|POP CULTURE)',h): scope='other'
                elif scope=='pre' and h=='PREVIEWS PUBLICATIONS': pass
            continue
        txt=''
        for x in f[code+1:]:
            if x.strip(): txt=x;break
        rows.append((y,m,f[code],txt,scope,f[:code]))
pickle.dump(rows,open('rows.pkl','wb'))
print(len(rows))
print(heads.most_common(0))
