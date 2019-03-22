# -*- coding: utf-8 -*-
u'''
โค้ดสำหรับนำเข้าไฟล์แบบจำลอง .pmx หรือ .pmd เข้ามาในมายา
'''

import maya.cmds as mc
import pymel.core as pm
import sys,os,math,itertools,time,codecs
import maya.OpenMaya as om
import maya.OpenMayaAnim as oma
import pymeshio.pmx.reader
import pymeshio.pmd.reader
import pymeshio.converter
from chipatha import romaji,chuedidi,cross,chueam_placed2d

# อ่านโมเดล
def an_model(chue_tem_file):
    # ถ้าเป็น pmd ให้แปลงเป็น pmx ก่อนค่อยดำเนินการต่อ
    if(chue_tem_file[-3:]=='pmx'):
        mmddata = pymeshio.pmx.reader.read_from_file(chue_tem_file)
    elif('pmd' in chue_tem_file):
        mmddata = pymeshio.pmd.reader.read_from_file(chue_tem_file)
        mmddata = pymeshio.converter.pmd_to_pmx(mmddata)
    else:
        print('pmxとpmdファイルしか使用できません')
        raise
    return mmddata



# สร้างโพลิกอน รวมทั้งวัสดุและเท็กซ์เจอร์
def sang_poly(chue_tem_file,mmddata,khanat=8,ao_alpha_map=1,yaek_poly=0,watsadu=1,yaek_alpha=0):
    try:
        from PIL import Image
    except ImportError:
        yaek_alpha = 0
    
    chue_file = os.path.basename(chue_tem_file) # ชื่อไฟล์ไม่รวมพาธ
    # ชื่อโมเดลเอาชื่อไฟล์มาตัดสกุลออกแล้วเปลี่ยนเป็นภาษาญี่ปุ่นเป็นโรมาจิให้หมด
    chue_model = romaji(chuedidi(mmddata.name,os.path.splitext(chue_file)[0]))
    vers = int(mc.about(version=1).split(' ')[0])>=2018 # เวอร์ชันเป็น 2018 ขึ้นไปหรือไม่
    
    print(u'面を作成中')
    if(yaek_poly):
        # ถ้าเลือกว่าจะแยกโพลิกอนก็ยังไม่ต้องทำอะไร
        list_chue_nod_poly = []
    else:
        # ถ้าไม่ได้เลือกว่าจะแยกโพลิกอนก็ให้สร้างโพลิกอนผิวเลย
        n_chut = len(mmddata.vertices) # จำนวนจุดยอดของโมเดล
        chut = om.MFloatPointArray(n_chut)
        u = om.MFloatArray(n_chut)
        v = om.MFloatArray(n_chut)
        # วนซ้ำไล่ดึงข้อมูลของจุดยอดแต่ละจุด
        for i,c in enumerate(mmddata.vertices):
            # ตั้งค่าตำแหน่งของจุดยอด
            p = c.position
            p = om.MFloatPoint(p.x*khanat,p.y*khanat,-p.z*khanat)
            chut.set(p,i)
            # ตั้งค่า uv
            u[i] = c.uv.x
            v[i] = 1.-c.uv.y
        
        n_index = 0 # จำนวนจุดที่ใช้ได้
        list_index_chut = []
        # วนซ้ำเพื่อป้อนค่าดัชนีของจุด
        for i in range(0,len(mmddata.indices),3):
            ic0 = mmddata.indices[i]
            ic1 = mmddata.indices[i+1]
            ic2 = mmddata.indices[i+2]
            if(ic0!=ic1!=ic2!=ic0): # หน้าที่ใช้ได้คือจะต้องไม่ใช้จุดซ้ำกันในหน้าเดียว
                list_index_chut.extend([ic2,ic1,ic0]) # ใส่จุดลงในลิสต์
                n_index += 3

        index_chut = om.MIntArray(n_index)
        for i,ic in enumerate(list_index_chut):
            index_chut.set(ic,i)

        n_na = n_index/3 # จำนวนหน้า
        array_n_chut_to_na = om.MIntArray(n_na,3) # จำนวนจุดต่อหน้า ตั้งให้แต่ละหน้ามี 3 จุดทั้งหมด
        
        trans_fn = om.MFnTransform()
        trans_obj = trans_fn.create()
        trans_fn.setName(chue_model)
        chue_nod_poly = trans_fn.name()
        fn_mesh = om.MFnMesh()
        # สร้างโพลิกอนจากข้อมูลทั้งหมดที่เตรียมไว้
        fn_mesh.create(n_chut,n_na,chut,array_n_chut_to_na,index_chut,u,v,trans_obj)
        fn_mesh.setName(chue_nod_poly+'Shape')
        fn_mesh.assignUVs(array_n_chut_to_na,index_chut)
        
        # เพิ่มค่าองค์ประกอบที่บอกว่ามาจาก MMD
        mc.addAttr(chue_nod_poly,ln='chakMMD',nn=u'MMDから',at='bool')
        mc.setAttr(chue_nod_poly+'.chakMMD',1)
        
        # ทำให้โปร่งใสได้ สำหรับอาร์โนลด์
        if(watsadu==4):
            mc.setAttr(chue_nod_poly+'.aiOpaque',0)
        
        # ถ้าไม่เอาสีผิวก็ให้ใส่ผิวตั้งต้นแล้วก็ไม่ต้องสร้างวัสดุแล้ว
        if(not watsadu):
            mc.select(chue_nod_poly)
            mc.hyperShade(a='lambert1')
            return chue_nod_poly,[]
    
    
    
    # สร้างวัสดุพื้นผิว
    path_file = os.path.dirname(chue_tem_file) # พาธของไฟล์โมเดล
    set_index_tex = set([mat.texture_index for mat in mmddata.materials]) # เซ็ตของไฟล์เท็กซ์เจอร์ที่ถูกใช้
    list_chue_nod_file = [] # ลิสต์เก็บชื่อโหนดของไฟล์เท็กซ์เจอร์
    list_chue_nod_file_alpha = [] # ลิสต์เก็บชื่อโหนดของไฟล์อัลฟาของเท็กซ์เจอร์
    for i,tex in enumerate(mmddata.textures):
        path_tem_tex = os.path.join(*([path_file]+tex.split('\\'))) # ไฟล์เท็กซ์เจอร์ เพิ่มพาธของไฟล์โมเดลลงไป
        chue_tex = tex.replace('\\','_').replace('/','_').replace('.','_')
        chue_tex = romaji(chue_tex) # เปลี่ยนชื่อเป็นโรมาจิ
        
        chue_nod_file = chue_tex+'_file_'+chue_model#+'_%d'%os.stat(chue_tem_file).st_mtime
        chue_nod_file_alpha = chue_nod_file
        if(i in set_index_tex):#if(not mc.objExists(chue_nod_file) and i in set_index_tex):
            # สร้างโหนดไฟล์เท็กซ์เจอร์
            chue_nod_file = mc.shadingNode('file',at=1,n=chue_nod_file)
            chue_nod_file_alpha = chue_nod_file
            mc.setAttr(chue_nod_file+'.ftn',path_tem_tex,typ='string')
            # สร้างโหนด placed2d
            chue_nod_placed2d = mc.shadingNode('place2dTexture',au=1,n=chue_tex+'_placed2d_'+chue_model)
            
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
    
    
    
    list_mat_ao_alpha = []
    # ถ้าเลือกว่าจะทำอัลฟาแม็ป
    if(ao_alpha_map):
        try:
            # ลองหาดูว่าไฟล์โมเดลเคยมีบันทึกการทำอัลฟาแม็ปหรือไม่ ถ้ามีก็ดึงข้อมูลที่ว่าวัสดุไหนจะทำอัลฟาแม็ป
            with codecs.open(os.path.join(os.path.dirname(__file__),u'modelalpha.txt'),'r','utf-8') as f:
                for thaeo in f:
                    if(chue_tem_file in thaeo):
                        list_mat_ao_alpha = f.readline()[1:].strip().split('::')
                        break
        except: 0
    
    # สร้างโหนดวัสดุ
    nap_na = 0
    list_mat_mi_alpha = [] # ลิสต์เก็บวัสดุที่มีอัลฟา
    if(watsadu==4): # ดูเวอร์ชันของมายาเพื่อแยกแยะว่าใช้แอตทริบิวต์ของ aiStandard หรือ aiStandardSurface
        attr = [['color','KsColor','opacity','Ks','specularRoughness','Kd'],
                ['baseColor','specularColor','opacity','specular','specularRoughness','base']
        ][vers]
    # เริ่มวนไล่สร้างวัสดุทีละอัน
    for i,mat in enumerate(mmddata.materials):
        n_index = mat.vertex_count # จำนวนดัชนีจุด (เป็น 3 เท่าของจำนวนหน้า)
        if(n_index==0):
            continue
        n_na = n_index/3 # จำนวนหน้าที่วัสดุจะไปแปะลง
        
        # ตั้งชื่อให้เป็นโรมาจิ
        chue_mat = romaji(chuedidi(mat.name,u'watsadu%d'%i))
        
        chue_nod_mat = chue_mat+'_mat_'+chue_model#+'_%d'%os.stat(chue_tem_file).st_mtime
        if(0):#if(mc.objExists(chue_nod_mat)):
            chue_nod_sg = chue_nod_mat+'SG'
        else:
            # ดึงข้อมูลค่าคุณสมบัติต่างๆของวัสดุ
            i_tex = mat.texture_index # ดัชนีของเท็กซ์เจอร์ที่จะใช้ใส่วัสดุนี้
            dc = (mat.diffuse_color.r,mat.diffuse_color.g,mat.diffuse_color.b)
            ambc = (mat.ambient_color.r,mat.ambient_color.g,mat.ambient_color.b)
            spec = (mat.specular_color.r,mat.specular_color.g,mat.specular_color.b)
            opa = (mat.alpha,mat.alpha,mat.alpha)
            trans = (1-mat.alpha,1-mat.alpha,1-mat.alpha)
            sf = mat.specular_factor
            # สร้างโหนดวัสดุและตั้งค่าคุณสมบัติต่างๆของวัสดุตามข้อมูลที่ดึงมาได้
            if(watsadu==1):
                chue_nod_mat = mc.shadingNode('blinn',asShader=1,n=chue_nod_mat)
                mc.setAttr(chue_nod_mat+'.specularColor',*spec,typ='double3')
                mc.setAttr(chue_nod_mat+'.specularRollOff',0.75**(math.log(max(sf,2**-10),2)+1))
                mc.setAttr(chue_nod_mat+'.eccentricity',sf*0.01)
            elif(watsadu==2):
                chue_nod_mat = mc.shadingNode('phong',asShader=1,n=chue_nod_mat)
                mc.setAttr(chue_nod_mat+'.specularColor',*spec,typ='double3')
                mc.setAttr(chue_nod_mat+'.cosinePower',max((10000./max(sf,15)**2-3.357)/0.454,2))
            elif(watsadu==3):
                chue_nod_mat = mc.shadingNode('lambert',asShader=1,n=chue_nod_mat)
            
            if(watsadu in [1,2,3]):
                mc.setAttr(chue_nod_mat+'.color',*dc,typ='double3')
                if(i_tex==-1):
                    # กรณีที่ไม่ได้ใช้เท็กซ์เจอร์ แอมเบียนต์มักถูกปรับตามสีหลัก ต้องทำการปรับคืน
                    c = []
                    for a,d in zip(ambc,dc):
                        if(d!=0):
                            c.append(min(a/d,1))
                        else:
                            c.append(0)
                    mc.setAttr(chue_nod_mat+'.ambientColor',*ambc,typ='double3')
                else:
                    mc.setAttr(chue_nod_mat+'.ambientColor',*ambc,typ='double3')
                mc.setAttr(chue_nod_mat+'.transparency',*trans,typ='double3')
            elif(watsadu==4):
                # ใช้วัสดุเป็น aiStandard หรือ aiStandardSurface แล้วแต่เวอร์ชัน
                if(vers):
                    chue_nod_mat = mc.shadingNode('aiStandardSurface',asShader=1,n=chue_nod_mat)
                else:
                    chue_nod_mat = mc.shadingNode('aiStandard',asShader=1,n=chue_nod_mat)
                    
                mc.setAttr(chue_nod_mat+'.'+attr[0],*dc,typ='double3')
                mc.setAttr(chue_nod_mat+'.'+attr[1],*spec,typ='double3')
                mc.setAttr(chue_nod_mat+'.'+attr[2],*opa,typ='double3')
                mc.setAttr(chue_nod_mat+'.'+attr[3],0.75**(math.log(max(sf,0.5),2)+1))
                mc.setAttr(chue_nod_mat+'.'+attr[4],min(sf*0.01,1))
                mc.setAttr(chue_nod_mat+'.'+attr[5],0.8)
                
            # เก็บชื่อเดิม (ชื่อญี่ปุ่น) ของวัสดุไว้เผื่อใช้
            mc.addAttr(chue_nod_mat,ln='namae',nn=u'名前',dt='string')
            mc.setAttr(chue_nod_mat+'.namae',chuedidi(mat.name),typ='string')
            
            # ถ้าไม่มีเท็กซ์เจอร์จะเป็น -1 ก็ไม่ต้องไปเชื่อมต่อ
            if(i_tex>=0):
                chue_nod_file = list_chue_nod_file[i_tex] # โหนดไฟล์เท็กซ์เจอร์
                # เชื่อมต่อสีจากไฟล์เข้ากับวัสดุ
                if(vers and watsadu==4):
                    mc.connectAttr(chue_nod_file+'.outColor',chue_nod_mat+'.baseColor')
                else:
                    mc.connectAttr(chue_nod_file+'.outColor',chue_nod_mat+'.color')
                
                # ถ้าเลือกว่าจะทำอัลฟาแม็ปด้วย และไฟล์มีอัลฟาแม็ป
                if(ao_alpha_map and mc.getAttr(chue_nod_file+'.fileHasAlpha')==1): #  and mat.alpha==1.
                    if(mmddata.textures[i_tex].split('.')[-1].lower() in ['png','tga','dds','bmp']):
                        if(list_mat_ao_alpha!=[] and chue_mat not in list_mat_ao_alpha and ao_alpha_map==1):
                            # ถ้าไม่มีอยู่ในลิสต์ที่เลือกไว้แล้วว่าจะทำอัลฟาแม็ป
                            ao_alpha = 0
                        else:
                            chue_nod_file_alpha = list_chue_nod_file_alpha[i_tex] # โหนดไฟล์เท็กซ์เจอร์
                            # ถ้ามีอยู่ในลิสต์ที่ต้องการทำ หรือยังไม่ได้บันทึกข้อมูลการเลือกเอาไว้
                            if(watsadu in [1,2,3]):
                                mc.connectAttr(chue_nod_file_alpha+'.outTransparency',chue_nod_mat+'.transparency')
                            elif(watsadu==4):
                                mc.connectAttr(chue_nod_file_alpha+'.outAlpha',chue_nod_mat+'.opacityR')
                                mc.connectAttr(chue_nod_file_alpha+'.outAlpha',chue_nod_mat+'.opacityG')
                                mc.connectAttr(chue_nod_file_alpha+'.outAlpha',chue_nod_mat+'.opacityB')
                            ao_alpha = 1
                        list_mat_mi_alpha.append((chue_nod_mat,chue_mat,ao_alpha))
            
            chue_nod_sg = mc.sets(r=1,nss=1,em=1,n=chue_nod_mat+'SG')
            mc.connectAttr(chue_nod_mat+'.outColor',chue_nod_sg+'.surfaceShader', f=1)
        
        if(yaek_poly):
            # ถ้าเลือกว่าให้แยกโพลิกอนให้ทำการสร้างโพลิกอนแยกตามวัสดุขึ้นมาตรงนี้
            nap_index = nap_na*3
            
            n_index_chaidai = 0
            list_index_chut = []
            dic_chut = {} # ดิกเก็บเลขดัชนีของจุดยอดที่ถูกใช้
            k = 0 # ค่าดัชนีใหม่
            for j in range(0,n_index,3): # ค่าดัชนีจากในไฟล์
                ic0 = mmddata.indices[nap_index+j]
                ic1 = mmddata.indices[nap_index+j+1]
                ic2 = mmddata.indices[nap_index+j+2]
                if(ic0!=ic1!=ic2!=ic0):
                    if(ic0 not in dic_chut):
                        dic_chut[ic0] = k # จับคู่ดัชนีใหม่กับดัชนีในไฟล์
                        k += 1
                    if(ic1 not in dic_chut):
                        dic_chut[ic1] = k
                        k += 1
                    if(ic2 not in dic_chut):
                        dic_chut[ic2] = k
                        k += 1
                    list_index_chut.extend([dic_chut[ic2],dic_chut[ic1],dic_chut[ic0]])
                    n_index_chaidai += 3
            
            index_chut = om.MIntArray(n_index_chaidai)
            for j,ic in enumerate(list_index_chut):
                index_chut.set(ic,j)
            
            n_na_chaidai = n_index_chaidai/3
            array_n_chut_to_na = om.MIntArray(n_na_chaidai,3)
            
            n_chut = len(dic_chut)
            chut = om.MFloatPointArray(n_chut)
            u = om.MFloatArray(n_chut)
            v = om.MFloatArray(n_chut)
            
            for ic in dic_chut:
                k = dic_chut[ic]
                c = mmddata.vertices[ic]
                # ตั้งค่าตำแหน่งของจุดยอด
                p = c.position
                p = om.MFloatPoint(p.x*khanat,p.y*khanat,-p.z*khanat)
                chut.set(p,k)
                # ตั้งค่า uv
                u[k] = c.uv.x
                v[k] = 1.-c.uv.y
            
            trans_fn = om.MFnTransform()
            trans_obj = trans_fn.create()
            chue_nod_poly = chue_model+'_%d'%(i+1)
            while(mc.objExists(chue_nod_poly)):
                chue_nod_poly += u'_'
            trans_fn.setName(chue_nod_poly)
            chue_nod_poly = trans_fn.name()
            fn_mesh = om.MFnMesh()
            
            # สร้างโพลิกอน
            fn_mesh.create(n_chut,n_na_chaidai,chut,array_n_chut_to_na,index_chut,u,v,trans_obj)
            fn_mesh.setName(chue_nod_poly+'Shape')
            fn_mesh.assignUVs(array_n_chut_to_na,index_chut)
            
            # ทำให้โปร่งใสได้ สำหรับอาร์โนลด์
            if(watsadu==4):
                mc.setAttr(chue_nod_poly+'.aiOpaque',0)
                
            # เพิ่มค่าองค์ประกอบที่บอกว่ามาจาก MMD
            mc.addAttr(chue_nod_poly,ln='chakMMD',nn=u'MMDから',at='bool')
            mc.setAttr(chue_nod_poly+'.chakMMD',1)
            
            # ใส่วัสดุให้กับผิว
            mc.sets(chue_nod_poly+'.f[%s:%s]'%(0,n_na_chaidai-1),fe=chue_nod_sg)
            nap_na += n_na # นับไล่หน้าต่อ
            
            list_chue_nod_poly.append(chue_nod_poly)
            
        else:
            # ถ้าไม่ได้เลือกว่าจะแยกโพลิกอนก็แค่ให้นำวัสดุมาแปะกับผิวที่สร้างไว้แล้ว
            mc.sets(chue_nod_poly+'.f[%s:%s]'%(nap_na,nap_na+n_na-1),fe=chue_nod_sg) # ใส่วัสดุให้กับผิวตามหน้าที่กำหนด
            nap_na += n_na # นับไล่หน้าต่อ
    
    if(yaek_poly):
        chue_nod_poly = mc.group(list_chue_nod_poly,n=chue_model)
    return chue_nod_poly,list_mat_mi_alpha

def sang_bs(mmddata,chue_nod_poly,khanat):
    print(u'blend shapeを作成中')
    list_chue_nod_bs = [[],[],[],[]] # ลิสต์เก็บชื่อโหนดเบลนด์เชปแต่ละหมวด (คิ้ว, ตา, ปาก, อื่นๆ)
    list_chue_bs_doem = [[],[],[],[]] # ลิสต์เก็บชื่อเดิม (ชื่อญี่ปุ่น) ของเบลนด์เชปแต่ละหมวด
    list_panel = [[],[],[],[]] # ลิสต์เก็บเลขแสดงแผง เก็บไว้เผื่อใช้ตอนแปลงกลับ
    for i,mo in enumerate(mmddata.morphs):
        # สร้างเบลนด์เชปขึ้นมาเฉพาะกรณีที่เป็นมอร์ฟเลื่อนตำแหน่งจุด มอร์ฟแบบอื่นทำเป็นเบลนด์เชปไม่ได้
        if(mo.morph_type==1):
            # ชื่อเบลนด์เชปต้องแปลงเป็นอักษรโรมัน
            chue_bs = romaji(chuedidi(mo.name,u'bs%d'%i))
            # ลอกโพลิกอนตัวเดิมมาเพื่อใช้ทำเบลนด์เชป
            chue_nod_poly_bs = mc.duplicate(chue_nod_poly,n=chue_bs)[0]
            
            sl = om.MSelectionList()
            sl.add(chue_nod_poly_bs)
            dagpath = om.MDagPath()
            sl.getDagPath(0,dagpath)
            fn_mesh = om.MFnMesh(dagpath)
            chut = om.MFloatPointArray() # สร้างอาเรย์เก็บตำแหน่งจุด
            fn_mesh.getPoints(chut) # ใส่ค่าตำแหน่งจุดให้อาเรย์
            
            for off in mo.offsets:
                vi = off.vertex_index # ดัชนีของจุดที่เปลี่ยนตำแหน่ง
                d = off.position_offset # ค่าตำแหน่งที่เปลี่ยนไปของแต่ละจุด
                p = chut[vi] # ตำแหน่งเดิมของจุดบนโพลิกอน
                chut.set(vi,p.x+d.x*khanat,p.y+d.y*khanat,p.z-d.z*khanat) # แก้ค่าตำแหน่งจุด
            
            fn_mesh.setPoints(chut) # นำค่าตำแหน่งจุดใหม่ที่ได้มาตั้งให้โพลิกอนสำหรับทำเบลนด์เชป
            
            list_chue_nod_bs[mo.panel-1].append(chue_nod_poly_bs)
            list_chue_bs_doem[mo.panel-1].append(chuedidi(mo.name,chue_bs))
            list_panel[mo.panel-1].append(mo.panel)
        else:
            print(u'~! morph '+chuedidi(mo.name)+u'はblend shapeを作れません')
    
    # รวมเป็นลิสต์เดียวต่อเนื่องกัน เรียงตามหมวดหมู่
    list_chue_nod_bs = list(itertools.chain(*list_chue_nod_bs))
    it_chue_bs_doem = (u'%s๑%s๑%d'%(chue_nod_bs,chue_doem,panel) for chue_nod_bs,chue_doem,panel in zip(list_chue_nod_bs,itertools.chain(*list_chue_bs_doem),itertools.chain(*list_panel)))
    
    mc.select(list_chue_nod_bs,chue_nod_poly)
    # สร้างโหนดเบลนด์เชปขึ้นมา
    chue_nod_bs = mc.blendShape(n='bs_'+chue_nod_poly)[0]
    mc.delete(list_chue_nod_bs) # ลบโพลิกอนสำหรับทำเบลนด์เชปทิ้ง ไม่ต้องใช้แล้ว
    # บันทึกชื่อเดิมทั้งหมดของเบลนด์เชปเก็บไว้ เผื่อได้ใช้
    mc.addAttr(chue_nod_bs,ln='namae',nn=u'名前',dt='string')
    mc.setAttr(chue_nod_bs+'.namae',u'๐'.join(it_chue_bs_doem),typ='string')



# สร้างกระดูก
def sang_kraduk(mmddata,chue_nod_poly,khanat,ao_ik):
    print(u'骨を作成中')
    list_chue_nod_kho = [] # ลิสต์เก็บชื่อของโหนดข้อ
    for i,b in enumerate(mmddata.bones):
        # แก้ชื่อข้อต่อให้เป็นโรมาจิ
        chue_kho = romaji(chuedidi(b.name,u'kho%d'%i))
        p = b.position # ตำแหน่งของข้อต่อ
        mc.select(d=1)
        # สร้างข้อต่อตามตำแหน่งที่กำหนด
        chue_nod_kho = mc.joint(p=[p.x*khanat,p.y*khanat,-p.z*khanat],rad=khanat/2,n=chue_kho+'_'+chue_nod_poly)
        
        # เก็บชื่อเดิมไว้เผื่อใช้
        mc.addAttr(chue_nod_kho,ln='namae',nn=u'名前',dt='string')
        mc.setAttr(chue_nod_kho+'.namae',chuedidi(b.name,chue_nod_kho),typ='string')
        
        # ซ่อนข้อต่อที่ไม่จำเป็นต้องเห็น
        if(b.getIkFlag() or not b.getVisibleFlag()):
            mc.setAttr(chue_nod_kho+'.drawStyle',2)
        else:
            mc.setAttr(chue_nod_kho+'.drawStyle',0)
        
        # ตั้งค่าการจัดวางแกนหมุนของข้อ
        if(b.getLocalCoordinateFlag() or b.getFixedAxisFlag()):
            if(b.getFixedAxisFlag()):
                kaen_x = b.fixed_axis
                kaen_z = cross([0.0, 1.0, 0.0],kaen_x)
            else:
                kaen_x = b.local_x_vector
                kaen_z = b.local_z_vector
            kaen_y = cross(kaen_z,kaen_x)
            
            array_mun = [kaen_x[0],kaen_x[1],-kaen_x[2],0.,
                         kaen_y[0],kaen_y[1],-kaen_y[2],0.,
                         kaen_z[0],kaen_z[1],-kaen_z[2],0.,
                         0.,0.,0.,1.]
            matrix_mun = om.MMatrix() # สร้างเมทริกซ์หมุน
            om.MScriptUtil.createMatrixFromList(array_mun,matrix_mun)
            trans = om.MTransformationMatrix(matrix_mun)
            mum_euler = trans.eulerRotation().asVector()
            
            mc.setAttr(chue_nod_kho+'.jointOrientX',math.degrees(mum_euler.x))
            mc.setAttr(chue_nod_kho+'.jointOrientY',math.degrees(mum_euler.y))
            mc.setAttr(chue_nod_kho+'.jointOrientZ',math.degrees(mum_euler.z))
        
        list_chue_nod_kho.append(chue_nod_kho)
    
    list_mi_ik = [] # ลิสต์ของข้อต่อที่มี IK
    list_chue_nod_nok = [] # ลิสต์ของข้อต่อที่อยู่นอกสุด
    
    for i,b in enumerate(mmddata.bones):
        chue_nod_kho = list_chue_nod_kho[i]
            
        if(b.parent_index>=0):
            # ผูกติดข้อต่อแต่ละข้อเข้าด้วยกัน
            chue_nod_parent = list_chue_nod_kho[b.parent_index]
            mc.connectJoint(chue_nod_kho,chue_nod_parent,pm=1)
        else:
            list_chue_nod_nok.append(chue_nod_kho)
        
        # แก้ปัญหากรณีที่มุมหมุนของกระดูกมีค่าแปลกๆ (เกิดขึ้นได้อย่างไรยังไม่รู้แน่ชัด)
        if(round(mc.getAttr(chue_nod_kho+'.rx'))==-360.):
            mc.setAttr(chue_nod_kho+'.rx',0)
        if(round(mc.getAttr(chue_nod_kho+'.ry'))==-360.):
            mc.setAttr(chue_nod_kho+'.ry',0)
        if(round(mc.getAttr(chue_nod_kho+'.rz'))==-360.):
            mc.setAttr(chue_nod_kho+'.rz',0)
        if(round(mc.getAttr(chue_nod_kho+'.rx'))%360==180. and round(mc.getAttr(chue_nod_kho+'.ry'))%360==180. and round(mc.getAttr(chue_nod_kho+'.rz'))%360==180.):
            mc.setAttr(chue_nod_kho+'.rx',0)
            mc.setAttr(chue_nod_kho+'.ry',0)
            mc.setAttr(chue_nod_kho+'.rz',0)
        
        if(b.getExternalRotationFlag()):
            # ตั้งมุมการหมุนให้ข้อที่เปลี่ยนมุมตามการหมุนของข้ออื่น
            chue_nod_effect = list_chue_nod_kho[b.effect_index] # โหนดข้อที่ส่งผลให้
            x = mc.getAttr(chue_nod_effect+'.jointOrientX')
            y = mc.getAttr(chue_nod_effect+'.jointOrientY')
            z = mc.getAttr(chue_nod_effect+'.jointOrientZ')
            mc.setAttr(chue_nod_kho+'.jointOrientX',x)
            mc.setAttr(chue_nod_kho+'.jointOrientY',y)
            mc.setAttr(chue_nod_kho+'.jointOrientZ',z)
            
            # ตั้งเอ็กซ์เพรชชันให้ข้อที่เปลี่ยนมุมตามการหมุนของข้ออื่น
            ef = b.effect_factor
            s = '%s.rotateX = %s.rotateX * %s;\n'%(chue_nod_kho,chue_nod_effect,ef)
            s += '%s.rotateY = %s.rotateY * %s;\n'%(chue_nod_kho,chue_nod_effect,ef)
            s += '%s.rotateZ = %s.rotateZ * %s;\n'%(chue_nod_kho,chue_nod_effect,ef)
            mc.expression(s=s,n='expression_%s_%s'%(chue_nod_kho,chue_nod_effect))
        
        if(b.getExternalTranslationFlag()):
            # ตั้งเอ็กซ์เพรชชันให้ข้อที่เลื่อนตำแหน่งตามตำแหน่งของข้ออื่น
            chue_nod_effect = list_chue_nod_kho[b.effect_index] # โหนดข้อที่ส่งผลให้
            ef = b.effect_factor
            s = '%s.translateX = %s.translateX * %s;\n'%(chue_nod_kho,chue_nod_effect,ef)
            s += '%s.translateY = %s.translateY * %s;\n'%(chue_nod_kho,chue_nod_effect,ef)
            s += '%s.translateZ = %s.translateZ * %s;\n'%(chue_nod_kho,chue_nod_effect,ef)
            mc.expression(s=s,n='expression_%s_%s'%(chue_nod_kho,chue_nod_effect))
        
        if(b.ik):
            list_mi_ik.append(i) # เก็บโหนดที่มี IK

        

    # สร้าง IK ถ้าเลือกไว้ว่าให้สร้าง
    if(ao_ik):
        list_chue_nod_ik = [] # ลิสต์เก็บชื่อโหนด IK
        for i in list_mi_ik:
            b = mmddata.bones[i]
            index_kho = [b.ik.target_index]+[l.bone_index for l in b.ik.link]
            for j in range(0,len(b.ik.link)):
                kho1 = list_chue_nod_kho[index_kho[j]]
                kho2 = list_chue_nod_kho[index_kho[j+1]]
                mc.select(kho1,kho2)
                chue_nod_ik = mc.ikHandle(n=list_chue_nod_kho[i]+'_IK',sol='ikRPsolver')[0]
                list_chue_nod_ik.append(chue_nod_ik)
    
    
    
    nod_skin = pm.skinCluster(list_chue_nod_kho,chue_nod_poly,mi=4,tsb=1)
    
    nod_poly = pm.PyNode(chue_nod_poly)
    path_mesh = om.MDagPath()
    sl = om.MSelectionList()
    sl.add(nod_poly.fullPath())
    sl.getDagPath(0,path_mesh)
    
    obj_skin = om.MObject()
    sl = om.MSelectionList()
    sl.add(nod_skin.name())
    sl.getDependNode(0,obj_skin)
    fn_skin = oma.MFnSkinCluster(obj_skin)
    
    sl = om.MSelectionList()
    list_influ = []
    for i,chue_nod_kho in enumerate(list_chue_nod_kho):
        dagpath = om.MDagPath()
        sl.add(pm.PyNode(chue_nod_kho).fullPath())
        sl.getDagPath(i,dagpath)
        idx = fn_skin.indexForInfluenceObject(dagpath)
        list_influ.append(idx)
    
    n_kho = len(mmddata.bones)
    list_namnak = []
    for v in mmddata.vertices:
        namnak = [0.]*n_kho
        d = v.deform
        
        if(isinstance(d,pymeshio.pmx.Bdef1)):
            # ส่วนที่ได้รับอิทธิพลจากแค่จุดเดียว
            namnak[d.index0] = 1.
        elif(isinstance(d,(pymeshio.pmx.Bdef2,pymeshio.pmx.Sdef))):
            # ส่วนที่ได้รับอิทธิพลจาก 2 จุด
            namnak[d.index0] += d.weight0
            namnak[d.index1] += 1.-d.weight0
        elif(isinstance(d,pymeshio.pmx.Bdef4)):
            # ส่วนที่ได้รับอิทธิพลจาก 4 จุด
            namnak[d.index0] += d.weight0
            namnak[d.index1] += d.weight1
            namnak[d.index2] += d.weight2
            namnak[d.index3] += 1.-d.weight0-d.weight1-d.weight2
        list_namnak.extend(namnak)
    
    n_chut = len(mmddata.vertices) # จำนวนจุดยอด
    util = om.MScriptUtil()
    util.createFromList(list_namnak,n_kho*n_chut)
    array_namnak = om.MDoubleArray(util.asDoublePtr(),n_kho*n_chut)
    
    util = om.MScriptUtil()
    util.createFromList(list_influ,n_kho)
    array_influ = om.MIntArray(util.asIntPtr(),n_kho)
    
    fn_compo = om.MFnSingleIndexedComponent()
    compo = fn_compo.create(om.MFn.kMeshVertComponent)
    util = om.MScriptUtil()
    util.createFromList(range(n_chut),n_chut)
    index_chut = om.MIntArray(util.asIntPtr(),n_chut)
    fn_compo.addElements(index_chut)
    # ตั้งค่าน้ำหนักของอิทธิพลที่แต่ละข้อมีต่อแต่ละจุดบนโพลิกอน
    fn_skin.setWeights(path_mesh,compo,array_influ,array_namnak,1)
    
    for chue_nod_kho in list_chue_nod_kho:
        if(chue_nod_kho not in list_chue_nod_nok):
            mc.rename(chue_nod_kho,chue_nod_kho.replace('_'+chue_nod_poly,''))
    return list_chue_nod_nok


def sangkhuen(chue_tem_file,khanat,yaek_poly=0,ao_bs=1,ao_kraduk=1,ao_ik=0,watsadu=1,ao_alpha_map=1,yaek_alpha=0):
    t_roem = time.time() # เริ่มจับเวลา
    
    mmddata = an_model(chue_tem_file) # อ่านข้อมูลโมเดล
    # สร้างโพลิกอน
    chue_nod_poly,list_mat_mi_alpha = sang_poly(chue_tem_file,mmddata,khanat,ao_alpha_map,yaek_poly,watsadu,yaek_alpha)
    
    if(not yaek_poly):
        # สร้างเบลนด์เชป (ถ้าติ๊กว่าให้สร้าง)    
        if(ao_bs):
            sang_bs(mmddata,chue_nod_poly,khanat)
        # สร้างกระดูก (ถ้าติ๊กว่าให้สร้าง)
        if(ao_kraduk):
            list_chue_nod_nok = sang_kraduk(mmddata,chue_nod_poly,khanat,ao_ik)
    
    mc.select(chue_nod_poly)
    
    if(not yaek_poly):
        mc.polyNormal(); mc.polyNormal()
    
        if(ao_kraduk):
            mc.select(list_chue_nod_nok)
    
    print(u'作成完了。%.2fかかりました'%(time.time()-t_roem))
    return chue_nod_poly,list_mat_mi_alpha