# -*- coding: utf-8 -*-
u'''
โค้ดในส่วนของ GUI
'''
import maya.cmds as mc
from sang import sangkhuen
import sang_x
import imp,os,codecs
import sang
from chipatha import khokhwam
import imp
import chipatha
imp.reload(chipatha)

try:
    imp.find_module('PySide2')
    from PySide2.QtWidgets import *
    from PySide2.QtGui import *
    from PySide2.QtCore import *
except ImportError:
    from PySide.QtGui import *
    from PySide.QtCore import *

# หน้าต่างหลักสำหรับสร้าง
class Natangsang(QWidget):
    def __init__(self):
        QWidget.__init__(self,None,Qt.WindowStaysOnTopHint)
        
        self.file_khatangton = os.path.join(os.path.dirname(__file__),u'khatangton.txt')
        try:
            # อ่านข้อมูลค่าตั้งต้น
            with codecs.open(self.file_khatangton,'r',encoding='utf-8') as f:
                phasa = int(f.readline().split('=')[-1].strip())
                chue_file = unicode(f.readline().split('=')[-1].strip())
                khanat = unicode(f.readline().split('=')[-1].strip())
                yaek_poly = int(f.readline().split('=')[-1].strip())
                ao_bs = int(f.readline().split('=')[-1].strip())
                ao_kraduk = int(f.readline().split('=')[-1].strip())
                ao_ik = int(f.readline().split('=')[-1].strip())
                watsadu = int(f.readline().split('=')[-1].strip())
                ao_alpha_map = int(f.readline().split('=')[-1].strip())
        except:
            # ถ้าไม่มีไฟล์อยู่ก็สร้างค่าตั้งต้นใหม่
            phasa = 0
            chue_file = u''
            khanat = '8.0'
            yaek_poly = 0
            ao_bs = 1
            ao_kraduk = 1
            ao_ik = 0
            watsadu = 1
            ao_alpha_map = 1
        
        self.khronglak = QVBoxLayout() # โครงหลักของหน้าต่าง
        self.setLayout(self.khronglak)
        
        qhbl = QHBoxLayout()
        self.khronglak.addLayout(qhbl)
        self.lueak_phasa = [QButtonGroup(),QRadioButton(u'ไทย'),QRadioButton(u'日本語'),QRadioButton(u'中文')]
        self.lueak_phasa[phasa+1].setChecked(1)
        self.lueak_phasa[0].addButton(self.lueak_phasa[1],1)
        self.lueak_phasa[0].addButton(self.lueak_phasa[2],2)
        self.lueak_phasa[0].addButton(self.lueak_phasa[3],3)
        self.lueak_phasa[0].buttonClicked.connect(self.saikhokhwam)
        qhbl.addStretch()
        qhbl.addWidget(self.lueak_phasa[1])
        qhbl.addWidget(self.lueak_phasa[2])
        qhbl.addWidget(self.lueak_phasa[3])
        
        qhbl = QHBoxLayout()
        self.khronglak.addLayout(qhbl)
        self.ql_chue_file = QLabel()
        font = self.ql_chue_file.font()
        font.setPointSize(16)
        font.setFamily('Tahoma')
        self.ql_chue_file.setFont(font)
        qhbl.addWidget(self.ql_chue_file)
        self.chong_chue_file = QLineEdit(chue_file) # ช่องใส่ชื่อไฟล์
        qhbl.addWidget(self.chong_chue_file)
        self.chong_chue_file.setFixedWidth(300)
        self.pum_lueak_file = QPushButton(u'...') # ปุ่มค้นไฟล์
        qhbl.addWidget(self.pum_lueak_file)
        self.pum_lueak_file.clicked.connect(self.lueak_file)
        
        qhbl = QHBoxLayout()
        self.khronglak.addLayout(qhbl)
        self.ql_khanat = QLabel()
        self.ql_khanat.setFont(font)
        qhbl.addWidget(self.ql_khanat) # ช่องใส่ขนาด
        self.chong_khanat = QLineEdit(khanat)
        qhbl.addWidget(self.chong_khanat)
        self.chong_khanat.setFixedWidth(80)
        qhbl.addWidget(QLabel(u'x'))
        qhbl.addStretch()
        
        qhbl = QHBoxLayout()
        self.khronglak.addLayout(qhbl)
        self.tick_yaek_poly = QCheckBox()
        self.tick_yaek_poly.setFont(font)
        qhbl.addWidget(self.tick_yaek_poly)
        self.tick_yaek_poly.setChecked(yaek_poly)
        self.tick_yaek_poly.clicked.connect(self.sang_kraduk_dai_mai)
        
        qhbl = QHBoxLayout()
        self.khronglak.addLayout(qhbl)
        self.tick_bs = QCheckBox()
        self.tick_bs.setFont(font)
        qhbl.addWidget(self.tick_bs)
        self.tick_bs.setChecked(ao_bs)
        
        self.tick_kraduk = QCheckBox()
        self.tick_kraduk.setFont(font)
        qhbl.addWidget(self.tick_kraduk)
        self.tick_kraduk.setChecked(ao_kraduk)
        self.tick_kraduk.clicked.connect(self.sang_ik_dai_mai)
        
        self.tick_ik = QCheckBox()
        self.tick_ik.setFont(font)
        qhbl.addWidget(self.tick_ik)
        self.tick_ik.setChecked(ao_ik)
        
        qhbl.addStretch()
        
        qhbl = QHBoxLayout()
        self.khronglak.addLayout(qhbl)
        self.ql_watsadu = QLabel()
        self.ql_watsadu.setFont(font)
        qhbl.addWidget(self.ql_watsadu)
        self.lueak_phiu = QComboBox()
        ss = [u'',u'blinn',u'phong',u'lambert'] # ชนิดของวัสดุ
        if(mc.objExists('defaultArnoldRenderOptions')): # ถ้ามีอาร์โนลด์อยู่
            ss.append(u'aiStandard (Arnold)') # ก็ใส่ aiStandard ไปด้วย
            mc.setAttr('defaultArnoldRenderOptions.autotx',0) # ทำให้ไม่มีการแปลงเท็กซ์เจอร์เป็น .tx โดยอัตโนมัติ
            mc.setAttr('defaultArnoldRenderOptions.use_existing_tiled_textures',0)
        for s in ss:
            self.lueak_phiu.addItem(s)
        self.lueak_phiu.setCurrentIndex(watsadu)
        if(self.lueak_phiu.currentIndex()==-1):
            self.lueak_phiu.setCurrentIndex(1)
        self.lueak_phiu.setFont(font)
        qhbl.addWidget(self.lueak_phiu)
        
        self.lueak_phiu.currentIndexChanged.connect(self.sang_alpha_dai_mai)
        qhbl.addStretch()
        
        ql = QLabel('alpha map')
        ql.setFont(font)
        self.khronglak.addWidget(ql)
        
        # เลือกวิธีการจัดการกับอัลฟา
        qhbl = QHBoxLayout()
        self.khronglak.addLayout(qhbl)
        qhbl.addWidget(QLabel('      '))
        self.tick_alpha = [QButtonGroup(),QRadioButton(),QRadioButton(),QRadioButton()]
        self.tick_alpha[ao_alpha_map+1].setChecked(1)
        
        for i in range(1,4):
            self.tick_alpha[0].addButton(self.tick_alpha[i],i)
            self.tick_alpha[i].setFont(font)
            qhbl.addWidget(self.tick_alpha[i])
        
        qhbl.addStretch()
        self.sang_alpha_dai_mai()
        self.sang_kraduk_dai_mai()
        
        self.pum_roem_sang = QPushButton() # ปุ่มเริ่มสร้าง
        self.pum_roem_sang.setFont(font)
        self.khronglak.addWidget(self.pum_roem_sang)
        self.pum_roem_sang.clicked.connect(self.roem_sang)
        
        self.saikhokhwam()
    
    # เมื่อกดปุ่มค้นไฟล์
    def lueak_file(self):
        self.setWindowFlags(self.windowFlags() & ~Qt.WindowStaysOnTopHint)
        chue_file = QFileDialog.getOpenFileName(filter="PMD/PMX/X (*.pmd *.pmx *.x)")
        if(type(chue_file)==tuple):
            chue_file = unicode(chue_file[0])
        else:
            chue_file = unicode(chue_file)
        self.chong_chue_file.setText(chue_file)
        self.setWindowFlags(self.windowFlags() | Qt.WindowStaysOnTopHint)
        self.show()
    
    def sang_kraduk_dai_mai(self):
        dai = not self.tick_yaek_poly.isChecked()
        self.tick_bs.setEnabled(dai)
        self.tick_kraduk.setEnabled(dai)
        self.tick_ik.setEnabled(dai and self.tick_kraduk.isChecked())
        if(not dai and self.lueak_phiu.currentIndex()==0):
            self.lueak_phiu.setCurrentIndex(1)
            for i in range(1,4):
                self.tick_alpha[i].setEnabled(1)
    
    def sang_alpha_dai_mai(self):
        tp = self.lueak_phiu.currentIndex()!=0
        if(tp==0):
            self.tick_yaek_poly.setChecked(0)
            self.sang_kraduk_dai_mai()
        for i in range(1,4):
            self.tick_alpha[i].setEnabled(tp)
    
    def sang_ik_dai_mai(self):
        self.tick_ik.setEnabled(self.tick_kraduk.isChecked())
    
    # เริ่มสร้างโมเดล
    def roem_sang(self):
        # ดึงข้อมูลจากช่องต่างๆที่กรอกและติ๊กไว้
        phasa = self.lueak_phasa[0].checkedId()-1
        chue_file = unicode(self.chong_chue_file.text())
        khanat = float(self.chong_khanat.text())
        yaek_poly = int(self.tick_yaek_poly.isChecked())
        ao_bs = int(self.tick_bs.isChecked())
        ao_kraduk = int(self.tick_kraduk.isChecked())
        ao_ik = int(self.tick_ik.isChecked())
        watsadu = self.lueak_phiu.currentIndex()
        ao_alpha_map = self.tick_alpha[0].checkedId()-1
        
        if(chue_file[-2]!='.'):
            # ถ้าเป็น .pmd หรือ .pmx
            chue_node_poly,list_mat_mi_alpha = sangkhuen(chue_file,khanat,yaek_poly,ao_bs,ao_kraduk,ao_ik,watsadu,ao_alpha_map)
        else:
            # ถ้าเป็น .x
            sang_x.sangkhuen(chue_file,khanat,ao_alpha_map,yaek_poly,watsadu)
            list_mat_mi_alpha = []
        
        # เมื่อสร้างสำเร็จแล้วให้บันทึกค่าที่เลือกไว้เป็นค่าตั้งต้นสำหรับคราวต่อไป
        with codecs.open(self.file_khatangton,'w','utf-8') as f:
            f.write(u'ภาษา = '+unicode(phasa)+'\n')
            f.write(u'ชื่อไฟล์ = '+chue_file+'\n')
            f.write(u'ขนาด = '+unicode(self.chong_khanat.text())+'\n')
            f.write(u'แยกโพลิกอนตามวัสดุ = %d\n'%yaek_poly)
            f.write(u'สร้าง blend shape = %d\n'%ao_bs)
            f.write(u'สร้างกระดูก = %d\n'%ao_kraduk)
            f.write(u'สร้าง IK = %d\n'%ao_ik)
            f.write(u'วัสดุ = %d\n'%watsadu)
            f.write(u'สร้าง alpha map = %d\n'%ao_alpha_map)
        self.close()
        # เปิดหน้าต่างสำหรับคัดเลือกวัสดุที่จะทำอัลฟาแม็ป
        if(list_mat_mi_alpha and ao_alpha_map==1):
            self.natangmai = Natang_alpha(chue_file,list_mat_mi_alpha,phasa)
            self.natangmai.show()
    
    # ใส่ข้อความตามภาษาที่เลือก
    def saikhokhwam(self):
        ps = self.lueak_phasa[0].checkedId()-1
        self.setWindowTitle(khokhwam[0][ps])
        self.ql_chue_file.setText(khokhwam[1][ps])
        self.ql_khanat.setText(khokhwam[2][ps])
        self.tick_yaek_poly.setText(khokhwam[3][ps])
        self.tick_bs.setText(khokhwam[4][ps])
        self.tick_kraduk.setText(khokhwam[5][ps])
        self.tick_ik.setText(khokhwam[6][ps])
        self.ql_watsadu.setText(khokhwam[7][ps])
        self.lueak_phiu.setItemText(0,khokhwam[8][ps])
        self.tick_alpha[1].setText(khokhwam[9][ps])
        self.tick_alpha[2].setText(khokhwam[10][ps])
        self.tick_alpha[3].setText(khokhwam[11][ps])
        self.pum_roem_sang.setText(khokhwam[12][ps])

# หน้าต่างคัดเลือกวัสดุที่จะเอาอัลฟาแม็ป
class Natang_alpha(QWidget):
    def __init__(self,chue_file,list_mat_mi_alpha,ps=0):
        QWidget.__init__(self,None,Qt.WindowStaysOnTopHint)
        self.chue_file = chue_file
        self.list_mat_mi_alpha = list_mat_mi_alpha
        self.setWindowTitle(khokhwam[13][ps])
        self.khronglak = QVBoxLayout()
        self.setLayout(self.khronglak)
        
        qvbl = QVBoxLayout()
        self.khronglak.addLayout(qvbl)
        self.klum_tick_bs = QButtonGroup()
        self.klum_tick_bs.setExclusive(0)
        self.dict_tick_bs = {}
        for i,mat in enumerate(list_mat_mi_alpha):
            tick_bs = QCheckBox(mat[0])
            qvbl.addWidget(tick_bs)
            tick_bs.setChecked(mat[2])
            self.klum_tick_bs.addButton(tick_bs,i+1)
            self.dict_tick_bs[i+1] = tick_bs
            
        self.klum_tick_bs.buttonClicked[int].connect(self.chueam_alpha)
        
        self.pum_setsin = QPushButton(khokhwam[14][ps])
        font = self.pum_setsin.font()
        font.setPointSize(18)
        font.setFamily('Tahoma')
        self.pum_setsin.setFont(font)
        self.khronglak.addWidget(self.pum_setsin)
        self.pum_setsin.clicked.connect(self.setsin)
    
    # เมื่อติ๊กช่องเลือกเอาไม่เอาอัลฟา
    def chueam_alpha(self,i):
        mat = self.list_mat_mi_alpha[i-1][0]
        list_connect = mc.listConnections(mat,c=1,p=1)
        tex = list_connect[list_connect.index(mat+'.color')+1].replace('.outColor','')
        #mc.select(mc.sets(mat+'SG',q=1))
        if(self.klum_tick_bs.button(i).isChecked()):
            # ติ๊กเอา ให้ทำการเชื่อมต่อ
            mc.connectAttr(tex+'.outTransparency',mat+'.transparency')
            print(u'เชื่อม %s กับ %s'%(mat,tex))
        else:
            # ติ๊กไม่เอา ให้ตัดการเชื่อมต่อ
            mc.disconnectAttr(tex+'.outTransparency',mat+'.transparency')
            print(u'ตัดการเชื่อม %s กับ %s'%(mat,tex))
    
    # เสร็จสิ้นการเลือกวัสดุที่จะเอาอัลฟา บันทึกข้อมูลใส่ไฟล์
    def setsin(self):
        s = []
        for i in self.dict_tick_bs:
            if(self.klum_tick_bs.button(i).isChecked()):
                s.append(self.list_mat_mi_alpha[i-1][1])
        file_model_alpha = os.path.join(os.path.dirname(__file__),u'modelalpha.txt')
        ss = []
        try:
            with codecs.open(file_model_alpha,'r','utf-8') as f:
                for thaeo in f:
                    if(self.chue_file in thaeo):
                        f.readline()
                    else:
                        if(thaeo!='\n'): ss.append(thaeo)
        except: 0
        with codecs.open(file_model_alpha,'w','utf-8') as f:
            f.write(''.join(ss)+u'\n---- '+self.chue_file+u'\n>'+'::'.join(s))
        self.close()

# เริ่มโปรแกรม
def roem():
    qAp = QApplication.instance()
    if(qAp==None):
        qAp = QApplication(sys.argv)
    natang = Natangsang()
    natang.show()
    return natang