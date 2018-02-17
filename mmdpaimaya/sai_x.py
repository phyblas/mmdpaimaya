# -*- coding: utf-8 -*-
u'''
โค้ดสำหรับนำเข้าไฟล์แบบจำลอง .x เข้ามาในมายา
'''

import maya.cmds as mc
import sys,os,math,re,time
import maya.OpenMaya as om
from mmdpaimaya.chipatha import romaji,chuedidi,chueam_placed2d

class Material:
    def __init__(self):
        'วัสดุ'
        
class Xdata:
    def __init__(self,chue_tem_file):
        self.posizioni_vertici = [] # ลิสต์ตำแหน่งของจุดยอดทั้งหมด
        self.uv_vertici = [] # ลิสต์ค่า uv ของจุดยอดทั้งหมด
        self.indici_vertici = [] # ลิสต์ดัชนีของจุดยอดที่ใช้ในแต่ละหน้า
        self.indici_materiali = [] # ลิสต์ดัชนีบอกวัสดุที่ใช้ในแต่ละหน้า
        self.materiali = [] # ลิสต์วัสดุทั้งหมด
        self.tex = [] # ลิสต์เก็บเท็กซ์เจอร์ทั้งหมด
        n_tex = 0
        chaimaidai = [] # ลิสต์เก็บดัชนีของหน้าที่ใช้การไม่ได้
        
        # เปิดไฟล์ขึ้นมาเพื่ออ่านทีละบรรทัดดึงข้อมูล
        with open(chue_tem_file,'r') as file_x:
            s = file_x.readline()
            while(s):
                s = s.strip()
                if(s and s.split()[0]=='Mesh'): # หาส่วนที่ให้ข้อมูลตำแหน่งจุดยอด
                    while('{' not in s):
                        s = file_x.readline()
                    s = file_x.readline()
                    n = int(s.split(';')[0])
                    # ไล่ป้อนค่าตำแหน่งจุดยอดเก็บในลิสต์
                    for i in range(n):
                        s = file_x.readline().strip().split(';')
                        self.posizioni_vertici.append([float(s[0]),float(s[1]),-float(s[2])])
                    s = file_x.readline()
                    while(s.strip()==''):
                        s = file_x.readline()
                    n = int(s.split(';')[0])
                    # ไล่ป้อนค่าเลขดัชนีของจุดยอดที่ใช้ในแต่ละหน้าเก็บลงลิสต์
                    for i in range(n):
                        s = file_x.readline().strip()
                        ss = s.split(';')[1].split(',')
                        
                        ic = [int(x) for x in reversed(ss) if x] # ไล่จากจุดท้ายมาหน้า
                        if(len(set(ic))==len(ic)):
                            # ถ้าในหน้าหนึ่งใช้จุดต่างกันทั้งหมดจึงเอาข้อมูลจุดนั้นมาใช้
                            self.indici_vertici.append(ic)
                        else:
                            # ถ้าในหน้าหนึ่งมีการใช้จุดซ้ำกันให้ตัดทิ้งเลย
                            chaimaidai.append(i)
                if(s and s.split()[0]=='MeshTextureCoords'): # หาส่วนที่ให้ข้อมูลค่า uv
                    while('{' not in s):
                        s = file_x.readline()
                    s = file_x.readline()
                    n = int(s.split(';')[0])
                    # ไล่ป้อนค่า uv ของจุดยอดเก็บลงลิสต์
                    for i in range(n):
                        s = file_x.readline().strip().split(';')
                        if(len(s)<=2 or ',' in s[0]):
                            s = s[0].split(',')
                        self.uv_vertici.append([float(s[0]),1-float(s[1])])
                    while('}' not in s):
                        s = file_x.readline()
                if(s and s.split()[0]=='MeshMaterialList'): # หาส่วนที่แสดงรายชื่อวัสดุต่างๆ
                    while('{' not in s):
                        s = file_x.readline()
                    s = file_x.readline()
                    self.facce = [[]]*int(s.split(';')[0])
                    s = file_x.readline()
                    n = int(s.split(';')[0])
                    for i in range(n-1):
                        s = file_x.readline().strip().split(',')[0]
                        self.indici_materiali += [int(s)]
                    s = file_x.readline().strip().split(';')[0]
                    self.indici_materiali += [int(s)]
                
                while(s and s.split()[0]=='Material'): # หาส่วนที่ไล่เรียงรายชื่อวัสดุ
                    mat = Material()
                    while('{' not in s):
                        s = file_x.readline()
                    s = file_x.readline().strip().split(';')
                    mat.kd = (float(s[0]),float(s[1]),float(s[2])) # สีธรรมชาติ
                    mat.tf = float(s[3]) # ความทึบแสง
                    s = file_x.readline().strip().split(';')
                    mat.ns = float(s[0]) # ขนาดสเป็กคิวลาร์
                    s = file_x.readline().strip().split(';')
                    mat.ks = (float(s[0]),float(s[1]),float(s[2])) # สีสเป็กคิวลาร์
                    s = file_x.readline().strip().split(';')
                    mat.ka = (float(s[0]),float(s[1]),float(s[2])) # สีแอมเบียนต์
                    
                    s = file_x.readline().strip()
                    while(s==''):
                        s = file_x.readline().strip()
                    if(s.split()[0]=='TextureFilename'): # กรณีที่มีเท็กซ์เจอร์
                        while('{' not in s):
                            s = file_x.readline().strip()
                        ss = s.split('{')[1]
                        if(not ss.strip()):
                            ss = file_x.readline().strip()
                        ss = re.findall(r'"(.+?)(?:\*.+)?";',ss)[0]
                        chue_tex = ss.replace(r'\\','/')
                        if(chue_tex in self.tex): # เท็กซ์เจอร์มีอยู่แล้ว ใช้ดัชนีนั้น
                            mat.tex = self.tex.index(chue_tex)
                        else: # ยังไม่มีเท็กซ์เจอร์นี้ ใส่เพิ่มเข้าไป ได้เป็นดัชนีใหม่
                            self.tex.append(chue_tex)
                            mat.tex = n_tex
                            n_tex += 1
                        while('}' not in s):
                            s = file_x.readline().strip()
                    else:
                        mat.tex = -1
                    while('}' not in s):
                        s = file_x.readline()
                    
                    self.materiali.append(mat)
                s = file_x.readline()
        
        # ตัดดัชนีของจุดที่ใช้การไม่ได้ออกจากรายการวัสดุด้วย
        for cmd in reversed(chaimaidai):
            self.indici_materiali.pop(cmd)
        
    

def sangkhuen(chue_tem_file,khanat=8,ao_alpha_map=1,yaek_poly=0,watsadu=1,yaek_alpha=0):
    t_roem = time.time() # เริ่มจับเวลา
    chue_model = romaji(chuedidi(os.path.splitext(os.path.basename(chue_tem_file))[0]))
    path_file = os.path.dirname(chue_tem_file)
    xdata = Xdata(chue_tem_file)
    set_mat = set(xdata.indici_materiali)
    set_index_tex = set([m.tex for i,m in enumerate(xdata.materiali) if i in set_mat])
    
    vers = int(mc.about(version=1))>=2018 # เวอร์ชันเป็น 2018 ขึ้นไปหรือไม่
    try:
        from PIL import Image
    except ImportError:
        yaek_alpha = 0
    
    if(watsadu==4): # ดูเวอร์ชันของมายาเพื่อแยกแยะว่าใช้แอตทริบิวต์ของ aiStandard หรือ aiStandardSurface
        attr = [['color','KsColor','opacity','Ks','specularRoughness','Kd'],
                ['baseColor','specularColor','opacity','specular','specularRoughness','base']
        ][vers]
    
    if(watsadu or yaek_poly):
        # สร้างเท็กซ์เจอร์
        list_chue_nod_file = [] # ลิสต์เก็บชื่อโหนดของไฟล์เท็กซ์เจอร์
        list_chue_nod_file_alpha = [] # ลิสต์เก็บชื่อโหนดของไฟล์อัลฟาของเท็กซ์เจอร์
        for i,tex in enumerate(xdata.tex):
            tex = chuedidi(tex)
            path_tem_tex = os.path.join(path_file,tex) # ไฟล์เท็กซ์เจอร์ เพิ่มพาธของไฟล์โมเดลลงไป
            chue_tex = tex.replace('\\','_').replace('/','_').replace('.','_')
            chue_tex = romaji(chue_tex) # เปลี่ยนชื่อเป็นโรมาจิ
            chue_nod_file = chue_tex+'_file_'+chue_model
            chue_nod_file_alpha = chue_nod_file
            if(i in set_index_tex):
                # สร้างโหนดไฟล์เท็กซ์เจอร์
                chue_nod_file = mc.shadingNode('file',at=1,n=chue_nod_file)
                chue_nod_file_alpha = chue_nod_file
                # สร้างโหนด placed2d
                chue_nod_placed2d = mc.shadingNode('place2dTexture',au=1,n=chue_tex+'_placed2d_'+chue_model)
                mc.setAttr(chue_nod_file+'.ftn',path_tem_tex,typ='string')
                
                # เชื่อมค่าต่างๆของโหนด placed2d เข้ากับโหนดไฟล์
                for cp in chueam_placed2d:
                    mc.connectAttr('%s.%s'%(chue_nod_placed2d,cp[0]),'%s.%s'%(chue_nod_file,cp[1]),f=1)
                
                # กรณีที่เลือกว่าจะแยกอัลฟาไปอีกไฟล์ และไฟล์นั้นมีอัลฟาอยู่ด้วย
                if(yaek_alpha and ao_alpha_map and mc.getAttr(chue_nod_file+'.fileHasAlpha')==1):
                    file_phap = Image.open(path_tem_tex) # เปิดอ่านไฟล์ด้วย PIL
                    file_alpha = file_phap.split()[-1] # สกัดเอาเฉพาะอัลฟา
                    pta = os.path.split(path_tem_tex)
                    path_tem_alpha = os.path.join(pta[0],u'00arufa_'+pta[1]) # ชื่อไฟล์ใหม่ที่จะสร้าง แค่เติมคำนำหน้า
                    file_alpha.save(path_tem_alpha) # สร้างไฟล์ค่าอัลฟา
                    chue_nod_file_alpha = mc.shadingNode('file',at=1,n=chue_nod_file+'_alpha') # โหนดไฟล์อัลฟา
                    mc.setAttr(chue_nod_file_alpha+'.ftn',path_tem_alpha,typ='string')
                    mc.setAttr(chue_nod_file_alpha+'.alphaIsLuminance',1)
                    for cp in chueam_placed2d: # เชื่อมกับโหนด placed2d อันเดียวกับของไฟล์ภาพ
                        mc.connectAttr('%s.%s'%(chue_nod_placed2d,cp[0]),'%s.%s'%(chue_nod_file_alpha,cp[1]),f=1)     
            
            list_chue_nod_file.append(chue_nod_file)
            list_chue_nod_file_alpha.append(chue_nod_file_alpha)
        
        # สร้างโหนดวัสดุ
        list_chue_nod_mat = []
        list_chue_nod_sg = []
        for i,mat in enumerate(xdata.materiali):
            if(i not in set_mat):
                list_chue_nod_mat.append('')
                list_chue_nod_sg.append('')
                continue
            chue_mat = u'watsadu%d'%i
            chue_nod_mat = chue_mat+'_mat_'+chue_model
            
            opa = (mat.tf,mat.tf,mat.tf)
            trans = (1-mat.tf,1-mat.tf,1-mat.tf)
            
            if(watsadu==1):
                chue_nod_mat = mc.shadingNode('blinn',asShader=1,n=chue_nod_mat)
                mc.setAttr(chue_nod_mat+'.specularColor',*mat.ks,typ='double3')
                mc.setAttr(chue_nod_mat+'.specularRollOff',0.75**(math.log(max(mat.ns,2**-10))+1))
                mc.setAttr(chue_nod_mat+'.eccentricity',mat.ns*0.01)
            elif(watsadu==2):
                chue_nod_mat = mc.shadingNode('phong',asShader=1,n=chue_nod_mat)
                mc.setAttr(chue_nod_mat+'.specularColor',*mat.ks,typ='double3')
                mc.setAttr(chue_nod_mat+'.cosinePower',max((10000./max(mat.ns,15)**2-3.357)/0.454,2))
            elif(watsadu==3):
                chue_nod_mat = mc.shadingNode('lambert',asShader=1,n=chue_nod_mat)
            
            if(watsadu in [1,2,3]):
                mc.setAttr(chue_nod_mat+'.color',*mat.kd,typ='double3')
                mc.setAttr(chue_nod_mat+'.ambientColor',*mat.ka,typ='double3')
                mc.setAttr(chue_nod_mat+'.transparency',*trans,typ='double3')
            elif(watsadu==4):
                if(vers):
                    chue_nod_mat = mc.shadingNode('aiStandardSurface',asShader=1,n=chue_nod_mat)
                else:
                    chue_nod_mat = mc.shadingNode('aiStandard',asShader=1,n=chue_nod_mat)
                
                mc.setAttr(chue_nod_mat+'.'+attr[0],*mat.kd,typ='double3')
                mc.setAttr(chue_nod_mat+'.'+attr[1],*mat.ks,typ='double3')
                mc.setAttr(chue_nod_mat+'.'+attr[2],*opa,typ='double3')
                mc.setAttr(chue_nod_mat+'.'+attr[3],0.75**(math.log(max(mat.ns,0.36788))+1))
                mc.setAttr(chue_nod_mat+'.'+attr[4],min(mat.ns*0.01,1))
                mc.setAttr(chue_nod_mat+'.'+attr[5],0.8)
            
            i_tex = mat.tex # ดัชนีของเท็กซ์เจอร์ที่จะใช้ใส่วัสดุนี้
            if(i_tex>=0):
                chue_nod_file = list_chue_nod_file[i_tex] # โหนดไฟล์เท็กซ์เจอร์
                # เชื่อมต่อสีจากไฟล์เข้ากับวัสดุ
                if(vers and watsadu==4):
                    mc.connectAttr(chue_nod_file+'.outColor',chue_nod_mat+'.baseColor')
                else:
                    mc.connectAttr(chue_nod_file+'.outColor',chue_nod_mat+'.color')
                # ถ้าเลือกว่าจะทำอัลฟาแม็ปด้วย และไฟล์มีอัลฟาแม็ป
                if(ao_alpha_map and mc.getAttr(chue_nod_file+'.fileHasAlpha')==1):
                    if(xdata.tex[i_tex].split('.')[-1].lower() in ['png','tga','dds','bmp']):
                        if(watsadu in [1,2,3]):
                            mc.connectAttr(chue_nod_file_alpha+'.outTransparency',chue_nod_mat+'.transparency')
                        elif(watsadu==4):
                            mc.connectAttr(chue_nod_file_alpha+'.outAlpha',chue_nod_mat+'.opacityR')
                            mc.connectAttr(chue_nod_file_alpha+'.outAlpha',chue_nod_mat+'.opacityG')
                            mc.connectAttr(chue_nod_file_alpha+'.outAlpha',chue_nod_mat+'.opacityB')
            chue_nod_sg = mc.sets(r=1,nss=1,em=1,n=chue_nod_mat+'SG')
            mc.connectAttr(chue_nod_mat+'.outColor',chue_nod_sg+'.surfaceShader', f=1)
            list_chue_nod_mat.append(chue_nod_mat)
            list_chue_nod_sg.append(chue_nod_sg)
    else:
        0
        
    # วนซ้ำไล่ดึงข้อมูลของแต่ละหน้า
    n_mat = len(xdata.materiali) # จำนวนวัสดุทั้งหมดที่มี
    n_na = len(xdata.indici_vertici) # จำนวนหน้าทั้งหมด
    list_list_index_chut = [[] for _ in [0]*n_mat] # ลิสต์เก็บลิสต์ของดัชนีจุดในแต่ละวัสดุ
    list_list_n_chut_to_na = [[] for _ in [0]*n_mat] # ลิสต์เก็บลิสต์ของจำนวนจุดต่อหน้าในแต่ละวัสดุ
    list_n_na_to_mat = [0]*n_mat # ลิสต์เก็บจำนวนของหน้าต่อวัสดุ
    list_n_index_to_mat = [0]*n_mat # ลิสต์เก็บจำนวนดัชนีจุดต่อวัสดุ
    
    # ไล่ดึงข้อมูลของดัชนีจุดทั้งหมดในแต่ละหน้าแล้วแยกใส่ในลิสต์แยกตามวัสดุ
    for k in range(n_na):
        im = xdata.indici_materiali[k]
        chut_nai_na = xdata.indici_vertici[k]
        list_list_index_chut[im].extend(chut_nai_na)
        list_list_n_chut_to_na[im].append(len(chut_nai_na))
        list_n_na_to_mat[im] += 1
        list_n_index_to_mat[im] += len(chut_nai_na)
    
    # แยกกรณีระหว่างแยกกับไม่แยกโพลิกอน
    if(yaek_poly and watsadu):
        # ถ้าเลือกว่าจะแยกโพลิกอน
        list_chue_nod_poly = []
        nap_na = 0
        nap_index = 0
        for i in range(n_mat):
            chue_nod_sg = list_chue_nod_sg[i]
            n_na_to_mat = list_n_na_to_mat[i]
            if(n_na_to_mat==0):
                continue
            n_index_to_mat = list_n_index_to_mat[i]
            dict_chut = {} # ดิกเก็บเลขดัชนีของจุดยอดที่ถูกใช้
            k = 0 # ค่าดัชนีใหม่
            list_index_chut = []
            for j in range(n_index_to_mat):
                ic = list_list_index_chut[i][j] # ค่าดัชนีจากในข้อมูลเดิม
                if(ic not in dict_chut):
                    dict_chut[ic] = k # จับคู่ดัชนีใหม่กับดัชนีเดิม
                    k += 1
                list_index_chut.append(dict_chut[ic])
            
            index_chut = om.MIntArray(n_index_to_mat)
            for j,ic in enumerate(list_index_chut):
                index_chut.set(ic,j)
            
            array_n_chut_to_na = om.MIntArray(n_na_to_mat) # อาเรย์เก็บจำนวนจุดต่อหน้า
            j = 0
            for n_chut_to_na in list_list_n_chut_to_na[i]:
                array_n_chut_to_na.set(n_chut_to_na,j)
                j += 1
            
            n_chut_to_mat = len(dict_chut) # จำนวนจุดยอดต่อวัสดุ
            chut = om.MFloatPointArray(n_chut_to_mat)
            u = om.MFloatArray(n_chut_to_mat)
            v = om.MFloatArray(n_chut_to_mat)
            
            for ic in dict_chut:
                k = dict_chut[ic]
                # ตั้งค่าตำแหน่งของจุดยอด
                p = xdata.posizioni_vertici[ic]
                p = om.MFloatPoint(p[0]*khanat,p[1]*khanat,p[2]*khanat)
                chut.set(p,k)
                # ตั้งค่า uv
                u[k],v[k] = xdata.uv_vertici[ic]
            
            trans_fn = om.MFnTransform()
            trans_obj = trans_fn.create()
            chue_nod_poly = chue_model+'_%d'%(i+1)
            while(mc.objExists(chue_nod_poly)):
                chue_nod_poly += u'_'
            trans_fn.setName(chue_nod_poly)
            chue_nod_poly = trans_fn.name()
            fn_mesh = om.MFnMesh()
            
            # สร้างโพลิกอน
            fn_mesh.create(n_chut_to_mat,n_na_to_mat,chut,array_n_chut_to_na,index_chut,u,v,trans_obj)
            
            fn_mesh.setName(chue_nod_poly+'Shape')
            fn_mesh.assignUVs(array_n_chut_to_na,index_chut)
            
            # ทำให้โปร่งใสได้ สำหรับอาร์โนลด์
            if(watsadu==4):
                mc.setAttr(chue_nod_poly+'.aiOpaque',0)
            
            # ใส่วัสดุให้กับผิว
            mc.sets(chue_nod_poly+'.f[0:%s]'%(n_na_to_mat-1),fe=chue_nod_sg)
            list_chue_nod_poly.append(chue_nod_poly)
            
            nap_na += n_na_to_mat # นับไล่หน้าต่อ
            nap_index += n_index_to_mat
            
        chue_nod_poly = mc.group(list_chue_nod_poly,n=chue_model)
    else:
        # ถ้าไม่ได้เลือกว่าจะแยกโพลิกอน
        n_chut = len(xdata.posizioni_vertici) # จำนวนจุดยอดของโมเดล
        chut = om.MFloatPointArray(n_chut)
        u = om.MFloatArray(n_chut)
        v = om.MFloatArray(n_chut)
        
        # วนซ้ำไล่ดึงข้อมูลของจุดยอดแต่ละจุด
        for i,p in enumerate(xdata.posizioni_vertici):
            # ตั้งค่าตำแหน่งของจุดยอด
            p = om.MFloatPoint(p[0]*khanat,p[1]*khanat,p[2]*khanat)
            chut.set(p,i)
            # ตั้งค่า uv
            u[i],v[i] = xdata.uv_vertici[i]
        
        n_index = sum(list_n_index_to_mat)
        index_chut = om.MIntArray(n_index) # ค่าดัชนีของจุดทั้งหมด รวมทุกจุดจากทุกวัสดุ
        i = 0
        for list_index_chut in list_list_index_chut:
            for ic in list_index_chut:
                index_chut.set(ic,i)
                i += 1
        
        array_n_chut_to_na = om.MIntArray(n_na) # อาเรย์จำนวนจุดต่อหน้า รวมของทุกวัสดุทั้งหมดเข้าด้วยกัน
        i = 0
        for list_n_chut_to_na in list_list_n_chut_to_na:
            for n_chut_to_na in list_n_chut_to_na:
                array_n_chut_to_na.set(n_chut_to_na,i)
                i += 1
        
        trans_fn = om.MFnTransform()
        trans_obj = trans_fn.create()
        trans_fn.setName(chue_model)
        chue_nod_poly = trans_fn.name()
        fn_mesh = om.MFnMesh()
        
        # สร้างโพลิกอนจากข้อมูลทั้งหมดที่เตรียมไว้
        fn_mesh.create(n_chut,n_na,chut,array_n_chut_to_na,index_chut,u,v,trans_obj)
        fn_mesh.setName(chue_nod_poly+'Shape')
        fn_mesh.assignUVs(array_n_chut_to_na,index_chut)
        
        # ทำให้โปร่งใสได้ สำหรับอาร์โนลด์
        if(watsadu==4):
            mc.setAttr(chue_nod_poly+'.aiOpaque',0)
        
        # ใส่วัสดุ ถ้าเลือกว่าจะเอาสีผิว
        if(watsadu):
            nap_na = 0
            for i in range(n_mat):
                if(i in set_mat):
                    chue_nod_sg = list_chue_nod_sg[i]
                    mc.sets(chue_nod_poly+'.f[%s:%s]'%(nap_na,nap_na+n_na-1),fe=chue_nod_sg) # ใส่วัสดุให้กับผิวตามหน้าที่กำหนด
                    nap_na += list_n_na_to_mat[i] # นับไล่หน้าต่อ
        else: # ถ้าไม่เอาสีผิวก็ป้อนวัสดุตั้งต้นให้
            mc.select(chue_nod_poly)
            mc.hyperShade(a='lambert1')
    
    print(u'作成完了。%.2fかかりました'%(time.time()-t_roem))
    return chue_nod_poly
