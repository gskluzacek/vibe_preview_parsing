import pickle,re,random,collections
r=pickle.load(open('rows.pkl','rb'))
random.seed(7)
P=[x for x in r if x[4] in('premier','comicsblk')]
META=r'\((?:C: \d-\d-\d|MR|A|O/A|RES|Net|NOTE PRICE|[A-Z]{3}\d{6}|STAR\d+| ?OF \d+)\)'
def strip(t): return re.sub(r'\s+',' ',re.sub(META,'',t)).strip()
groups={
 'issue+words after (artist/variant/subtitle mix)':lambda t:re.search(r'#\d+ (?!\(|CVR|VAR)[A-Z]+ [A-Z]+ [A-Z]+',strip(t)) and 'CVR' not in t,
 'CVR with name before and after':lambda t:re.search(r'#\d+ [A-Z]+ [A-Z]+ (CVR|VAR) [A-Z]',t),
 'volume with subtitle':lambda t:re.search(r'(TP|GN|HC) VOL \d+ [A-Z]+ [A-Z]+ [A-Z]+ [A-Z]+',strip(t)),
 'non-meta paren group':lambda t:re.search(r'\((?!C: |MR\)|A\)|O/A|RES|Net|NOTE|[A-Z]{3}\d{6}|STAR|OF)[A-Z ]+\)',t) and '#' in t,
 'no marker long':lambda t:not re.search(r'#|VOL|\b(TP|GN|HC|SC|ONE SHOT)\b',t) and len(strip(t))>45,
 'multi edition/variant tokens':lambda t:re.search(r'#\d+.*(VAR|CVR).*(ED|SGN|PTG)',t),
 'title with digits/by':lambda t:re.search(r'\bBY [A-Z]+ [A-Z]+',t) and '#' in t,
}
out=[]
for g,f in groups.items():
    c=[x for x in P if f(x[3])]
    print('##',g,len(c))
    for x in random.sample(c,4 if g!='non-meta paren group' else 4): out.append(x[3]); print(x[0],x[3])
