# -*- coding: utf-8 -*-
'''
.xファイルからポリゴンのデータを読み込んでpmxモデルに変換するコードです。
'''

import re,os
from . import pmx

def load2pmx(chue_tem_file):
    chue_file = os.path.splitext(os.path.basename(chue_tem_file))[0]
    path_file = os.path.dirname(chue_tem_file)
    pmx_model = pmx.Model() # まずは空っぽのpmxモデルを準備しておく
    pmx_model.name = chue_file # ファイルの名前をモデルの名前にする
    pmx_model.vertices = []
    pmx_model.faces = []
    pmx_model.materials = []
    pmx_model.textures = []
    lis_watsadu_nai_na = [] # 各面の材質の番号を収めるリスト
    lis_chue_tex = [] # テクスチャの名前を収めるリスト
    lis_na = [] # 面の位置を収めるリスト。後で材質の順で並べ直す
    
    try: #UTF8で読んで問題ないかどうかチェック
        with open(chue_tem_file,'r',encoding='utf-8') as file_x:
            file_x.read()
            encoding = 'utf-8'
    except: # 問題あったらshift jis
        encoding = 'shift_jis'
    
    with open(chue_tem_file,'r',encoding=encoding) as file_x:
        s = file_x.readline()
        while(s):
            s = s.strip()
            
            # 頂点の情報が書かれているところ
            if(s and s.split()[0]=='Mesh'):
                while('{' not in s):
                    s = file_x.readline()
                s = file_x.readline()
                n = int(s.split(';')[0])
                # 頂点の位置をリストに入れていく
                for i in range(n):
                    s = file_x.readline().strip().split(';')
                    vtx = pmx.Vertex()
                    vtx.co = [float(s[0]),float(s[1]),float(s[2])]
                    pmx_model.vertices.append(vtx)
                s = file_x.readline()
                while(s.strip()==''):
                    s = file_x.readline()
                n = int(s.split(';')[0])
                # 各面に使う頂点の番号をリストに入れていく
                for i in range(n):
                    s = file_x.readline().strip()
                    ss = s.split(';')[1].split(',')
                    
                    ic = [int(x) for x in reversed(ss) if x] # 最後から最初
                    lis_na.append(ic)
            
            # uvの情報が書かれているところ
            if(s and s.split()[0]=='MeshTextureCoords'):
                while('{' not in s):
                    s = file_x.readline()
                s = file_x.readline()
                n = int(s.split(';')[0])
                # 頂点のuvを収めるリストに入れていく
                for i in range(n):
                    s = file_x.readline().strip().split(';')
                    if(len(s)<=2 or ',' in s[0]):
                        s = s[0].split(',')
                    pmx_model.vertices[i].uv = [float(s[0]),float(s[1])]
                while('}' not in s):
                    s = file_x.readline()
            
            # 各面に使う材質の情報が書かれているところ
            if(s and s.split()[0]=='MeshMaterialList'):
                while('{' not in s):
                    s = file_x.readline()
                s = file_x.readline()
                s = file_x.readline()
                n = int(s.split(';')[0])
                for i in range(n-1):
                    s = file_x.readline().strip().split(',')[0]
                    lis_watsadu_nai_na.append(int(s))
                s = file_x.readline().strip().split(';')[0]
                lis_watsadu_nai_na.append(int(s))
                
            i_mat = 0
            i_tex = 0
            # 材質の情報が書かれているところ
            while(s and s.split()[0]=='Material'):
                mat = pmx.Material() # 空っぽの材質オブジェクトを作っておく
                mat.name = 'mat_%d'%i # 番号で名前を付ける
                while('{' not in s):
                    s = file_x.readline()
                s = file_x.readline().strip().split(';')
                mat.diffuse = [float(s[0]),float(s[1]),float(s[2]),float(s[3])] # ベース色
                s = file_x.readline().strip().split(';')
                ns = float(s[0]) # スペキュラ
                s = file_x.readline().strip().split(';')
                mat.specular = (float(s[0]),float(s[1]),float(s[2]),ns) # スペキュラ色
                s = file_x.readline().strip().split(';')
                mat.ambient = (float(s[0]),float(s[1]),float(s[2])) # アンビアント色
                
                s = file_x.readline().strip()
                while(s==''):
                    s = file_x.readline().strip()
                # テクスチャを使っている材質の場合
                if(s.split()[0]=='TextureFilename'):
                    while('{' not in s):
                        s = file_x.readline().strip()
                    ss = s.split('{')[1]
                    if(not ss.strip()):
                        ss = file_x.readline().strip()
                    ss = re.findall(r'"(.+?)(?:\*.+)?";',ss)[0]
                    chue_tex = ss.replace(r'\\','/')
                    if(chue_tex in lis_chue_tex): # もしこのテクスチャがすでにリストにあればその番号を使う
                        mat.texture = lis_chue_tex.index(chue_tex)
                    else: # もしこのテクスチャがまだリストを追加して、新しい番号を付ける
                        lis_chue_tex.append(chue_tex)
                        mat.texture = i_tex
                        i_tex += 1 # テクスチャの番号を数え続ける
                    while('}' not in s):
                        s = file_x.readline().strip()
                else:
                    mat.tex = -1 # テクスチャを使っていない材質の場合
                while('}' not in s):
                    s = file_x.readline()
                
                pmx_model.materials.append(mat) # この材質をモデルの材質のリストに入れる
                i_mat += 1 # 材質の番号を数え続ける
            
            s = file_x.readline()
            
    for chue_tex in lis_chue_tex:
        tex = pmx.Texture()
        tex.path = os.path.join(path_file,chue_tex)
        pmx_model.textures.append(tex)
    # 各材質を使う面の番号を収めるリストのリスト
    na_nai_watsadu = [[] for _ in range(len(pmx_model.materials))]
    for i in range(len(lis_watsadu_nai_na)):
        na_nai_watsadu[lis_watsadu_nai_na[i]].append(lis_na[i])
    # 材質の順で面の順番を並べ替える
    for i,mat in enumerate(pmx_model.materials):
        mat.vertex_count = len(na_nai_watsadu[i])*3 # 各材質を使う面の数×3
        pmx_model.faces.extend(na_nai_watsadu[i])
    
    return pmx_model # .xファイルのデータを入れ終わったモデル