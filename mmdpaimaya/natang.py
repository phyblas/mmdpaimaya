# -*- coding: utf-8 -*-
import maya.cmds as mc
from sang import sangkhuen
import imp,os,codecs
import sang

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
                chue_file = unicode(f.readline().split('=')[-1].strip())
                khanat = unicode(f.readline().split('=')[-1].strip())
                yaek_poly = int(f.readline().split('=')[-1].strip())
                ao_bs = int(f.readline().split('=')[-1].strip())
                ao_kraduk = int(f.readline().split('=')[-1].strip())
                ao_ik = int(f.readline().split('=')[-1].strip())
                ao_siphiu = int(f.readline().split('=')[-1].strip())
                ao_alpha_map = int(f.readline().split('=')[-1].strip())
        except:
            # ถ้าไม่มีไฟล์อยู่กสร้างค่าตั้งต้นใหม่
            chue_file = u''
            khanat = '8.0'
            yaek_poly = 0
            ao_bs = 1
            ao_kraduk = 1
            ao_ik = 0
            ao_siphiu = 1
            ao_alpha_map = 1
        
        self.setWindowTitle(u'~ MMD ไป Maya ~')
        self.khronglak = QVBoxLayout() # โครงหลักของหน้าต่าง
        self.setLayout(self.khronglak)
        
        qhbl = QHBoxLayout()
        self.khronglak.addLayout(qhbl)
        qhbl.addWidget(QLabel(u'ไฟล์'))
        self.chong_chue_file = QLineEdit(chue_file) # ช่องใส่ชื่อไฟล์
        qhbl.addWidget(self.chong_chue_file)
        self.chong_chue_file.setFixedWidth(300)
        self.pum_lueak_file = QPushButton(u'...') # ปุ่มค้นไฟล์
        qhbl.addWidget(self.pum_lueak_file)
        self.pum_lueak_file.clicked.connect(self.lueak_file)
        
        qhbl = QHBoxLayout()
        self.khronglak.addLayout(qhbl)
        qhbl.addWidget(QLabel(u'ขนาด')) # ช่องใส่ขนาด
        self.chong_khanat = QLineEdit(khanat)
        qhbl.addWidget(self.chong_khanat)
        self.chong_khanat.setFixedWidth(80)
        qhbl.addWidget(QLabel(u'x'))
        qhbl.addStretch()
        
        qhbl = QHBoxLayout()
        self.khronglak.addLayout(qhbl)
        self.tick_yaek_poly = QCheckBox(u'แยกโพลิกอนตามวัสดุ')
        qhbl.addWidget(self.tick_yaek_poly)
        self.tick_yaek_poly.setChecked(yaek_poly)
        self.tick_yaek_poly.clicked.connect(self.sang_kraduk_dai_mai)
        
        qhbl = QHBoxLayout()
        self.khronglak.addLayout(qhbl)
        self.tick_bs = QCheckBox(u'สร้าง blend shape')
        qhbl.addWidget(self.tick_bs)
        self.tick_bs.setChecked(ao_bs)
        
        self.tick_kraduk = QCheckBox(u'สร้างกระดูก')
        qhbl.addWidget(self.tick_kraduk)
        self.tick_kraduk.setChecked(ao_kraduk)
        self.tick_kraduk.clicked.connect(self.sang_ik_dai_mai)
        
        self.tick_ik = QCheckBox(u'สร้าง IK')
        qhbl.addWidget(self.tick_ik)
        self.tick_ik.setChecked(ao_ik)
        
        qhbl.addStretch()
        
        qhbl = QHBoxLayout()
        self.khronglak.addLayout(qhbl)
        self.tick_siphiu = QCheckBox(u'ใส่สีผิว')
        qhbl.addWidget(self.tick_siphiu)
        self.tick_siphiu.setChecked(ao_siphiu)
        self.tick_siphiu.clicked.connect(self.sang_alpha_dai_mai)
        
        self.tick_alpha = QCheckBox(u'สร้าง alpha map')
        qhbl.addWidget(self.tick_alpha)
        self.tick_alpha.setChecked(ao_alpha_map)
        
        qhbl.addStretch()
        self.sang_alpha_dai_mai()
        self.sang_kraduk_dai_mai()
        
        self.pum_roem_sang = QPushButton(u'เริ่มสร้าง') # ปุ่มเริ่มสร้าง
        self.khronglak.addWidget(self.pum_roem_sang)
        self.pum_roem_sang.clicked.connect(self.roem_sang)
    
    # เมื่อกดปุ่มค้นไฟล์
    def lueak_file(self):
        self.setWindowFlags(self.windowFlags() & ~Qt.WindowStaysOnTopHint)
        chue_file = QFileDialog.getOpenFileName(filter="PMD/PMX (*.pmd *.pmx)")
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
        if(not dai and not self.tick_siphiu.isChecked()):
            self.tick_siphiu.setChecked(1)
            self.tick_alpha.setEnabled(1)
    
    def sang_alpha_dai_mai(self):
        self.tick_alpha.setEnabled(self.tick_siphiu.isChecked())
    
    def sang_ik_dai_mai(self):
        self.tick_ik.setEnabled(self.tick_kraduk.isChecked())
    
    # เริ่มสร้างโมเดล
    def roem_sang(self):
        # ดึงข้อมูลจากช่องต่างๆที่กรอกและติ๊กไว้
        chue_file = unicode(self.chong_chue_file.text())
        khanat = float(self.chong_khanat.text())
        yaek_poly = int(self.tick_yaek_poly.isChecked())
        ao_bs = int(self.tick_bs.isChecked())
        ao_kraduk = int(self.tick_kraduk.isChecked())
        ao_ik = int(self.tick_ik.isChecked())
        ao_siphiu = int(self.tick_siphiu.isChecked())
        ao_alpha_map = int(self.tick_alpha.isChecked())
        chue_node_poly,list_mat_mi_alpha = sangkhuen(chue_file,khanat,yaek_poly,ao_bs,ao_kraduk,ao_ik,ao_siphiu,ao_alpha_map)
        # เมื่อสร้างสำเร็จแล้วให้บันทึกค่าที่เลือกไว้เป็นค่าตั้งต้นสำหรับคราวต่อไป
        with codecs.open(self.file_khatangton,'w','utf-8') as f:
            f.write(u'ชื่อไฟล์ = '+chue_file+'\n')
            f.write(u'ขนาด = '+unicode(self.chong_khanat.text())+'\n')
            f.write(u'แยกโพลิกอนตามวัสดุ = %d\n'%yaek_poly)
            f.write(u'สร้าง blend shape = %d\n'%ao_bs)
            f.write(u'สร้างกระดูก = %d\n'%ao_kraduk)
            f.write(u'สร้าง IK = %d\n'%ao_ik)
            f.write(u'ใส่สีผิว = %d\n'%ao_siphiu)
            f.write(u'สร้าง alpha map = %d\n'%ao_alpha_map)
        self.close()
        # เปิดหน้าต่างสำหรับคัดเลือกวัสดุที่จะทำอัลฟาแม็ป
        if(list_mat_mi_alpha):
            self.natangmai = Natang_alpha(chue_file,list_mat_mi_alpha)
            self.natangmai.show()



# หน้าต่างคัดเลือกวัสดุที่จะเอาอัลฟาแม็ป
class Natang_alpha(QWidget):
    def __init__(self,chue_file,list_mat_mi_alpha):
        QWidget.__init__(self,None,Qt.WindowStaysOnTopHint)
        self.chue_file = chue_file
        self.list_mat_mi_alpha = list_mat_mi_alpha
        self.setWindowTitle(u'~ เลือกว่าวัสดุไหนจะเอา alpha map ~')
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
        
        self.pum_setsin = QPushButton(u'เสร็จสิ้น')
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