from common import *
import difflib
a=open(D+'JAN09_original_txt','rb').read();b=open(D+'JAN09.txt','rb').read()
print('JAN09: orig is prefix of txt?',b.startswith(a[:-3]), 'orig tail',a[-12:],'txt at that point',b[len(a)-3:len(a)+12], 'extra bytes', len(b)-len(a))
print('lines orig',a.count(b'\r\n'),'txt',b.count(b'\r\n'))
a=open(D+'DEC15_original_txt','rb').read();b=open(D+'DEC15.txt','rb').read()
print('DEC15 starts BOM',a[:3]==b'\xef\xbb\xbf','rest identical',a[3:]==b, len(a),len(b))
a=open(D+'JUN17_original_txt','rb').read();b=open(D+'JUN17.txt','rb').read()
print('JUN17 head',a[:4]); t=a.decode('utf-16')
print('BOM char',repr(t[:1]))
ta=t.lstrip('﻿');tb=b.decode('utf-8')
print('identical after decode',ta==tb,len(ta),len(tb))
la=ta.split('\r\n');lb=tb.split('\r\n')
print(len(la),len(lb))
d=[x for x in difflib.unified_diff(la,lb,lineterm='',n=0)]
print(len(d));print([x[:140] for x in d[:40]])
