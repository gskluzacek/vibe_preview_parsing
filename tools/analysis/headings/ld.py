import re,json,glob
D=glob.glob('/Volumes/U34-Bolt/Personal/development/github/previews/old_code/Preview*Parsing/previews*parsing/bipolar_2014_08_16.sql')[0]
rows=[];on=False;blocks=[]
with open(D,encoding='latin-1') as f:
    for n,l in enumerate(f,1):
        if n<286: continue
        if l.startswith('INSERT INTO `previews_hdg_lvls`'): on=True;continue
        if not on:
            if n>1200: break
            continue
        m=re.match(r"\((\d+), (\d+), (NULL|\d+), (NULL|'Y'), '((?:[^']|'')*)', '[^']*'\)([,;])",l)
        if not m: print('BAD',n,l[:60]);on=False;continue
        rows.append((int(m[1]),int(m[2]),None if m[3]=='NULL' else int(m[3]),m[4]!='NULL',m[5].replace("''","'")))
        if m[6]==';': on=False;blocks.append(n)
json.dump(rows,open('hdg_lvls.json','w'))
print(len(rows),blocks)
