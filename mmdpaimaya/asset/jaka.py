# -*- coding: utf-8 -*-
'''
pykakasiとjaconvで日本語をロマジに変換する関数
'''

import re
from pykakasi import kakasi
from jaconv import h2z as hanzen, z2h as zenhan

kakasi = kakasi()
kakasi.setMode('H','a')
kakasi.setMode('K','a')
kakasi.setMode('J','a')
kakasi.setMode('E','a')
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
        x = '_'+x[1:]
    x = re.sub('[一-龥]','_',x)
    x = re.sub('[ก-๙]','_',x)
    x = re.sub(r'\W','_',x)
    return x
