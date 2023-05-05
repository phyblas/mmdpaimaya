# -*- coding: utf-8 -*-
import os,math,itertools,time,re
from . import mmdio
from .asset.jaka import romaji
import maya.cmds as mc
import maya.api.OpenMaya as om
import maya.api.OpenMayaAnim as oma

def sang(chue_tem_file,satsuan=1,yaek_poly=False,ao_bs=True,ao_kraduk=True,watsadu=1):
    t_roem = time.time() # 開始
    print('モデルインポート開始')
    
    sakun = os.path.splitext(chue_tem_file)[1] # 拡張子
    
    try:
        if(sakun=='.pmx'):
            pmx_model = mmdio.pmx.load(chue_tem_file)
        elif(sakun=='.pmd'):
            pmx_model = mmdio.pmd.load2pmx(chue_tem_file)
        elif(sakun=='.x'):
            pmx_model = mmdio.xxx.load2pmx(chue_tem_file)
        else:
            print('pmxとpmdとxファイルしか使用できません')
            raise
    except:
        print('モデルに何か問題があって、ファイルの読み込みは失敗です')
        raise
    
    chue_nod_model = romaji(pmx_model.name) # モデルの名前をロマジに変換してモデルのノードの名前にする
    if(not chue_nod_model or set(chue_nod_model)=={'_'}):
        chue_nod_model = romaji(os.path.basename(chue_tem_file).split('.')[0])
    lis_chue_nod_kho_nok = [] # 一番外のジョイントのノードの名前を収めるリスト
    chue_nod_skin = None
    chue_nod_bs = None
    # その名前のノードがすでに存在している場合'_'を追加する
    while(mc.objExists(chue_nod_model)):
        chue_nod_model += '_'
    
    print('ポリゴン作成')
    if(yaek_poly): # ポリゴンを分割する場合、今まだ何もしなくていい
        lis_chue_nod_poly_mat = []
    else:
        # pmxモデルから頂点の位置とuv一つずつ入れていく
        lis_xyz = [] # 頂点の位置を収めるリスト
        lis_u = [] # 頂点のuvを収めるリスト
        lis_v = []
        lis_norm = [] # 頂点の法線を収めるリスト
        for vtx in pmx_model.vertices:
            try:
                lis_xyz.append(om.MFloatPoint(vtx.co[0]*satsuan,vtx.co[1]*satsuan,-vtx.co[2]*satsuan))
            except: # 大きすぎたりとエラーが出る場合もあるので、(0,0,0)にする
                lis_xyz.append(om.MFloatPoint(0,0,0))
            lis_u.append(vtx.uv[0]) # 頂点のuvをリストに収める
            lis_v.append(1.-vtx.uv[1])
            if(vtx.normal): # 頂点の法線のデータがあった場合
                lis_norm.append(om.MFloatVector(vtx.normal[0],vtx.normal[1],-vtx.normal[2]))
        
        lis_index_chut = [] # この面に使う頂点を収めるリスト
        lis_n_chut_nai_na = [] # この面に使う頂点の数を収めるリスト
        lis_na_ni_chai_mai = [] # この面が使うかどうかという情報を収めるリスト
        for i_chut_nai_na in pmx_model.faces:
            i_chut_nai_na = list(dict.fromkeys(i_chut_nai_na)) # この面に使う頂点
            n_chut_nai_na = len(i_chut_nai_na) # この面に使う頂点の数
            if(n_chut_nai_na>=3): # 重複しない頂点が3以上ある場合のみ、この面を使う
                lis_index_chut.extend(i_chut_nai_na)
                lis_n_chut_nai_na.append(n_chut_nai_na)
                lis_na_ni_chai_mai.append(True) # この面を使う
            else:
                lis_na_ni_chai_mai.append(False) # この面を使わない
        
        chue_nod_poly = sang_poly(chue_nod_model,lis_xyz,lis_index_chut,lis_n_chut_nai_na,lis_u,lis_v,lis_norm)
        
        if(not watsadu): # 材質を使わないと選択したら全部ただのlambertにする
            mc.select(chue_nod_poly)
            mc.hyperShade(assign='lambert1')
    
    set_index_tex = set([mat.texture for mat in pmx_model.materials])
    lis_chue_nod_file = [] # テクスチャファイルの名前を収めるリスト
    # テクスチャを作成する
    for i,tex in enumerate(pmx_model.textures):
        path_tem_tex = tex.path
        chue_tex = os.path.basename(path_tem_tex) # テクスチャの名前
        chue_tex = re.sub(r'\W','_',chue_tex)
        chue_tex = romaji(chue_tex) # テクスチャの名前をロマジにする
        chue_nod_file = chue_tex+'_file_'+chue_nod_model
        # 使われているテクスチャだけshadingNodeのノードを作る
        if(i in set_index_tex):
            # 同じ名前が既存である場合、ノードの名前が自動的に変更される
            chue_nod_file = mc.shadingNode('file',asTexture=True,name=chue_nod_file)
            mc.setAttr(chue_nod_file+'.ftn',path_tem_tex,typ='string')
            # place2dのノードを作る
            chue_nod_placed2d = mc.shadingNode('place2dTexture',asUtility=True,name=chue_tex+'_placed2d_'+chue_nod_model)
            # place2dノードの値とファイルノードの値を接続する
            for cp in chueam_placed2d:
                mc.connectAttr('%s.%s'%(chue_nod_placed2d,cp[0]),'%s.%s'%(chue_nod_file,cp[1]),force=1)
            
        lis_chue_nod_file.append(chue_nod_file)
    
    # 材質を作成する
    nap_na_nai_mat = 0 # すでに材質を付けた面の数
    for i_mat,mat in enumerate(pmx_model.materials):
        if(mat.vertex_count==0): # 面一つもないならスキップ
            continue
        n_na_nai_mat = int(mat.vertex_count/3) # この材質を付ける面の数
        chue_mat = romaji(mat.name)
        chue_nod_mat = chue_mat+'_mat_'+chue_nod_model
        
        i_tex = mat.texture # この材質に付けるテクスチャの番号
        dc = mat.diffuse[:3] # 拡散色
        ambc = mat.ambient # 環境色
        spec = mat.specular[:3] # 反射色
        alpha = mat.diffuse[3] # 不透明度
        opa = [alpha,alpha,alpha]
        trans = [1-alpha,1-alpha,1-alpha] # 透明度
        sf = mat.specular[3] # 反射強度
        
        if(watsadu==1):
            chue_nod_mat = mc.shadingNode('blinn',asShader=True,name=chue_nod_mat)
            mc.setAttr(chue_nod_mat+'.specularColor',*spec,typ='double3')
            mc.setAttr(chue_nod_mat+'.specularRollOff',min(0.75**(math.log(max(sf,2**-10),2)+1),1))
            mc.setAttr(chue_nod_mat+'.eccentricity',sf*0.01)
        elif(watsadu==2):
            chue_nod_mat = mc.shadingNode('phong',asShader=1,n=chue_nod_mat)
            mc.setAttr(chue_nod_mat+'.specularColor',*spec,typ='double3')
            mc.setAttr(chue_nod_mat+'.cosinePower',max((10000./max(sf,15)**2-3.357)/0.454,2))
        elif(watsadu==3 or not watsadu):
            chue_nod_mat = mc.shadingNode('lambert',asShader=1,name=chue_nod_mat)
            
        if(watsadu in [1,2,3]):
            mc.setAttr(chue_nod_mat+'.color',*dc,typ='double3')
            mc.setAttr(chue_nod_mat+'.ambientColor',*ambc,typ='double3')
            mc.setAttr(chue_nod_mat+'.transparency',*trans,typ='double3')
        elif(watsadu==4): # arnoldを使う場合
            chue_nod_mat = mc.shadingNode('standardSurface',asShader=True,name=chue_nod_mat)
            mc.setAttr(chue_nod_mat+'.baseColor',*dc,typ='double3')
            mc.setAttr(chue_nod_mat+'.specularColor',*spec,typ='double3')
            mc.setAttr(chue_nod_mat+'.opacity',*opa,typ='double3')
            mc.setAttr(chue_nod_mat+'.specular',0.75**(math.log(max(sf,0.5),2)+1))
            mc.setAttr(chue_nod_mat+'.specularRoughness',min(sf*0.01,1))
            mc.setAttr(chue_nod_mat+'.base',1)
        
        # 日本語の名前も一応収めておく
        mc.addAttr(chue_nod_mat,longName='namae',niceName='名前',dataType='string')
        mc.setAttr(chue_nod_mat+'.namae',mat.name,typ='string')
        if(i_tex>=0):
            chue_nod_file = lis_chue_nod_file[i_tex]
            if(watsadu!=4):
                mc.connectAttr(chue_nod_file+'.outColor',chue_nod_mat+'.color')
            else:
                mc.connectAttr(chue_nod_file+'.outColor',chue_nod_mat+'.baseColor')
                
            tex = pmx_model.textures[i_tex]
            if(mc.getAttr(chue_nod_file+'.fileHasAlpha') and tex.path[-3:].lower() in ['png','tga','dds','bmp']):
                # テクスチャノードのアルファを材質ノードに接続する
                if(watsadu in [1,2,3]):
                    mc.connectAttr(chue_nod_file+'.outTransparency',chue_nod_mat+'.transparency')
                elif(watsadu==4):
                    mc.connectAttr(chue_nod_file+'.outAlpha',chue_nod_mat+'.opacityR')
                    mc.connectAttr(chue_nod_file+'.outAlpha',chue_nod_mat+'.opacityG')
                    mc.connectAttr(chue_nod_file+'.outAlpha',chue_nod_mat+'.opacityB')
                
        chue_nod_sg = mc.sets(renderable=1,noSurfaceShader=1,empty=1,name=chue_nod_mat+'SG')
        mc.connectAttr(chue_nod_mat+'.outColor',chue_nod_sg+'.surfaceShader', force=True)
        
        if(yaek_poly):
            lis_index_chut_mat = []
            lis_n_chut_nai_na_nai_mat = []
            dic_chut = {}
            k = 0
            for i_chut_nai_na in pmx_model.faces[nap_na_nai_mat:nap_na_nai_mat+n_na_nai_mat]:
                i_chut_nai_na = list(dict.fromkeys(i_chut_nai_na))
                n_chut_nai_na = len(i_chut_nai_na)
                if(n_chut_nai_na>=3):
                    for j in range(n_chut_nai_na):
                        if(i_chut_nai_na[j] not in dic_chut):
                            dic_chut[i_chut_nai_na[j]] = k # 元の番号と新しい番号を繋ぐ辞書
                            k += 1
                        lis_index_chut_mat.append(dic_chut[i_chut_nai_na[j]])
                    lis_n_chut_nai_na_nai_mat.append(n_chut_nai_na)
            
            lis_xyz_mat = []
            lis_u_mat = []
            lis_v_mat = []
            lis_norm_mat = []
            for ic in dic_chut:
                k = dic_chut[ic]
                vtx = pmx_model.vertices[ic]
                try:
                    lis_xyz_mat.append(om.MFloatPoint(vtx.co[0]*satsuan,vtx.co[1]*satsuan,-vtx.co[2]*satsuan))
                except:
                    lis_xyz_mat.append(om.MFloatPoint(0,0,0))
                lis_u_mat.append(vtx.uv[0])
                lis_v_mat.append(1.-vtx.uv[1])
                lis_norm_mat.append(om.MFloatVector(vtx.normal[0],vtx.normal[1],-vtx.normal[2]))
            
            # この材質のポリゴンを作成する
            chue_nod_poly_mat = sang_poly(chue_nod_model+'_%d'%(i_mat+1),lis_xyz_mat,lis_index_chut_mat,lis_n_chut_nai_na_nai_mat,lis_u_mat,lis_v_mat,lis_norm_mat)
            n_na_chai_mat = len(lis_n_chut_nai_na_nai_mat) # 実際に使う面の数
            mc.sets(chue_nod_poly_mat+'.f[%s:%s]'%(0,n_na_chai_mat-1),forceElement=chue_nod_sg)
            lis_chue_nod_poly_mat.append(chue_nod_poly_mat)
        else:
            nap_na_chai0 = sum(lis_na_ni_chai_mai[:nap_na_nai_mat])
            nap_na_chai1 = sum(lis_na_ni_chai_mai[:nap_na_nai_mat+n_na_nai_mat])
            # 指定の面に材質を貼る
            mc.sets(chue_nod_poly+'.f[%s:%s]'%(nap_na_chai0,nap_na_chai1-1),forceElement=chue_nod_sg)
        
        nap_na_nai_mat += n_na_nai_mat # 面の数を数え続ける
    
    if(yaek_poly):
        chue_nod_poly = mc.group(lis_chue_nod_poly_mat,name=chue_nod_model)
    
    
    if(ao_bs and not yaek_poly):
        print('ブレンドシェープ作成')
        # 各パネル（眉、目、口、他）
        lis_chue_nod_poly_bs = [[],[],[],[]] # ブレンドシェープを作るためのポリゴンのノードのリストを収める
        lis_chue_bs_doem = [[],[],[],[]] # 元の名前（日本の名前）を収めるリスト
        for i,mo in enumerate(pmx_model.morphs):
            # 頂点モーフをブレンドシェープに変換する。他のモーフは変換できないので無視する
            if(mo.type_index()==1):
                # ブレンドシェープの名前はロマジに変換しなければならない
                chue_bs = romaji(mo.name)
                # ブレンドシェープを作るために、元のポリゴンをコピーする
                chue_nod_poly_bs = mc.duplicate(chue_nod_poly,name=chue_bs)[0]
                
                selelis = om.MSelectionList()
                selelis.add(chue_nod_poly_bs)
                dagpath = selelis.getDagPath(0)
                fn_mesh = om.MFnMesh(dagpath)
                arr_chut = fn_mesh.getPoints() # 頂点の位置が入っている配列
                
                for off in mo.offsets:
                    vi = off.index # 動く頂点の番号
                    d = off.offset # 元の位置から動く距離
                    p = arr_chut[vi] # 元の頂点のいち
                    arr_chut[vi] = [p[0]+d[0]*satsuan,p[1]+d[1]*satsuan,p[2]-d[2]*satsuan] # 頂点が動いた後の位置を配列に入れる
                
                fn_mesh.setPoints(arr_chut)
                lis_chue_nod_poly_bs[mo.category-1].append(chue_nod_poly_bs)
                lis_chue_bs_doem[mo.category-1].append(mo.name)
        
        # 一つのリストにする。順番はパネルによる
        lis_chue_nod_poly_bs = list(itertools.chain(*lis_chue_nod_poly_bs))
        mc.select(lis_chue_nod_poly_bs,chue_nod_poly)
        # ブレンドシェープのノードを作成する
        chue_nod_bs = mc.blendShape(name='bs_'+chue_nod_poly)[0]
        mc.delete(lis_chue_nod_poly_bs) # すでにブレンドシェープを作るために使ったポリゴンは用済みだから消す
    
    if(ao_kraduk and not yaek_poly):
        print('ジョイント作成')
        lis_chue_nod_kho = [] # ジョイントの名前を収めるリスト
        for b in pmx_model.bones:
            mc.select(deselect=1)
            chue_kho = romaji(b.name)
            loc = b.location # ジョイントの位置
            # ジョイントの半径
            if('yubi' in chue_kho): # 指は小さめ
                r_kho = satsuan/4
            elif(chue_kho=='sentaa'): # サンターは大きめ
                r_kho = satsuan
            else: # その他
                r_kho = satsuan/2   
            # ジョイントのノードを作成する
            chue_nod_kho = mc.joint(position=[loc[0]*satsuan,loc[1]*satsuan,-loc[2]*satsuan],radius=r_kho,name=chue_nod_poly+ '_'+chue_kho)
            mc.addAttr(chue_nod_kho,longName='namae',niceName='名前',dataType='string') # 日本語の名前も一応ここに収めておく
            mc.setAttr(chue_nod_kho+'.namae',b.name,typ='string')
            
            if(b.isIK or not b.visible): # 表示しないジョイント
                mc.setAttr(chue_nod_kho+'.drawStyle',2)
            else:
                mc.setAttr(chue_nod_kho+'.drawStyle',0)
            # ローカル軸が指定されている場合
            if(b.localCoordinate or b.axis):
                if(b.axis): # x軸だけが指定されている場合
                    kaen_x = b.axis
                    kaen_z = cross([0.0,1.0,0.0],kaen_x)
                else: # x軸もz軸も指定されている場合
                    kaen_x = b.localCoordinate.x_axis
                    kaen_z = b.localCoordinate.z_axis
                kaen_y = cross(kaen_z,kaen_x)
                # ジョイントの方向を表すオイラー角に変換するための行列
                matrix_mun = om.MMatrix([kaen_x[0],kaen_x[1],-kaen_x[2],0.,
                                         kaen_y[0],kaen_y[1],-kaen_y[2],0.,
                                         kaen_z[0],kaen_z[1],-kaen_z[2],0.,
                                         0.,0.,0.,1.])
                mum_euler = om.MTransformationMatrix(matrix_mun).rotation()
                # できたオイラー角の単位がラジアンなので角度に変換する
                ox = math.degrees(mum_euler.x)
                oy = math.degrees(mum_euler.y)
                oz = math.degrees(mum_euler.z)
                mc.setAttr(chue_nod_kho+'.jointOrient',ox,oy,oz) # ジョイントの方向
            
            lis_chue_nod_kho.append(chue_nod_kho)
        
        for i,b in enumerate(pmx_model.bones):
            chue_nod_kho = lis_chue_nod_kho[i]
            if(b.parent>=0):
                # ジョイントを結び合う
                chue_nod_parent = lis_chue_nod_kho[b.parent]
                mc.connectJoint(chue_nod_kho,chue_nod_parent,parentMode=1)
            else:
                lis_chue_nod_kho_nok.append(chue_nod_kho)
            
            # 回転角の不具合がある場合の解決
            if(round(mc.getAttr(chue_nod_kho+'.rx'))%360==0):
                mc.setAttr(chue_nod_kho+'.rx',0)
            if(round(mc.getAttr(chue_nod_kho+'.ry'))%360==0):
                mc.setAttr(chue_nod_kho+'.ry',0)
            if(round(mc.getAttr(chue_nod_kho+'.rz'))%360==0):
                mc.setAttr(chue_nod_kho+'.rz',0)
            if(round(mc.getAttr(chue_nod_kho+'.rx'))%360==180 and round(mc.getAttr(chue_nod_kho+'.ry'))%360==180 and round(mc.getAttr(chue_nod_kho+'.rz'))%360==180):
                mc.setAttr(chue_nod_kho+'.r',0,0,0)
            
            if(b.hasAdditionalRotate):
                # 回転付与のあるジョイントの場合
                chue_nod_effect = lis_chue_nod_kho[b.additionalTransform[0]] # 影響を与えるノード
                jo = mc.getAttr(chue_nod_effect+'.jointOrient')[0] # このジョイントの方向を取得
                mc.setAttr(chue_nod_kho+'.jointOrient',*jo) # 同じジョイントの方向にする
                
                # 回転付与をエクスプレッションにする
                ef = b.additionalTransform[1] # 付与率
                s = '%s.rotateX = %s.rotateX * %s;\n'%(chue_nod_kho,chue_nod_effect,ef)
                s += '%s.rotateY = %s.rotateY * %s;\n'%(chue_nod_kho,chue_nod_effect,ef)
                s += '%s.rotateZ = %s.rotateZ * %s;\n'%(chue_nod_kho,chue_nod_effect,ef)
                mc.expression(string=s,name='expression_%s_%s'%(chue_nod_kho,chue_nod_effect))
            
            if(b.hasAdditionalLocation):
                # 移動付与をエクスプレッションにする
                chue_nod_effect = lis_chue_nod_kho[b.additionalTransform[0]] # 影響を与えるノード
                ef = b.additionalTransform[1] # 付与率
                s = '%s.translateX = %s.translateX * %s;\n'%(chue_nod_kho,chue_nod_effect,ef)
                s += '%s.translateY = %s.translateY * %s;\n'%(chue_nod_kho,chue_nod_effect,ef)
                s += '%s.translateZ = %s.translateZ * %s;\n'%(chue_nod_kho,chue_nod_effect,ef)
                mc.expression(string=s,name='expression_%s_%s'%(chue_nod_kho,chue_nod_effect))
        
        selelis = om.MSelectionList()
        selelis.add(chue_nod_poly)
        dagpath_mesh = selelis.getDagPath(0)
        
        chue_nod_skin = 'skin_'+chue_nod_poly
        chue_nod_skin = mc.skinCluster(lis_chue_nod_kho,chue_nod_poly,maximumInfluences=4,toSelectedBones=True,name=chue_nod_skin)[0] # スキンのノードを作成する
        selelis = om.MSelectionList()
        selelis.add(chue_nod_skin)
        obj_skin = selelis.getDependNode(0)
        fn_skin = oma.MFnSkinCluster(obj_skin)
        
        n_kho = len(pmx_model.bones)
        lis_namnak = [] # 重みの値を収めるリスト
        for vtx in pmx_model.vertices:
            namnak = [0.]*n_kho # この頂点に対する各ジョイントの影響の重み
            if(vtx.weight.type==mmdio.pmx.BoneWeight.BDEF1):
                # 2つだけのジョイントの影響を受ける場合
                namnak[vtx.weight.bones[0]] = 1.
            elif(vtx.weight.type==mmdio.pmx.BoneWeight.BDEF2):
                # 2つのジョイントの影響を受ける場合
                namnak[vtx.weight.bones[0]] += vtx.weight.weights[0]
                namnak[vtx.weight.bones[1]] += 1.-vtx.weight.weights[0]
            elif(vtx.weight.type==mmdio.pmx.BoneWeight.SDEF):
                # SDEFの場合もBDEF2と同様に2つのジョイント扱い
                namnak[vtx.weight.bones[0]] += vtx.weight.weights.weight
                namnak[vtx.weight.bones[1]] += 1.-vtx.weight.weights.weight
            elif(vtx.weight.type==mmdio.pmx.BoneWeight.BDEF4):
                # 4つのジョイントの影響を受ける場合
                namnak[vtx.weight.bones[0]] += vtx.weight.weights[0]
                namnak[vtx.weight.bones[1]] += vtx.weight.weights[1]
                namnak[vtx.weight.bones[2]] += vtx.weight.weights[2]
                namnak[vtx.weight.bones[3]] += 1.-vtx.weight.weights[0]-vtx.weight.weights[1]-vtx.weight.weights[2]
            lis_namnak.extend(namnak)
        
        n_chut = len(pmx_model.vertices) # 頂点の数
        arr_index_chut = om.MIntArray(range(n_chut)) # 頂点の番号の配列
        arr_namnak = om.MDoubleArray(lis_namnak) # 重みの値の配列
        arr_index_influ = om.MIntArray(range(n_kho)) # ジョイントの番号の配列
        fn_compo = om.MFnSingleIndexedComponent()
        compo = fn_compo.create(om.MFn.kMeshVertComponent)
        fn_compo.addElements(arr_index_chut)
        # ポリゴンに対するそれぞれのジョウントの影響の重みの値を設置する
        fn_skin.setWeights(dagpath_mesh,compo,arr_index_influ,arr_namnak,1)
        
        for chue_nod_kho in lis_chue_nod_kho:
            if(chue_nod_kho not in lis_chue_nod_kho_nok):
                mc.rename(chue_nod_kho,chue_nod_kho.replace(chue_nod_poly+'_',''))
    
    # 日本語の名前も一応収めておく
    mc.addAttr(chue_nod_poly,longName='namae',niceName='名前',dataType='string')
    mc.setAttr(chue_nod_poly+'.namae',pmx_model.name,typ='string')
    
    mc.select(chue_nod_poly)
    if(ao_kraduk):
        mc.select(lis_chue_nod_kho_nok)
    
    try:
        mc.setAttr('hardwareRenderingGlobals.transparencyAlgorithm',3)
        mc.setAttr('defaultArnoldRenderOptions.autotx',0)
        mc.setAttr('defaultArnoldRenderOptions.use_existing_tiled_textures',0)
    except:
        0

    print('モデルインポート完了。%.2f秒かかりました'%(time.time()-t_roem))
    return chue_nod_poly,lis_chue_nod_kho_nok,chue_nod_skin,chue_nod_bs



def sang_poly(chue_nod_poly,lis_xyz,lis_index_chut,lis_n_chut_nai_na,lis_u,lis_v,lis_norm=None):
    # 頂点のデータを収めておいたリストをmayaの配列オブジェクトにする
    arr_xyz = om.MFloatPointArray(lis_xyz) # 頂点の位置
    arr_index_chut = om.MIntArray(lis_index_chut) # 頂点の番号
    arr_n_chut_nai_na = om.MIntArray(lis_n_chut_nai_na) # 各面に使う頂点の数
    arr_u = om.MFloatArray(lis_u) # 頂点のuv
    arr_v = om.MFloatArray(lis_v)
    
    trans_fn = om.MFnTransform()
    trans_obj = trans_fn.create()
    trans_fn.setName(chue_nod_poly)
    chue_nod_poly = trans_fn.name()
    # 準備しておいたデータから全てのポリゴンメッシュを作成する
    fn_mesh = om.MFnMesh()
    fn_mesh.create(arr_xyz,arr_n_chut_nai_na,arr_index_chut,arr_u,arr_v,trans_obj)
    fn_mesh.setName(chue_nod_poly+'Shape')
    fn_mesh.assignUVs(arr_n_chut_nai_na,arr_index_chut)
    if(lis_norm):
        fn_mesh.setVertexNormals(lis_norm,om.MIntArray(range(len(lis_xyz))))

    # 一応MMDからのモデルだという情報をポリゴンのノードに刻んでおく
    mc.addAttr(chue_nod_poly,longName='MMD_model',niceName='MMDからのモデル',attributeType='bool')
    mc.setAttr(chue_nod_poly+'.MMD_model',True)
    mc.setAttr(chue_nod_poly+'.aiOpaque',0) # arnoldを使う時に不透明度を有効にする
    return chue_nod_poly


def cross(a,b):
    c = [a[1]*b[2]-a[1]*b[1],
         a[2]*b[0]-a[2]*b[2],
         a[0]*b[1]-a[0]*b[0]]
    return c

# place2dTextureノードとfileノードが接続するアトリビュートの名前
chueam_placed2d = [
    ['coverage','coverage'],
    ['translateFrame','translateFrame'],
    ['rotateFrame','rotateFrame'],
    ['mirrorU','mirrorU'],
    ['mirrorV','mirrorV'],
    ['stagger','stagger'],
    ['wrapU','wrapU'],
    ['wrapV','wrapV'],
    ['repeatUV','repeatUV'],
    ['offset','offset'],
    ['rotateUV','rotateUV'],
    ['noiseUV','noiseUV'],
    ['vertexUvOne','vertexUvOne'],
    ['vertexUvTwo','vertexUvTwo'],
    ['vertexUvThree','vertexUvThree'],
    ['vertexCameraOne','vertexCameraOne'],
    ['outUV','uv'],
    ['outUvFilterSize','uvFilterSize'],
]