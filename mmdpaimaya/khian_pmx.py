# -*- coding: utf-8 -*-
u'''
โค้ดสร้างโมเดล .pmx ขึ้นมาจากในมายา
'''

import io,math,sys,os,re,time,shutil
import maya.cmds as mc
import pymel.core as pm
import maya.OpenMaya as om
import maya.OpenMayaAnim as oma
from pymeshio import pmx
from pymeshio import common
from pymeshio.pmx.writer import write as pmxwri
from pymeshio.pmx.reader import read_from_file as pmxread
f_riang_namnak = lambda x:x[1]



def khiankhuen(chue_tem_file='',khanat_ok=0.125,chai_kraduk=1,chai_bs=1,chai_watsadu=1,lok_tex=1,mod_sph=1,tex_sph=''):
    t0 = time.time()
    chue_path_file = os.path.dirname(chue_tem_file)
    shoki = os.path.join(os.path.dirname(__file__),u'shoki.pmx')
    model = pmxread(shoki) # สร้างโมเดล pmx ตั้งต้น
    # เพื่อความรวดเร็ว ดึง append มาเก็บไว้ก่อน
    model_vert_ap = model.vertices.append
    model_ind_ap = model.indices.append
    model_bon_ap = model.bones.append
    model_mat_ap = model.materials.append
    model_mor_ap = model.morphs.append
    model_slot_ap1 = model.display_slots[1].references.append
    model_slot_ap2 = model.display_slots[2].references.append
    
    # โหนดโพลิกอนทั้งหมดที่เลือกอยู่
    list_chue_nod_poly = mc.filterExpand(mc.ls(tr=1,sl=1),sm=12)
    list_chue_nod_shep = []
    list_chue_nod_skin = []
    list_matrix_mun = [0]
    if(list_chue_nod_poly==None): # กรณีที่ไม่ได้เลือกโพลิกอนไว้เลย
        print(u'ポリゴンは選択せれていません')
        return
    
    for chue_nod_poly in list_chue_nod_poly:
        # โหนดรูปร่างของโพลิกอนนั้นๆ
        chue_nod_shep = mc.listRelatives(chue_nod_poly,s=1)[0]
        list_chue_nod_shep.append(chue_nod_shep)
        # หาโหนด skin ที่ใช้กับโพลิกอนนั้นๆ
        if(chai_kraduk):
            for chue_nod_skin in mc.ls(typ='skinCluster'):
                if(chue_nod_shep in mc.skinCluster(chue_nod_skin,q=1,g=1)):
                    list_chue_nod_skin.append(chue_nod_skin)
                    break
            # ถ้าหาไม่เจอก็คือไม่มี
            else:
                list_chue_nod_skin.append(0)
    
    if(chai_kraduk):
        dic_chue_nod_kho = {u'全ての親':0}
        i_kho = 1
        for k in mc.ls(typ='joint',l=1):
            # ถ้ามีอยู่แล้วก็ข้ามไปได้เลย
            if(k in dic_chue_nod_kho):
                continue
            # หาว่าตรึงอยู่กับสกินที่ใช้หรือเปล่า
            for chue_nod_skin in list_chue_nod_skin:
                if(chue_nod_skin and k in (pm.PyNode(x).fullPath() for x in mc.skinCluster(chue_nod_skin,q=1,inf=1))):
                    break
            # ถ้าไม่มีเลยก็ข้ามไป
            else:
                continue
            # หาตัวรากฐาน
            parent = mc.listRelatives(k,p=1,f=1)
            if(parent):
                pp = ['']
                for p in parent[0].split('|')[1:]:
                    pp.append(p)
                    pj = '|'.join(pp)
                    if(mc.nodeType(pj)=='joint'):
                        parent = pj
                        break
                else:
                    parent = k
            else:
                parent = k # ถ้าไม่มีก็คือตัวมันเองเป็น
            # ถ้าตัวรากฐานมีอยู่แล้วก็ข้ามไปได้เลย
            if(parent in dic_chue_nod_kho):
                continue
            # ถ้ายังไม่มีก็ใส่ข้อมูลเข้าไปทั้งตัวรากฐานและลูกทั้งหมด
            list_child = mc.listRelatives(parent,ad=1,f=1)
            list_cp = [parent]
            if(list_child):
                list_cp += list(reversed(list_child))
            for j,chue_nod_kho in enumerate(list_cp):
                dic_chue_nod_kho[chue_nod_kho] = i_kho+j
            for chue_nod_kho in list_cp:
                if(mc.objExists(chue_nod_kho+'.namae')):
                    namae = mc.getAttr(chue_nod_kho+'.namae')
                else:
                    namae = u'骨%d'%i_kho
                kw = {'name':namae,'english_name':chue_nod_kho,'layer':0,'flag':2074}
                kho = pm.PyNode(chue_nod_kho)
                p = kho.getTranslation(space='world')
                kw['position'] = common.Vector3(p.x*khanat_ok,p.y*khanat_ok,-1*p.z*khanat_ok)
                try:
                    chue_parent = kho.getParent().fullPath()
                    parent_index = dic_chue_nod_kho[chue_parent]
                    kw['parent_index'] = parent_index
                except:
                    parent_index = 0
                    kw['parent_index'] = 0
                    kw['flag'] += 4 # ให้ขยับได้อิสระ
                child = kho.getChildren()
                if(len(child)==1):
                    kw['tail_index'] = dic_chue_nod_kho[child[0].fullPath()]
                    kw['flag'] += 1
                else:
                    kw['tail_index'] = -1
                
                
                jo = mc.getAttr(chue_nod_kho+'.jo')[0]
                mm = list_matrix_mun[parent_index]
                if(jo==(0,0,0)):
                    if(not mm):
                        kw['flag'] -= 2048
                    list_matrix_mun.append(mm)
                else:
                    mm *= 1
                    if(mm):
                        mm *= om.MEulerRotation(math.radians(jo[0]),math.radians(jo[1]),math.radians(jo[2])).asMatrix()
                    else:
                        mm = om.MEulerRotation(math.radians(jo[0]),math.radians(jo[1]),math.radians(jo[2])).asMatrix()
                    list_matrix_mun.append(mm)
                
                if(mm):
                    kw['local_x_vector'] = common.Vector3(mm(0,0),mm(0,1),-mm(0,2))
                    kw['local_z_vector'] = common.Vector3(mm(2,0),mm(2,1),-mm(2,2))
                    
                model_bon_ap(pmx.Bone(**kw))
                
                # ใส่ข้อต่อลงในแผงควบคุม ถ้าไม่ใช่ท่อนปลายสุด
                if(child):
                    model_slot_ap2((0,i_kho))
                i_kho += 1
    
    
    
    list_tamnaeng = []
    list_norm = []
    list_u = []
    list_v = []
    
    list_lek_tamnaeng_nai_na = []
    list_na_to_poly = []
    list_chut_to_poly = []
    
    lai_lek_tamnaeng = 0
    lai_lek_norm = 0
    lai_lek_uv = 0
    
    list_lek_chut_mai = []
    dic_str_chut = {}
    lai_lek = 0
    
    list_chue_nod_bs = mc.ls(typ='blendShape')
    
    i_poly = 0 # โพลิกอนอันที่เท่าไหร่
    for chue_nod_poly in list_chue_nod_poly:
        chue_nod_shep = list_chue_nod_shep[i_poly]
        nod_shape = pm.PyNode(chue_nod_shep)
        
        if(chai_kraduk):
            chue_nod_skin = list_chue_nod_skin[i_poly]
            if(chue_nod_skin):
                dic_kho = {} # ดิกเชื่อมโยงเลขข้อสำหรับสกินนี้ กับเลขดัชนีของข้อต่อที่ลำดับตามดิกที่สร้างตอนแรก
                for i,chue_nod_kho in enumerate(mc.skinCluster(chue_nod_skin,q=1,inf=1)):
                    dic_kho[i] = dic_chue_nod_kho[pm.PyNode(chue_nod_kho).fullPath()]
                
                # โค้ดยาวๆก้อนนี้มีไว้เพื่อดึงข้อมูลน้ำหนักที่เชื่อมข้อต่อกับโพลิกอน
                nod_skin = pm.PyNode(chue_nod_skin)
                obj_skin = om.MObject()
                sl = om.MSelectionList()
                sl.add(nod_skin.name())
                sl.getDependNode(0,obj_skin)
                fn_skin = oma.MFnSkinCluster(obj_skin)
                path_mesh = om.MDagPath()
                sl = om.MSelectionList()
                sl.add(nod_shape.fullPath())
                sl.getDagPath(0,path_mesh)
                nod_shape.fullPath()
                path_inf = om.MDagPathArray()
                n_inf = fn_skin.influenceObjects(path_inf)
                util = om.MScriptUtil()
                util.createFromList(range(n_inf),n_inf)
                id_inf = om.MIntArray(util.asIntPtr(),n_inf)
                n_vert = nod_shape.numVertices()
                fn_comp = om.MFnSingleIndexedComponent()
                components = fn_comp.create(om.MFn.kMeshVertComponent)
                util = om.MScriptUtil()
                util.createFromList(range(n_vert),n_vert)
                id_vert = om.MIntArray(util.asIntPtr(),n_vert)
                fn_comp.addElements(id_vert)
                list_namnak = om.MDoubleArray() # ได้ข้อมูลน้ำหนักเป็นลิสต์ ยาว = จำนวนข้อ x จำนวนจุดยอด
                fn_skin.getWeights(path_mesh,components,id_inf,list_namnak)
                n_kho = len(dic_kho) # จำนวนข้อ
        
        if(chai_bs):
            w = [] # ลิสต์เก็บค่าน้ำหนักเดิมของเบลนด์เชปทั้งหมด
            # หาเบลนด์เชปคัดเอาเฉพาะที่เชื่อมกับโพลิกอนตัวนี้อยู่
            list_chue_nod_bs_ni = []
            for chue_nod_bs in list_chue_nod_bs:
                # ดูว่านี่เป็นโพลิกอนที่เชื่อมอยู่กับเบลนด์เชปอันนี้หรือเปล่า
                if(chue_nod_shep not in mc.blendShape(chue_nod_bs,q=1,g=1)):
                    continue
                print(chue_nod_bs)
                try: # try เพื่อกันกรณีที่มีโหนดเบลนด์เชปอยู่แต่ไม่มีเบลนด์เชปอยู่เลย
                    ww = mc.getAttr(chue_nod_bs+'.w[*]') # เก็บค่าน้ำหนักปัจจุบันไว้
                except:
                    continue
                if(type(ww)==float):
                    ww = [ww] # เพื่อกันกรณีที่มีอยู่แค่ตัวเดียว จะได้ค่าไม่เป็นลิสต์ ต้องทำให้เป็นลิสต์เหมือนกันหมด
                w.append(ww)
                mc.setAttr(chue_nod_bs+'.w[*]',*[0]*len(ww)) # ตั้งน้ำหนักให้เป็น 0 ไว้ก่อน
                list_chue_nod_bs_ni.append(chue_nod_bs)
        
        # เก็บค่าตำแหน่งจุด
        tamnaeng = nod_shape.getPoints(space='world')
        list_tamnaeng.extend(tamnaeng)
        list_chut_to_na,vertid = nod_shape.getVertices()
        chut_to_poly = len(vertid)
        
        # เก็บค่าเส้นตั้งฉาก
        norm = nod_shape.getNormals(space='world')
        list_norm.extend(norm)
        normid = nod_shape.getNormalIds()[1]
        
        # เก็บค่า uv
        u,v = nod_shape.getUVs()
        list_u.extend(u)
        list_v.extend(v)
        uvid = nod_shape.getAssignedUVs()[1]
        
        list_samliam_to_na,list_lek_chut = nod_shape.getTriangles()
        list_lek_tamnaeng_nai_na_to_poly = []
        lai_samliam = 0
        
        # ดึงข้อมูลเบลนด์เชป
        list_chue_bs = []
        if(chai_bs):
            list_tamnaeng_bs = []
            list_luean_bs = []
            list_luean_bs_ap = []
            for i,chue_nod_bs in enumerate(list_chue_nod_bs_ni):
                # ถ้ามีข้อมูลชื่อญี่ปุ่นหรือช่องให้ดึงมา
                if(mc.objExists(chue_nod_bs+'.namae')):
                    try:
                        dic_namae = dict(namae.split(u'๑',1) for namae in mc.getAttr(chue_nod_bs+'.namae').split(u'๐'))
                    except:
                        dic_namae = {}
                else:
                    dic_namae = {}
                    
                lenw = len(w[i]) # จำนวนเบลนด์เชปในโหนดนั้นๆ
                for i,bs in enumerate(mc.listAttr(chue_nod_bs+'.w',m=1)):
                    # ตั้งให้น้ำหนักเป็น 1 แค่แบบเดียวทีละแบบ ที่เหลือเป็น 0 ไปก่อน
                    ww = [0]*lenw
                    ww[i] = 1
                    mc.setAttr(chue_nod_bs+'.w[*]',*ww)
                    # ดึงข้อมูลตำแหน่งที่เลื่อนแล่้ว
                    tamnaeng_bs = nod_shape.getPoints(space='world')
                    list_tamnaeng_bs.append(tamnaeng_bs)
                    if(bs in dic_namae):
                        namae = dic_namae[bs].split(u'๑')
                        try:
                            list_chue_bs.append((namae[0],bs,int(namae[1])))
                        except:
                            list_chue_bs.append((namae[0],bs,4))
                    # ถ้าไม่ได้มีชื่อที่ตั้งเก็บไว้ในโหนดแต่แรกก็ให้ใช้ทั้งชื่อญี่ปุ่นและชื่ออังกฤษเป็นชื่อเดียวกัน
                    else:
                        list_chue_bs.append((bs,bs,4))
                    luean_bs = []
                    list_luean_bs.append(luean_bs)
                    list_luean_bs_ap.append(luean_bs.append)
            # เปลี่ยนรูปร่างกลับคืนเดิมด้วย
            for i,chue_nod_bs in enumerate(list_chue_nod_bs_ni):
                mc.setAttr(chue_nod_bs+'.w[*]',*w[i])
        
        n_bs = len(list_chue_bs)
        list_lek_chut_mai_to_poly = []
        i = 0
        for samliam_to_na,chut_to_na in zip(list_samliam_to_na,list_chut_to_na):
            dic_lai_lek = {}
            
            for j in range(chut_to_na):
                lek_tamnaeng = vertid[i]
                lek_norm = normid[i]
                lek_uv = uvid[i]
                str_chut = '%d:%d:%d'%(lek_tamnaeng+lai_lek_tamnaeng,lek_norm+lai_lek_norm,lek_uv+lai_lek_uv)
                if(str_chut in dic_str_chut):
                    lek_chut_mai = dic_str_chut[str_chut]
                else:
                    lek_chut_mai = lai_lek
                    dic_str_chut[str_chut] = lek_chut_mai
                    
                    #ถ้ามีเชื่อมสกินอยู่ก็ดึงน้ำหนักมาใช้
                    if(chai_kraduk and chue_nod_skin):
                        w = [] # ลิสต์เก็บทูเพิลของ (ดัชนีข้อ,ค่าน้ำหนัก)
                        # ดึงข้อมูลน้ำหนักจากลิสต์น้ำหนัก ความยาวเท่ากับจำนวนข้อ
                        for i_namnak,namnak in enumerate(list_namnak[lek_tamnaeng*n_kho:(lek_tamnaeng+1)*n_kho]):
                            # คัดเฉพาะที่ไม่น้อยจนเกือบ 0 เท่านั้น
                            if(namnak>0.001):
                                w.append((dic_kho[i_namnak],namnak))
                        if(len(w)>3):
                            # ถ้ามากเกิน 4 ให้เรียงเอาอันที่มากก็พอ
                            if(len(w)>4):
                                w.sort(key=f_riang_namnak,reverse=1)
                                w = w[:4]
                            w_ruam = w[0][1]+w[1][1]+w[2][1]+w[3][1]
                            ww0 = w[0][1]/w_ruam
                            ww1 = w[1][1]/w_ruam
                            ww2 = w[2][1]/w_ruam
                            ww3 = w[3][1]/w_ruam
                            deform = pmx.Bdef4(w[0][0],w[1][0],w[2][0],w[3][0],ww0,ww1,ww2,ww3)
                        elif(len(w)==3):
                            w_ruam = w[0][1]+w[1][1]+w[2][1]
                            ww0 = w[0][1]/w_ruam
                            ww1 = w[1][1]/w_ruam
                            ww2 = w[2][1]/w_ruam
                            deform = pmx.Bdef4(w[0][0],w[1][0],w[2][0],-1,ww0,ww1,ww2,0.)
                        elif(len(w)==2):
                            ww0 = w[0][1]/(w[0][1]+w[1][1])
                            deform = pmx.Bdef2(w[0][0],w[1][0],ww0)
                        elif(len(w)==1):
                            deform = pmx.Bdef1(w[0][0])
                        else:
                            deform = pmx.Bdef1(0)
                    # ถ้าไม่ได้เชื่อมกับสกินก็ให้ตรึงกับข้อรากฐานให้หมด
                    else:
                        deform = pmx.Bdef1(0)
                    
                    p = list_tamnaeng[lek_tamnaeng+lai_lek_tamnaeng]
                    position = common.Vector3(p[0]*khanat_ok,p[1]*khanat_ok,-p[2]*khanat_ok)
                    nm = list_norm[lek_norm+lai_lek_norm]
                    normal = common.Vector3(nm[0],nm[1],-nm[2])
                    uv = common.Vector2(list_u[lek_uv+lai_lek_uv],1.-list_v[lek_uv+lai_lek_uv])
                    
                    # สร้างจุดจากข้อมูลที่ดึงมาได้ แล้วเพื่มเข้าไปในลิสต์ของจุด
                    vertex = pmx.Vertex(position,normal,uv,deform,edge_factor=1.)
                    model_vert_ap(vertex)
                    
                    for i_bs in range(n_bs):
                        p1 = list_tamnaeng_bs[i_bs][lek_tamnaeng]
                        po = common.Vector3((p1[0]-p[0])*khanat_ok,(p1[1]-p[1])*khanat_ok,(p[2]-p1[2])*khanat_ok)
                        # เอาข้อมูลเฉพาะจุดที่มีการเปลี่ยนตำแหน่ง
                        if(po.getNorm()>0):
                            list_luean_bs_ap[i_bs](pmx.VertexMorphOffset(lai_lek,po))
                    lai_lek += 1
                
                dic_lai_lek[lek_tamnaeng+lai_lek_tamnaeng] = lek_chut_mai
                i += 1
                
            
            ll = []
            for j in range(lai_samliam*3,(lai_samliam+samliam_to_na)*3,3):
                for jj in range(3):
                    lek_tamnaeng = list_lek_chut[j+2-jj]
                    lek_chut_mai = dic_lai_lek[lek_tamnaeng+lai_lek_tamnaeng]
                    ll.append(lek_chut_mai)
            lai_samliam += samliam_to_na
            list_lek_chut_mai_to_poly.append(ll)
        
        # สร้างมอร์ฟทั้งหมดจากข้อมูลเบลนด์เชปที่เตรียมไว้
        if(chai_bs):
            for i_mor,(chue_bs,luean_bs) in enumerate(zip(list_chue_bs,list_luean_bs)):
                model_mor_ap(pmx.Morph(name=chue_bs[0],english_name=chue_bs[1],panel=chue_bs[2],morph_type=1,offsets=luean_bs))
                model_slot_ap1((1,i_mor))
            
        list_na_to_poly.append(vertid)
        list_chut_to_poly.append(chut_to_poly)
        lai_lek_tamnaeng += len(tamnaeng)
        lai_lek_norm += len(norm)
        lai_lek_uv += len(u)
        list_lek_tamnaeng_nai_na.append(list_lek_tamnaeng_nai_na_to_poly)
        list_lek_chut_mai.append(list_lek_chut_mai_to_poly)
        i_poly += 1
        
    
    
    # ถ้าเลือกจะสร้างวัสดุด้วยก็สร้างแล้วเรียงจุดในหน้าตามวัสดุ
    if(chai_watsadu):
        list_chue_nod_mat = [] # ลิสต์เก็บโหนดวัสดุ
        list_chue_nod_sg = [] # ลิสต์เก็บโหนด sg
        i_tex = 0 # ดัชนีเท็กซ์เจอร์
        i_mat = 0 # ดัชนีวัสดุ
        for mat in mc.ls(mat=1):
            # เอาเฉพาะวัสดุที่มี sg เท่านั้น
            try:
                liscon = mc.listConnections(mat+'.outColor')
                sg = liscon[0]
                list_na = mc.sets(sg,q=1) # ดูว่ามีหน้าไหนที่ใช้วัสดุนี้
                if(not list_na):
                    if(len(liscon)>1):
                        sg = liscon[1]
                        list_na = mc.sets(sg,q=1)
                    # หากไม่ถูกใช้อยู่ก็ข้าม
                    if(not list_na):
                        continue
            except:
                continue
            
            n_chut_to_mat = 0 # จำนวนจุดของหน้านี้ (= 3 เท่าของจำนวนหน้า)
            for na in list_na:
                if('[' in na):
                    chue_nod_poly,na0,na1 = re.findall(r'(\w+).f\[(\d+):?(\d+)?]',na)[0]
                    na0 = int(na0)
                    if(na1==''):
                        na1 = na0
                    else:
                        na1 = int(na1)
                else:
                    chue_nod_poly = mc.listRelatives(na,p=1)[0]
                    na0 = 0
                    na1 = mc.polyEvaluate(chue_nod_poly,f=1)-1
                
                # ถ้าอยู่ในลิสต์ของโพลิกอนที่เลือกอยู่ให้หาเลขดัชนีของโพลิกอนนั้นในลิสต์
                if(chue_nod_poly in list_chue_nod_poly):
                    lek_nod_poly = list_chue_nod_poly.index(chue_nod_poly)
                # ถ้าไม่อยู่ในลิสต์ก็ข้ามไปเลย
                else:
                    continue
                
                for lai_na in range(na0,na1+1):
                    for lek in list_lek_chut_mai[lek_nod_poly][lai_na]:
                        model_ind_ap(lek)
                        n_chut_to_mat += 1
            
            # ถ้าวัสดุนี้ไม่ถูกใช้ในโพลิกอนที่เลือกอยู่เลยก็ข้าม
            if(n_chut_to_mat==0):
                continue
            if(mc.objExists(mat+'.namae')):
                namae = mc.getAttr(mat+'.namae')
            else:
                namae = u'材質%d'%(i_mat+1)
            # ค่าองค์ประกอบต่างๆของวัสดุ เก็บไว้ในดิกก่อน
            
            kw = {'name':namae,'english_name':mat,
                'diffuse_color':common.RGB(1,1,1),'alpha':1,
                'specular_factor':0.5,'specular_color':common.RGB(0.,0.,0.),
                'ambient_color':common.RGB(0.5,0.5,0.5),
                'flag':1,'edge_color':common.RGBA(0.,0.,0.,1.),'edge_size':1,
                'texture_index':-1,'sphere_texture_index':-1,'sphere_mode':0,
                'toon_sharing_flag':0,'toon_texture_index':-1,'vertex_count':n_chut_to_mat}
            # ใส่ try กันกรณีที่เป็นวัสดุชนิดแปลกๆที่ไม่สามารถอ่านค่าได้ปกติ
            try:
                nodetype = mc.nodeType(mat) # ชนิดของวัสดุ
                # หาดูว่าวัสดุนี้ใช้เท็กซ์เจอร์หรือไม่
                if(nodetype!='aiStandardSurface'):
                    chue_nod_tex = mc.listConnections(mat+'.color')
                else:
                    chue_nod_tex = mc.listConnections(mat+'.baseColor')
                # ถ้ามีเท็กซ์เจอร์ และเป็นไฟล์
                if(chue_nod_tex):
                    if(mc.nodeType(chue_nod_tex[0])=='file'):
                        chue_tem_file_tex = mc.getAttr(chue_nod_tex[0]+'.ftn') # ชื่อไฟล์
                        # ถ้ามีชื่อไฟล์นี้อยู่แล้ว
                        if(chue_tem_file_tex in model.textures):
                            kw['texture_index'] = model.textures.index(chue_tem_file_tex)
                        # ถ้ายังไม่มีก็เพิ่มเข้าไป
                        else:
                            chue_tex = os.path.basename(chue_tem_file_tex)
                            model.textures.append(chue_tex)
                            # ถ้าเลือกว่าจะคัดลอกไฟล์เท็กซ์เจอร์ก็ทำการคัดลอก
                            if(lok_tex):
                                shutil.copyfile(chue_tem_file_tex,os.path.join(chue_path_file,chue_tex))
                            kw['texture_index'] = i_tex
                            i_tex += 1 # นับไล่ดัชนีเท็กซ์เจอร์ต่อ
                    else:
                        print(u'テクスチャ%sはファイルではないため使えません'%chue_nod_tex[0])
                    dc = [1.,1.,1.]
                # ถ้าไม่ใช้เท็กซ์เจอร์ไฟล์จึงกำหนดสีผิว
                else:
                    if(nodetype!='aiStandardSurface'):
                        dc = mc.getAttr(mat+'.color')[0]
                    else:
                        dc = mc.getAttr(mat+'.baseColor')[0]
                    dc = [min(max(s,0.),1.) for s in dc]
                    kw['diffuse_color'] = common.RGB(*dc)
                
                if(nodetype not in ['aiStandard','aiStandardSurface']):
                    tran = sum(mc.getAttr(mat+'.transparency')[0])/3 # ความโปร่งใสใช้เป็นค่าเฉลี่ย
                    kw['alpha'] = min(max(1-tran,0),1.)
                    # ค่าสีแอมเบียนต์ให้คูณสีผิวไปด้วย
                    ac = [min(max(s,0.),1.)*d for s,d in zip(mc.getAttr(mat+'.ambientColor')[0],dc)]
                    kw['ambient_color'] = common.RGB(*ac)
                    # เฉพาะ blinn เท่านั้นจึงเก็บค่าสเป็กคิวลาร์ นอกนั้นใช้ค่าตั้งต้น
                    if(nodetype=='blinn'):
                        sr = min(max(mc.getAttr(mat+'.specularRollOff'),0.1),1.)
                        kw['specular_factor'] = round(math.pow(2,math.log(sr,0.75)-1))
                        kw['specular_color'] = common.RGB(*[min(max(s,0.),1.) for s in mc.getAttr(mat+'.specularColor')[0]])
                # กรณี aiStandard
                else:
                    opa = sum(mc.getAttr(mat+'.opacity')[0])/3 # ความทึบแสงใช้เป็นค่าเฉลี่ย
                    kw['alpha'] = min(max(opa,0.),1.)
                    if(nodetype!='aiStandardSurface'):
                        kw['specular_color'] = common.RGB(*[min(max(s,0.),1.) for s in mc.getAttr(mat+'.KsColor')[0]])
                    else:
                        kw['specular_color'] = common.RGB(*[min(max(s,0.),1.) for s in mc.getAttr(mat+'.specularColor')[0]])
                    sr = max(mc.getAttr(mat+'.specularRoughness'),0.1)
                    kw['specular_factor'] = round(math.pow(2,math.log(sr,0.75)-1))
                    kw['ambient_color'] = common.RGB(0,0,0)
            except:
                print u'材質%sに問題が見つかりました'%mat
            
            model_mat_ap(pmx.Material(**kw)) # เพิ่มวัสดุเข้าไปในโมเดล
            
            list_chue_nod_mat.append(mat)
            list_chue_nod_sg.append(sg)
            i_mat += 1
        
        if(mod_sph):
            i = len(model.textures)
            model.textures.append(tex_sph)
            for mat in model.materials:
                mat.sphere_mode = mod_sph
                mat.sphere_texture_index = i
            
    # ถ้าเลือกไม่เอาวัสดุก็ให้ใช้เป็นวัสดุตั้งต้นแบบเดียวกันหมด
    else:
        n_chut_to_mat = 0
        for list_lek_chut_nai_poly in list_lek_chut_mai:
            for list_lek_chut_nai_na in list_lek_chut_nai_poly:
                n_chut_to_mat += len(list_lek_chut_nai_na)
                for lek_chut in list_lek_chut_nai_na:
                    model_ind_ap(lek_chut)
        
        model_mat_ap(pmx.Material(name=u'材質1',english_name='',
                diffuse_color=common.RGB(0.5,0.5,0.5),alpha=1,
                specular_factor=0.5,specular_color=common.RGB(0.5,0.5,0.5),
                ambient_color=common.RGB(0.25,0.25,0.25),
                flag=1,edge_color=common.RGBA(0.,0.,0.,1.),edge_size=1,
                texture_index=-1,sphere_texture_index=-1,sphere_mode=0,
                toon_sharing_flag=0,toon_texture_index=-1,vertex_count=n_chut_to_mat))
    
    chue_model = os.path.basename(chue_tem_file).split('.')[0]
    model.name = chue_model
    model.english_name = chue_model
    if(not model.display_slots[2].references):
        model.display_slots.pop()
    
    with io.open(chue_tem_file,'wb') as s:
        pmxwri(s,model)
    mc.select(list_chue_nod_poly)
    
    print(u'ファイル%s作成完了。%.2f秒かかりました'%(chue_tem_file,time.time()-t0))