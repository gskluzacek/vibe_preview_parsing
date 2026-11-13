import json,collections
r=json.load(open('hdg_lvls.json'))
by={x[0]:x for x in r}
print(collections.Counter(x[1] for x in r), len(set(x[0] for x in r)))
print('pull',sum(x[3] for x in r))
print('L1',[x[4] for x in r if x[1]==1])
# parent level check
bad=[x for x in r if x[2] and by[x[2]][1]!=x[1]-1]; print('parent lvl mismatch',len(bad))
print('L1 with parent',sum(1 for x in r if x[1]==1 and x[2]))
import random;random.seed(1)
for L in(2,3):
    s=[x for x in r if x[1]==L]; print(L,[ (x[4],by[x[2]][4]) for x in random.sample(s,12)])
names=collections.defaultdict(list)
for x in r: names[x[4]].append((x[1],x[2]))
d={k:v for k,v in names.items() if len(v)>1}
print('dup names',len(d),list(d.items())[:15])
print('L1 children',collections.Counter(by[x[2]][4] for x in r if x[2] and x[1]==2))
print('L3 under L2->L1',collections.Counter(by[by[x[2]][2]][4] for x in r if x[1]==3))
