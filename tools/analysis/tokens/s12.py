import pickle,re,collections
r=pickle.load(open('rows.pkl','rb'))
T=[x[3] for x in r]
def cnt(p): 
    rx=re.compile(p); return sum(1 for t in T if rx.search(t))
pats=['\\bCOLL\\b','\\bCOLL ED\\b','COLLECTED EDITION','HC W/ DUST JACKET','DUST JACKET','OMNIBUS TP VOL','\\bPKT\\b','VOL (ONE|TWO|THREE)\\b','VOL \\d+ #\\d+','\\bSGN\\b','LTD ED','SP ED','PX ED','NYCC 2009 EX','NYCC \\d{4} EX','SDCC ED','GOLD ED','US ED','UK ED','AUXILIARY ED','AUXILIARY CVR','AUXILIARY','FIRST LOOK ED','PULP EDITION OMEGA','EXPANDED REG ED','COMPLETE TPB COLLECTION','SPANISH ED','30TH ANN','\\bANNUAL\\b','CHRISTMAS SP','HOLIDAYS SPECIAL','SERIES SPECIAL','\\bSPECIAL\\b','DIRECTORS CUT','DOUBLE-SIZED','\\bNUDE\\b','DOUBLE DIGEST','COMPLETE BAG SET','BAG SET','REG CVR','CVR A','COVER A','VAR CVR','GATEFOLD CVR','SKETCH VAR CVR','DIRECT MARKET CVR','DIREC MARKET CVR','\\bW/ SKETCH','\\bCGC\\b','\\bNEWSSTAND\\b','\\bGN VOL \\d+','\\bTP VOL \\d+','\\bONE SHOT #\\d','#\\d+ ONE SHOT','\\bONE SHOT\\b','ONE-SHOT','\\(ONE SHOT\\)','\\bTPB\\b','\\bSC VOL','HC VOL','\\bC/O\\b','\\(NET\\)','\\bNOW\\b','\\bCOMBO PACK','\\bCOMPLETE SET','\\bCOVER SET','\\bCVR SET','\\bSET\\b','\\bBUNDLE\\b','\\bPACK\\b','\\bW/ ','\\bSE\\b','\\bEXC\\b','\\bEX\\b','\\bPOSTER\\b','\\bDVD\\b','\\bBLU-RAY\\b']
for p in pats: print(cnt(p),'\t',p)
# OSW with ONE SHOT
print('OSW with ONE SHOT',sum(1 for t in T if '(OSW)' in t and 'ONE SHOT' in t))
print('(ONGOING) before #',sum(1 for t in T if re.search(r'\(ONGOING\) #',t)))
print('ONGOING w/o parens',cnt(r'(?<!\()ONGOING(?!\))'))
# net vs price field
import glob
# reload price field
from config import COF_DIR as D
pf=collections.Counter()
for fn in glob.glob(D+'*.txt'):
    for ln in open(fn,encoding='latin-1'):
        f=ln.rstrip('\r\n').split('\t')
        for i,x in enumerate(f[:3]):
            if re.fullmatch(r'[A-Z]{3}\d\d \d{4}',x):
                txt=[y for y in f[i+1:] if y.strip()]
                if len(txt)>=3:
                    net='(Net)' in txt[0]
                    pf[(net,re.sub(r'[\d.,]+','n',txt[2])[:12])]+=1
                break
for k,v in sorted(pf.items(),key=lambda a:-a[1])[:14]: print(k,v)
