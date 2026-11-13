exec(open('/private/tmp/claude-501/-Volumes-U34-Bolt-Personal-development-github-vibe-preview-parsing/961fccd7-e904-460f-abf8-159486acec47/scratchpad/lines/common.py').read())
from collections import Counter
d1=O+'originals/Archive 2/';fs={f[:5]:f for _,_,f in files()};c=Counter();ex=[]
for f in sorted(os.listdir(d1)):
    a=open(d1+f,'rb').read();b=open(D+fs[f[:5]],'rb').read()
    if a==b: c['byte-identical']+=1
    elif a.decode('cp1252','replace')==b.decode('utf-8'): c['identical after cp1252->utf8']+=1
    else:
        c['other']+=1; ex.append(f)
print(c,ex)
