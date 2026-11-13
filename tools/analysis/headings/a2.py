import config
import pickle,collections,json,csv,re
files,out=pickle.load(open('rec.pkl','rb'))
r=json.load(open('hdg_lvls.json'))
dl=collections.defaultdict(set)
for x in r: dl[x[4]].add(x[1])
ex=list(csv.reader(open(config.HEADING_EXTRACT,encoding='utf-8'),delimiter='\t',quoting=csv.QUOTE_NONE))
hdr=ex[0];ex=[dict(zip(hdr,x)) for x in ex[1:]]
print(len(ex),collections.Counter(e['file_name'] for e in ex),collections.Counter(e['hdg_lvl'] for e in ex))
print('dup_pvl_id nonempty',sum(1 for e in ex if e['dup_pvl_id']), 'pg range',min(int(e['pg_nbr']) for e in ex),max(int(e['pg_nbr']) for e in ex))
print('indent consistent with lvl',collections.Counter((e['hdg_lvl'],len(e['indent'])-len(e['indent'].lstrip('-'))) for e in ex))
print([ (e['dup_pvl_id'],e['line_text'],e['hdg_lvl']) for e in ex if e['dup_pvl_id']][:8])
# vs JAN09 file
jan=[s for k,s in out['JAN09.txt'] if k=='HDG']
et=[e['line_text'].strip() for e in ex]
print('JAN09 hdg lines',len(jan),'extract rows',len(et),'seq equal',jan==et)
import difflib
sm=difflib.SequenceMatcher(None,jan,et,autojunk=False)
for tag,i1,i2,j1,j2 in sm.get_opcodes():
    if tag!='equal':print(tag,jan[i1:i2][:4],et[j1:j2][:4])
# compare to dump
agree=dis=miss=0;ex_dis=[];ex_miss=[]
amb=0
for e in ex:
    n=e['line_text'].strip().strip('"');
    if not e['hdg_lvl']: continue
    l=int(e['hdg_lvl'])
    if n not in dl: miss+=1;ex_miss.append((n,l));continue
    if l in dl[n]: agree+=1
    else: dis+=1;ex_dis.append((n,l,sorted(dl[n])))
    if len(dl[n])>1: amb+=1
print('agree',agree,'disagree',dis,'name not in dump',miss,'ambig names',amb)
print(ex_dis[:20]);print(ex_miss[:30])
# distinct
names=set(e['line_text'].strip() for e in ex); print('distinct extract names',len(names))
# all JAN09 hdgs vs dump names
print('JAN09 distinct',len(set(jan)),'in dump',len(set(jan)&set(dl)))
# all-corpus headings in dump
allh=collections.Counter(s for f in files for k,s in out[f] if k=='HDG')
inn=sum(1 for s in allh if s in dl);print('corpus distinct',len(allh),'in dump',inn,'occ coverage',sum(v for s,v in allh.items() if s in dl)/sum(allh.values()))
print('dump names never in corpus',len([n for n in dl if n not in allh]))
# 2009-2014 only (dump era)
allh14=collections.Counter(s for f in files if int(f[3:5])<=14 for k,s in out[f] if k=='HDG')
print('<=2014 distinct',len(allh14),'in dump',sum(1 for s in allh14 if s in dl))
print([s for s in allh14 if s not in dl][:30])
