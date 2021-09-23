# -*- coding: utf-8 -*-
'''
.pmdファイルのデータを読み込んでpmdモデルオブジェクトに変換して、またpmxモデルオブジェクトに変換するコード。
ここのコードはpowroupiさんのblender_mmd_toolsからの書き換えです。
https://github.com/powroupi/blender_mmd_tools
'''

import struct,re,logging,collections,os,copy
from . import pmx

class InvalidFileError(Exception):
    pass
class UnsupportedVersionError(Exception):
    pass

class FileStream:
    def __init__(self, path, file_obj):
        self.__path = path
        self.__file_obj = file_obj
        self.__header = None

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_value, traceback):
        self.close()

    def path(self):
        return self.__path

    def header(self):
        if self.__header is None:
            raise Exception
        return self.__header

    def setHeader(self, pmx_header):
        self.__header = pmx_header

    def close(self):
        if self.__file_obj is not None:
            logging.debug('close the file("%s")', self.__path)
            self.__file_obj.close()
            self.__file_obj = None


class  FileReadStream(FileStream):
    def __init__(self, path, pmx_header=None):
        self.__fin = open(path, 'rb')
        FileStream.__init__(self, path, self.__fin)


    # READ / WRITE methods for general types
    def readInt(self):
        v, = struct.unpack('<i', self.__fin.read(4))
        return v

    def readUnsignedInt(self):
        v, = struct.unpack('<I', self.__fin.read(4))
        return v

    def readShort(self):
        v, = struct.unpack('<h', self.__fin.read(2))
        return v

    def readUnsignedShort(self):
        v, = struct.unpack('<H', self.__fin.read(2))
        return v

    def readStr(self, size):
        buf = self.__fin.read(size)
        try:
            index = buf.index(b'\x00')
            t = buf[:index]
            return t.decode('shift-jis')
        except ValueError:
            if buf[0] == b'\xfd':
                return ''
            try:
                return buf.decode('shift-jis')
            except UnicodeDecodeError:
                logging.warning('found a invalid shift-jis string.')
                return ''

    def readFloat(self):
        v, = struct.unpack('<f', self.__fin.read(4))
        return v

    def readVector(self, size):
        fmt = '<'
        for i in range(size):
            fmt += 'f'
        return list(struct.unpack(fmt, self.__fin.read(4*size)))

    def readByte(self):
        v, = struct.unpack('<B', self.__fin.read(1))
        return v

    def readBytes(self, length):
        return self.__fin.read(length)

    def readSignedByte(self):
        v, = struct.unpack('<b', self.__fin.read(1))
        return v


class Header:
    PMD_SIGN = b'Pmd'
    VERSION = 1.0

    def __init__(self):
        self.sign = self.PMD_SIGN
        self.version = self.VERSION
        self.model_name = ''
        self.comment = ''

    def load(self, fs):
        sign = fs.readBytes(3)
        if sign != self.PMD_SIGN:
            raise InvalidFileError('Not PMD file')
        version = fs.readFloat()
        if version != self.version:
            raise InvalidFileError('Not suppored version')

        self.model_name = fs.readStr(20)
        self.comment = fs.readStr(256)

class Vertex:
    def __init__(self):
        self.position = [0.0, 0.0, 0.0]
        self.normal = [1.0, 0.0, 0.0]
        self.uv = [0.0, 0.0]
        self.bones = [-1, -1]
        self.weight = 0 # min:0, max:100
        self.enable_edge = 0 # 0: on, 1: off

    def load(self, fs):
        self.position = fs.readVector(3)
        self.normal = fs.readVector(3)
        self.uv = fs.readVector(2)
        self.bones[0] = fs.readUnsignedShort()
        self.bones[1] = fs.readUnsignedShort()
        self.weight = fs.readByte()
        self.enable_edge = fs.readByte()

class Material:
    def __init__(self):
        self.diffuse = []
        self.specular_intensity = 0.5
        self.specular = []
        self.ambient = []
        self.toon_index = 0
        self.edge_flag = 0
        self.vertex_count = 0
        self.texture_path = ''
        self.sphere_path = ''
        self.sphere_mode = 1

    def load(self, fs):
        self.diffuse = fs.readVector(4)
        self.specular_intensity = fs.readFloat()
        self.specular = fs.readVector(3)
        self.ambient = fs.readVector(3)
        self.toon_index = fs.readByte()
        self.edge_flag = fs.readByte()
        self.vertex_count = fs.readUnsignedInt()
        tex_path = fs.readStr(20)
        t = tex_path.split('*')
        if not re.search(r'\.sp([ha])$', t[0], flags=re.I):
            self.texture_path = t.pop(0)
        if len(t) > 0:
            self.sphere_path = t.pop(0)
            if 'aA'.find(self.sphere_path[-1]) != -1:
                self.sphere_mode = 2

class Bone:
    def __init__(self):
        self.name = ''
        self.name_e = ''
        self.parent = 0xffff
        self.tail_bone = 0xffff
        self.type = 1
        self.ik_bone = 0
        self.position = []

    def load(self, fs):
        self.name = fs.readStr(20)
        self.parent = fs.readUnsignedShort()
        if self.parent == 0xffff:
            self.parent = -1
        self.tail_bone = fs.readUnsignedShort()
        if self.tail_bone == 0xffff:
            self.tail_bone = -1
        self.type = fs.readByte()
        self.ik_bone = fs.readUnsignedShort()
        self.position = fs.readVector(3)

class IK:
    def __init__(self):
        self.bone = 0
        self.target_bone = 0
        self.ik_chain = 0
        self.iterations = 0
        self.control_weight = 0.0
        self.ik_child_bones = []

    def __str__(self):
        return '<IK bone: %d, target: %d, chain: %s, iter: %d, weight: %f, ik_children: %s'%(
            self.bone,
            self.target_bone,
            self.ik_chain,
            self.iterations,
            self.control_weight,
            self.ik_child_bones)

    def load(self, fs):
        self.bone = fs.readUnsignedShort()
        self.target_bone = fs.readUnsignedShort()
        self.ik_chain = fs.readByte()
        self.iterations = fs.readUnsignedShort()
        self.control_weight = fs.readFloat()
        self.ik_child_bones = []
        for i in range(self.ik_chain):
            self.ik_child_bones.append(fs.readUnsignedShort())

class MorphData:
    def __init__(self):
        self.index = 0
        self.offset = []

    def load(self, fs):
        self.index = fs.readUnsignedInt()
        self.offset = fs.readVector(3)

class VertexMorph:
    def __init__(self):
        self.name = ''
        self.name_e = ''
        self.type = 0
        self.data = []

    def load(self, fs):
        self.name = fs.readStr(20)
        data_size = fs.readUnsignedInt()
        self.type = fs.readByte()
        for i in range(data_size):
            t = MorphData()
            t.load(fs)
            self.data.append(t)

class RigidBody:
    def __init__(self):
        self.name = ''
        self.bone = -1
        self.collision_group_number = 0
        self.collision_group_mask = 0
        self.type = 0
        self.size = []
        self.location = []
        self.rotation = []
        self.mass = 0.0
        self.velocity_attenuation = 0.0
        self.rotation_attenuation = 0.0
        self.friction = 0.0
        self.bounce = 0.0
        self.mode = 0

    def load(self, fs):
        self.name = fs.readStr(20)
        self.bone = fs.readUnsignedShort()
        if self.bone == 0xffff:
            self.bone = -1
        self.collision_group_number = fs.readByte()
        self.collision_group_mask = fs.readUnsignedShort()
        self.type = fs.readByte()
        self.size = fs.readVector(3)
        self.location = fs.readVector(3)
        self.rotation = fs.readVector(3)
        self.mass = fs.readFloat()
        self.velocity_attenuation = fs.readFloat()
        self.rotation_attenuation = fs.readFloat()
        self.bounce = fs.readFloat()
        self.friction = fs.readFloat()
        self.mode = fs.readByte()

class Joint:
    def __init__(self):
        self.name = ''
        self.src_rigid = 0
        self.dest_rigid = 0

        self.location = []
        self.rotation = []

        self.maximum_location = []
        self.minimum_location = []
        self.maximum_rotation = []
        self.minimum_rotation = []

        self.spring_constant = []
        self.spring_rotation_constant = []

    def load(self, fs):
        self.name = fs.readStr(20)

        self.src_rigid = fs.readUnsignedInt()
        self.dest_rigid = fs.readUnsignedInt()

        self.location = fs.readVector(3)
        self.rotation = fs.readVector(3)

        self.maximum_location = fs.readVector(3)
        self.minimum_location = fs.readVector(3)
        self.maximum_rotation = fs.readVector(3)
        self.minimum_rotation = fs.readVector(3)

        self.spring_constant = fs.readVector(3)
        self.spring_rotation_constant = fs.readVector(3)

class Model:
    def __init__(self):
        self.header = None
        self.vertices = []
        self.faces = []
        self.materials = []
        self.iks = []
        self.morphs = []
        self.facial_disp_names = []
        self.bone_disp_names = []
        self.bone_disp_lists = {}
        self.name = ''
        self.comment = ''
        self.name_e = ''
        self.comment_e = ''
        self.toon_textures = []
        self.rigid_bodies = []
        self.joints = []


    def load(self, fs):
        #logging.info('importing pmd model from %s...', fs.path())

        header = Header()
        header.load(fs)

        self.name = header.model_name
        self.comment = header.comment

        #logging.info('Model name: %s', self.name)
        #logging.info('Comment: %s', self.comment)

        #logging.info('')
        #logging.info('------------------------------')
        #logging.info('Load Vertices')
        #logging.info('------------------------------')
        self.vertices = []
        vert_count = fs.readUnsignedInt()
        for i in range(vert_count):
            v = Vertex()
            v.load(fs)
            self.vertices.append(v)
        #logging.info('the number of vetices: %d', len(self.vertices))
        #logging.info('finished importing vertices.')

        #logging.info('')
        #logging.info('------------------------------')
        #logging.info(' Load Faces')
        #logging.info('------------------------------')
        self.faces = []
        face_vert_count = fs.readUnsignedInt()
        for i in range(int(face_vert_count/3)):
            f1 = fs.readUnsignedShort()
            f2 = fs.readUnsignedShort()
            f3 = fs.readUnsignedShort()
            self.faces.append((f3, f2, f1))
        #logging.info('the number of faces: %d', len(self.faces))
        #logging.info('finished importing faces.')

        #logging.info('')
        #logging.info('------------------------------')
        #logging.info(' Load Materials')
        #logging.info('------------------------------')
        self.materials = []
        material_count = fs.readUnsignedInt()
        for i in range(material_count):
            mat = Material()
            mat.load(fs)
            self.materials.append(mat)

            #logging.info('Material %d', i)
            logging.debug('  Vertex Count: %d', mat.vertex_count)
            logging.debug('  Diffuse: (%.2f, %.2f, %.2f, %.2f)', *mat.diffuse)
            logging.debug('  Specular: (%.2f, %.2f, %.2f)', *mat.specular)
            logging.debug('  Specular Intensity: %f', mat.specular_intensity)
            logging.debug('  Ambient: (%.2f, %.2f, %.2f)', *mat.ambient)
            logging.debug('  Toon Index: %d', mat.toon_index)
            logging.debug('  Edge Type: %d', mat.edge_flag)
            logging.debug('  Texture Path: %s', str(mat.texture_path))
            logging.debug('  Sphere Texture Path: %s', str(mat.sphere_path))
            logging.debug('')
        #logging.info('Loaded %d materials', len(self.materials))

        #logging.info('')
        #logging.info('------------------------------')
        #logging.info(' Load Bones')
        #logging.info('------------------------------')
        self.bones = []
        bone_count = fs.readUnsignedShort()
        for i in range(bone_count):
            bone = Bone()
            bone.load(fs)
            self.bones.append(bone)

            #logging.info('Bone %d: %s', i, bone.name)
            logging.debug('  Name(english): %s', bone.name_e)
            logging.debug('  Location: (%f, %f, %f)', *bone.position)
            logging.debug('  Parent: %s', str(bone.parent))
            logging.debug('  Related Bone: %s', str(bone.tail_bone))
            logging.debug('  Type: %s', bone.type)
            logging.debug('  IK bone: %s', str(bone.ik_bone))
            logging.debug('')
        #logging.info('----- Loaded %d bones', len(self.bones))

        #logging.info('')
        #logging.info('------------------------------')
        #logging.info(' Load IKs')
        #logging.info('------------------------------')
        self.iks = []
        ik_count = fs.readUnsignedShort()
        for i in range(ik_count):
            ik = IK()
            ik.load(fs)
            self.iks.append(ik)

            #logging.info('IK %d', i)
            logging.debug('  Bone: %s(index: %d)', self.bones[ik.bone].name, ik.bone)
            logging.debug('  Target Bone: %s(index: %d)', self.bones[ik.target_bone].name, ik.target_bone)
            logging.debug('  IK Chain: %d', ik.ik_chain)
            logging.debug('  IK Iterations: %d', ik.iterations)
            logging.debug('  Wegiht: %d', ik.control_weight)
            for j, c in enumerate(ik.ik_child_bones):
                logging.debug('    Bone %d: %s(index: %d)', j, self.bones[c].name, c)
            logging.debug('')
        #logging.info('----- Loaded %d IKs', len(self.iks))

        #logging.info('')
        #logging.info('------------------------------')
        #logging.info(' Load Morphs')
        #logging.info('------------------------------')
        self.morphs = []
        morph_count = fs.readUnsignedShort()
        for i in range(morph_count):
            morph = VertexMorph()
            morph.load(fs)
            self.morphs.append(morph)
            #logging.info('Vertex Morph %d: %s', i, morph.name)
        #logging.info('----- Loaded %d materials', len(self.morphs))

        #logging.info('')
        #logging.info('------------------------------')
        #logging.info(' Load Display Items')
        #logging.info('------------------------------')
        self.facial_disp_morphs = []
        t = fs.readByte()
        for i in range(t):
            u = fs.readUnsignedShort()
            self.facial_disp_morphs.append(u)
            #logging.info('Facial %d: %s', i, self.morphs[u].name)

        self.bone_disp_lists = collections.OrderedDict()
        bone_disps = []
        t = fs.readByte()
        for i in range(t):
            name = fs.readStr(50)
            self.bone_disp_lists[name] = []
            bone_disps.append(name)

        t = fs.readUnsignedInt()
        for i in range(t):
            bone_index = fs.readUnsignedShort()
            disp_index = fs.readByte()
            self.bone_disp_lists[bone_disps[disp_index-1]].append(bone_index)

        #for i, (k, items) in enumerate(self.bone_disp_lists.items()):
            #logging.info('  Frame %d: %s', i, k.rstrip())
            #for j, b in enumerate(items):
                #logging.info('    Bone %d: %s(index: %d)', j, self.bones[b].name, b)
        #logging.info('----- Loaded display items')

        #logging.info('')
        #logging.info('===============================')
        #logging.info(' Load Display Items')
        #logging.info('   try to load extended data sections...')
        #logging.info('')

        # try to load extended data sections.
        try:
            eng_flag = fs.readByte()
        except Exception:
            #logging.info('found no extended data sections')
            #logging.info('===============================')
            return
        #logging.info('===============================')

        #logging.info('')
        #logging.info('------------------------------')
        #logging.info(' Load a extended data for english')
        #logging.info('------------------------------')
        if eng_flag:
            #logging.info('found a extended data for english.')
            self.name_e = fs.readStr(20)
            self.comment_e = fs.readStr(256)
            for i in range(len(self.bones)):
                self.bones[i].name_e = fs.readStr(20)

            for i in range(1, len(self.morphs)):
                self.morphs[i].name_e = fs.readStr(20)

            #logging.info(' Name(english): %s', self.name_e)
            #logging.info(' Comment(english): %s', self.comment_e)

            bone_disps_e = []
            for i in range(len(bone_disps)):
                t = fs.readStr(50)
                bone_disps_e.append(t)
                #logging.info(' Bone name(english) %d: %s', i, t)
        #logging.info('----- Loaded english data.')

        #logging.info('')
        #logging.info('------------------------------')
        #logging.info(' Load toon textures')
        #logging.info('------------------------------')
        self.toon_textures = []
        for i in range(10):
            t = fs.readStr(100)
            self.toon_textures.append(t)
            #logging.info('Toon Texture %d: %s', i, t)
        #logging.info('----- Loaded %d textures', len(self.toon_textures))

        #logging.info('')
        #logging.info('------------------------------')
        #logging.info(' Load Rigid Bodies')
        #logging.info('------------------------------')
        rigid_count = fs.readUnsignedInt()
        self.rigid_bodies = []
        for i in range(rigid_count):
            rigid = RigidBody()
            rigid.load(fs)
            self.rigid_bodies.append(rigid)
            #logging.info('Rigid Body %d: %s', i, rigid.name)
            logging.debug('  Bone: %s', rigid.bone)
            logging.debug('  Collision group: %d', rigid.collision_group_number)
            logging.debug('  Collision group mask: 0x%x', rigid.collision_group_mask)
            logging.debug('  Size: (%f, %f, %f)', *rigid.size)
            logging.debug('  Location: (%f, %f, %f)', *rigid.location)
            logging.debug('  Rotation: (%f, %f, %f)', *rigid.rotation)
            logging.debug('  Mass: %f', rigid.mass)
            logging.debug('  Bounce: %f', rigid.bounce)
            logging.debug('  Friction: %f', rigid.friction)
            logging.debug('')
        #logging.info('----- Loaded %d rigid bodies', len(self.rigid_bodies))

        #logging.info('')
        #logging.info('------------------------------')
        #logging.info(' Load Joints')
        #logging.info('------------------------------')
        joint_count = fs.readUnsignedInt()
        self.joints = []
        for i in range(joint_count):
            joint = Joint()
            joint.load(fs)
            self.joints.append(joint)
            #logging.info('Joint %d: %s', i, joint.name)
            logging.debug('  Rigid A: %s (index: %d)', self.rigid_bodies[joint.src_rigid].name, joint.src_rigid)
            logging.debug('  Rigid B: %s (index: %d)', self.rigid_bodies[joint.dest_rigid].name, joint.dest_rigid)
            logging.debug('  Location: (%f, %f, %f)', *joint.location)
            logging.debug('  Rotation: (%f, %f, %f)', *joint.rotation)
            logging.debug('  Location Limit: (%f, %f, %f) - (%f, %f, %f)', *(joint.minimum_location + joint.maximum_location))
            logging.debug('  Rotation Limit: (%f, %f, %f) - (%f, %f, %f)', *(joint.minimum_rotation + joint.maximum_rotation))
            logging.debug('  Spring: (%f, %f, %f)', *joint.spring_constant)
            logging.debug('  Spring(rotation): (%f, %f, %f)', *joint.spring_rotation_constant)
            logging.debug('')
        #logging.info('----- Loaded %d joints', len(self.joints))

        #logging.info('finished importing the model.')

def load(path):
    with FileReadStream(path) as fs:
        #logging.info('****************************************')
        #logging.info(' mmd_tools.pmd module')
        #logging.info('----------------------------------------')
        #logging.info(' Start load model data form a pmd file')
        #logging.info('            by the mmd_tools.pmd modlue.')
        #logging.info('')

        model = Model()
        model.load(fs)

        #logging.info(' Finish loading.')
        #logging.info('----------------------------------------')
        #logging.info(' mmd_tools.pmd module')
        #logging.info('****************************************')
        return model

def load2pmx(target_path):
    pmd_model = load(target_path)

    #logging.info('')
    #logging.info('****************************************')
    #logging.info(' mmd_tools.import_pmd module')
    #logging.info('----------------------------------------')
    #logging.info(' Start to convert pmx data into pmd data')
    #logging.info('              by the mmd_tools.pmd modlue.')
    #logging.info('')

    pmx_model = pmx.Model()

    pmx_model.name = pmd_model.name
    pmx_model.name_e = pmd_model.name_e
    pmx_model.comment = pmd_model.comment
    pmx_model.comment_e = pmd_model.comment_e

    pmx_model.vertices = []

    # convert vertices
    #logging.info('')
    #logging.info('------------------------------')
    #logging.info(' Convert Vertices')
    #logging.info('------------------------------')
    for v in pmd_model.vertices:
        pmx_v = pmx.Vertex()
        pmx_v.co = v.position
        pmx_v.normal = v.normal
        pmx_v.uv = v.uv
        pmx_v.additional_uvs= []
        pmx_v.edge_scale = 1

        weight = pmx.BoneWeight()
        if v.bones[0] != v.bones[1]:
            weight.type = pmx.BoneWeight.BDEF2
            weight.bones = v.bones
            weight.weights = [float(v.weight)/100.0]
        else:
            weight.type = pmx.BoneWeight.BDEF1
            weight.bones = [v.bones[0]]
            weight.weights = [float(v.weight)/100.0]

        pmx_v.weight = weight

        pmx_model.vertices.append(pmx_v)
    #logging.info('----- Converted %d vertices', len(pmx_model.vertices))

    #logging.info('')
    #logging.info('------------------------------')
    #logging.info(' Convert Faces')
    #logging.info('------------------------------')
    for f in pmd_model.faces:
        pmx_model.faces.append(f)
    #logging.info('----- Converted %d faces', len(pmx_model.faces))

    knee_bones = []

    #logging.info('')
    #logging.info('------------------------------')
    #logging.info(' Convert Bones')
    #logging.info('------------------------------')
    for i, bone in enumerate(pmd_model.bones):
        pmx_bone = pmx.Bone()
        pmx_bone.name = bone.name
        pmx_bone.name_e = bone.name_e
        pmx_bone.location = bone.position
        pmx_bone.parent = bone.parent
        if bone.type != 9 and bone.type != 8:
            pmx_bone.displayConnection = bone.tail_bone
        else:
            pmx_bone.displayConnection = -1
        if pmx_bone.displayConnection <= 0:
            pmx_bone.displayConnection = [0.0, 0.0, 0.0]
        pmx_bone.isIK = False
        if bone.type == 0:
            pmx_bone.isMovable = False
        elif bone.type == 1:
            pass
        elif bone.type == 2:
            pmx_bone.transform_order = 1
        elif bone.type == 4:
            pmx_bone.isMovable = False
        elif bone.type == 5:
            pmx_bone.hasAdditionalRotate = True
            pmx_bone.additionalTransform = (bone.ik_bone, 1.0)
        elif bone.type == 7:
            pmx_bone.visible = False
        elif bone.type == 8:
            pmx_bone.isMovable = False
            '''
            tail_loc=mathutils.Vector(pmd_model.bones[bone.tail_bone].position)
            loc = mathutils.Vector(bone.position)
            vec = tail_loc - loc
            vec.normalize()
            pmx_bone.axis=list(vec)
            '''
        elif bone.type == 9:
            pmx_bone.visible = False
            pmx_bone.hasAdditionalRotate = True
            pmx_bone.additionalTransform = (bone.tail_bone, float(bone.ik_bone)/100.0)

        if bone.type >= 4:
            pmx_bone.transform_order = 2

        pmx_model.bones.append(pmx_bone)

        if re.search(u'ひざ$', pmx_bone.name):
            knee_bones.append(i)

    for i in pmx_model.bones:
        if i.parent != -1 and pmd_model.bones[i.parent].type == 2:
            i.transform_order = 1
    #logging.info('----- Converted %d boness', len(pmx_model.bones))

    #logging.info('')
    #logging.info('------------------------------')
    #logging.info(' Convert IKs')
    #logging.info('------------------------------')
    applied_ik_bones = []
    for ik in pmd_model.iks:
        if ik.bone in applied_ik_bones:
            #logging.info('The bone %s is targeted by two or more IK bones.', pmx_model.bones[ik.bone].name)
            b = pmx_model.bones[ik.bone]
            t = copy.deepcopy(b)
            t.name += '+'
            t.parent = ik.bone
            t.ik_links = []
            pmx_model.bones.append(t)
            ik.bone = len(pmx_model.bones) - 1
            #logging.info('Duplicate the bone: %s -> %s', b.name, t.name)
        pmx_bone = pmx_model.bones[ik.bone]
        logging.debug('Add IK settings to the bone %s', pmx_bone.name)
        pmx_bone.isIK = True
        pmx_bone.target = ik.target_bone
        pmx_bone.loopCount = ik.iterations
        for i in ik.ik_child_bones:
            ik_link = pmx.IKLink()
            ik_link.target = i
            if i in knee_bones:
                ik_link.maximumAngle = [-0.5, 0.0, 0.0]
                ik_link.minimumAngle = [-180.0, 0.0, 0.0]
                #logging.info('  Add knee constraints to %s', i)
            logging.debug('  IKLink: %s(index: %d)', pmx_model.bones[i].name, i)
            pmx_bone.ik_links.append(ik_link)
        applied_ik_bones.append(ik.bone)
    #logging.info('----- Converted %d bones', len(pmd_model.iks))

    texture_map = {}
    #logging.info('')
    #logging.info('------------------------------')
    #logging.info(' Convert Materials')
    #logging.info('------------------------------')
    for i, mat in enumerate(pmd_model.materials):
        pmx_mat = pmx.Material()
        pmx_mat.name = '材質%d'%(i+1)
        pmx_mat.name_e = 'Material%d'%(i+1)
        pmx_mat.diffuse = mat.diffuse
        pmx_mat.specular = mat.specular + [mat.specular_intensity]
        pmx_mat.ambient = mat.ambient
        pmx_mat.enabled_self_shadow = True # pmd doesn't support this
        pmx_mat.enabled_self_shadow_map = abs(mat.diffuse[3] - 0.98) > 1e-7 # consider precision error
        pmx_mat.enabled_toon_edge = (mat.edge_flag != 0)
        pmx_mat.vertex_count = mat.vertex_count
        if len(mat.texture_path) > 0:
            tex_path = mat.texture_path
            if tex_path not in texture_map:
                #logging.info('  Create pmx.Texture %s', tex_path)
                tex = pmx.Texture()
                tex.path = os.path.normpath(os.path.join(os.path.dirname(target_path), tex_path))
                pmx_model.textures.append(tex)
                texture_map[tex_path] = len(pmx_model.textures) - 1
            pmx_mat.texture = texture_map[tex_path]
        if len(mat.sphere_path) > 0:
            tex_path = mat.sphere_path
            if tex_path not in texture_map:
                #logging.info('  Create pmx.Texture %s', tex_path)
                tex = pmx.Texture()
                tex.path = os.path.normpath(os.path.join(os.path.dirname(target_path), tex_path))
                pmx_model.textures.append(tex)
                texture_map[tex_path] = len(pmx_model.textures) - 1
            pmx_mat.sphere_texture = texture_map[tex_path]
            pmx_mat.sphere_texture_mode = mat.sphere_mode
        pmx_model.materials.append(pmx_mat)
    #logging.info('----- Converted %d materials', len(pmx_model.materials))

    #logging.info('')
    #logging.info('------------------------------')
    #logging.info(' Convert Morphs')
    #logging.info('------------------------------')
    t = list(filter(lambda x: x.type == 0, pmd_model.morphs))
    if len(t) == 0:
        logging.error('Not found the base morph')
        logging.error('Skip converting vertex morphs.')
    else:
        if len(t) > 1:
            logging.warning('Found two or more base morphs.')
        vertex_map = []
        for i in t[0].data:
            vertex_map.append(i.index)

        for morph in pmd_model.morphs:
            logging.debug('Vertex Morph: %s', morph.name)
            if morph.type == 0:
                continue
            pmx_morph = pmx.VertexMorph(morph.name, morph.name_e, morph.type)
            for i in morph.data:
                mo = pmx.VertexMorphOffset()
                mo.index = vertex_map[i.index]
                mo.offset = i.offset
                pmx_morph.offsets.append(mo)
            pmx_model.morphs.append(pmx_morph)
    #logging.info('----- Converted %d morphs', len(pmx_model.morphs))

    #logging.info('')
    #logging.info('------------------------------')
    #logging.info(' Convert Rigid bodies')
    #logging.info('------------------------------')
    for rigid in pmd_model.rigid_bodies:
        pmx_rigid = pmx.Rigid()

        pmx_rigid.name = rigid.name

        pmx_rigid.bone = rigid.bone
        pmx_rigid.collision_group_number = rigid.collision_group_number
        pmx_rigid.collision_group_mask = rigid.collision_group_mask
        pmx_rigid.type = rigid.type

        pmx_rigid.size = rigid.size

        # a location parameter of pmd.RigidBody is the offset from the relational bone or the center bone.
        if rigid.bone == -1:
            t = 0
        else:
            t = rigid.bone
        #pmx_rigid.location = mathutils.Vector(pmx_model.bones[t].location) + mathutils.Vector(rigid.location)
        pmx_rigid.rotation = rigid.rotation

        pmx_rigid.mass = rigid.mass
        pmx_rigid.velocity_attenuation = rigid.velocity_attenuation
        pmx_rigid.rotation_attenuation = rigid.rotation_attenuation
        pmx_rigid.bounce = rigid.bounce
        pmx_rigid.friction = rigid.friction
        pmx_rigid.mode = rigid.mode

        pmx_model.rigids.append(pmx_rigid)
    #logging.info('----- Converted %d rigid bodies', len(pmx_model.rigids))

    #logging.info('')
    #logging.info('------------------------------')
    #logging.info(' Convert Joints')
    #logging.info('------------------------------')
    for joint in pmd_model.joints:
        pmx_joint = pmx.Joint()

        pmx_joint.name = joint.name
        pmx_joint.src_rigid = joint.src_rigid
        pmx_joint.dest_rigid = joint.dest_rigid

        pmx_joint.location = joint.location
        pmx_joint.rotation = joint.rotation

        pmx_joint.maximum_location = joint.minimum_location
        pmx_joint.minimum_location = joint.maximum_location
        pmx_joint.maximum_rotation = joint.minimum_rotation
        pmx_joint.minimum_rotation = joint.maximum_rotation

        pmx_joint.spring_constant = joint.spring_constant
        pmx_joint.spring_rotation_constant = joint.spring_rotation_constant

        pmx_model.joints.append(pmx_joint)
    #logging.info('----- Converted %d joints', len(pmx_model.joints))

    #logging.info(' Finish converting pmd into pmx.')
    #logging.info('----------------------------------------')
    #logging.info(' mmd_tools.import_pmd module')
    #logging.info('****************************************')

    return pmx_model
