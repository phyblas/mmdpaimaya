# -*- coding: utf-8 -*-
u'''
GUI ควบคุมการนำเข้าและส่งออกระหว่าง MMD และมายา
'''
import maya.cmds as mc
import sai_pmx,sai_x,khian_pmx
import imp,os,codecs
from chipatha import khokhwam
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
        QWidget.__init__(self,None)
        self.setWindowFlags(Qt.WindowStaysOnTopHint)
        
        self.file_khatangton = os.path.join(os.path.dirname(__file__),u'khatangton.txt')
        try:
            # อ่านข้อมูลค่าตั้งต้น
            with codecs.open(self.file_khatangton,'r',encoding='utf-8') as f:
                phasa = int(f.readline().split('=')[-1].strip())
                yuthaep = int(f.readline().split('=')[-1].strip())
                chue_file = unicode(f.readline().split('=')[-1].strip())
                khanat = unicode(f.readline().split('=')[-1].strip())
                yaek_poly = int(f.readline().split('=')[-1].strip())
                ao_bs = int(f.readline().split('=')[-1].strip())
                ao_kraduk = int(f.readline().split('=')[-1].strip())
                ao_ik = int(f.readline().split('=')[-1].strip())
                watsadu = int(f.readline().split('=')[-1].strip())
                ao_alpha_map = int(f.readline().split('=')[-1].strip())
                yaek_alpha = int(f.readline().split('=')[-1].strip())
                
                chue_file_mmd = f.readline().split('=')[-1].strip()
                khanat_ok = unicode(f.readline().split('=')[-1].strip())
                chai_kraduk = int(f.readline().split('=')[-1].strip())
                chai_bs = int(f.readline().split('=')[-1].strip())
                chai_watsadu = int(f.readline().split('=')[-1].strip())
                lok_tex = int(f.readline().split('=')[-1].strip())
                mod_sph = int(f.readline().split('=')[-1].strip())
                tex_sph = unicode(f.readline().split('=')[-1].strip())
        except:
            # ถ้าไม่มีไฟล์อยู่ก็สร้างค่าตั้งต้นใหม่
            phasa = 0
            yuthaep = 0
            chue_file = u''
            khanat = '8.0'
            yaek_poly = 0
            ao_bs = 1
            ao_kraduk = 1
            ao_ik = 0
            watsadu = 1
            ao_alpha_map = 2
            yaek_alpha = 0
            chue_file_mmd = ''
            khanat_ok = '0.125'
            chai_kraduk = 1
            chai_bs = 1
            chai_watsadu = 1
            lok_tex = 1
            mod_sph = 0
            tex_sph = ''
        
        
        self.khronglak = QVBoxLayout()
        self.setLayout(self.khronglak)
        
        # ส่วนเปลี่ยนภาษา
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
        
        self.phaeng = QTabWidget()
        self.khronglak.addWidget(self.phaeng) # โครงหลักของหน้าต่าง
        
        # โครงส่วนนำเข้า
        widget = QWidget()
        self.phaeng.addTab(widget,'mmd > maya')
        self.khrong_mmdmaya = QVBoxLayout()
        widget.setLayout(self.khrong_mmdmaya)
        
        # โครงส่วนส่งออก
        widget = QWidget()
        self.phaeng.addTab(widget,'maya > mmd')
        self.khrong_mayammd = QVBoxLayout() # โครงหลักของหน้าต่าง
        widget.setLayout(self.khrong_mayammd)
        
        self.phaeng.setCurrentIndex(yuthaep) # ตั้งแท็บเริ่มต้น
        
        
        
        # ส่วนนำเข้า
        qhbl = QHBoxLayout()
        self.khrong_mmdmaya.addLayout(qhbl)
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
        self.khrong_mmdmaya.addLayout(qhbl)
        self.ql_khanat = QLabel()
        self.ql_khanat.setFont(font)
        qhbl.addWidget(self.ql_khanat) # ช่องใส่ขนาด
        self.chong_khanat = QLineEdit(khanat)
        qhbl.addWidget(self.chong_khanat)
        self.chong_khanat.setFixedWidth(80)
        qhbl.addWidget(QLabel(u'x'))
        qhbl.addStretch()
        
        qhbl = QHBoxLayout()
        self.khrong_mmdmaya.addLayout(qhbl)
        self.tick_yaek_poly = QCheckBox()
        self.tick_yaek_poly.setFont(font)
        qhbl.addWidget(self.tick_yaek_poly)
        self.tick_yaek_poly.setChecked(yaek_poly)
        self.tick_yaek_poly.clicked.connect(self.sang_kraduk_dai_mai)
        
        qhbl = QHBoxLayout()
        self.khrong_mmdmaya.addLayout(qhbl)
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
        self.khrong_mmdmaya.addLayout(qhbl)
        self.ql_watsadu = QLabel()
        self.ql_watsadu.setFont(font)
        qhbl.addWidget(self.ql_watsadu)
        self.lueak_phiu = QComboBox()
        ss = [u'',u'blinn',u'phong',u'lambert'] # ชนิดของวัสดุ
        if(mc.objExists('defaultArnoldRenderOptions')): # ถ้ามีอาร์โนลด์อยู่
            if(int(mc.about(version=1))<2018):
                ss.append(u'aiStandard (Arnold)') # ก็ใส่ aiStandard ไปด้วย
            else:
                ss.append(u'aiStandardSurface (Arnold)') # ก็ใส่ aiStandard ไปด้วย
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
        self.khrong_mmdmaya.addWidget(ql)
        
        # เลือกวิธีการจัดการกับอัลฟา
        qhbl = QHBoxLayout()
        self.khrong_mmdmaya.addLayout(qhbl)
        qhbl.addWidget(QLabel('      '))
        self.tick_alpha = [QButtonGroup(),QRadioButton(),QRadioButton(),QRadioButton()]
        self.tick_alpha[ao_alpha_map+1].setChecked(1)
        
        for i in range(1,4):
            self.tick_alpha[0].addButton(self.tick_alpha[i],i)
            self.tick_alpha[i].setFont(font)
            qhbl.addWidget(self.tick_alpha[i])
        qhbl.addStretch()
        
        qhbl = QHBoxLayout()
        self.khrong_mmdmaya.addLayout(qhbl)
        self.tick_yaek_alpha = QCheckBox()
        self.tick_yaek_alpha.setFont(font)
        qhbl.addWidget(self.tick_yaek_alpha)
        try:
            import PIL
            self.mipil = 1
            self.tick_yaek_alpha.setChecked(yaek_alpha)
        except ImportError:
            self.mipil = 0
            self.tick_yaek_alpha.setChecked(0)
        qhbl.addStretch()
        
        self.sang_alpha_dai_mai()
        self.sang_kraduk_dai_mai()
        
        self.pum_roem_sang = QPushButton() # ปุ่มเริ่มสร้าง
        self.pum_roem_sang.setFont(font)
        self.khrong_mmdmaya.addWidget(self.pum_roem_sang)
        self.pum_roem_sang.clicked.connect(self.roem_sang)
        
        
        
        # ส่วนส่งออก
        qhbl = QHBoxLayout()
        self.khrong_mayammd.addLayout(qhbl)
        self.ql_chue_file_mmd = QLabel()
        self.ql_chue_file_mmd.setFont(font)
        qhbl.addWidget(self.ql_chue_file_mmd)
        self.chong_chue_file_mmd = QLineEdit(chue_file_mmd) # ช่องใส่ชื่อไฟล์
        qhbl.addWidget(self.chong_chue_file_mmd)
        self.chong_chue_file_mmd.setFixedWidth(300)
        self.pum_lueak_file_mmd = QPushButton(u'...') # ปุ่มค้นไฟล์
        qhbl.addWidget(self.pum_lueak_file_mmd)
        self.pum_lueak_file_mmd.clicked.connect(self.lueak_file_mmd)
        qhbl.addStretch()
        
        qhbl = QHBoxLayout()
        self.khrong_mayammd.addLayout(qhbl)
        self.ql_khanat_mmd = QLabel()
        self.ql_khanat_mmd.setFont(font)
        qhbl.addWidget(self.ql_khanat_mmd) # ช่องใส่ขนาด
        self.chong_khanat_mmd = QLineEdit(khanat_ok)
        qhbl.addWidget(self.chong_khanat_mmd)
        self.chong_khanat_mmd.setFixedWidth(80)
        qhbl.addWidget(QLabel(u'x'))
        qhbl.addStretch()
        
        qhbl = QHBoxLayout()
        self.khrong_mayammd.addLayout(qhbl)
        self.tick_kraduk_mmd = QCheckBox()
        self.tick_kraduk_mmd.setFont(font)
        qhbl.addWidget(self.tick_kraduk_mmd)
        self.tick_kraduk_mmd.setChecked(chai_kraduk)
        
        qhbl = QHBoxLayout()
        self.khrong_mayammd.addLayout(qhbl)
        self.tick_bs_mmd = QCheckBox()
        self.tick_bs_mmd.setFont(font)
        qhbl.addWidget(self.tick_bs_mmd)
        self.tick_bs_mmd.setChecked(chai_bs)
        
        qhbl = QHBoxLayout()
        self.khrong_mayammd.addLayout(qhbl)
        self.tick_watsadu_mmd = QCheckBox()
        self.tick_watsadu_mmd.setFont(font)
        qhbl.addWidget(self.tick_watsadu_mmd)
        self.tick_watsadu_mmd.setChecked(chai_watsadu)
        
        qhbl = QHBoxLayout()
        self.khrong_mayammd.addLayout(qhbl)
        self.tick_lok_tex = QCheckBox()
        self.tick_lok_tex.setFont(font)
        qhbl.addWidget(self.tick_lok_tex)
        self.tick_lok_tex.setChecked(lok_tex)
        
        qhbl = QHBoxLayout()
        self.khrong_mayammd.addLayout(qhbl)
        self.ql_lueak_sph = QLabel()
        self.ql_lueak_sph.setFont(font)
        qhbl.addWidget(self.ql_lueak_sph)
        self.lueak_sph = QComboBox()
        for s in [u'- 無効',u'× 乗算スフィア',u'+ 加算スフィア',u'サブTex']:
            self.lueak_sph.addItem(s)
        self.lueak_sph.setCurrentIndex(mod_sph)
        if(self.lueak_sph.currentIndex()==-1):
            self.lueak_sph.setCurrentIndex(1)
        self.lueak_sph.setFont(font)
        qhbl.addWidget(self.lueak_sph)
        qhbl.addStretch()
        
        qhbl = QHBoxLayout()
        self.khrong_mayammd.addLayout(qhbl)
        self.ql_sph = QLabel()
        self.ql_sph.setFont(font)
        qhbl.addWidget(self.ql_sph) # ช่องใส่ขนาด
        self.chong_sph = QLineEdit(tex_sph)
        qhbl.addWidget(self.chong_sph)
        self.chong_sph.setFixedWidth(160)
        qhbl.addStretch()
        
        self.khrong_mayammd.addStretch()
        
        self.pum_roem_sang_mmd = QPushButton() # ปุ่มเริ่มสร้าง
        self.pum_roem_sang_mmd.setFont(font)
        self.khrong_mayammd.addWidget(self.pum_roem_sang_mmd)
        self.pum_roem_sang_mmd.clicked.connect(self.roem_sang)
        
        
        
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
        self.tick_yaek_alpha.setEnabled(tp and self.mipil)
    
    def sang_ik_dai_mai(self):
        self.tick_ik.setEnabled(self.tick_kraduk.isChecked())
    
    # เริ่มสร้างโมเดล
    def roem_sang(self):
        # ดึงข้อมูลจากช่องต่างๆที่กรอกและติ๊กไว้
        phasa = self.lueak_phasa[0].checkedId()-1
        yuthaep = self.phaeng.currentIndex() 
        chue_file = unicode(self.chong_chue_file.text())
        khanat = float(self.chong_khanat.text())
        yaek_poly = int(self.tick_yaek_poly.isChecked())
        ao_bs = int(self.tick_bs.isChecked())
        ao_kraduk = int(self.tick_kraduk.isChecked())
        ao_ik = int(self.tick_ik.isChecked())
        watsadu = self.lueak_phiu.currentIndex()
        ao_alpha_map = self.tick_alpha[0].checkedId()-1
        yaek_alpha = int(self.tick_yaek_alpha.isChecked())
        
        chue_file_mmd = unicode(self.chong_chue_file_mmd.text())
        if('.' not in chue_file_mmd):
            chue_file_mmd += '.pmx'
        khanat_ok = float(self.chong_khanat_mmd.text())
        chai_kraduk = int(self.tick_kraduk_mmd.isChecked())
        chai_bs = int(self.tick_bs_mmd.isChecked())
        chai_watsadu = int(self.tick_watsadu_mmd.isChecked())
        lok_tex = int(self.tick_lok_tex.isChecked())
        mod_sph = self.lueak_sph.currentIndex()
        tex_sph = unicode(self.chong_sph.text())
        
        if(yuthaep==0):
            if(chue_file[-2]!='.'):
                # ถ้าเป็น .pmd หรือ .pmx
                chue_node_poly,list_mat_mi_alpha = sai_pmx.sangkhuen(chue_file,khanat,yaek_poly,ao_bs,ao_kraduk,ao_ik,watsadu,ao_alpha_map,yaek_alpha)
            else:
                # ถ้าเป็น .x
                sai_x.sangkhuen(chue_file,khanat,ao_alpha_map,yaek_poly,watsadu,yaek_alpha)
                list_mat_mi_alpha = []
        else:
            khian_pmx.khiankhuen(chue_file_mmd,khanat_ok,chai_kraduk,chai_bs,chai_watsadu,lok_tex,mod_sph,tex_sph)
        
        # เมื่อสร้างสำเร็จแล้วให้บันทึกค่าที่เลือกไว้เป็นค่าตั้งต้นสำหรับคราวต่อไป
        with codecs.open(self.file_khatangton,'w','utf-8') as f:
            f.write(u'ภาษา = %d\n'%phasa)
            f.write(u'อยู่แท็บ = %d\n'%yuthaep)
            f.write(u'ชื่อไฟล์ = %s\n'%chue_file)
            f.write(u'ขนาด = %s\n'%unicode(self.chong_khanat.text()))
            f.write(u'แยกโพลิกอนตามวัสดุ = %d\n'%yaek_poly)
            f.write(u'สร้าง blend shape = %d\n'%ao_bs)
            f.write(u'สร้างกระดูก = %d\n'%ao_kraduk)
            f.write(u'สร้าง IK = %d\n'%ao_ik)
            f.write(u'วัสดุ = %d\n'%watsadu)
            f.write(u'สร้าง alpha map = %d\n'%ao_alpha_map)
            f.write(u'แยกไฟล์ alpha = %d\n'%yaek_alpha)
            f.write(u'ชื่อไฟล์ pmx = %s\n'%chue_file_mmd)
            f.write(u'ขนาดส่งออก = %s\n'%unicode(self.chong_khanat_mmd.text()))
            f.write(u'ใช้กระดูก = %d\n'%chai_kraduk)
            f.write(u'ใช้เบลนด์เชป = %d\n'%chai_bs)
            f.write(u'ใช้วัสดุ = %d\n'%chai_watsadu)
            f.write(u'คัดลอกเท็กซ์เจอร์ = %d\n'%lok_tex)
            f.write(u'โหมดของ sph = %d\n'%mod_sph)
            f.write(u'ไฟล์ sph = %s\n'%tex_sph)
            
        self.close()
        # เปิดหน้าต่างสำหรับคัดเลือกวัสดุที่จะทำอัลฟาแม็ป
        if(yuthaep==0 and list_mat_mi_alpha and ao_alpha_map==1):
            self.natangmai = Natang_alpha(chue_file,list_mat_mi_alpha,watsadu,phasa)
            self.natangmai.show()
    
    # เมื่อกดปุ่มค้นไฟล์
    def lueak_file_mmd(self):
        self.setWindowFlags(self.windowFlags() & ~Qt.WindowStaysOnTopHint)
        chue_file_mmd = QFileDialog.getSaveFileName()
        if(type(chue_file_mmd)==tuple):
            chue_file_mmd = unicode(chue_file_mmd[0])
        else:
            chue_file_mmd = unicode(chue_file_mmd)
        self.chong_chue_file_mmd.setText(chue_file_mmd)
        self.setWindowFlags(self.windowFlags() | Qt.WindowStaysOnTopHint)
        self.show()
        
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
        self.tick_yaek_alpha.setText(khokhwam[12][ps])
        self.pum_roem_sang.setText(khokhwam[13][ps])
        
        self.ql_chue_file_mmd.setText(khokhwam[16][ps])
        self.ql_khanat_mmd.setText(khokhwam[2][ps])
        self.tick_kraduk_mmd.setText(khokhwam[5][ps])
        self.tick_bs_mmd.setText(khokhwam[17][ps])
        self.tick_watsadu_mmd.setText(khokhwam[18][ps])
        self.tick_lok_tex.setText(khokhwam[19][ps])
        self.ql_lueak_sph.setText(khokhwam[20][ps])
        self.ql_sph.setText(khokhwam[21][ps])
        self.pum_roem_sang_mmd.setText(khokhwam[22][ps])

# หน้าต่างคัดเลือกวัสดุที่จะเอาอัลฟาแม็ป
class Natang_alpha(QWidget):
    def __init__(self,chue_file,list_mat_mi_alpha,watsadu,ps=0):
        QWidget.__init__(self,None,Qt.WindowStaysOnTopHint)
        self.chue_file = chue_file
        self.list_mat_mi_alpha = list_mat_mi_alpha
        self.watsadu = watsadu
        self.setWindowTitle(khokhwam[14][ps])
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
        
        self.pum_setsin = QPushButton(khokhwam[15][ps])
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
        try:
            tex = list_connect[list_connect.index(mat+'.color')+1].replace('.outColor','')
        except:
            tex = list_connect[list_connect.index(mat+'.baseColor')+1].replace('.outColor','')
        if(self.klum_tick_bs.button(i).isChecked()):
            # ติ๊กเอา ให้ทำการเชื่อมต่อ
            if(self.watsadu!=4):
                mc.connectAttr(tex+'.outTransparency',mat+'.transparency')
            else:
                mc.connectAttr(tex+'.outAlpha',mat+'.opacityR')
                mc.connectAttr(tex+'.outAlpha',mat+'.opacityG')
                mc.connectAttr(tex+'.outAlpha',mat+'.opacityB')
            print(u'%sと%sを繋ぐ'%(mat,tex))
        else:
            # ติ๊กไม่เอา ให้ตัดการเชื่อมต่อ
            if(self.watsadu!=4):
                mc.disconnectAttr(tex+'.outTransparency',mat+'.transparency')
            else:
                mc.disconnectAttr(tex+'.outAlpha',mat+'.opacityR')
                mc.disconnectAttr(tex+'.outAlpha',mat+'.opacityG')
                mc.disconnectAttr(tex+'.outAlpha',mat+'.opacityB')
            print(u'%sから%sを外す'%(mat,tex))
    
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