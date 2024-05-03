# -*- coding: utf-8 -*-
'''
PySideによるGUI
'''

import os,re
try:
    from PySide6.QtWidgets import QWidget \
        , QLabel, QLineEdit, QComboBox \
        , QPushButton, QCheckBox, QButtonGroup, QRadioButton \
        , QHBoxLayout, QVBoxLayout, QScrollArea \
        , QFileDialog, QMessageBox
    from PySide6.QtCore import Qt
except:
    from PySide2.QtWidgets import QWidget \
        , QLabel, QLineEdit, QComboBox \
        , QPushButton, QCheckBox, QButtonGroup, QRadioButton \
        , QHBoxLayout, QVBoxLayout, QScrollArea \
        , QFileDialog, QMessageBox
    from PySide2.QtCore import Qt
    
import maya.cmds as mc
from maya import mel
from . import pmxpaimaya,mayapaipmx
from .asset.hik import dic_hik,kangkhaen

class Natanglak(QWidget):
    '''
    メインのウィンドウ
    '''
    def __init__(self):
        QWidget.__init__(self)
        self.setWindowFlags(Qt.WindowStaysOnTopHint)
        self.setWindowTitle('~ mmdpaimaya ~')
        self.setStyleSheet('font-size: 16px; color: #eff;')
        vbl = QVBoxLayout()
        self.setLayout(vbl)

        self.btn_mmdmaya = QPushButton('MMD > Maya')
        vbl.addWidget(self.btn_mmdmaya)
        self.btn_mmdmaya.clicked.connect(lambda: self.poet_pit_natang('mmdmaya'))
        self.btn_mmdmaya.setFixedSize(320,45)

        self.btn_hik = QPushButton('Human IKの管理')
        vbl.addWidget(self.btn_hik)
        self.btn_hik.clicked.connect(lambda: self.poet_pit_natang('humanik'))
        self.btn_hik.setFixedSize(320,30)

        self.btn_mayammd = QPushButton('Maya > MMD')
        vbl.addWidget(self.btn_mayammd)
        self.btn_mayammd.clicked.connect(lambda: self.poet_pit_natang('mayammd'))
        self.btn_mayammd.setFixedSize(320,45)

        self.natangyoi = {'mmdmaya':None,'humanik':None,'mayammd':None}

    def poet_pit_natang(self,na):
        if(self.natangyoi[na]):
            self.natangyoi[na].close()
            self.natangyoi[na] = None
        else:
            if(na=='mmdmaya'):
                self.natangyoi[na] = Natang_mmdmaya(self)
            elif(na=='humanik'):
                self.natangyoi[na] = Natang_humanik(self)
            elif(na=='mayammd'):
                self.natangyoi[na] = Natang_mayammd(self)
            self.natangyoi[na].show()

    def keyPressEvent(self,e):
        if(e.key()==Qt.Key_Escape):
            self.close() # escを押したら閉じる

    def closeEvent(self,e):
        for na in self.natangyoi:
            if(self.natangyoi[na]):
                self.natangyoi[na].close()


class Natang_mmdmaya(QWidget):
    '''
    mmdモデルからmayaへインポートするためのウィンドウ
    '''
    def __init__(self,parent):
        QWidget.__init__(self)
        self.setAcceptDrops(True)
        self.parent = parent
        self.setWindowFlags(Qt.WindowStaysOnTopHint)
        self.setWindowTitle('~ MMD > Maya ~')
        self.setStyleSheet('font-size: 15px; color: #ddf;')
        vbl = QVBoxLayout()
        self.setLayout(vbl)

        self.file_khatangton = os.path.join(os.path.dirname(__file__),'asset','khatangton1.txt')
        try:
            with open(self.file_khatangton,'r',encoding='utf-8') as f:
                chue_tem_file = f.readline().split('=')[-1].strip()
                satsuan = f.readline().split('=')[-1].strip()
                yaek_poly = int(f.readline().split('=')[-1].strip())
                ao_bs = int(f.readline().split('=')[-1].strip())
                ao_kraduk = int(f.readline().split('=')[-1].strip())
                watsadu = int(f.readline().split('=')[-1].strip())
                pit_mai = int(f.readline().split('=')[-1].strip())
        except:
            chue_tem_file = ''
            satsuan = '8'
            yaek_poly = 0
            ao_bs = 1
            ao_kraduk = 1
            watsadu = 4
            pit_mai = 1

        hbl = QHBoxLayout()
        vbl.addLayout(hbl)
        hbl.addWidget(QLabel('ファイル'))
        self.le_chue_file = QLineEdit(chue_tem_file)
        hbl.addWidget(self.le_chue_file)
        self.le_chue_file.setFixedWidth(300)
        self.le_chue_file.textChanged.connect(self.chue_thuk_kae)
        self.btn_khon_file = QPushButton('...')
        hbl.addWidget(self.btn_khon_file)
        self.btn_khon_file.clicked.connect(self.khon_file)

        hbl = QHBoxLayout()
        vbl.addLayout(hbl)
        hbl.addWidget(QLabel('尺度'))
        self.le_satsuan = QLineEdit(satsuan)
        hbl.addWidget(self.le_satsuan)
        self.le_satsuan.setFixedWidth(100)
        self.le_satsuan.textEdited.connect(self.satsuan_thuk_kae)
        hbl.addWidget(QLabel('×'))
        hbl.addStretch()

        self.cb_yaek_poly = QCheckBox('材質ごとにポリゴンを分割する')
        vbl.addWidget(self.cb_yaek_poly)

        self.cb_ao_kraduk = QCheckBox('骨も作る')
        vbl.addWidget(self.cb_ao_kraduk)

        self.cb_ao_bs = QCheckBox('ブレンドシェープも作る')
        vbl.addWidget(self.cb_ao_bs)

        hbl = QHBoxLayout()
        vbl.addLayout(hbl)
        hbl.addWidget(QLabel('材質'))
        self.cbb_watsadu = QComboBox()
        hbl.addWidget(self.cbb_watsadu)
        self.cbb_watsadu.addItem('無い')
        self.cbb_watsadu.addItem('blinn')
        self.cbb_watsadu.addItem('phong')
        self.cbb_watsadu.addItem('lambert')
        self.cbb_watsadu.addItem('standardSurface')
        hbl.addStretch()

        hbl = QHBoxLayout()
        vbl.addLayout(hbl)
        hbl.addStretch()
        self.btn_roem_sang = QPushButton('作成開始')
        hbl.addWidget(self.btn_roem_sang)
        self.btn_roem_sang.clicked.connect(self.roem_sang)
        self.btn_roem_sang.setFixedSize(220,50)
        self.chue_thuk_kae(self.le_chue_file.text())
        self.cb_pit = QCheckBox('終わったらこの\nウィンドウを閉じる')
        hbl.addWidget(self.cb_pit)

        self.cb_yaek_poly.setChecked(yaek_poly)
        self.cb_ao_kraduk.setChecked(ao_kraduk)
        self.cb_ao_bs.setChecked(ao_bs)
        self.cbb_watsadu.setCurrentIndex(watsadu)
        self.cb_yaek_poly.toggled.connect(lambda:self.chue_thuk_kae(self.le_chue_file.text()))
        self.cb_pit.setChecked(pit_mai)

    def chue_thuk_kae(self,chue_file): # ファイルの名前が更新されたら
        sakun = chue_file.split('.')[-1]
        sang_dai = (sakun.lower() in ['pmd','pmx','x'])
        self.btn_roem_sang.setEnabled(sang_dai)
        self.btn_roem_sang.setStyleSheet(['text-decoration: line-through; color: #aab;',''][sang_dai])
        dai = chue_file[-2:]!='.x' and not self.cb_yaek_poly.isChecked()
        self.cb_ao_kraduk.setEnabled(dai)
        self.cb_ao_bs.setEnabled(dai)
        self.cb_ao_kraduk.setStyleSheet(['text-decoration: line-through; color: #aab;',''][dai])
        self.cb_ao_bs.setStyleSheet(['text-decoration: line-through; color: #aab;',''][dai])

    def khon_file(self): # 読み込むファイルをブラウスする
        self.setWindowFlags(self.windowFlags() & ~Qt.WindowStaysOnTopHint)
        chue_file,ok = QFileDialog.getOpenFileName(filter='PMD/PMX/X (*.pmd *.pmx *.x)')
        if(ok):
            self.le_chue_file.setText(chue_file)
        self.setWindowFlags(self.windowFlags() | Qt.WindowStaysOnTopHint)
        self.show()


    def dragEnterEvent(self,e):
        if(e.mimeData().hasUrls()): # ファイルがドラッグされたら使える
            e.accept()

    def dropEvent(self,e):
        self.le_chue_file.setText(e.mimeData().urls()[0].toLocalFile()) # ドラッグされたファイルの名前を取得する

    def satsuan_thuk_kae(self,kha): # 尺度が更新されたら
        try:
            float(kha)
        except:
            self.le_satsuan.setText('1')

    def roem_sang(self): # ボタンがクリックされたら、作成は開始
        chue_tem_file = self.le_chue_file.text()
        try:
            satsuan = float(self.le_satsuan.text())
        except:
            self.le_satsuan.setText('1')
            satsuan = 1.
        yaek_poly = self.cb_yaek_poly.isChecked()
        ao_bs = not yaek_poly and self.cb_ao_bs.isChecked()
        ao_kraduk = not yaek_poly and self.cb_ao_kraduk.isChecked()
        watsadu = self.cbb_watsadu.currentIndex()
        # ここでmayaのシーンの中でモデルを作る
        pmxpaimaya.sang(chue_tem_file,satsuan,yaek_poly,ao_bs,ao_kraduk,watsadu)

        pit_mai = self.cb_pit.isChecked() # 今回使った設定を保存しておく
        with open(self.file_khatangton,'w',encoding='utf-8') as f:
            f.write('ファイルの名前 = %s\n'%chue_tem_file)
            f.write('尺度 = %f\n'%satsuan)
            f.write('ポリゴンの分割 = %d\n'%yaek_poly)
            f.write('ブレンドシェープ = %d\n'%ao_bs)
            f.write('ジョイント = %d\n'%ao_kraduk)
            f.write('材質 = %d\n'%watsadu)
            f.write('閉じる = %d\n'%pit_mai)

        if(pit_mai): # 終わったらこのウィンドウを閉じる
            self.close()

    def keyPressEvent(self,e): # escが押されたら閉じる
        if(e.key()==Qt.Key_Escape):
            self.close() # escを押したら閉じる

    def closeEvent(self,e):
        self.parent.natangyoi['mmdmaya'] = None


class Natang_humanik(QWidget):
    '''
    Human IKを管理するためのウィンドウ
    '''
    def __init__(self,parent):
        QWidget.__init__(self)
        self.parent = parent
        self.setWindowFlags(Qt.WindowStaysOnTopHint)
        self.setWindowTitle('~ Human IK管理 ~')
        self.setStyleSheet('font-size: 15px; color: #ddf;')
        self.resize(450,350)
        vbl = QVBoxLayout()
        self.setLayout(vbl)
        hbl = QHBoxLayout()
        vbl.addLayout(hbl)
        self.cbb_poly = QComboBox()
        hbl.addWidget(self.cbb_poly)
        self.cbb_poly.setEditable(True)
        self.btn_hikdef = QPushButton('定義')
        hbl.addWidget(self.btn_hikdef)
        self.btn_hikdef.setFixedWidth(60)
        self.btn_hikdef.clicked.connect(self.hikdef)

        lis_chue_nod_poly = []
        for chue_nod_shep in mc.ls('*Shape',shapes=1):
            chue_nod_poly = chue_nod_shep[:-5]
            if(mc.objExists(chue_nod_poly) and 'MMD_model' in mc.listAttr(chue_nod_poly)):
                lis_chue_nod_poly.append(chue_nod_poly)
                self.cbb_poly.addItem(chue_nod_poly)

        self.sca = QScrollArea()
        vbl.addWidget(self.sca)
        self.wdg = QWidget()
        self.sca.setWidget(self.wdg)
        self.vbl = QVBoxLayout()
        self.wdg.setLayout(self.vbl)

        self.btn_sang_hik = QPushButton('コントロールリグの作成')
        vbl.addWidget(self.btn_sang_hik)
        self.btn_sang_hik.clicked.connect(self.hikcori)
        self.btn_sang_hik.setEnabled(False)

    def hikdef(self):
        chue_nod_kho_nok = None
        chue_nod_poly = self.cbb_poly.currentText()
        if(mc.objExists(chue_nod_poly)):
            # 全ての親のノードを探す
            if(mc.objExists(chue_nod_poly+'_sentaa')):
                chue_nod_kho_nok = chue_nod_poly+'_sentaa'
            elif(mc.objExists(chue_nod_poly+'_subetenooya')):
                chue_nod_kho_nok = chue_nod_poly+'_subetenooya'

        if(not chue_nod_kho_nok):
            QMessageBox.about(self,'何か間違いかも','該当のジョイントが見つかりません')
            return

        self.wdg.setFixedSize(600,2000)
        self.btn_hikdef.setEnabled(False)
        self.cbb_poly.setEnabled(False)
        dic_chue = {}
        if(chue_nod_kho_nok[0]!='|'):
            chue_nod_kho_nok = '|'+chue_nod_kho_nok
        set_hik = set(mc.ls(type='HIKCharacterNode'))
        mel.eval('hikCreateDefinition')
        chue_nod_hik = (set(mc.ls(type='HIKCharacterNode'))-set_hik).pop()
        chue_nod_hik = mc.rename(chue_nod_hik,'HIK_'+chue_nod_poly)
        lis_chue_nod_kho = [chue_nod_kho_nok]+mc.listRelatives(chue_nod_kho_nok,allDescendents=True,fullPath=True)
        for lek in dic_hik:
            hbl = QHBoxLayout()
            self.vbl.addLayout(hbl)
            lb = QLabel(dic_hik[lek][0])
            hbl.addWidget(lb)
            lb.setFixedWidth(80)
            # 該当な名前のノードが見つけるまで繰り返す
            for chue_nod_kho in lis_chue_nod_kho:
                khonha = re.findall(r'\|%s$'%dic_hik[lek][1],chue_nod_kho)
                if(khonha): # 該当な名前のノードを見つけた
                    dic_chue[lek] = chue_nod_kho
                    break
            else: # 該当な名前のノードが見つからない場合、指のノードだけの対策
                if(lek>=51 and lek not in range(54,94,4)):
                    lis_chue_nod_plai = mc.listRelatives(dic_chue[lek-1],fullPath=True)
                    if(lis_chue_nod_plai and len(lis_chue_nod_plai)==1):
                        chue_nod_plai = lis_chue_nod_plai[0]
                        dic_chue[lek] = chue_nod_plai
            
            if(lek in dic_chue): # ノードわ見つけた場合
                mel.eval('hikSetCharacterObject %s %s %d 0'%(dic_chue[lek],chue_nod_hik,lek))

                btn = QPushButton('選択') # 押したらそのノードが選択されるというボタン
                hbl.addWidget(btn)
                btn.setFixedSize(50,30)

                le = QLineEdit(dic_chue[lek]) # ノードの名前を表示
                hbl.addWidget(le)
                btn.clicked.connect((lambda x: (lambda: mc.select(x.text())))(le))
                le.setFixedWidth(400)
                le.setStyleSheet('font-size: 12px; color: #ffe;')
            else: # ノードが見つからなかった場合
                lb = QLabel('見つかりません')
                hbl.addWidget(lb)
                lb.setFixedWidth(400)
                lb.setStyleSheet('color: #fab;')
            
            hbl.addStretch()

        kangkhaen(dic_chue) # 手を広げる
        self.vbl.addStretch()
        self.btn_sang_hik.setEnabled(True)

    def hikcori(self):
        self.parent.close()
        mel.eval('hikCreateControlRig')

    def keyPressEvent(self,e):
        if(e.key()==Qt.Key_Escape):
            self.close() # escを押したら閉じる

    def closeEvent(self,e):
        self.parent.natangyoi['humanik'] = None


class Natang_mayammd(QWidget):
    '''
    mayaからmmdモデルの.pmxファイルへエクスポートするためのウィンドウ
    '''
    def __init__(self,parent):
        QWidget.__init__(self)
        self.parent = parent
        self.setWindowFlags(Qt.WindowStaysOnTopHint)
        self.setWindowTitle('~ Maya > MMD ~')
        self.setStyleSheet('font-size: 15px; color: #ddf;')
        vbl = QVBoxLayout()
        self.setLayout(vbl)

        self.file_khatangton = os.path.join(os.path.dirname(__file__),'asset','khatangton2.txt')
        try:
            with open(self.file_khatangton,'r',encoding='utf-8') as f:
                chue_tem_file = f.readline().split('=')[-1].strip()
                satsuan = f.readline().split('=')[-1].strip()
                chai_bs = int(f.readline().split('=')[-1].strip())
                chai_kraduk = int(f.readline().split('=')[-1].strip())
                chai_watsadu = int(f.readline().split('=')[-1].strip())
                lok_tex = int(f.readline().split('=')[-1].strip())
                thangmot = int(f.readline().split('=')[-1].strip())
                pit_mai = int(f.readline().split('=')[-1].strip())
        except:
            chue_tem_file = ''
            satsuan = '0.125'
            chai_bs = True
            chai_kraduk = True
            chai_watsadu = True
            lok_tex = False
            thangmot = False
            pit_mai = True

        hbl = QHBoxLayout()
        vbl.addLayout(hbl)
        hbl.addWidget(QLabel('ファイル'))
        self.le_chue_file = QLineEdit(chue_tem_file)
        hbl.addWidget(self.le_chue_file)
        self.le_chue_file.setFixedWidth(300)
        self.le_chue_file.textChanged.connect(self.chue_thuk_kae)
        self.btn_khon_file = QPushButton('...')
        hbl.addWidget(self.btn_khon_file)
        self.btn_khon_file.clicked.connect(self.khon_file)

        hbl = QHBoxLayout()
        vbl.addLayout(hbl)
        hbl.addWidget(QLabel('尺度'))
        self.le_satsuan = QLineEdit(satsuan)
        hbl.addWidget(self.le_satsuan)
        self.le_satsuan.setFixedWidth(100)
        self.le_satsuan.textEdited.connect(self.satsuan_thuk_kae)
        hbl.addWidget(QLabel('×'))
        hbl.addStretch()

        self.cb_chai_kraduk = QCheckBox('骨も作る')
        vbl.addWidget(self.cb_chai_kraduk)
        self.cb_chai_kraduk.setChecked(chai_kraduk)

        self.cb_chai_bs = QCheckBox('モーフも作る')
        vbl.addWidget(self.cb_chai_bs)
        self.cb_chai_bs.setChecked(chai_bs)

        self.cb_chai_watsadu = QCheckBox('材質を使う')
        vbl.addWidget(self.cb_chai_watsadu)
        self.cb_chai_watsadu.setChecked(chai_watsadu)

        self.cb_lok_tex = QCheckBox('テクスチャファイルをコピーする')
        vbl.addWidget(self.cb_lok_tex)
        self.cb_lok_tex.setChecked(lok_tex)

        hbl = QHBoxLayout()
        vbl.addLayout(hbl)
        hbl.addWidget(QLabel('使うポリゴン'))
        self.btng = QButtonGroup()
        self.rb_thangmot = QRadioButton('全部')
        hbl.addWidget(self.rb_thangmot)
        self.btng.addButton(self.rb_thangmot)
        self.rb_thilueak = QRadioButton('選択されている')
        hbl.addWidget(self.rb_thilueak)
        self.btng.addButton(self.rb_thilueak)
        hbl.addStretch()

        if(thangmot):
            self.rb_thangmot.setChecked(True)
        else:
            self.rb_thilueak.setChecked(True)

        hbl = QHBoxLayout()
        vbl.addLayout(hbl)
        hbl.addStretch()
        self.btn_roem_sang = QPushButton('作成開始')
        hbl.addWidget(self.btn_roem_sang)
        self.btn_roem_sang.clicked.connect(self.roem_sang)
        self.btn_roem_sang.setFixedSize(220,50)
        self.chue_thuk_kae(self.le_chue_file.text())
        self.cb_pit = QCheckBox('終わったらこの\nウィンドウを閉じる')
        hbl.addWidget(self.cb_pit)
        self.cb_pit.setChecked(pit_mai)

    def khon_file(self):
        self.setWindowFlags(self.windowFlags() & ~Qt.WindowStaysOnTopHint)
        chue_file,ok = QFileDialog.getSaveFileName(filter='PMX (*.pmx)')
        if(ok):
            self.le_chue_file.setText(chue_file)
        self.setWindowFlags(self.windowFlags() | Qt.WindowStaysOnTopHint)
        self.show()

    def chue_thuk_kae(self,chue_file):
        sakun = chue_file.split('.')[-1]
        sang_dai = (sakun.lower()=='pmx')
        self.btn_roem_sang.setEnabled(sang_dai)
        self.btn_roem_sang.setStyleSheet(['text-decoration: line-through; color: #aab;',''][sang_dai])

    def satsuan_thuk_kae(self,kha):
        try:
            float(kha)
        except:
            self.le_satsuan.setText('1')

    def roem_sang(self):
        chue_tem_file = self.le_chue_file.text()
        try:
            satsuan = float(self.le_satsuan.text())
        except:
            self.le_satsuan.setText('1')
            satsuan = 1.
        chai_watsadu = self.cb_chai_watsadu.isChecked()
        chai_bs = self.cb_chai_bs.isChecked()
        chai_kraduk = self.cb_chai_kraduk.isChecked()
        lok_tex = self.cb_lok_tex.isChecked()
        thangmot = self.btng.checkedButton()==self.rb_thangmot
        mayapaipmx.sang(chue_tem_file,satsuan,chai_kraduk,chai_bs,chai_watsadu,lok_tex,thangmot)

        pit_mai = self.cb_pit.isChecked()
        with open(self.file_khatangton,'w',encoding='utf-8') as f:
            f.write('ファイルの名前 = %s\n'%chue_tem_file)
            f.write('尺度 = %f\n'%satsuan)
            f.write('ブレンドシェープ = %d\n'%chai_bs)
            f.write('ジョイント = %d\n'%chai_kraduk)
            f.write('材質 = %d\n'%chai_watsadu)
            f.write('テクスチャのコピー = %d\n'%lok_tex)
            f.write('ポリゴン全部 = %d\n'%thangmot)
            f.write('閉じる = %d\n'%pit_mai)

        if(pit_mai):
            self.close()

    def keyPressEvent(self,e):
        if(e.key()==Qt.Key_Escape):
            self.close() # escを押したら閉じる

    def closeEvent(self,e):
        self.parent.natangyoi['mayammd'] = None
