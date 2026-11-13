exec(open('/private/tmp/claude-501/-Volumes-U34-Bolt-Personal-development-github-vibe-preview-parsing/961fccd7-e904-460f-abf8-159486acec47/scratchpad/lines/common.py').read())
for y,m,f in files():
    L=open(D+f,'rb').read().decode('utf-8').split('\r\n')
    for i,l in enumerate(L,1):
        fl=l.split('\t')
        if l.count('\t')>=2 and f not in('JAN13.txt','JUL13.txt') and not re.fullmatch(r'[A-Z]{3}\d\d \d{4}',fl[1].strip() if len(fl)>1 else ''):
            print(f,i,repr(l[:130]))
            if 'DO NOT' in l: print([x[:80] for x in L[i-3:i+2]])
# 7-tab (SEP15) lines
L=open(D+'SEP15.txt','rb').read().decode('utf-8').split('\r\n')
for i,l in enumerate(L,1):
    if l.count('\t')==7: print('SEP15',i,repr(l[:130]))
for f in ['JAN19.txt','JUL11.txt','MAR18.txt']:
  L=open(D+f,'rb').read().decode('utf-8').split('\r\n')
  for i,l in enumerate(L,1):
    if l.count('\t')==5 or (l.count('\t')>=5 and not l.endswith('\t')): print(f,i,repr(l[:130]))
