import pickle,re,random
r=pickle.load(open('rows.pkl','rb'))
random.seed(11)
P=[x for x in r if x[4] in('premier','comicsblk')]
pats=[r'INCV|COPY',r'\bPT \d+',r'#\d+ \(OF \d+\) [A-Z]+ [A-Z]+ [A-Z]+',r'#\d+-\d+|#\d+ & #',r'\bDF\b.*SGN',r'\bVOL \d+ #\d+',r'\bSUB(SCRIPTION)? VAR',r'\bVAR\b.*\bVAR\b|\bCVR\b.*\bCVR\b',r'[A-Z]+ [A-Z]+ #\d+ [A-Z]+ [A-Z]+ [A-Z]+ [A-Z]+',r'\b[A-Z]{1,3}\d?\b ED\b|\bPREM HC\b',r'HC .* HC|TP .* TP|GN .* GN',r'\bWRAP CVR|\bMAIN CVR|\bCONNECTING VAR']
for p in pats:
    c=[x[3] for x in P if re.search(p,x[3])]
    print(p,len(c)); [print('   ',t) for t in random.sample(c,2)]
