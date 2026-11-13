import pickle,collections,statistics
r=pickle.load(open('rows.pkl','rb'))
T=[x[3] for x in r]
print('items',len(T),'distinct',len(set(T)))
L=sorted(len(t) for t in T)
print('len min/med/mean/p90/p99/max',L[0],statistics.median(L),round(statistics.mean(L),1),L[int(.9*len(L))],L[int(.99*len(L))],L[-1])
import itertools
hist=collections.Counter(min(l//10*10,100) for l in L); print(sorted(hist.items()))
c=collections.Counter(''.join(T))
print('lower',sum(1 for t in T if any(ch.islower() for ch in t)))
print('nonascii',sum(1 for t in T if any(ord(ch)>127 for ch in t)),[ (ch,n) for ch,n in c.items() if ord(ch)>127][:20])
print('punct',[(ch,n) for ch,n in c.most_common() if not ch.isalnum() and ch!=' '])
print('digits',sum(n for ch,n in c.items() if ch.isdigit()))
print('lead/trail space',sum(1 for t in T if t!=t.strip()),'double space',sum(1 for t in T if '  ' in t))
print('lowercase examples',[t for t in T if any(ch.islower() for ch in t)][:5])
print([t for t in T if any(ord(ch)>127 for ch in t)][:5])
