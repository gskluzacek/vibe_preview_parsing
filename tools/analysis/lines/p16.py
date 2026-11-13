from common import *
import difflib
a=open(D+'JAN09_original_txt','rb').read().decode('latin-1').split('\r\n');b=open(D+'JAN09.txt','rb').read().decode('utf-8').split('\r\n')
print(len(a),len(b))
for x in difflib.unified_diff(a,b,lineterm='',n=0): print(repr(x))
print([ (i,l) for i,l in enumerate(a,1) if any(ord(c)>127 for c in l)])
