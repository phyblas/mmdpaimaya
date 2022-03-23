# -*- coding: utf-8 -*-
'''
Human IKに使うジョイントの名前の正規表現の辞書。
'''
import maya.cmds as mc
import math

dic_hik = {
    0: ['センター','.*sentaa'],
    1: ['下半身','kahanshin'],
    2: ['左足','hidariashi'],
    3: ['左膝','hidarihiza'],
    4: ['左足首','hidariashikubi'],
    5: ['右足','migiashi'],
    6: ['右膝','migihiza'],
    7: ['右足首','migiashikubi'],
    8: ['上半身','jouhanshin'],
    9: ['左腕','hidariude'],
    10: ['左肘','hidarihiji'],
    11: ['左手首','hidarite(kubi)?'],
    12: ['右腕','migiude'],
    13: ['右肘','migihiji'],
    14: ['右手首','migite(kubi)?'],
    15: ['頭','atama'],
    18: ['左肩','hidarikata'],
    19: ['右肩','migikata'],
    20: ['首','kubi'],
    23: ['上半身2','jouhanshin2'],
    45: ['左腕捩','hidariudemojiri'],
    46: ['左手捩','hidaritemojiri'],
    47: ['右腕捩','migiudemojiri'],
    48: ['右手捩','migitemojiri'],
    50: ['左親指0','hidarioyayubi0M?'],
    51: ['左親指1','hidarioyayubi1'],
    52: ['左親指2','hidarioyayubi2'],
    53: ['左親指先','hidarioyayubi.*saki'],
    54: ['左人差指1','hidari(hitosashi|nin)yubi1'],
    55: ['左人差指2','hidari(hitosashi|nin)yubi2'],
    56: ['左人差指3','hidari(hitosashi|nin)yubi3'],
    57: ['左人差指先','hidari(hitosashi|nin)yubi.*saki'],
    58: ['左中指1','(sachuu|hidarinaka)yubi1'],
    59: ['左中指2','(sachuu|hidarinaka)yubi2'],
    60: ['左中指3','(sachuu|hidarinaka)yubi3'],
    61: ['左中指先','(sachuu|hidarinaka)yubi.*saki'],
    62: ['左薬指1','hidarikusuriyubi1'],
    63: ['左薬指2','hidarikusuriyubi2'],
    64: ['左薬指3','hidarikusuriyubi3'],
    65: ['左薬指先','hidarikusuriyubi.*saki'],
    66: ['左小指1','hidarikoyubi1'],
    67: ['左小指2','hidarikoyubi2'],
    68: ['左小指3','hidarikoyubi3'],
    69: ['左小指先','hidarikoyubi.*saki'],
    74: ['右親指0','migioyayubi0M?'],
    75: ['右親指1','migioyayubi1'],
    76: ['右親指2','migioyayubi2'],
    77: ['右親指先','migioyayubi.*saki'],
    78: ['右人差指1','migi(hitosashi|nin)yubi1'],
    79: ['右人差指2','migi(hitosashi|nin)yubi2'],
    80: ['右人差指3','migi(hitosashi|nin)yubi3'],
    81: ['右人差指先','migi(hitosashi|nin)yubi.*saki'],
    82: ['右中指1','(uchuu|miginaka)yubi1'],
    83: ['右中指2','(uchuu|miginaka)yubi2'],
    84: ['右中指3','(uchuu|miginaka)yubi3'],
    85: ['右中指先','(uchuu|miginaka)yubi.*saki'],
    86: ['右薬指1','migikusuriyubi1'],
    87: ['右薬指2','migikusuriyubi2'],
    88: ['右薬指3','migikusuriyubi3'],
    89: ['右薬指先','migikusuriyubi.*saki'],
    90: ['右小指1','migikoyubi1'],
    91: ['右小指2','migikoyubi2'],
    92: ['右小指3','migikoyubi3'],
    93: ['右小指先','migikoyubi.*saki']
}

def kangkhaen(dic_chue):
    la = dic_chue[9] # 左腕
    lh = dic_chue[11] # 左手
    ra = dic_chue[12] # 右腕
    rh = dic_chue[14] # 右手
    # まず全部のジョイントの回転を0に戻す
    for kho in dic_chue.values():
        mc.setAttr(kho+'.r',0,0,0)

    xyz_la = mc.xform(la,query=True,translation=True,worldSpace=True)
    xyz_lh0 = mc.xform(lh,query=True,translation=True,worldSpace=True)
    xyz_ra = mc.xform(ra,query=True,translation=True,worldSpace=True)
    xyz_rh0 = mc.xform(rh,query=True,translation=True,worldSpace=True)

    atan_l = math.degrees(math.atan2(xyz_la[1]-xyz_lh0[1],xyz_lh0[0]-xyz_la[0]))
    atan_r = math.degrees(math.atan2(xyz_ra[1]-xyz_rh0[1],xyz_ra[0]-xyz_rh0[0]))

    mc.setAttr(la+'.rz',atan_l)
    mc.setAttr(ra+'.rz',-atan_r)

    xyz_lh1 = mc.xform(lh,query=True,translation=True,worldSpace=True)
    if(xyz_lh1[1]<xyz_lh0[1]):
        mc.setAttr(la+'.rz',-atan_l)
    xyz_rh1 = mc.xform(rh,query=True,translation=True,worldSpace=True)
    if(xyz_rh1[1]<xyz_rh0[1]):
        mc.setAttr(ra+'.rz',atan_r)

    xyz_lh1 = mc.xform(lh,query=True,translation=True,worldSpace=True)
    if(abs(xyz_lh1[1]-xyz_lh0[1])<abs(xyz_lh1[2]-xyz_lh0[2])):
        mc.setAttr(la+'.rz',0)
        mc.setAttr(la+'.rx',atan_l)
        xyz_lh1 = mc.xform(lh,query=True,translation=True,worldSpace=True)
        if(xyz_lh1[1]<xyz_lh0[1]):
            mc.setAttr(la+'.rx',-atan_l)
    xyz_rh1 = mc.xform(rh,query=True,translation=True,worldSpace=True)
    if(abs(xyz_rh1[1]-xyz_rh0[1])<abs(xyz_rh1[2]-xyz_rh0[2])):
        mc.setAttr(ra+'.rz',0)
        mc.setAttr(ra+'.rx',-atan_r)
        xyz_rh1 = mc.xform(rh,query=True,translation=True,worldSpace=True)
        if(xyz_rh1[1]<xyz_rh0[1]):
            mc.setAttr(ra+'.rx',atan_r)
