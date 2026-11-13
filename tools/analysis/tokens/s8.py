import pickle,re,collections
r=pickle.load(open('rows.pkl','rb'))
cands={'CVR':r'\bCVR\b','VAR':r'\bVAR\b','CVR A':r'\bCVR A\b','CVR B':r'\bCVR B\b','CVR C':r'\bCVR C\b','CVR D':r'\bCVR D\b','CVR E':r'\bCVR E\b','CVR F':r'\bCVR F\b','CVR G+':r'\bCVR [G-Z]\b','COVER A':r'\bCOVER [A-Z]\b','REG CVR':r'\bREG CVR\b','MAIN CVR':r'\bMAIN CVR\b','WRAP CVR':r'\bWRAP CVR\b','SUBSCRIPTION VAR':r'\bSUBSCRIPTION VAR\b','CONNECTING VAR':r'\bCONNECTING VAR\b','VAR ED':r'\bVAR ED\b','INCV':r'\bINCV\b','1:nn ratio':r'\b1:\d+\b','COPY INCV':r'\bCOPY\b','PX':r'\bPX\b','DF':r'\bDF\b','NEWSSTAND':r'\bNEWSSTAND\b','POLYBAGGED':r'\bPOLYBAG','(2016)-style year':r'\(20\d\d\)','(N52)':r'\(N52\)','(REBIRTH)':r'\(REBIRTH\)','(NEW ARC)':r'\(NEW ARC\)','(CURR PTG)':r'\(CURR PTG\)','CURR PTG bare':r'\bCURR PTG\b','NEW PTG':r'\bNEW PTG\b','(NOTE PRICE)':r'\(NOTE PRICE\)','(OSW)':r'\(OSW\)','(PD)':r'\(PD\)','(O/A)':r'\(O/A\)','(RES)':r'\(RES\)','(Net)':r'\(Net\)','(ONGOING)':r'\(ONGOING\)','(STAR#)':r'\(STAR\d+\)','(MR)':r'\(MR\)','(A)':r'\(A\)','5TH+ PTG':r'\b(?:[5-9]|1\d)TH PTG','2ND PTG':r'\b2ND PTG','2ND PRINTING':r'\b2ND PRINTING','ONE-SHOT':r'ONE-SHOT','(ONE SHOT)':r'\(ONE SHOT\)','#decimal':r'#\d+\.\d+','#range':r'#\d+-\d+','#&':r'#\w+ & #\w+','( OF n) stray space':r'\( OF','(OF n)':r'\(OF \d','BUNDLE OF':r'BUNDLE OF','(nnCT)':r'\(\d+ ?CT\)','(PT n)':r'\(PT \d','PT n paren-text':r'\([^()]+ PT \d+\)','BAG SET':r'BAG SET','PREORDER ED':r'PRE-?ORDER','B&W':r'\bB&W\b','(JUL######)':r'\([A-Z]{3}\d{6}\)','C: nn-n-n 2digit':r'\(C: \d\d?-\d-\d\d\)','(C: with other fmt)':r'\(C:(?! \d-\d-\d\))','T/S':r'\bT/S\b','HC':r'\bHC\b','TP':r'\bTP\b','TPB':r'\bTPB\b','GN':r'\bGN\b','OMNIBUS':r'\bOMNIBUS\b','SGN':r'\bSGN\b','LTD ED':r'\bLTD ED\b','SP ED':r'\bSP ED\b','PX ED':r'\bPX ED\b','SDCC':r'\bSDCC\b','NYCC':r'\bNYCC\b','C2E2':r'\bC2E2\b','ECCC':r'\bECCC\b','WW':r'\bWW\b','PREM HC':r'\bPREM HC\b','DLX':r'\bDLX\b','AF':r'\bAF\b','FIG':r'\bFIG\b','STATUE':r'\bSTATUE\b','BMB':r'\bBMB\b','Metadata hash#':r'#\w*[A-Z]\w*'}
out=[]
for k,p in cands.items():
    rx=re.compile(p); f=None;c=0;lastm=None
    for x in r:
        if rx.search(x[3]):
            c+=1
            if f is None: f=(x[0],x[1],x[3])
            lastm=(x[0],x[1])
    out.append((k,c,f,lastm))
for k,c,f,l in out: print(k,c,f and f'{f[0]}-{f[1]:02d}',l and f'last {l[0]}-{l[1]:02d}',(f[2] if f else ''))
