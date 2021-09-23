# -*- coding: utf-8 -*-

import os,math,time,shutil,re
from . import mmdio
import maya.cmds as mc
import maya.api.OpenMaya as om
import maya.api.OpenMayaAnim as oma
import pymel.core as pm
f_riang_namnak = lambda x:x[1]

def sang(chue_tem_file,satsuan_ok=1,chai_kraduk=True,chai_bs=True,chai_watsadu=True,lok_tex=False,thangmot=False):
    t0 = time.time() # 開始
    print('"%s"へのエクスポート開始'%chue_tem_file)
    chue_path_file = os.path.dirname(chue_tem_file)
    shoki = os.path.join(os.path.dirname(__file__),'asset','model00.pmx')
    pmx_model = mmdio.pmx.load(shoki) # 初期のpmxモデル
    # もっと速くするために予めappendメソッドを準備しておく
    model_vert_ap = pmx_model.vertices.append # 頂点
    model_face_ap = pmx_model.faces.append # 面
    model_bon_ap = pmx_model.bones.append # 骨
    model_mat_ap = pmx_model.materials.append # 材質
    model_mor_ap = pmx_model.morphs.append # モーフ
    model_dis1_ap = pmx_model.display[1].data.append # 表示ょの表示枠
    model_dis2_ap = pmx_model.display[2].data.append # 可動域の表示枠
    if(thangmot):
        lis_chue_nod_poly = mc.filterExpand(mc.ls(transforms=1),selectionMask=12)
        print(lis_chue_nod_poly)
        if(lis_chue_nod_poly==None): # ポリゴンが全然ない場合
            print('このシーンの中にポリゴンはありません')
            return
    else:
        lis_chue_nod_poly = mc.filterExpand(mc.ls(transforms=1,selection=1),selectionMask=12)
        if(lis_chue_nod_poly==None): # 選択されているポリゴンが一つもない場合
            print('ポリゴンは選択せれていません')
            return
    print('エクスポートするポリゴン：%s'%lis_chue_nod_poly)

    lis_chue_nod_shep = [] # 全てのシェープのノードを収めるリスト
    lis_chue_nod_skin = [] # 全てのスキンのノードを収めるリスト
    lis_chue_tex = [] # テクスチャの名前を収めるリスト
    lis_matrix_mun = [0]
    
    for chue_nod_poly in lis_chue_nod_poly:
        # このポリゴンのシェープのノード
        chue_nod_shep = mc.listRelatives(chue_nod_poly,shapes=True,fullPath=True)[0]
        lis_chue_nod_shep.append(chue_nod_shep)
        # 骨もエクスポートすると選択した場合
        if(chai_kraduk):
            for chue_nod_skin in mc.ls(typ='skinCluster'): # このポリゴンに使うスキンのノード
                # このスキンのノードに接続されているシェープのノードは、このホリゴンのシェープのノードに接続していれば、このスキンを使う
                if(pm.PyNode(chue_nod_shep).name() in mc.skinCluster(chue_nod_skin,query=True,geometry=True)):
                    lis_chue_nod_skin.append(chue_nod_skin)
                    break
            # このポリゴンと接続されているスキンがない場合
            else:
                lis_chue_nod_skin.append(0)
    
    if(chai_kraduk): # ここで骨を作成しておく
        dic_chue_nod_kho = {'全ての親':0} # 一番外のジョイント
        i_kho = 1 # ジョイントの順番をカウントする
        for k in mc.ls(typ='joint',long=True):
            # このジョイントがすでに作成された場合、スキップする
            if(k in dic_chue_nod_kho):
                continue
            # 使用するスキンのノードと接続されているかどうか
            for chue_nod_skin in lis_chue_nod_skin:
                if(chue_nod_skin and k in (pm.PyNode(x).fullPath() for x in mc.skinCluster(chue_nod_skin,query=True,influence=True))):
                    break
            # 接続されていない場合、このジョイントはスキップ
            else:
                continue
            # 親ジョイントを探す
            parent = mc.listRelatives(k,parent=True,fullPath=True)
            if(parent): # 親ジョイントがある場合
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
                parent = k # 親がない場合、このジョイントそのもの
            # その親がすでに作られた場合、スキップする
            if(parent in dic_chue_nod_kho):
                continue
            # まだないければ、このジョイントを子ジョイントと共に新しく追加する
            lis_child = mc.listRelatives(parent,allDescendents=True,fullPath=True)
            lis_cp = [parent] # 親と全ての子のジョイントを収めるリスト
            if(lis_child):
                lis_cp += list(reversed(lis_child))
            # 親と子のジョイントの名前を全部収める
            for j,chue_nod_kho in enumerate(lis_cp):
                dic_chue_nod_kho[chue_nod_kho] = i_kho+j
            for chue_nod_kho in lis_cp:
                # ボーンを作って初期値を与える
                bone = mmdio.pmx.Bone()
                bone.name = '骨%d'%i_kho # 番号で日本語名を付ける
                bone.name_e = chue_nod_kho # 英語名はジョイントのノードの名前を使う
                bone.isRotatable = True # 全てのボーンは回転可能
                bone.isMovable = False # 親のないボーンだけ移動可能
                bone.visible = True # 全てのボーン表示
                bone.isControllable = True # 全てのボーンは操作できる
                bone.isIK = False # IKは使わない
                bone.hasAdditionalRotate = False # 回転付与
                bone.hasAdditionalLocation = False # 移動付与
                bone.transAfterPhis = False # 物理後
                
                nod_kho = pm.PyNode(chue_nod_kho) # このジョイントのノード
                p = mc.xform(chue_nod_kho,query=True,t=True,ws=True) # このジョイントの位置
                bone.location = [p[0]*satsuan_ok,p[1]*satsuan_ok,-1*p[2]*satsuan_ok]
                try:
                    chue_parent = nod_kho.getParent().fullPath()
                    bone.parent = dic_chue_nod_kho[chue_parent]
                except:
                    bone.parent = 0
                    bone.isMovable = True
                child = nod_kho.getChildren()
                if(len(child)==1):
                    bone.displayConnection = dic_chue_nod_kho[child[0].fullPath()]
                else:
                    bone.displayConnection = -1
    
    
                jo = mc.getAttr(chue_nod_kho+'.jointOrient')[0]
                mm = lis_matrix_mun[bone.parent]
                if(jo==(0,0,0)):
                    lis_matrix_mun.append(mm)
                else:
                    mm *= 1
                    if(mm):
                        mm *= om.MEulerRotation(math.radians(jo[0]),math.radians(jo[1]),math.radians(jo[2])).asMatrix()
                    else:
                        mm = om.MEulerRotation(math.radians(jo[0]),math.radians(jo[1]),math.radians(jo[2])).asMatrix()
                    lis_matrix_mun.append(mm)
                    
                if(mm):
                    x_axis = [mm.getElement(0,0),mm.getElement(0,1),-mm.getElement(0,2)]
                    z_axis = [mm.getElement(2,0),mm.getElement(2,1),-mm.getElement(2,2)]
                    
                    bone.localCoordinate = mmdio.pmx.Coordinate(x_axis,z_axis)
                    
                model_bon_ap(bone)
    
                # 子を持っているジョイントだけを表示枠に入れる
                if(child):
                    model_dis2_ap((0,i_kho))
                i_kho += 1
    
    
    lis_tamnaeng = []
    lis_norm = []
    lis_u = []
    lis_v = []
    
    lis_lek_tamnaeng_nai_na = []
    lis_na_nai_poly = []
    lis_chut_nai_poly = []
    
    lai_lek_tamnaeng = 0
    lai_lek_norm = 0
    lai_lek_uv = 0
    
    lis_lek_chut_mai = []
    dic_tup_chut = {}
    lai_lek = 0
    lis_chue_nod_bs = mc.ls(typ='blendShape')
    i_poly = 0 # ポリゴンの順番
    for chue_nod_poly in lis_chue_nod_poly:
        if(chai_kraduk):
            chue_nod_skin = lis_chue_nod_skin[i_poly]
            if(chue_nod_skin):
                dic_kho = {} # ジョイントの番号とジョイントの名前の辞書
                for i,chue_nod_kho in enumerate(mc.skinCluster(chue_nod_skin,query=True,influence=True)):
                    dic_kho[i] = dic_chue_nod_kho[pm.PyNode(chue_nod_kho).fullPath()]
                
                # ジョイントとポリゴンの接続される重みを取得する
                selelis = om.MSelectionList()
                selelis.add(chue_nod_skin)
                obj_skin = selelis.getDependNode(0)
                fn_skin = oma.MFnSkinCluster(obj_skin)
                selelis = om.MSelectionList()
                selelis.add(chue_nod_shep)
                dagpath_mesh = selelis.getDagPath(0)
                path_influ = fn_skin.influenceObjects()
                n_influ = len(path_influ)
                arr_index_influ = om.MIntArray(range(n_influ))
                
                fn_compo = om.MFnSingleIndexedComponent()
                compo = fn_compo.create(om.MFn.kMeshVertComponent)
                # 重みのリストができた。長さはジョイント数×頂点数
                lis_namnak = fn_skin.getWeights(dagpath_mesh,compo,arr_index_influ)
    
        if(chai_bs):
            w_doem = [] # 元の重みの値を収めるリスト
            # このポリゴンに接続しているブレンドシェープのノードだけ取る
            lis_chue_nod_bs_ni = []
            for chue_nod_bs in lis_chue_nod_bs:
                # これがこのブレンドシェープに接続しているポリゴンであるかどうかチェック
                if(pm.PyNode(chue_nod_shep).name() not in mc.blendShape(chue_nod_bs,query=True,geometry=True)):
                    continue # 違ったらスキップ
                try:
                    ww = mc.getAttr(chue_nod_bs+'.w[*]') # 元の重みを収めておく
                except:
                    ww = [] # 空っぽのブレンドシェープのノードの場合、エラーが出る
                    continue
                if(type(ww)==float):
                    ww = [ww] # 一つしかない場合は返り値がリストにはならないので、全部リストにしておく
                w_doem.append(ww)
                mc.setAttr(chue_nod_bs+'.w[*]',*[0]*len(ww)) # まずは全部の重みを0にしておく
                lis_chue_nod_bs_ni.append(chue_nod_bs)
    
        # 頂点の位置
        selelis = om.MSelectionList()
        selelis.add(chue_nod_shep)
        fnmesh = om.MFnMesh(selelis.getDagPath(0))
        tamnaeng = fnmesh.getPoints(space=om.MSpace.kWorld)
        lis_tamnaeng.extend(tamnaeng)
        lis_chut_nai_na,vertid = fnmesh.getVertices()
        chut_nai_poly = len(vertid)
    
        # 頂点の法線
        norm = fnmesh.getNormals(space=om.MSpace.kWorld)
        lis_norm.extend(norm)
        normid = fnmesh.getNormalIds()[1]
    
        # 頂点のuv
        u,v = fnmesh.getUVs()
        lis_u.extend(u)
        lis_v.extend(v)
        uvid = fnmesh.getAssignedUVs()[1]
    
        # その面に構成する三角形の数と頂点
        lis_samliam_nai_na,lis_lek_chut = fnmesh.getTriangles()
        lis_lek_tamnaeng_nai_na_nai_poly = []
        lai_samliam = 0
    
        lis_chue_bs = []
        if(chai_bs):
            lis_tamnaeng_bs = [] # 移動した後の頂点の位置を収めるリスト
            lis_luean_bs = []
            lis_luean_bs_ap = []
            for i,chue_nod_bs in enumerate(lis_chue_nod_bs_ni):
                n_bs_nai_nod = len(w_doem[i]) # そのノードにある全てのブレンドシェープ
                # 一つずつブレンドシェープを処理する
                for i,bs in enumerate(mc.listAttr(chue_nod_bs+'.w',multi=True)):
                    # 他は全部0にしておいて、そのブレンドシェープ一つだけ1にする
                    ww = [0]*n_bs_nai_nod
                    ww[i] = 1
                    mc.setAttr(chue_nod_bs+'.w[*]',*ww)
                    # 移動した後の頂点の位置
                    tamnaeng_bs = fnmesh.getPoints(space=om.MSpace.kWorld)
                    lis_tamnaeng_bs.append(tamnaeng_bs)
                    lis_chue_bs.append(bs)
                    luean_bs = []
                    lis_luean_bs.append(luean_bs)
                    lis_luean_bs_ap.append(luean_bs.append)
            # 重みを元に戻す
            for i,chue_nod_bs in enumerate(lis_chue_nod_bs_ni):
                mc.setAttr(chue_nod_bs+'.w[*]',*w_doem[i])
    
        n_bs = len(lis_chue_bs)
        lis_lek_chut_mai_nai_poly = []
        i = 0
        for samliam_nai_na,chut_nai_na in zip(lis_samliam_nai_na,lis_chut_nai_na):
            # その面の三角形の数、その面の頂点の数
            dic_lai_lek = {}
            for j in range(chut_nai_na):
                lek_tamnaeng = vertid[i]
                lek_norm = normid[i]
                lek_uv = uvid[i]
                tup_chut = (lek_tamnaeng+lai_lek_tamnaeng,lek_norm+lai_lek_norm,lek_uv+lai_lek_uv)
                if(tup_chut in dic_tup_chut):
                    lek_chut_mai = dic_tup_chut[tup_chut]
                else:
                    lek_chut_mai = lai_lek
                    dic_tup_chut[tup_chut] = lek_chut_mai
    
                    # スキンと接続している場合、重みの値を取る
                    bowe = mmdio.pmx.BoneWeight()
                    if(chai_kraduk and chue_nod_skin):
                        n_kho = len(dic_kho) # ジョイントの数
                        w = [] # [ノード名, 重み]リストを収めるリスト
                        # 重みのリストから重みの値を取る。長さはn_kho
                        for i_namnak,namnak in enumerate(lis_namnak[lek_tamnaeng*n_kho:(lek_tamnaeng+1)*n_kho]):
                            # 重みが小さすぎないジョイントの[ノード名, 重み]だけ取る
                            if(namnak>0.001):
                                w.append([dic_kho[i_namnak],namnak])
    
                        if(len(w)>3): # 4つ以上ある場合
                            if(len(w)>4): # 4つだけ取る
                                w.sort(key=f_riang_namnak,reverse=1)
                                w = w[:4]
                            w_ruam = w[0][1]+w[1][1]+w[2][1]+w[3][1] # この4の重みの足し算
                            ww0 = w[0][1]/w_ruam
                            ww1 = w[1][1]/w_ruam
                            ww2 = w[2][1]/w_ruam
                            ww3 = w[3][1]/w_ruam
                            bowe.bones = [w[0][0],w[1][0],w[2][0],w[3][0]]
                            bowe.weights = [ww0,ww1,ww2,ww3]
                            bowe.type = mmdio.pmx.BoneWeight.BDEF4
                        elif(len(w)==3):
                            w_ruam = w[0][1]+w[1][1]+w[2][1]
                            ww0 = w[0][1]/w_ruam
                            ww1 = w[1][1]/w_ruam
                            ww2 = w[2][1]/w_ruam
                            bowe.bones = [w[0][0],w[1][0],w[2][0],-1]
                            bowe.weights = [ww0,ww1,ww2,0.]
                            bowe.type = mmdio.pmx.BoneWeight.BDEF4
                        elif(len(w)==2):
                            ww0 = w[0][1]/(w[0][1]+w[1][1])
                            bowe.bones = [w[0][0],w[1][0]]
                            bowe.weights = [ww0]
                            bowe.type = mmdio.pmx.BoneWeight.BDEF2
                        elif(len(w)==1):
                            bowe.bones = [w[0][0]]
                            bowe.type = mmdio.pmx.BoneWeight.BDEF1
                        else:
                            bowe.bones = [0]
                            bowe.type = mmdio.pmx.BoneWeight.BDEF1
                    # スキンに接続していない場合は全部一番外のジョイントのノードに繋ぐ
                    else:
                        bowe.bones = [0]
                        bowe.type = mmdio.pmx.BoneWeight.BDEF1
    
                    # 取得した頂点データからモデルの頂点のリストに追加
                    vtx = mmdio.pmx.Vertex()
                    p = lis_tamnaeng[lek_tamnaeng+lai_lek_tamnaeng]
                    vtx.co = [p[0]*satsuan_ok,p[1]*satsuan_ok,-p[2]*satsuan_ok]
                    nm = lis_norm[lek_norm+lai_lek_norm]
                    vtx.normal = [nm[0],nm[1],-nm[2]]
                    vtx.uv = [lis_u[lek_uv+lai_lek_uv],1.-lis_v[lek_uv+lai_lek_uv]]
                    vtx.weight = bowe
                    vtx.edge_factor = 1.
                    model_vert_ap(vtx) # モデルの頂点のリストに追加
    
                    for i_bs in range(n_bs):
                        p1 = lis_tamnaeng_bs[i_bs][lek_tamnaeng]
                        po = [(p1[0]-p[0])*satsuan_ok,(p1[1]-p[1])*satsuan_ok,(p[2]-p1[2])*satsuan_ok]
                        # 位置の変更が起きる頂点だけ取る
                        if(po[0]**2+po[1]**2+po[2]**2>0):
                            vmoffset = mmdio.pmx.VertexMorphOffset()
                            vmoffset.index = lai_lek
                            vmoffset.offset = po
                            lis_luean_bs_ap[i_bs](vmoffset)
                    lai_lek += 1
    
                dic_lai_lek[lek_tamnaeng+lai_lek_tamnaeng] = lek_chut_mai
                i += 1
    
            ll = []
            for j in range(lai_samliam*3,(lai_samliam+samliam_nai_na)*3,3):
                for jj in range(3):
                    lek_tamnaeng = lis_lek_chut[j+2-jj]
                    lek_chut_mai = dic_lai_lek[lek_tamnaeng+lai_lek_tamnaeng]
                    ll.append(lek_chut_mai)
            lai_samliam += samliam_nai_na
            lis_lek_chut_mai_nai_poly.append(ll)
    
        # 準備しておいたブレンドシェープのデータからモーフを作成する
        if(chai_bs):
            for i_mor,(chue_bs,luean_bs) in enumerate(zip(lis_chue_bs,lis_luean_bs)):
                morph = mmdio.pmx.VertexMorph(name=chue_bs,name_e=chue_bs,category=4)
                morph.offsets = luean_bs
                model_mor_ap(morph)
                model_dis1_ap((1,i_mor))
    
        lis_na_nai_poly.append(vertid)
        lis_chut_nai_poly.append(chut_nai_poly)
        lai_lek_tamnaeng += len(tamnaeng)
        lai_lek_norm += len(norm)
        lai_lek_uv += len(u)
        lis_lek_tamnaeng_nai_na.append(lis_lek_tamnaeng_nai_na_nai_poly)
        lis_lek_chut_mai.append(lis_lek_chut_mai_nai_poly)
        i_poly += 1
    
    # 材質を使う場合
    if(chai_watsadu):
        i_tex = 0 # テクスチャの番号
        i_mat = 0 # 材質の番号
        for chue_mat in mc.ls(materials=True):
            # sgと繋がっている材質だけ取る
            liscon = mc.listConnections(chue_mat+'.outColor')
            if(not liscon):
                continue # sgと繋がっていない材質はスキップ
            sg = liscon[0]
            lis_na = mc.sets(sg,query=True) # この材質を使っている面のリスト
            if(not lis_na):
                if(len(liscon)>1):
                    sg = liscon[1]
                    lis_na = mc.sets(sg,query=True)
                # 全然使われていない場合、この材質をスキップ
                if(not lis_na):
                    continue
    
            n_chut_nai_mat = 0 # この面の中の頂点の数
            for na in lis_na:
                if('[' in na):
                    chue_nod_poly,na0,na1 = re.findall(r'(\w+).f\[(\d+):?(\d+)?]',na)[0]
                    na0 = int(na0)
                    if(na1==''):
                        na1 = na0
                    else:
                        na1 = int(na1)
                else:
                    chue_nod_poly = mc.listRelatives(na,parent=True)[0]
                    na0 = 0
                    na1 = mc.polyEvaluate(chue_nod_poly,face=True)-1
    
                # 選択されたポリゴンのリストの中にある場合、そのポリゴンの番号を取る
                if(chue_nod_poly in lis_chue_nod_poly):
                    lek_nod_poly = lis_chue_nod_poly.index(chue_nod_poly)
                # このリストにない場合、無視する
                else:
                    continue
    
                for lai_na in range(na0,na1+1): # モデルの面のリストに追加
                    lek_chut_nai_na = lis_lek_chut_mai[lek_nod_poly][lai_na]
                    for ii in range(0,len(lek_chut_nai_na),3):
                        model_face_ap(lek_chut_nai_na[ii:ii+3])
                        n_chut_nai_mat += 3
    
            # 選択されているポリゴンの中で使われていない材質は無視する
            if(n_chut_nai_mat==0):
                continue
            if(mc.objExists(chue_mat+'.namae')):
                namae = mc.getAttr(chue_mat+'.namae')
            else:
                namae = '材質%d'%(i_mat+1)
            # 材質を作成して、まずは初期値を与える
            mat = mmdio.pmx.Material()
            mat.name = namae
            mat.name_e = chue_mat
            mat.diffuse = [1,1,1,1]
            mat.specular = [0,0,0,0.5]
            mat.ambient = [0.5,0.5,0.5]
            mat.edge_color = [0,0,0,1]
            mat.edge_size = 1
            mat.texture = -1
            mat.sphere_texture = -1
            mat.sphere_texture_mode = 0
            mat.is_shared_toon_texture = False
            mat.toon_texture = -1
            mat.comment = ''
            mat.vertex_count = n_chut_nai_mat
            mat.is_double_sided = True
    
            # 普通に使えない材質の場合、エラーが出る
            try:
                nodetype = mc.nodeType(chue_mat) # 材質のシェーディングタイプ
                # テクスチャが使われるかどうかを調べる
                if(nodetype in ['standardSurface','aiStandardSurface']):
                    chue_nod_tex = mc.listConnections(chue_mat+'.baseColor')
                else: # blinn、lambert、phongなど
                    chue_nod_tex = mc.listConnections(chue_mat+'.color')
                # ファイルのテクスチャが使われている材質の場合
                if(chue_nod_tex):
                    if(mc.nodeType(chue_nod_tex[0])=='file'):
                        chue_tem_file_tex = mc.getAttr(chue_nod_tex[0]+'.ftn') # このテクスチャのファイルの名前
                        # 既存のファイルの場合、これを使う
                        if(chue_tem_file_tex in lis_chue_tex):
                            mat.texture = lis_chue_tex.index(chue_tem_file_tex)
                        # まだない場合、追加する
                        else:
                            lis_chue_tex.append(chue_tem_file_tex)
                            texture = mmdio.pmx.Texture()
                            texture.path = os.path.join(chue_tem_file_tex)
                            # テクスチャのファイルをコピーすると選択しておいた場合
                            if(lok_tex):
                                chue_tex = os.path.basename(chue_tem_file_tex)
                                chue_tem_path_tex_mai = os.path.join(chue_path_file,chue_tex)
                                shutil.copyfile(chue_tem_file_tex,chue_tem_path_tex_mai)
                                texture.path = os.path.join(chue_tem_path_tex_mai)
                            pmx_model.textures.append(texture)
                            mat.texture = i_tex
                            i_tex += 1 # テクスチャの番号を数え続ける
                    else:
                        print('注意：テクスチャ%sはファイルではないため無視されます'%chue_nod_tex[0])
                    dc = [1.,1.,1.]
                # テクスチャが使われていない材質の場合、拡散色の値を使う
                else:
                    if(nodetype in ['standardSurface','aiStandardSurface']):
                        dc = mc.getAttr(chue_mat+'.baseColor')[0]
                    else:
                        dc = mc.getAttr(chue_mat+'.color')[0]
                    dc = [min(max(s,0.),1.) for s in dc]
                    mat.diffuse[:3] = dc
    
                if(nodetype not in ['standardSurface','aiStandardSurface']):
                    tran = sum(mc.getAttr(chue_mat+'.transparency')[0])/3 # 透明度は3色の平均値を使う
                    mat.diffuse[3] = min(max(1-tran,0),1.)
                    mat.ambient = [min(max(s,0.),1.)*d for s,d in zip(mc.getAttr(chue_mat+'.ambientColor')[0],dc)]
                    # blinnだけスペキュラを使う
                    if(nodetype=='blinn'):
                        sr = min(max(mc.getAttr(chue_mat+'.specularRollOff'),0.1),1.)
                        mat.specular[3] = round(math.pow(2,math.log(max(sr,0.1),0.75)-1))
                        mat.specular[:3] = [min(max(s,0.),1.) for s in mc.getAttr(chue_mat+'.specularColor')[0]]
                # standardSurfaceの場合
                else:
                    opa = sum(mc.getAttr(chue_mat+'.opacity')[0])/3 # 不透明度は3色の平均値を使う
                    mat.diffuse[3] = min(max(opa,0.),1.)
                    mat.specular[:3] = [min(max(s,0.),1.) for s in mc.getAttr(chue_mat+'.specularColor')[0]]
                    sr = max(mc.getAttr(chue_mat+'.specularRoughness'),0.1)
                    mat.specular[3] = round(math.pow(2,math.log(max(sr,0.1),0.75)-1))
                    mat.ambient = [0,0,0] # standardSurfaceの場合にアンビアントがないので
            except:
                print('材質%sに問題が見つかったようです'%chue_mat)
    
            model_mat_ap(mat) # モデルの材質のリストに収める
            i_mat += 1
    
    # 材質を使わないと選択した場合、全部同じ材質にする
    else:
        n_chut_nai_mat = 0
        for lis_lek_chut_nai_poly in lis_lek_chut_mai:
            for lis_lek_chut_nai_na in lis_lek_chut_nai_poly:
                n_chut_nai_mat += len(lis_lek_chut_nai_na)
                for i in range(0,len(lis_lek_chut_nai_na),3):
                    model_face_ap(lis_lek_chut_nai_na[i:i+3])
    
        mat = mmdio.pmx.Material()
        mat.name = '材質1'
        mat.name_e = ''
        mat.diffuse = [0.5,0.5,0.5,1]
        mat.specular = [0.5,0.5,0.5,0.5]
        mat.ambient = [0.25,0.25,0.25]
        mat.edge_color = [0,0,0,1]
        mat.edge_size = 1
        mat.texture = -1
        mat.sphere_texture = -1
        mat.sphere_texture_mode = 0
        mat.is_shared_toon_texture = False
        mat.toon_texture = -1
        mat.comment = ''
        mat.vertex_count = n_chut_nai_mat
        mat.is_double_sided = True
        model_mat_ap(mat)
    
    chue_model = os.path.basename(chue_tem_file).split('.')[0]
    pmx_model.name = chue_model
    pmx_model.name_e = chue_model
    if(not pmx_model.display[2].data):
        pmx_model.display.pop()
    
    mmdio.pmx.save(chue_tem_file,pmx_model)
    mc.select(lis_chue_nod_poly)
    print('"%s"へエクスポート完了。\n%.2f秒かかりました'%(chue_tem_file,time.time()-t0))
