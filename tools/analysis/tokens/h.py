import re
from config import COF_DIR as D
for fn in ['JAN13','JUN15','MAR20']:
    t=open(D+fn+'.txt',encoding='latin-1').read().replace('\r','').split('\n')
    out=[]
    for i,l in enumerate(t):
        if l and '\t' not in l.strip('\t') and not l.startswith('PAGE') and re.search(r'^(COMICS|PREMIER|MERCH|BOOKS|MAGAZ|PREVIEWS PUB|APPAREL|TOYS|GAMES|COLLECTIBLES|FEATURED|ADULT)',l.strip()): out.append((i,l.strip()))
    print(fn,out)
