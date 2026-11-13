import pickle,re,collections as C
items=pickle.load(open('items.pkl','rb'))
std={'','SS','SPOT','OA','FI','KIDS','GEM','OA SS','OA FI','SS KIDS','OA SPOT','OA KIDS','SS SPOT'}
odd=[x for x in items if x[4][0] not in std]
print(len(odd),C.Counter(x[0] for x in odd))
for x in odd[:6]+odd[-3:]: print(x[0],x[1],repr(x[4])[:230])
# those with non-std flag and dated?
print(C.Counter((x[3],bool(x[4][3])) for x in odd))
print(C.Counter(x[4][1][:3] if re.match(r'[A-Z]{3}\d\d \d{4}$',x[4][1]) else 'BAD' for x in odd))
