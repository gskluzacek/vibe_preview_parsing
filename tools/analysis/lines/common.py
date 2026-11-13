import os,re,glob
D='/Volumes/U34-Bolt/Personal/development/github/previews_parsing/cof_files/'
O='/Volumes/U34-Bolt/Personal/development/github/previews/old_code/Preview Parsing/previews parsing/'
M=['JAN','FEB','MAR','APR','MAY','JUN','JUL','AUG','SEP','OCT','NOV','DEC']
def files():
    r=[]
    for f in sorted(os.listdir(D)):
        m=re.fullmatch(r'([A-Z]{3})(\d\d)\.txt',f)
        if m: r.append((int(m[2])+(2000 if int(m[2])<80 else 1900),M.index(m[1])+1,f))
    return sorted(r)
