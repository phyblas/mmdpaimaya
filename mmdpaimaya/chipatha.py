# -*- coding: utf-8 -*-
import re
from pykakasi import kakasi
from jctconv import h2z as hanzen, z2h as zenhan

# แก้ชื่อพยายามถอดยูนิโค้ดชนิดต่างๆเท่าท่จะทำได้
def chuedidi(s,f=u''):
    if(s==u''): return f
    try: return unicode(s)
    except:
        try: return unicode(s,'shift-jis')
        except:
            try: return unicode(s,sys.getdefaultencoding())
            except:
                try: return unicode(s,sys.getfilesystemencoding())
                except:
                    try: return unicode(s,'utf-8')
                    except:
                        return f

# แปลงชื่อภาษาญี่ปุ่นเป็นโรมาจิ
kakasi = kakasi()
kakasi.setMode('H','a'),kakasi.setMode('K','a'),kakasi.setMode('J','a'),kakasi.setMode('E','a')
kakasi = kakasi.getConverter().do
kazu = ['rei','ichi','ni','san','shi','go','roku','shichi','hachi','kyuu']

def romaji(x):
    x = hanzen(x,kana=1,digit=0,ascii=0)
    x = zenhan(x,kana=0,digit=1,ascii=1)
    x = kakasi(x)
    x = re.sub(r'(\S)-',r'\1\1',x)
    try:
        if(x[0] in '0123456789'):
            x = kazu[int(x[0])]+x[1:]
    except:
        x = 'jianx'
    return re.sub(r'\W','_',x)

# คำนวณค่าครอสเว็กเตอร์
def cross(a,b):
    c = [a[1]*b[2]-a[1]*b[1],
         a[2]*b[0]-a[2]*b[2],
         a[0]*b[1]-a[0]*b[0]]
    return c