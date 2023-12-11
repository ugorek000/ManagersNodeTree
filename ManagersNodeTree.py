bl_info = {'name':"ManagersNodeTree", 'author':"ugorek",
           'version':(2,3,4), 'blender':(4,0,2), #2023.12.11
           'description':"For .blend and other high level management.",
           'location':"NodeTreeEditor",
           'warning':"Имеет неизведанным образом ненулевой риск (ненулевого) повреждения данных. Будьте аккуратны и делайте бэкапы.",
           'category':"System",
           'wiki_url':"https://github.com/ugorek000/ManagersNodeTree/wiki", 'tracker_url':"https://github.com/ugorek000/ManagersNodeTree/issues"}
thisAddonName = bl_info['name']

from builtins import len as length
import bpy, re, ctypes
import nodeitems_utils
import math, mathutils

bl_ver = bpy.app.version

list_classes = []
list_clsToAddon = []
list_clsToChangeTag = []

class AddonPrefs(bpy.types.AddonPreferences):
    bl_idname = thisAddonName

def GetDicsIco(tgl):
    return 'DISCLOSURE_TRI_DOWN' if tgl else 'DISCLOSURE_TRI_RIGHT'

#todo0 добавить новые ноды со специфичным предназначением:
#менеджер кеймапов с обоими фильтрами одновременно
#icon viewer
#custom props manager full
#высокоуровневый assertor

class ManagersTree(bpy.types.NodeTree):
    """For .blend and other high level management"""
    bl_idname = 'ManagersNodeTree'
    bl_label = "Managers Node Tree"
    bl_icon = 'FILE_BLEND'

list_classes += [ManagersTree]

def MnUpdateNclass(nd):
    if hasattr(nd,'nclass'):
        BNode.get_fields(nd).typeinfo.contents.nclass = nd.nclass
        #for wn in bpy.context.window_manager.windows:
        #    for ar in wn.screen.areas: ar.tag_redraw(); break

def MnUpdateAllNclassFromTree(tgl=True):
    global isDataOnRegisterDoneTgl
    isDataOnRegisterDoneTgl = False
    ##
    name = "tehn"+chr(8203)
    tree = bpy.data.node_groups.get(name) or bpy.data.node_groups.new(name, ManagersTree.bl_idname)
    for li in list_clsToChangeTag:
        name = li.bl_idname
        nd = tree.nodes.get(name) or tree.nodes.new(name)
        nd.name = name
        MnUpdateNclass(nd)
        if tgl:
            tree.nodes.remove(nd)
    if tgl:
        bpy.data.node_groups.remove(tree)

dict_ndLastAlert = {}

pw22 = 1/2.2
def MnTimerUpdateSetAlertColor(nd, context):
    dict_ndLastAlert.setdefault(nd, False)
    nd.use_custom_color = (dict_ndLastAlert[nd])and(any(nd.alertColor))
    col = nd.alertColor
    nd.color = (col[0]**pw22, col[1]**pw22, col[2]**pw22)

class MntPads():
    nclass = 0
    def InitNodePreChain(self,context):pass
    def InitNode(self,context):pass
    def DrawExtPreChain(self,context,colLy):pass
    def DrawExtNode(self,context,colLy,prefs):pass
    def DrawPreChain(self,context,colLy):pass
    def DrawNode(self,context,colLy,prefs):pass
class MntPreChainBase(bpy.types.Node, MntPads):
    def init(self, context):
        if isDataOnRegisterDoneTgl: #Для первого ключения аддона, когда handlers.load_post очевидным образом не был доступен.
            bpy.app.timers.register(functools.partial(MnUpdateAllNclassFromTree, True))
        #Записать в self.prefs = Prefs() почему не работает, пришлось в draw()'ах передавать.
        self.InitNodePreChain(context) #Редкий.
        self.InitNode(context)
    def draw_buttons_ext(self, context, layout):
        colLy = layout.column()
        self.DrawExtPreChain(context, colLy)
        self.DrawExtNode(context, colLy, Prefs())
    def draw_buttons(self, context, layout):
        colLy = layout.column()
        prefs = Prefs()
        if prefs.debugLy:
            colLy.label(text=str(random.random()), icon='SEQUENCE_COLOR_0'+str(random.randint(1, 9)))
        self.DrawPreChain(context, colLy)
        self.DrawNode(context, colLy, prefs)
class MntNodeRoot(MntPreChainBase):
    def DrawExtPreChain(self, context, colLy):
        colLy.prop(self,'width', text="Node width", slider=True)
    def DrawPreChain(self, context, colLy):
        AddThinSep(colLy, .1) #!.
class MntNodeAlertness(MntNodeRoot, MntPreChainBase):
    alertColor: bpy.props.FloatVectorProperty(name="Alert color", default=(0.0, 0.0, 0.0), min=0, max=1, size=3, subtype='COLOR', update=MnTimerUpdateSetAlertColor)
    def DrawExtPreChain(self, context, colLy):
        MntNodeRoot.DrawExtPreChain(self, context, colLy)
        AddNiceColorProp(colLy, self,'alertColor')
    def DrawPreChain(self, context, colLy):
        dict_ndLastAlert.setdefault(self, False)
        MntNodeRoot.DrawPreChain(self, context, colLy)
    def ProcAlertState(self, dataState):
        alertState = not not dataState
        if alertState!=dict_ndLastAlert[self]:
            dict_ndLastAlert[self] = alertState
            bpy.app.timers.register(functools.partial(MnTimerUpdateSetAlertColor, self, None))
#        if (any(self.alertColor))and(any(self.color)!=dict_ndLastAlert[self]): #Иногда может заесть (пока зачемено только в процессе разработки), так что пусть будет для подстраховки.
            #Осторожно с бесконечным обновлением.
#            dict_ndLastAlert[self] = alertState
#            bpy.app.timers.register(functools.partial(MnTimerUpdateSetAlertColor, self, None))
class MntNodeWithOnlyMatter(MntNodeAlertness):
    isOnlyMatter: bpy.props.BoolProperty(name="Matter display only", default=False)
    def DrawExtPreChain(self, context, colLy):
        MntNodeAlertness.DrawExtPreChain(self, context, colLy)
        colLy.prop(self,'isOnlyMatter')

class AtHomePoll(nodeitems_utils.NodeCategory):
    @classmethod
    def poll(cls, context):
        return context.space_data.tree_type==ManagersTree.bl_idname
class PublicPoll(nodeitems_utils.NodeCategory):
    @classmethod
    def poll(cls, context):
        return context.space_data.tree_type!=ManagersTree.bl_idname

dict_tupleShiftAList = {}

class Sacat(): #"Sacat" = "ShiftA Category".
    def __init__(self, ClsPoll):
        self.ClsPoll = ClsPoll
        self.list_orderBlid = []

list_sacatOrder = ["Managers", "Special", "RNA", "Color", "Text", "Solemn", "Script", "Self", "Exotic"]
dist_sacatOrderMap = {li:cyc for cyc, li in enumerate(list_sacatOrder)}

def AddToSacat(list_orderClass, name, ClsPoll):
    dict_tupleShiftAList.setdefault(name, Sacat(ClsPoll))
    for li in list_orderClass:
        len = length(li)
        sett = li[2] if len>2 else {}
        labl = li[3] if len>3 else None
        dict_tupleShiftAList[name].list_orderBlid.append( (li[0], li[1].bl_idname, labl, sett) )

list_tupleСlsToPublic = []

class SubMenuPublicManagers(bpy.types.Menu):
    bl_idname = "NODE_MT_public_managers"
    bl_label = "Manager"
    def draw(self, context):
        colLy = self.layout.column()
        for li in list_tupleСlsToPublic:
            op = colLy.operator('node.add_node', text=li[1].bl_label)
            op.use_transform = True
            op.type = li[1].bl_idname
def DrawPublicMnt(self, context):
    self.layout.menu(SubMenuPublicManagers.bl_idname)
def DoPublish(tgl):
    if bl_ver>(3,9,9):
        for txt in {"shader", "geometry", "compositor", "texture"}:
            eval(f"bpy.types.NODE_MT_{txt}_node_add_all.{'append' if tgl else 'remove'}")(DrawPublicMnt)
    else:
        txt = SubMenuPublicManagers.bl_label
        list_nodeCategories = [PublicPoll(txt, txt, items=[nodeitems_utils.NodeItem(li[1].bl_idname) for li in sorted(list_tupleСlsToPublic, key=lambda a:a[0])])]
        try:
            nodeitems_utils.register_node_categories('MANAGER_NODES_pub', list_nodeCategories)
        except:
            nodeitems_utils.unregister_node_categories('MANAGER_NODES_pub')
            nodeitems_utils.register_node_categories('MANAGER_NODES_pub', list_nodeCategories)
list_classes += [SubMenuPublicManagers]

mntSaCatName = 'MANAGER_NODES'
def RegisterNodeCategories():
    list_nodeCategories = []
    for li in sorted(dict_tupleShiftAList.items(), key=lambda a: dist_sacatOrderMap.get(a[0], -1)):
        name = li[0]
        items = [nodeitems_utils.NodeItem(li[1], label=li[2], settings=li[3]) for li in sorted(li[1].list_orderBlid, key=lambda a:a[0])]
        list_nodeCategories.append(li[1].ClsPoll(name.replace(" ", ""), #Заметка: идентификатор так же не должен оканчиваться на "_".
                                                 name.replace("_", ""), #См. в AddToSacat(); имя и идентификатор используются с одного и того же (пробел выше не поможет для одного слова).
                                                 items=items))
    try:
        nodeitems_utils.register_node_categories(mntSaCatName, list_nodeCategories)
    except:
        nodeitems_utils.unregister_node_categories(mntSaCatName)
        nodeitems_utils.register_node_categories(mntSaCatName, list_nodeCategories)
    DoPublish(True)
def UnregisterNodeCategories():
    nodeitems_utils.unregister_node_categories(mntSaCatName)
    DoPublish(False)

#node_categories = [
#    # identifier, label, items list
#    MyNodeCategory('SOMENODES', "Some Nodes", items=[
#        # our basic node
#        NodeItem("CustomNodeType"),
#    ]),
#    MyNodeCategory('OTHERNODES', "Other Nodes", items=[
#        # the node item can have additional settings,
#        # which are applied to new nodes
#        # NOTE: settings values are stored as string expressions,
#        # for this reason they should be converted to strings using repr()
#        NodeItem("CustomNodeType", label="Node A", settings={
#            "my_string_prop": repr("Lorem ipsum dolor sit amet"),
#            "my_float_prop": repr(1.0),
#        }),
#        NodeItem("CustomNodeType", label="Node B", settings={
#            "my_string_prop": repr("consectetur adipisicing elit"),
#            "my_float_prop": repr(2.0),
#        }),
#    ]),
#]

class StructBase(ctypes.Structure):
    _subclasses = []
    __annotations__ = {}
    def __init_subclass__(cls):
        cls._subclasses.append(cls)
    def InitStructs():
        for cls in StructBase._subclasses:
            fields = []
            for field, value in cls.__annotations__.items():
                fields.append((field, value))
            if fields:
                cls._fields_ = fields
            cls.__annotations__.clear()
        StructBase._subclasses.clear()

class BNodeType(StructBase): #source\blender\blenkernel\BKE_node.h
    idname:         ctypes.c_char*64
    type:           ctypes.c_int
    ui_name:        ctypes.c_char*64
    ui_description: ctypes.c_char*256
    ui_icon:        ctypes.c_int
    if bl_ver>(3,9,9):
        char:           ctypes.c_void_p
    width:          ctypes.c_float
    minwidth:       ctypes.c_float
    maxwidth:       ctypes.c_float
    height:         ctypes.c_float
    minheight:      ctypes.c_float
    maxheight:      ctypes.c_float
    nclass:         ctypes.c_int16 #Эй, вы припёрлись сюда, чтобы взять цветные заголовки себе? Неет))00)0
                                             #Лучше попробуйте отреверсинженерить самостоятельно. Или задонатьте одной звездой на гитхабе.
                                             #И вообще, поищите какого-нибудь другого энтузиастского кодера, который реализовал это лучше меня.
class BNode(StructBase): #source\blender\makesdna\DNA_node_types.h:
    next:       ctypes.c_void_p
    prev:       ctypes.c_void_p
    inputs:     ctypes.c_void_p*2
    outputs:    ctypes.c_void_p*2
    name:       ctypes.c_char*64
    identifier: ctypes.c_int
    flag:       ctypes.c_int
    idname:     ctypes.c_char*64
    typeinfo:   ctypes.POINTER(BNodeType)
    @classmethod
    def get_fields(cls, so):
        return cls.from_address(so.as_pointer())

class BNodeSocket(StructBase): #Для MntNodeJoinFLoat.
    next:                   ctypes.c_void_p
    prev:                   ctypes.c_void_p
    prop:                   ctypes.c_void_p
    identifier:             ctypes.c_char*64
    name:                   ctypes.c_char*64
    storage:                ctypes.c_void_p
    type:                   ctypes.c_short
    flag:                   ctypes.c_short
    @classmethod
    def get_fields(cls, so):
        return cls.from_address(so.as_pointer())

StructBase.InitStructs()


tuple_tupleNctags = ((0,   'INPUT'),
                     (1,   'OUTPUT'),
                     (2,   'none'),
                     (3,   'OP_COLOR'),
                     (4,   'OP_VECTOR'),
                     (5,   'OP_FILTER'),
                     (6,   'GROUP'),
                     (8,   'CONVERTER'),
                     (9,   'MATTE'),
                     (10,  'DISTORT'),
                     (12,  'PATTERN'),
                     (13,  'TEXTURE'),
                     (32,  'SCRIPT'),
                     (33,  'INTERFACE'),
                     (40,  'SHADER'),
                     (41,  'GEOMETRY'),
                     (42,  'ATTRIBUTE'),
                     (100, 'LAYOUT'))

nntvSafeSetTgl = True
def NntvUpdateTagId(self, context):
    if nntvSafeSetTgl:
        tree = context.space_data.edit_tree
        aNd = tree.nodes.active
        BNode.get_fields(aNd).typeinfo.contents.nclass = tuple_tupleNctags[self.tagId][0]
def NntvTimerSetTagId(self, nclass):
    global nntvSafeSetTgl
    nntvSafeSetTgl = False
    self.tagId = [cyc for cyc, ti in enumerate(tuple_tupleNctags) if ti[0]==nclass][0]
    nntvSafeSetTgl = True
class NodeNclassTagViewer(MntNodeRoot):
    bl_idname = 'MntNodeNclassTagViewer'
    bl_label = "Nclass toggler"
    bl_icon = 'EXPERIMENTAL'
    bl_width_min = 140
    bl_width_default = 200
    #nclass = 100 #33 #InitNode()
    tagId: bpy.props.IntProperty(name="Tag", default=0, min=0, max=17, update=NntvUpdateTagId)
    def DrawNode(self, context, colLy, prefs):
        tree = context.space_data.edit_tree
        aNd = tree.nodes.active
        AddBoxLabelDir(colLy, aNd.bl_label if aNd else "", icon='NODE', active=not not aNd)
        if aNd:
            tuple = tuple_tupleNctags[self.tagId]
            nclass = BNode.get_fields(aNd).typeinfo.contents.nclass
            if tuple[0]!=nclass:
                bpy.app.timers.register(functools.partial(NntvTimerSetTagId, self, nclass))
            colLy.prop(self,'tagId', text=f"{tuple[0]}  –  {tuple[1]}", slider=True)

list_classes += [NodeNclassTagViewer]
AddToSacat([ (99,NodeNclassTagViewer) ], "Self", AtHomePoll)
list_tupleСlsToPublic += [(6, NodeNclassTagViewer)]
list_clsToChangeTag += [NodeNclassTagViewer]

#list_clsDev = []
#for num in [0, 1, 2, 3, 4, 5, 6, 8, 9, 10, 12, 13, 32, 33, 40, 41, 42, 100]:
#    exec(f"class NodeTestDev{num}(MntNodeRoot):"+"\n"+f" bl_idname = 'NodeTestDev{num}'"+"\n"+f" bl_label = 'NodeTestTag{num}'"+"\n"+f" nclass = {num}")
#    exec(f"list_clsDev.append(NodeTestDev{num})")
#list_classes += list_clsDev
#for li in list_clsDev:
#    AddToSacat([ (0,li) ], "Dev", AtHomePoll)

def AddThinSep(where, scaleY=0.25, scaleX=1.0):
    row = where.row(align=True)
    row.separator()
    row.scale_x = scaleX
    row.scale_y = scaleY

def GetLbBoxRaw(where, scale_y=0.5, scale_x=1.0):
    box = where.box()
    box.scale_y = scale_y
    box.scale_x = scale_x
    return box
def AddBoxLabelDir(where, text, icon='NONE', active=True, alignment='EXPAND'):
    box = GetLbBoxRaw(where)
    row = box.row(align=True)
    row.alignment = alignment
    if icon!='NONE':
        row.label(icon=icon)
    row.label(text=text)
    row.active = active
def GetLabeledDoubleBox(where, text, icon='NONE', active=True, alignment='EXPAND'):
    col = where.column(align=True)
    AddBoxLabelDir(col, text, icon, active, alignment)
    return col.box()

def AddDiscBoxLabel(where, who, prop, text, brightness=3, toCenter=True):
    tgl = getattr(who, prop)
    box = GetLbBoxRaw(where, 0.575)
    rowLabel = box.row(align=True)
    if toCenter:
        rowIco = rowLabel.row(align=True)
        rowIco.active = brightness//2%2
        rowIco.prop(who, prop, text="", icon=GetDicsIco(tgl), emboss=False)
        rowTxt = rowLabel.row(align=True)
        rowTxt.active = brightness%2
        rowTxt.prop(who, prop, text=text, emboss=False)
        row = rowLabel.row(align=True)
        row.alignment = 'CENTER'
        row.label() #Для ровного текста с toCenter==False.
    else:
        rowLabel.alignment = 'LEFT'
        rowLabel.prop(who, prop, text=text, icon=GetDicsIco(tgl), emboss=False)
        rowLabel.active = not not brightness
    return tgl
def GenDisclLabeledDoubleBox(where, who, prop, text, brightness=3, toCenter=True):
    col = where.column(align=True)
    tgl = AddDiscBoxLabel(col, who, prop, text, brightness, toCenter)
    return col.box().column() if tgl else None

def AddNiceColorProp(where, who, prop, align=False, txt="", decor=3):
    rowCol = where.row(align=align)
    rowLabel = rowCol.row()
    rowLabel.alignment = 'LEFT'
    rowLabel.label(text=txt if txt else who.bl_rna.properties[prop].name+":")
    rowLabel.active = decor%2
    rowProp = rowCol.row()
    rowProp.alignment = 'EXPAND'
    rowProp.prop(who, prop, text="")
    rowProp.active = decor//2%2

def GetNodeBoxDiscl(where, who, prop, self):
    return GenDisclLabeledDoubleBox(where, who, prop, self.bl_label)#+" Node")

def PlaceDebugProp(where, who, prop):
    rowDeb = where.row(align=True)
    rowLabel = rowDeb.row(align=True)
    rowLabel.alignment = 'CENTER'
    rowLabel.label(text="debug:")
    rowDeb.prop(who, prop)

def AddWarningLabel(where, text, alert=False):
    rowLabel = where.row(align=True)
    rowIco = rowLabel.row(align=True)
    rowIco.active = False
    rowIco.alert = alert
    rowIco.label(icon='ERROR')
    rowLabel.alignment = 'LEFT'
    rowLabel.label(text=" "+text)
def EvalAndAddPropExtended(where, who, prop, txt_eval, locals=None, txt="", fixWidth=48, txt_warning="", alertWarn=False, icon='NONE', canDraw=True, canExec=True):
    if canDraw:
        col = where.column(align=True)
        row = col.row(align=True)
        rowOther = row.row(align=True)
        rowOther.alignment = 'LEFT'
        rowProp = rowOther.row(align=True)
        rowProp.prop(who, prop, text=txt, icon=icon)
        rowProp.ui_units_x = fixWidth
        if txt_warning:
            AddWarningLabel(rowOther, txt_warning, alert=alertWarn)
    if canExec:
        try:
            result = eval(txt_eval if txt_eval else 'None', globals(), locals)
            return True, result
        except Exception as ex:
            col.label(text=str(ex), icon='ERROR')
            return False, None
def StencilAddFilterProp(self, prefs, where, prop='filter', ico=None, canDraw=True):
    if canDraw:
        row = where.row(align=True)
        row.active = prefs.allIsBrightFilters
        if ico:
            rowIco = row.row(align=True)
            rowIco.label(icon=ico)
            rowIco.active = False
    evaled = EvalAndAddPropExtended(row if canDraw else None, self, prop, f"re.compile(var)", locals={'var':getattr(self, prop)}, icon='SORTBYEXT', canDraw=canDraw)
    return evaled[1] if evaled[0] else None

def StencilTotalRow(prefs, where, *tupleDataIcos, decor=0):
    box = GetLbBoxRaw(where.row() if decor else where)
    rowMain = box.row(align=True)
    decorTotalRow = prefs.decorTotalRow
    rowTheme = rowMain.row(align=True)
    rowTheme.alignment = 'LEFT'
    rowLabel = rowTheme.row(align=True)
    rowLabel.alignment = 'LEFT'
    dec0 = decorTotalRow//16%2
    dec1 = 1-decorTotalRow//32%2
    if (dec1)or(dec0):
        rowLabel.label(text="Total"*dec1+":"*dec0, icon='ASSET_MANAGER' if dec0 else 'NONE')
    rowLabel.active = decorTotalRow//8%2
    ##
    isAutoCanonTotal = (length(tupleDataIcos)==2)and(length(tupleDataIcos[0])==2)and(length(tupleDataIcos[0])==2)
    type_tuple = type(())
    for cyc, hh in enumerate(tupleDataIcos):
        isTuple = type(hh)==type_tuple
        isMultiTot = (isTuple)and(length(hh)>2)
        if type(hh)!=str:
            rowIco = rowTheme.row(align=True)
            rowIco.label(icon=hh[0] if isTuple else 'RADIOBUT_ON') #RADIOBUT_ON  SNAP_FACE
            rowIco.active = decorTotalRow//2%2
            AddThinSep(rowIco, 1, 0.5)
        rowData = rowTheme.row(align=True)
        rowData.alignment = 'LEFT'
        if isMultiTot:
            rowTxt = rowData.row(align=True)
            rowTxt.alignment = 'LEFT'
            rowTxt.label(text=str(hh[1]))
            rowDiv = rowTxt.row(align=True)
            rowDiv.alignment = 'LEFT'
            rowDiv.label(text="/")
            rowDiv.active = False
            rowTxt.label(text=str(hh[2]))
        else:
            rowData.label(text=str(hh[1] if isTuple else hh))
        rowData.active = decorTotalRow%2
        if (isAutoCanonTotal)and(cyc==0)and(decorTotalRow//4%2):
            rowDiv = rowTheme.row(align=True)
            rowDiv.alignment = 'LEFT'
            rowDiv.label(text="/")
            rowDiv.active = False
    if decor==1:
        rowMain.label()

class PanelManagerNodesNode(bpy.types.Panel):
    bl_idname = 'MNT_PT_ManagerNodesNode'
    bl_label = "ManagerNodes Node"
    bl_space_type = 'NODE_EDITOR'
    bl_region_type = 'UI'
    bl_category = 'Mnt'
    bl_order = 256
    @classmethod
    def poll(cls, context):
        tree = context.space_data.edit_tree
        return (tree)and(tree.bl_idname==ManagersTree.bl_idname)
    def draw(self, context):
        colLy = self.layout.column()
        tree = context.space_data.edit_tree
        aNd = tree.nodes.active
        if aNd:
            AddBoxLabelDir(colLy, aNd.bl_label, icon='NODE')
            if hasattr(aNd, 'draw_buttons_ext'): #Для потерянных нодов.
                aNd.draw_buttons_ext(context, colLy)
            else:
                colLy.label(text="Node has no `draw_buttons_ext()`")
        else:
            AddBoxLabelDir(colLy, "", 'NODE', active=False)

class MtlOp(bpy.types.Operator):
    bl_idname = 'mnt.node_op_mtl'
    bl_label = "Op ManagerTrees List"
    bl_options = {'UNDO'}
    opt: bpy.props.StringProperty()
    who: bpy.props.StringProperty()
    def invoke(self, context, event):
        match self.opt:
            case 'Place':
                context.space_data.node_tree = bpy.data.node_groups[self.who]
                if event.shift:
                    bpy.ops.node.view_all('INVOKE_DEFAULT')
            case 'AllCenterFromActive':
                tree = context.space_data.edit_tree
                if tree.nodes:
                    ndTar = tree.nodes.active
                    if (not ndTar)or(not ndTar.select):
                        min = 32768
                        for nd in tree.nodes:
                            len = nd.location.length
                            if min>len:
                                min = len
                                ndTar = nd
                        ndTar.select = True
                    if ndTar.select:
                        loc = ndTar.location.copy()
                        for nd in tree.nodes:
                            nd.location -= loc
                            nd.location = (math.floor(nd.location.x/20-0.5)*20, math.floor(nd.location.y/20-0.5)*20)
                            nd.width = int(nd.width/20)*20
                            nd.select = False
                        tree.nodes.active = None
        return {'FINISHED'}
class PanelManagerTreeList(bpy.types.Panel):
    bl_idname = 'MNT_PT_ManagerTreeList'
    bl_label = "ManagerTrees List"
    bl_space_type = 'NODE_EDITOR'
    bl_region_type = 'UI'
    bl_category = 'Mnt'
    bl_order = 255
    @classmethod
    def poll(cls, context):
        return context.space_data.tree_type==ManagersTree.bl_idname
    def draw(self, context):
        colLy = self.layout.column()
        colList = colLy.column(align=True)
        tree = context.space_data.node_tree
        name = tree.name if tree else ""
        for ng in bpy.data.node_groups:
            if ng.bl_idname==ManagersTree.bl_idname:
                row = colList.row(align=True)
                rowIco = row.row(align=True)
                op = rowIco.operator(MtlOp.bl_idname, text="", icon='TRIA_LEFT', depress=name==ng.name)
                op.opt = 'Place'
                op.who = ng.name
                rowIco.scale_x = 2.0
                row.prop(ng,'name', text="")
                rowProp = row.row(align=True)
                rowProp.prop(ng,'use_fake_user', text="")
                rowProp.active = False
        colLy.operator(MtlOp.bl_idname, text="Offset nodes to world origin").opt = 'AllCenterFromActive'

list_classes += [PanelManagerNodesNode, MtlOp, PanelManagerTreeList]

class NodeManagersNodeTree(MntNodeRoot):
    bl_idname = 'MntNodeManagersNodeTree'
    bl_label = "Managers Node Tree"
    bl_width_max = 768
    bl_width_min = 128
    bl_width_default = 272
    @classmethod
    def poll(cls, tree):
        return tree.bl_idname==ManagersTree.bl_idname
    def DrawExtNode(self, context, colLy, prefs):
        if not context.preferences.use_preferences_save:
            colLy.operator('wm.save_userpref', text="Save Preferences"+" *"*context.preferences.is_dirty)
        colLy.operator(MntOpOldBlids.bl_idname, text="Register old nodes")
    def DrawNode(self, context, colLy, prefs):
        if True:
            rowLabel = colLy.row(align=True)
            rowLabel.alignment = 'CENTER'
            rowLabel.label(text="Manager Nodes by ugorek")
            rowLabel.operator('wm.url_open', text="My YouTube", icon='URL').url="www.youtube.com/c/ugorek000"
            rowLabel.active = False
        addonPrefs = context.preferences.addons[thisAddonName].preferences
        apClass = type(addonPrefs)
        apClass.layout = colLy
        try:
            getattr(addonPrefs,'draw', None)(colLy)
        except Exception as ex:
            colLy.label(text=str(ex), icon='ERROR')
        del apClass.layout

class NodeDummy(bpy.types.Node):
    bl_idname = 'MntNodeDummy'
    bl_label = "Dummy Node"
    bl_width_max = 1024
    bl_width_min = 0
    def draw_buttons_ext(self, context, layout):
        layout.prop(self,'width', text="Node width", slider=True)

list_classes += [NodeManagersNodeTree, NodeDummy]
AddToSacat([ (0,NodeManagersNodeTree), (1,NodeDummy) ], "Self", AtHomePoll)

def NipmAddTableOfProps(self, prefs, where, data, list_props, colSpec=None, canSep=True): #Некоторый бардак; было бы круто перелизать всё.
    def Eix(ix):
        if niptIsPlaceDebug:
            return " {"+str(ix)+"}"
        return ""
    #Пайка:
    isShowFilterErrors = self.isShowFilterErrors
    isPlaceExecAlerts = prefs.allIsPlaceExecAlerts
    isBrightFilters = prefs.allIsBrightFilters
    isBrightTableLabels = prefs.niptIsBrightTableLabels
    isBrightFilterErrors = prefs.niptIsBrightFilterErrors
    decorTable = prefs.niptDecorTable
    decorTotal = prefs.niptDecorTotal
    niptIsPlaceDebug = prefs.niptIsPlaceDebug
    #Начало:
    colMain = where.column()
    if decorTable%2:
        colMain.box()
    elif canSep:
        colMain.separator()
    colTotalTop = colMain.column(align=True)
    colTable = colMain.column(align=True)
    colTotalBottom = colMain.column(align=True)
    rowTable = colTable.row(align=True)
    if niptIsPlaceDebug:
        colTable.label(text="debug0:  "+str(list_props))
    #Препарировать список:
    for cyc, li in enumerate(list_props):
        txt_error = ""
        list_splt = li.split(".") #Для отсоединения конца после последней точки.
        txt_path = ".".join(list_splt[:-1]) #Всё что не ^ собрать обратно
        list_splt = list_splt[-1].split("[") #Для отсоединения индекса.
        txt_prop = list_splt[0] #Готовое имя последнего.
        ix = -1
        if length(list_splt)>1: #Вычленить индекс если есть.
            try:
                ix = int(list_splt[1].split("]")[0])
            except Exception as ex:
                txt_error = str(ex)+Eix(6)
        list_props[cyc] = ("."*(not not txt_path)+txt_path, txt_prop, ix, txt_error, li)
    if niptIsPlaceDebug:
        colTable.label(text="debug1:  "+str(list_props))
    #Узнать наличие дубликатов:
    isHaveDuplicates = length(list_props)!=length(set(list_props))
    #Преобразовать
    list_table = [ [None, li[0], li[1], li[2], li[3], li[4]] for li in list_props if li]
    if niptIsPlaceDebug:
        colTable.label(text="debug2:  "+str(list_table))
    try:
        for dt in data: #Нужно, чтобы отображение ошибки неитерируемости не дублировалось.
            break
        #Создать начала столбцов для таблицы:
        len = length(list_table)
        for cyc, (colWhere, propPath, propName, propIndx, txtError, rawProp) in enumerate(list_table):
            col = rowTable.row().column(align=True) #Чтобы колонки не слипались между собой, а так же отступ у первой колонки не слипается
            if (cyc==0)and(len>1): #Для одностолбцовой таблицы ненужный отступ справа не добавлять.
                rowTable.separator()
            AddBoxLabelDir(col, propName+(f'[{propIndx}]' if propIndx!=-1 else ""), active=isBrightTableLabels)
            row = col.row() #Для фильтра с предупреждением
            isMatrix = False
            try:
                getattr(eval("data[0]"+propPath), propName) #Перед фильтром, чтобы в случае ошибки он не отображался.
                if (propName.startswith("matrix"))and(propIndx==-1):
                    txtError = "matrix[-1] not supported"+Eix(7)
                    isMatrix = True
                if not txtError: #Для 'invalid literal', но перезаписывать от строчки выше.
                    row.active = isBrightFilters
                    row.prop(self.filters.get(rawProp),'filter', text="", icon='SCRIPT')
            except Exception as ex:
                txtError = str(ex)+Eix(8)
            if (isPlaceExecAlerts)and(not txtError):
                AddWarningLabel(row, "eval() !")
            if txtError:
                col.label(text=txtError+Eix(1), icon='INFO' if isMatrix else 'ERROR')
            elif decorTable//4%2:
                col.box()
            col.separator()
            #Записать:
            list_table[cyc][0] = col
            list_table[cyc][4] = txtError
        if niptIsPlaceDebug:
            colTable.label(text="debug3:  "+re.sub("<[^<]+>","<>",str(list_table)))
        #Выполнить прекомпилер:
        try:
            exec(self.precomp, globals(), None)
        except Exception as ex:
            (colSpec if colSpec else colTable).label(text=str(ex)+Eix(2), icon='ERROR') #Отображать в перезаписываемой или по "хронологии".
            return
        sco = 0 #Если нужно будет возвращать, то вынести за пределы большого try, (но не помню почему).
        for dt in data:
            #isHaveDuplicates -- для переключения в режим "или".
            #list_table -- Если список props пустой, будет Total max/max. Поэтому False здесь, чтобы было Total 0.
            can = (not isHaveDuplicates)and(not not list_table)
            dict_errors = {}
            isBright = True
            for cyc, (colWhere, propPath, propName, propIndx, txtError, rawProp) in enumerate(list_table):
                try:
                    if txtError: #Не проверять, чтобы все строки не помечались как содержащие ошибку в этом столбце.
                        continue
                    pr = eval("dt"+propPath)
                    isErrorInProp = True
                    val = getattr(pr, propName)
                    isErrorInProp = False
                    txt = self.filters.get(rawProp).filter
                    tgl = bool(eval(txt if txt else "True", globals(), {'val':val}))
                    if isHaveDuplicates:
                        can |= tgl
                    else:
                        can &= tgl
                except Exception as ex:
                    dict_errors[colWhere] = str(ex)
                    isBright = (isBrightFilterErrors)and(isErrorInProp)
                    can = isShowFilterErrors #Если ошибка, то отображать весь ряд вместе с ячейкой ошибки.
            if can:
                for colWhere, propPath, propName, propIndx, txtError, rawProp in list_table:
                    if txtError: #Не отображать ничего, если ошибка для всего столбца-свойства.
                        continue
                    row = colWhere.row(align=True)
                    row.active = isBright
                    txt = dict_errors.get(colWhere, "")
                    if txt:
                        row.label(text=str(txt)+Eix(3), icon='ERROR')
                    else:
                        pr = eval("dt"+propPath)
                        if pr:
                            if (pr.bl_rna.properties[propName].type=='BOOLEAN'):
                                row.prop(pr, propName, toggle=0)#, icon='CHECKBOX_HLT' if getattr(pr, propName) else 'CHECKBOX_DEHLT')
                            else:
                                row.prop(pr, propName, text="", index=propIndx, icon_only=pr.bl_rna.properties[propName].type=='FLOAT')
                        else:
                            row.label(text="Prop value is None"+Eix(4), icon='ERROR') #Учитывая цикл раньше, я забыл где это актуально.
                sco += 1
        if decorTable//2%2:
            colTable.separator()
            colTable.box()
        if decorTotal:
            colTotal = colTotalTop if decorTotal>0 else colTotalBottom
            StencilTotalRow(prefs, colTotal, ('RADIOBUT_OFF', sco), length(data), ('RNA', length(list_props)))
        self.ProcAlertState(sco)
    except Exception as ex:
        colMain.label(text=str(ex)+Eix(5), icon='ERROR')
        colMain.box()
    return list_props

def NipmSplitPropTxtToList(txt):
    return [li for li in re.findall("[^;,]+", txt.replace(" ", ""))]
def NipmUpdateNodeTableFilters(self, context):
    for li in NipmSplitPropTxtToList(self.props):
        if self.filters.get(li, None) is None:
            ci = self.filters.add()
            ci.name = li
            ci.filter = "True"

class NipmTablePropFilter(bpy.types.PropertyGroup):
    filter: bpy.props.StringProperty(name="Filter", default="")

def NipmAddPathNodePropEval(self, where, isPlaceExecAlerts, canDraw=True):
    evaled = EvalAndAddPropExtended(where, self,'path', self.path, icon='ZOOM_ALL', txt_warning="eval() !"*isPlaceExecAlerts, canDraw=canDraw)
    if not self.path:
        where.label(text="Input expected", icon='INFO')
        return None
    if evaled[0]:
        matter = evaled[1]
        if not matter:
            where.label(text="Data is None", icon='INFO')
            return None
        return matter
    return None
class NodeItemPropsTable(MntNodeWithOnlyMatter):
    bl_idname = 'MntNodeItemPropsTable'
    bl_label = "Item-Props Table"
    bl_icon = 'PROPERTIES' #Можно было и 'SPREADSHEET', но этот нод изначадбнл был создан по нужде высокоуровневого менеджмента.
    bl_width_max = 4096
    bl_width_min = 256
    bl_width_default = 640
    path:    bpy.props.StringProperty(name="Path",    default="")
    props:   bpy.props.StringProperty(name="Props",   default="", update=NipmUpdateNodeTableFilters)
    precomp: bpy.props.StringProperty(name="Precomp", default="")
    filters: bpy.props.CollectionProperty(type=NipmTablePropFilter)
    isShowFilterErrors: bpy.props.BoolProperty(name="Show rows with errors", default=True)
    nclass = 9
    def InitNode(self, context):
        self.path = "bpy.data.objects"
        self.props = "name, data; data.use_fake_user"
        self.precomp = "patr = re.compile(\".*\"); #precompiler here"
        self.filters[0].filter = "patr.search(val)"
        self.filters[1].filter = "re.search(\".*\", val.name)"
    def DrawInAddon(self, context, colLy, prefs):
        if colBox:=GetNodeBoxDiscl(colLy, prefs,'disclMnNipt', self):
            colProps = colBox.column(align=True)
            colProps.prop(prefs,'niptIsBrightTableLabels')
            colProps.prop(prefs,'niptIsBrightFilterErrors')
            colProps.prop(prefs,'niptDecorTable')
            colProps.prop(prefs,'niptDecorTotal')
            colProps.prop(prefs,'niptIsPlaceDebug')
    def DrawExtNode(self, context, colLy, prefs):
        colLy.prop(self,'isShowFilterErrors')
        self.DrawInAddon(context, colLy, prefs)
        PlaceDebugProp(colLy, self,'filters') #todo0 неплохо было бы запариться с отчисткой; и в MnAm тоже.
    def DrawNode(self, context, colLy, prefs):
        isPlaceExecAlerts = prefs.allIsPlaceExecAlerts
        isNotOnlyMatter = not self.isOnlyMatter
        colNodeProps = colLy.column(align=True)
        data = NipmAddPathNodePropEval(self, colNodeProps, isPlaceExecAlerts, canDraw=isNotOnlyMatter)
        colActive = colNodeProps.row().column(align=True)
        EvalAndAddPropExtended(colActive, self,'props', "", icon='RNA', txt_warning="eval() !"*isPlaceExecAlerts, canDraw=isNotOnlyMatter)
        if data:
            EvalAndAddPropExtended(colNodeProps, self,'precomp', "", icon='SCRIPT', txt_warning="exec() !"*isPlaceExecAlerts, alertWarn=True, canDraw=isNotOnlyMatter)
            list_props = NipmSplitPropTxtToList(self.props)
            NipmAddTableOfProps(self, prefs, colLy, data, list_props, colSpec=colNodeProps, canSep=isNotOnlyMatter)
        else:
            colActive.active = False

list_classes += [NipmTablePropFilter]
list_classes += [NodeItemPropsTable]
AddToSacat([ (0,NodeItemPropsTable) ], "RNA", AtHomePoll)
list_tupleСlsToPublic += [(4, NodeItemPropsTable)]
list_clsToChangeTag += [NodeItemPropsTable]

class AddonPrefs(AddonPrefs):
    disclMnNipt: bpy.props.BoolProperty(name="DisclMnNipt", default=False)
    niptIsBrightTableLabels: bpy.props.BoolProperty(name="Bright table labels", default=False)
    niptIsBrightFilterErrors: bpy.props.BoolProperty(name="Bright filter errors", default=False)
    niptDecorTable: bpy.props.IntProperty(name="Decor Table", default=6, min=0, max=7)
    niptDecorTotal: bpy.props.IntProperty(name="Decor Total", default=1, min=-1, max=1)
    niptIsPlaceDebug: bpy.props.BoolProperty(name="Place debug", default=False)

list_clsToAddon.append(NodeItemPropsTable)

class NodePropsNameViewer(MntNodeRoot):
    bl_idname = 'MntNodePropsNamePyViewer'
    bl_label = "Props Name Viewer"
    bl_icon = 'RNA' #RNA  RNA_ADD
    bl_width_max = 2048
    bl_width_min = 256
    bl_width_default = 384
    path:   bpy.props.StringProperty(name="Path",   default="")
    filter: bpy.props.StringProperty(name="Filter", default="")
    isShowIdentifier: bpy.props.BoolProperty(name="Show identifier", default=True)
    nclass = 9
    def InitNode(self, context):
        self.path = "bpy.context.space_data.edit_tree.nodes.active"
        self.filter = "re.search(\"\", val.identifier)"
    def DrawInAddon(self, context, colLy, prefs):
        if colBox:=GetNodeBoxDiscl(colLy, prefs,'disclMnNpnv', self):
            colProps = colBox.column(align=True)
            colProps.prop(prefs,'npnvIsBrightTableLabels')
            colProps.prop(prefs,'npnvDecorTable')
            colProps.prop(prefs,'npnvDecorTotal')
    def DrawExtNode(self, context, colLy, prefs):
        colLy.prop(self,'isShowIdentifier')
        self.DrawInAddon(context, colLy, prefs)
    def DrawNode(self, context, colLy, prefs):
        colNodeProps = colLy.column(align=True)
        isShowIdentifier = self.isShowIdentifier
        isPlaceExecAlerts = prefs.allIsPlaceExecAlerts
        isBrightFilters = prefs.allIsBrightFilters
        isBrightTableLabels = prefs.npnvIsBrightTableLabels
        decorTable = prefs.npnvDecorTable
        decorTotal = prefs.npnvDecorTotal
        target = NipmAddPathNodePropEval(self, colNodeProps, isPlaceExecAlerts)
        colActive = colNodeProps.row().column(align=True)
        AddThinSep(colLy, .2)
        EvalAndAddPropExtended(colActive, self,'filter', "", icon='SCRIPT', txt_warning="eval() !"*isPlaceExecAlerts)
        if target:
            AddThinSep(colLy)
            colTotalTop = colLy.column(align=True)
            colList = colLy.column(align=True)
            colTotalBottom = colLy.column(align=True)
            if decorTable//4%2:
                colList.box()
            spl = colList.row().split(factor=.5)
            AddBoxLabelDir(spl, "Name", active=isBrightTableLabels)
            AddBoxLabelDir(spl, "Value", active=isBrightTableLabels)
            if decorTable//2%2:
                colList.box()
            try:
                sco = 0
                for li in target.bl_rna.properties:
                    val = li
                    txt = self.filter
                    if eval(txt if txt else "True", globals(), {'val':val}):
                        spl = colList.row().split(factor=.5, align=True)
                        spl.prop(li,'identifier' if isShowIdentifier else 'name', text="", icon='PINNED' if (li.is_readonly or li.is_registered) else 'NONE')
                        row = spl.row(align=li.identifier.startswith('matrix'))
                        try: #Не знаю, как отличить 'RNAMeta' от "пропертабельных".
                            if (li.type=='BOOLEAN'):
                                row.prop(target, li.identifier)
                            else:
                                row.prop(target, li.identifier, text=None if getattr(li,'default_flag', False) else "")
                        except:
                            if hasattr(target, li.identifier):
                                row.label(text=str(getattr(target, li.identifier)))
                            else:
                                row.label(text="None")
                                row.active = False
                        sco += 1
                if decorTable%2:
                    colList.box()
                if decorTotal:
                    colTotal = colTotalTop if decorTotal>0 else colTotalBottom
                    StencilTotalRow(prefs, colTotal, ('RNA', sco), length(target.bl_rna.properties))
            except Exception as ex:
                colLy.label(text=str(ex), icon='ERROR')
        else:
            colActive.active = False

list_classes += [NodePropsNameViewer]
AddToSacat([ (1,NodePropsNameViewer) ], "RNA", AtHomePoll)
list_tupleСlsToPublic += [(3, NodePropsNameViewer)]
list_clsToChangeTag += [NodePropsNameViewer]

class AddonPrefs(AddonPrefs):
    disclMnNpnv: bpy.props.BoolProperty(name="DisclMnNpnv", default=False)
    npnvIsBrightTableLabels: bpy.props.BoolProperty(name="Bright table labels", default=False)
    npnvDecorTable: bpy.props.IntProperty(name="Decor Table", default=3, min=0, max=7)
    npnvDecorTotal: bpy.props.IntProperty(name="Decor Total", default=1, min=-1, max=1)

list_clsToAddon.append(NodePropsNameViewer)

import addon_utils, os, functools

def GetAddonsList():
    return [(mod, addon_utils.module_bl_info(mod)) for mod in addon_utils.modules(refresh=False)]

class NamOp(bpy.types.Operator):
    bl_idname = 'mnt.node_op_nam'
    bl_label = "NamOp"
    txt: bpy.props.StringProperty()
    def execute(self, context):
        if self.txt:
            import subprocess
            subprocess.Popen(f"explorer /select,{self.txt}")
        return {'FINISHED'}

def NamTimerCreateNewCi(ndTar, adnName):
    ci = ndTar.addons.add()
    ci.name = adnName
    ci.txt = adnName

isWorking = False
def NamUpdateNameOfAddon(self, context):
    global isWorking
    if isWorking:
        return
    isWorking = True
    self.txt = self.name
    isWorking = False
class NamAddons(bpy.types.PropertyGroup):
    discl: bpy.props.BoolProperty(name="Discl", default=False)
    txt: bpy.props.StringProperty(name="Addon name", default="", update=NamUpdateNameOfAddon)

def NamItemsAddonFilter(self, context):
    list_items = [ ('All', "All", ""), ('User',"User","") ]
    set_unique = set()
    for md in addon_utils.modules(refresh=False):
        blinfo = addon_utils.module_bl_info(md)
        set_unique.add(blinfo['category'])
    list_items.extend( [(cat,cat,"") for cat in sorted(set_unique)] )
    return list_items

def AddBlInfoFromOrder(where, mod, blinfo, txt_order="avdlwf"): #avdlwf красивее, чем dlfavw!
    def AddAnBlInfoLine(where, label, txt, isFile=False):
        rowMain = where.row(align=True)
        rowLabel = rowMain.row(align=True)
        rowLabel.alignment = 'CENTER'
        rowLabel.label(text=label)
        rowLabel.active = False
        if not isFile:
            rowMain.label(text=txt)
        else:
            rowMain.alignment = 'LEFT'
            rowMain.operator(NamOp.bl_idname, text=txt, emboss=False).txt = txt
    for ch in txt_order:
        target = [di for di in blinfo if di[0]==ch]
        target = target[0] if target else "hi"
        LCheck = lambda a: (target==a)and(blinfo[a])
        if (mod)and(ch=="f"):     AddAnBlInfoLine(where, "File:",        mod.__file__, True)
        if LCheck('description'): AddAnBlInfoLine(where, "Description:", blinfo['description'])
        if LCheck('location'):    AddAnBlInfoLine(where, "Location:",    blinfo['location'])
        if LCheck('author'):      AddAnBlInfoLine(where, "Author:",      blinfo['author'])
        if LCheck('version'):     AddAnBlInfoLine(where, "Version:",     ".".join(str(li) for li in blinfo['version']))
        if LCheck('warning'):
            rowMain = where.row(align=True)
            rowIco = rowMain.row(align=True)
            #rowIco.alert = True
            rowIco.label(icon='ERROR')
            rowIco.active = False
            AddAnBlInfoLine(rowMain, "Warning:", blinfo['warning'])
class NodeAddonsManager(MntNodeWithOnlyMatter): #Для этого аддона как аналог VLT у VL. (См. гит ugorek000/VoronoiLinker)
    bl_idname = 'MntNodeAddonsManager'
    bl_label = "Addons Manager"
    #bl_icon = 'PLUGIN'
    bl_width_max = 2048
    bl_width_min = 256
    bl_width_default = 512
    addons: bpy.props.CollectionProperty(type=NamAddons)
    filter: bpy.props.StringProperty(name="filter", default="")
    enum_filterByCat: bpy.props.EnumProperty(name="Filter by category", items=NamItemsAddonFilter)
    isShowDisabledAddons: bpy.props.BoolProperty(name="Disabled addons", default=False)
    nclass = 40
    def InitNode(self, context):
        self.filter = ".*"
        dict_usedExt = {ext.module for ext in bpy.context.preferences.addons}
        global isWorking
        isWorking = True
        for li in sorted(GetAddonsList(), key=lambda a: a[0].__name__ in dict_usedExt, reverse=True):
            ci = self.addons.add()
            ci.name = li[1]['name'] #Заметка: поскольку 'name' первым, см. топологию, isWorking не обязателен.
            ci.txt = ci.name
        isWorking = False
    def DrawInAddon(self, context, colLy, prefs):
        if colBox:=GetNodeBoxDiscl(colLy, prefs,'disclMnNam', self):
            colProps = colBox.column(align=True)
            colProps.prop(prefs,'namItemsAlignment')
            colProps.prop(prefs,'namIsSelfPraise')
            colProps.prop(prefs,'namDecorTable')
            colProps.prop(prefs,'namDecorItems')
            colProps.prop(prefs,'namDecorPrefsLabel')
            colProps.prop(prefs,'namDecorTotal')
            colProps.prop(prefs,'namIsShowButtons')
            colProps.prop(prefs,'namIsDetailedTotal')
    def DrawExtNode(self, context, colLy, prefs):
        self.DrawInAddon(context, colLy, prefs)
        PlaceDebugProp(colLy, self,'addons')
    def DrawNode(self, context, colLy, prefs):
        namDecorTable = prefs.namDecorTable
        isNotOnlyMatter = not self.isOnlyMatter
        if isNotOnlyMatter:
            #Quartet (1+3):
            row = colLy.row(align=True)
            row.row().operator('wm.save_userpref', text="Save Preferences"+(" *" if context.preferences.is_dirty else ""))
            row.prop(self,'enum_filterByCat', text="")
            row.row().operator('preferences.addon_install', text="Install...", icon='IMPORT')
            row.operator('preferences.addon_refresh', text="Refresh", icon='FILE_REFRESH')
            AddThinSep(colLy)
        #Filter:
        if not(patr:=StencilAddFilterProp(self, prefs, colLy, canDraw=isNotOnlyMatter)):
            return
        if isNotOnlyMatter:
            AddThinSep(colLy, .2)
        if namDecorTable%2:
            colLy.box()
        #Errors:
        if addon_utils.error_duplicates:
            colLy.label(text="Multiple add-ons with the same name found!", icon='ERROR')
            return
        if addon_utils.error_encoding:
            colLy.label(text="One or more addons do not have UTF-8 encoding (see console for details)", icon='ERROR')
            return
        #BoxList:
        colTheme = colLy.column(align=True)
        colTotalTop = colTheme.column(align=True)
        box = colTheme.box()
        colAddons = box.column(align=True)
        colErrors = colAddons.column(align=True)
        colTotalBottom = colTheme.column(align=True)
        #Prepare ly:
        dict_usedExt = {ext.module for ext in bpy.context.preferences.addons}
        tuple_userDirs = ( *[os.path.join(li,"addons") for li in bpy.utils.script_paths_pref()], bpy.utils.user_resource('SCRIPTS', path="addons") )
        tuple_userDirs = tuple(p for p in tuple_userDirs if p)
        list_addons = GetAddonsList()
        #Prepare for:
        set_modNames = {li[0].__name__ for li in list_addons}
        set_missingMods = {di for di in dict_usedExt if di not in set_modNames}
        len = length(dict_usedExt)-length(set_missingMods) #Омг, головная боль с ^.
        isSda = self.isShowDisabledAddons
        catf = self.enum_filterByCat
        can = True
        scoTot = 0
        scoDisp = 0
        scoDis = 0
        scoEnb = 0
        namItemsAlignment = prefs.namItemsAlignment
        namDecorPrefsLabel = prefs.namDecorPrefsLabel
        namIsShowButtons = prefs.namIsShowButtons
        namIsSelfPraise = prefs.namIsSelfPraise
        namDecorItems = prefs.namDecorItems
        try:
            #Matter:
            list_userAddonPaths = []
            entryTgl = False
            for cyc, (mod, blinfo) in enumerate(sorted(list_addons, key=lambda a: a[0].__name__ in dict_usedExt, reverse=True)):
                modName = mod.__name__
                adnName = blinfo['name']
                scoTot += 1
                if cyc==len:
                    colShowDis = colAddons.row().column(align=True) #Второй .row() для namItemsAlignment==0.
                    entryTgl = True
                if (cyc>=len)and(not isSda):
                    can = False
                if (catf!="All")and(catf!=blinfo['category'])and not( (catf=="User")and(mod.__file__.startswith(tuple_userDirs)) ):
                    continue
                if not patr.search(adnName):
                    continue
                if cyc>=len:
                    scoDis += 1
                else:
                    scoEnb += 1
                if not can:
                    continue
                if (namItemsAlignment>3)and(entryTgl):
                    AddThinSep(colAddons, .34)
                scoDisp += 1
                isEnabled = cyc<len #modName in dict_usedExt #not not context.preferences.addons.get(modName, False)
                rowRecord = (colAddons.row() if namItemsAlignment>1 else colAddons).row(align=True) #'namDecorItems==0'?
                #Disclosure:
                rowDiscl = rowRecord.row(align=True)
                if not self.addons.get(adnName, False):
                    bpy.app.timers.register(functools.partial(NamTimerCreateNewCi, self, adnName))
                    continue
                ci = self.addons[adnName]
                isDiscl = ci.discl
                rowDiscl.prop(ci,'discl', text="", icon='DISCLOSURE_TRI_'+('DOWN' if isDiscl else 'RIGHT'))
                rowDiscl.scale_x = 2.0
                rowDiscl.active = not isDiscl
                #Toggle addon register:
                rowEnabled = rowRecord.row(align=True)
                if modName==thisAddonName:
                    #rowEnabled.operator(NamOp.bl_idname, text="", icon='CHECKBOX_HLT')
                    rowEnabled.prop(ci,'discl', text="", icon='CHECKBOX_HLT', invert_checkbox=ci.discl)
                else:
                    ico = 'CHECKBOX_HLT' if isEnabled else 'CHECKBOX_DEHLT'
                    rowEnabled.operator('preferences.addon_disable' if isEnabled else 'preferences.addon_enable', text="", icon=ico).module = modName
                AddThinSep(rowRecord, 1.0, .5)
                #Addon name:
                colAddon = (rowRecord.row() if namDecorItems%2 else rowRecord).column(align=True)
                rowAddon = colAddon.row(align=True)
                isSelfAddonMarker = adnName==bl_info['name']
                if (namIsSelfPraise)and(blinfo['author']=="ugorek"):
                    rowIsMyAddonMarker = rowAddon.row(align=True)
                    rowIsMyAddonMarker.active = False
                    rowIsMyAddonMarker.alert = isSelfAddonMarker# or True #MONKEY
                    rowIsMyAddonMarker.label(icon='SOLO_ON' if isSelfAddonMarker else 'SOLO_OFF') #FONTPREVIEW  SNAP_FACE  MONKEY  SOLO_ON  SOLO_OFF
                if not(isSelfAddonMarker and namIsSelfPraise): #if True: #CtrlC-ability
                    rowLabel = rowAddon.row(align=True)
                    rowName = rowLabel.row(align=True)
                    rowName.prop(ci,'txt', text="")
                    isIcoInBox = True
                else:
                    box = rowAddon.box()
                    box.scale_y = 0.5
                    rowLabel = box.row(align=True)
                    rowName = rowLabel.row(align=True)
                    rowName.alert = (isSelfAddonMarker)and(namIsSelfPraise)
                    rowName.label(text=adnName)#, icon='PLUGIN')
                    isIcoInBox = False
                rowName.active = isEnabled
                if isDiscl:
                    box = (colAddon.row() if namDecorItems%2 else colAddon).box()
                    colAnBlInfo = box.column(align=True)
                    AddBlInfoFromOrder(colAnBlInfo, mod, blinfo)
                    if isEnabled:
                        addonPrefs = context.preferences.addons[modName].preferences
                        if (namDecorItems//2%2)or(addonPrefs):
                            if namDecorPrefsLabel:
                                row = colAddon.row(align=True)
                                row.alignment = ('LEFT','CENTER','RIGHT')[abs(namDecorPrefsLabel)-1]
                                if namDecorPrefsLabel>0:
                                    rowIco = row.row(align=True)
                                    rowIco.label(icon='PREFERENCES' if addonPrefs else 'INFO')
                                    rowIco.active = False
                                row.label(text="Preferences"+":"*(abs(namDecorPrefsLabel)!=3) if addonPrefs else "Addon has no prefs.")
                                row.active = False
                            if addonPrefs:
                                draw = getattr(addonPrefs,'draw', None)
                                if draw:
                                    apClass = type(addonPrefs)
                                    apClass.layout = colAddon
                                    try:
                                        draw(context)
                                    except:
                                        import traceback
                                        traceback.print_exc()
                                        #row.alert = True
                                        row.label(icon='ERROR')
                                        row.alert = False
                                        row.label(text="Error (see console)")
                                        #А так же в "общий" итог:
                                        row = colErrors.row(align=True)
                                        #row.label(icon='BLANK1')
                                        row.label(text=f"\"{modName}\" has error in draw().", icon='ERROR')
                                    del apClass.layout
                                else:
                                    row = colAddon.row(align=True)
                                    row.alignment = 'CENTER'
                                    row.label(text="draw() not found")
                                    row.active = False
                                colAddon.separator()
                if isIcoInBox:
                    box = rowLabel.box()
                    box.scale_y = .5
                    rowIcon = box.row(align=True)
                else:
                    rowIcon = rowLabel.row(align=True)
                rowIcon.label( icon={'OFFICIAL':'BLENDER', 'COMMUNITY':'COMMUNITY', 'TESTING':'EXPERIMENTAL'}.get(blinfo['support'], 'QUESTION') )
                rowIcon.active = blinfo['support']!='COMMUNITY'
                rowButs = rowAddon.row(align=True)
                rowButs.alignment = 'RIGHT'
                rowButs.scale_x = 1.15 #Откуда-то двукратный отступ.
                if (isDiscl)or(namIsShowButtons):
                    if not list_userAddonPaths:
                        for path in (bpy.utils.script_path_user(), *bpy.utils.script_paths_pref()):
                            if path is not None:
                                list_userAddonPaths.append(os.path.join(path,"addons"))
                    isUserAddon = False
                    for li in list_userAddonPaths:
                        if bpy.path.is_subdir(mod.__file__, li):
                            isUserAddon = True
                    if (blinfo['doc_url'])or(blinfo.get('tracker_url'))or(blinfo.get('wiki_url')):
                        if blinfo['doc_url']:
                            rowButs.operator('wm.url_open', text="", icon='HELP').url = blinfo['doc_url']
                        if blinfo.get('wiki_url'):
                            rowButs.operator('wm.url_open', text="", icon='HELP').url = blinfo['wiki_url']
                        if blinfo.get('tracker_url'):
                            rowButs.operator('wm.url_open', text="", icon='URL').url = blinfo['tracker_url']
                        elif not isUserAddon:
                            op = rowButs.operator("wm.url_open_preset", text="", icon='COPY_ID') #URL  COPY_ID
                            op.type = 'BUG_ADDON'
                            op.id = ("Name: %s %s\n" "Author: %s\n")%(adnName, str(blinfo['version']), blinfo['author'])
                    if (isUserAddon)and(not isSelfAddonMarker):
                        rowButs.operator("preferences.addon_remove", text="", icon='CANCEL').module = modName
                entryTgl = True
            if not scoDisp:
                if namDecorTable//8%2:
                    colAddons.box()
                else:
                    row = colAddons.row(align=True)
                    row.label(text="")
                    row.scale_y = 0.33
            #Missings:
            if set_missingMods:
                AddThinSep(colAddons, 0.5)
                rowLabel = colAddons.row(align=True)
                rowLabel.label(text="Missing script files")
                rowLabel.active = False
                for modMame in set_missingMods:
                    rowAdn = colAddons.row(align=True)
                    rowAdn.label(icon='ERROR')
                    if modMame in dict_usedExt:
                        rowAdn.operator('preferences.addon_disable', text="", icon='CHECKBOX_HLT', emboss=False).module = modMame
                    rowAdn.label(text=modMame, translate=False)
        except Exception as ex:
            colAddons.box().row(align=True).label(text=str(ex), icon='ERROR')
        #Disabled button discl:
        if scoDis:
            txt = "Disabled addons ("+str(scoDis)+")"
            tgl = namItemsAlignment%2==1
            if (tgl)and(scoEnb):
                AddThinSep(colShowDis, .34)
            if (namItemsAlignment>3)and(entryTgl):
                AddThinSep(colShowDis, .34)
            colShowDis.prop(self,'isShowDisabledAddons', text=txt, icon='TRIA_DOWN' if isSda else 'TRIA_RIGHT', toggle=1, invert_checkbox=isSda)
            if (tgl)and(isSda):
                AddThinSep(colShowDis, .34)
        #Total:
        dec = prefs.namDecorTotal
        if dec:
            colTotal = colTotalTop if dec>0 else colTotalBottom
            if dec<0:
                colSep = colTotal.column(align=True)
                rowSep = colTotal.row(align=True)
            colTot = colTotal.column(align=True)
            if dec>0:
                rowSep = colTotal.row(align=True)
                colSep = colTotal.column(align=True)
            dec = abs(dec)-1
            if prefs.namIsDetailedTotal:
                StencilTotalRow(prefs, colTot, ('CHECKBOX_HLT', len), ('CHECKBOX_DEHLT', length(list_addons)-len), ('RADIOBUT_OFF', scoDisp), scoTot, decor=(1+(1+dec)%2))
            else:
                StencilTotalRow(prefs, colTot, ('PLUGIN', scoDisp), scoTot, decor=(1+(1+dec)%2))
            if dec>2:
                AddThinSep(rowSep, 0.25*(1+(dec-3)//2))
            if namDecorTable//4%2:
                AddThinSep(colSep)
                colSep.box()
                AddThinSep(colSep)
        if namDecorTable//2%2:
            colLy.box()
        self.ProcAlertState(scoDisp)

list_classes += [NamAddons, NamOp]
list_classes += [NodeAddonsManager]
AddToSacat([ (1,NodeAddonsManager) ], "Special", AtHomePoll)
list_clsToChangeTag += [NodeAddonsManager]

class AddonPrefs(AddonPrefs):
    disclMnNam: bpy.props.BoolProperty(name="DisclMnNam", default=False)
    namItemsAlignment: bpy.props.IntProperty(name="Alignment between elements", default=4, min=0, max=5)
    namIsSelfPraise: bpy.props.BoolProperty(name="Self-praise", default=True)
    namDecorTable: bpy.props.IntProperty(name="Decor Table", default=1, min=0, max=15)
    namDecorItems: bpy.props.IntProperty(name="Decor Items", default=2, min=0, max=3)
    namDecorPrefsLabel: bpy.props.IntProperty(name="Decor Prefs label", default=2, min=-3, max=3)
    namDecorTotal: bpy.props.IntProperty(name="Decor Total", default=2, min=-7, max=7)
    namIsShowButtons: bpy.props.BoolProperty(name="Forcibly show buttons", default=False)
    namIsDetailedTotal: bpy.props.BoolProperty(name="Detailed total", default=False)

list_clsToAddon.append(NodeAddonsManager)

class NodeQuickNote(MntNodeAlertness):
    bl_idname = 'MntNodeQuickNote'
    bl_label = "Quick note"
    bl_width_max = 2048
    bl_width_min = 64
    bl_width_default = 256
    note: bpy.props.StringProperty(name="Note body", default="")
    nclass = 32
    def DrawNode(self, context, layout, prefs):
        layout.prop(self,'note', text="")
        self.ProcAlertState(self.note)

list_classes += [NodeQuickNote]
AddToSacat([ (0,NodeQuickNote) ], "Text", AtHomePoll)
list_tupleСlsToPublic += [(0, NodeQuickNote)]
list_clsToChangeTag += [NodeQuickNote]

class NnOp(bpy.types.Operator):
    bl_idname = 'mnt.node_op_nn'
    bl_label = "NamOp"
    bl_options = {'UNDO'}
    who: bpy.props.StringProperty()
    opt: bpy.props.StringProperty()
    def execute(self, context):
        if self.who:
            ndRepr = eval(self.who)
            match self.opt:
                case 'CollapseEmpties':
                    warpTo = -1
                    memo = ndRepr.memo
                    for cyc, ci in enumerate(ndRepr.memo):
                        if ci.body:
                            if warpTo>-1:
                                memo[warpTo].body = memo[cyc].body
                                memo[warpTo].name = memo[cyc].name
                                memo[cyc].body = ""
                                warpTo += 1
                        elif warpTo==-1:
                            warpTo = cyc
                    if warpTo!=-1:
                        for cyc in reversed(range(warpTo, length(memo))):
                            memo.remove(cyc)
                        ndRepr.linesCount = length(memo) #context.area.tag_redraw()
        return {'FINISHED'}

def NnUpdateCount(self, context):
    len = length(self.memo)
    for cyc in range(len, self.linesCount):
        ci = self.memo.add()
        ci.name = str(cyc)
    for cyc in reversed(range(self.linesCount, len)):
        self.memo.remove(cyc)
class NnNotepadLine(bpy.types.PropertyGroup):
    body: bpy.props.StringProperty(name="NpLTB", default="")

class NodeNotepad(MntNodeAlertness):
    bl_idname = 'MntNodeNotepad'
    bl_label = "Notepad"
    bl_width_max = 2048
    bl_width_min = 140
    bl_width_default = 384
    linesCount: bpy.props.IntProperty(name="Count of lines", min=0, max=256, soft_max=32, default=0, update=NnUpdateCount)
    decorLinesCount: bpy.props.IntProperty(name="Decor Lines count", default=3, min=0, max=4)
    memo: bpy.props.CollectionProperty(type=NnNotepadLine)
    nclass = 32
    def InitNode(self, context):
        self.linesCount = 5 #Заметка: NnUpdateCount().
    def DrawInAddon(self, context, colLy, prefs):
        if colBox:=GetNodeBoxDiscl(colLy, prefs,'disclMnNn', self):
            colProps = colBox.column(align=True)
            colProps.prop(prefs,'nnDecorMemo')
    def DrawExtNode(self, context, colLy, prefs):
        self.DrawInAddon(context, colLy, prefs)
        colLy.prop(self,'decorLinesCount') #<^ стандартизовать #todo2. #todo3 настройки нода в аддоне -- отдельной панелью со своим poll на наличие.
        colLy.prop(self,'linesCount')
        colLy.label(text="Operators:")
        op = colLy.operator(NnOp.bl_idname, text="Collapse empty lines")
        op.who = repr(self)
        op.opt = 'CollapseEmpties'
    def DrawNode(self, context, colLy, prefs):
        decorNum = prefs.nnDecorMemo//4%4
        decorBody = prefs.nnDecorMemo%4
        if self.decorLinesCount:
            decorLinesCount = self.decorLinesCount-1
            rowProp = colLy.row()
            if decorLinesCount//2%2:
                rowProp.alignment = 'LEFT'
                rowProp.scale_x = 1.2
            rowProp.prop(self,'linesCount')
            rowProp.active = decorLinesCount%2
        colNotepad = colLy.column(align=decorBody<2)
        len = length(str(self.linesCount))
        canAlert = any(self.alertColor)
        alertAcc = False
        for cyc, ci in enumerate(self.memo):
            rowLine = colNotepad.row(align=True)
            if decorNum:
                rowNum = rowLine.row(align=True)
                rowNum.alignment = 'CENTER'
                rowNum.active = decorNum>1
                rowNum.label(text=str(cyc+1).zfill(len)+":")
            rowBody = (rowLine.row() if decorBody else rowLine).row(align=True)
            rowBody.prop(ci,'body', text="")
            if canAlert:
                alertAcc |= not not ci.body
        if canAlert:
            self.ProcAlertState(alertAcc)

list_classes += [NnNotepadLine, NnOp]
list_classes += [NodeNotepad]
AddToSacat([ (1,NodeNotepad) ], "Text", AtHomePoll)
list_tupleСlsToPublic += [(7, NodeNotepad)]
list_clsToChangeTag += [NodeNotepad]

class AddonPrefs(AddonPrefs):
    disclMnNn: bpy.props.BoolProperty(name="DisclMnNn", default=False)
    nnDecorMemo: bpy.props.IntProperty(name="Decor Memo", default=4, min=0, max=11)

list_clsToAddon.append(NodeNotepad)

class NttfOp(bpy.types.Operator):
    bl_idname = 'mnt.node_op_nttf'
    bl_label = "NttfOp"
    bl_options = {'UNDO'}
    who: bpy.props.StringProperty()
    opt: bpy.props.StringProperty()
    dest: bpy.props.StringProperty()
    def invoke(self, context, event):
        if self.who:
            ndRepr = eval(self.who)
            match self.opt:
                #todo0 отрендерить текст чтобы узнать его ширину, а потом ширину нода на максимальный из них.
                case 'Shield':
                    ndRepr.regex = re.sub(r'\\.|(?=[+*\()[\]{}.^$?|])', lambda a:"\\" if a.span()[1]-a.span()[0]==0 else a.group(), ndRepr.regex) #re.escape(ndRepr.regex)
                case 'Warp':
                    maxSquare = 0
                    windowTar = None
                    areaTar = None
                    spaceTar = None
                    for wn in context.window_manager.windows if not event.shift else [context.window]:
                        for ar in wn.screen.areas:
                            if ar.type=='TEXT_EDITOR':
                                sp = ar.spaces[0]
                                if sp.type=='TEXT_EDITOR':
                                    square = ar.width*ar.height
                                    if maxSquare<square:
                                        maxSquare = square
                                        windowTar = wn
                                        areaTar = ar
                                        spaceTar = sp
                    if not spaceTar:
                        context.area.type = "TEXT_EDITOR"
                        windowTar = context.window
                        areaTar = context.area
                        spaceTar = context.space_data
                    dest = eval(self.dest)
                    spaceTar.text = bpy.data.texts.get(dest[0])
                    inx = dest[1]-1
                    with context.temp_override(window=windowTar, area=areaTar): #, space=spaceTar
                        bpy.ops.text.jump(line=inx+1)
                    spaceTar.text.select_set(inx, dest[2][0], inx, dest[2][1])
                    #todo0 было бы удобно сразу дать фокус ввода целевому окну; да вот хрен знает, как сделать.
        return {'FINISHED'}

class TtfResult:
    def __init__(self, inx, ln, rex, val):
        self.inx = inx
        self.ln = ln
        self.rex = rex
        self.val = val
class TtfSearch:
    def __init__(self, tbRef, zlen):
        self.tbRef = tbRef
        self.zlen = zlen
        self.list_result = []
class TtfFinder:
    def __init__(self):
        self.lastTimeRaw = 0
        self.list_search = []
        self.set_unique = set()

dict_nttfFinderCache = {}

import time

def NttfDoNdSearch(ndTar):
    if not dict_nttfFinderCache.get(ndTar, False):
        return
    list_search = dict_nttfFinderCache[ndTar].list_search
    set_unique = dict_nttfFinderCache[ndTar].set_unique
    list_search.clear()
    set_unique.clear()
    scoTotAll = 0
    if ndTar.regex:
        try:
            patr = re.compile(ndTar.regex)
        except:
            return
        if ndTar.tbPoi:
            list_tbs = [tb for tb in bpy.data.texts if tb!=ndTar.tbPoi] if ndTar.isReverseTbPoi else [ndTar.tbPoi]
        else:
            list_tbs = [*bpy.data.texts]
        if getattr(bpy.types.Text,'order', False):
            list_tbs.sort(key=lambda a: a.order)
        for tb in list_tbs:
            ttfSr = TtfSearch(tb, length(str(length(tb.lines))))
            for cyc, ln in enumerate(tb.lines):
                rex = patr.search(ln.body)
                if rex:
                    ttfSr.list_result.append(TtfResult(cyc+1, ln, rex, rex.group()))
                    set_unique.add(rex)
            list_search.append(ttfSr)
            scoTotAll += length(tb.lines)
    dict_nttfFinderCache[ndTar].scoTotAll = scoTotAll
    dict_nttfFinderCache[ndTar].lastTimeRaw = time.time()

def NttfUpdateRegex(self, context):
    NttfDoNdSearch(self)
def NttfUpdateTbPoi(self, context):
    self.isReverseTbPoi = False
class NodeTextblockTextFinder(MntNodeWithOnlyMatter):
    bl_idname = 'MntNodeTextblockTextFinder'
    bl_label = "Textblock Text Finder"
    bl_width_max = 2048
    bl_width_min = 256
    bl_width_default = 448
    tbPoi: bpy.props.PointerProperty(name="Text Block", type=bpy.types.Text, update=NttfUpdateTbPoi)
    regex: bpy.props.StringProperty(name="RegEx", default="", update=NttfUpdateRegex)
    isReverseTbPoi: bpy.props.BoolProperty(name="Reverse search", default=False, update=NttfUpdateRegex)
    isDisplayAsProp: bpy.props.BoolProperty(name="Display as prop", default=True)
    isDisplayUnique: bpy.props.IntProperty(name="Display unique", default=0, min=0, max=2)
    linesScaleY: bpy.props.FloatProperty(name="Lines scale Y", min=.4, max=1.5, default=.85)
    decorResults: bpy.props.IntProperty(name="Decor Results", default=11, min=0, max=31)
    nclass = 32
    def draw_label(self):
        #И так же поместить само выражение.
        return "Textblock LineText Finder  /"+self.regex+"/" #"–"
    def InitNode(self, context):
        self.regex = "^ *#\w+.+"
        if tb:=bpy.data.texts.get(".Compiled"):
            self.tbPoi = tb
            self.isReverseTbPoi = True
    def DrawInAddon(self, context, colLy, prefs):
        if colBox:=GetNodeBoxDiscl(colLy, prefs,'disclMnNttf', self):
            colProps = colBox.column(align=True)
            colProps.prop(prefs,'nttfItemsAlignment')
            colProps.prop(prefs,'nttfDecorTable')
            colProps.prop(prefs,'nttfDecorTotal')
    def DrawExtNode(self, context, colLy, prefs):
        colLy.prop(self,'linesScaleY')
        colLy.prop(self,'decorResults')
        self.DrawInAddon(context, colLy, prefs)
    def DrawNode(self, context, colLy, prefs):
        dict_nttfFinderCache.setdefault(self, TtfFinder())
        finder = dict_nttfFinderCache[self]
        if time.time()-finder.lastTimeRaw>0.5: #Для редактирования через prop'ы удобно иметь скорейший фидбек, если после редактирования оно перестанет удовлетворять условию фильтра.
            NttfDoNdSearch(self)
        isDisplayAsProp = self.isDisplayAsProp
        decorResults = self.decorResults
        isDisplayUnique = self.isDisplayUnique
        nttfItemsAlignment = prefs.nttfItemsAlignment
        nttfDecorTable = prefs.nttfDecorTable
        nttfDecorTotal = prefs.nttfDecorTotal
        isNotOnlyMatter = not self.isOnlyMatter
        if isNotOnlyMatter:
            rowTbPoi = colLy.row(align=True)
            rowLabel = rowTbPoi.row(align=True)
            rowLabel.alignment = 'CENTER'
            rowLabel.label(text="Search in:")
            rowReverse = rowTbPoi.row(align=True)
            rowReverse.prop(self,'isReverseTbPoi', text="", icon='ARROW_LEFTRIGHT')
            rowReverse.active = False
            rowTbPoi.prop(self,'tbPoi', text="")
        rowFilter = colLy.row() #todo1 макет для StencilAddFilterProp для выдачи ошибок.
        if isNotOnlyMatter:
            rowOptions = colLy.row(align=True)
            rowOptions.active = False
            rowOptions.alignment = 'LEFT'
            rowOptions.scale_y = 0.85
            op = rowOptions.operator(NttfOp.bl_idname, text="Shield") #"Escape" #icon='ITALIC'
            op.who = repr(self)
            op.opt = 'Shield'
            rowOptions.separator()
            rowOptions.separator()
            rowOptions.prop(self,'isDisplayAsProp') #icon='LONGDISPLAY'
            row = rowOptions.row(align=True)
            row.prop(self,'isDisplayUnique') #icon='TRACKER'
            row.scale_x = 0.65
        if patr:=StencilAddFilterProp(self, prefs, rowFilter, prop='regex', canDraw=isNotOnlyMatter):
            if nttfDecorTable//2%2:
                colLy.box()
            colTotalTop = colLy.column(align=True)
            colFounds = colLy.column(align=True)
            colTotalBottom = colLy.column(align=True)
            scoDisp = 0
            set_dataTb = {tb for tb in bpy.data.texts}
            list_search = finder.list_search
            for fdsr in reversed(list_search):
                if fdsr.tbRef not in set_dataTb:
                    list_search.remove(fdsr)
            set_uniqueDisplayed = set()
            for fdsr in list_search:
                if fdsr.list_result:
                    box = colFounds.row().box()
                    colTb = box.column(align=True)
                    row = colTb.row()
                    row.alert = decorResults//4%2
                    #row.prop(fdsr.tbRef,'name', text="", icon='TEXT')
                    AddBoxLabelDir(row, fdsr.tbRef.name, icon='TEXT')
                    row.active = decorResults%2
                    #todo1 наверное было бы удобно если иметь int свойство, переключаясь по которому происходит авто-варп на индекс найденного.
                    colList = colTb.column(align=True)
                    colList.scale_y = self.linesScaleY
                    set_uniqueDisplayedLocal = set()
                    for li in fdsr.list_result:
                        if isDisplayUnique:
                            if isDisplayUnique==1:
                                if li.val in set_uniqueDisplayedLocal:
                                    continue
                                set_uniqueDisplayedLocal.add(li.val)
                            if isDisplayUnique==2:
                                if li.val in set_uniqueDisplayed:
                                    continue
                                set_uniqueDisplayed.add(li.val)
                        rowResult = (colList.row() if nttfItemsAlignment else colList).row(align=True)
                        rowInx = rowResult.row(align=True)
                        rowInx.alignment = 'CENTER'
                        rowInx.active = False
                        rowInx.label(text=str(li.inx).zfill(fdsr.zlen)+":")
                        if isDisplayAsProp:
                            rowResult.prop(li.ln,'body', text="")
                        else:
                            rowResult.label(text=li.val)
                        if decorResults//8%2:
                            rowOp = rowResult.row(align=True)
                            op = rowOp.operator(NttfOp.bl_idname, text="", icon='RESTRICT_VIEW_ON') #RESTRICT_VIEW_ON  FORWARD
                            op.who = repr(self)
                            op.opt = 'Warp'
                            op.dest = repr((fdsr.tbRef.name, li.inx, li.rex.span()))
                            rowOp.active = decorResults//16%2
                        rowResult.active = decorResults//2%2
                        scoDisp += 1
            if nttfDecorTable%2:
                colLy.box()
            if nttfDecorTotal:
                StencilTotalRow(prefs, colTotalTop if nttfDecorTotal>0 else colTotalBottom, ('PRESET', scoDisp), ('ALIGN_JUSTIFY', finder.scoTotAll), decor=1) #RADIOBUT_OFF  PRESET  TRACKER
            self.ProcAlertState(scoDisp)

list_classes += [NttfOp]
list_classes += [NodeTextblockTextFinder]
AddToSacat([ (2,NodeTextblockTextFinder) ], "Text", AtHomePoll)
list_clsToChangeTag += [NodeTextblockTextFinder]

class AddonPrefs(AddonPrefs):
    disclMnNttf: bpy.props.BoolProperty(name="DisclMnNttf", default=False)
    nttfItemsAlignment: bpy.props.BoolProperty(name="Alignment between elements", default=False)
    nttfDecorTable: bpy.props.IntProperty(name="Decor Table", default=2, min=0, max=3)
    nttfDecorTotal: bpy.props.IntProperty(name="Decor Total", default=1, min=-1, max=1)

list_clsToAddon.append(NodeTextblockTextFinder)

import random

def NcnUpdateCol(self, context):
    can = self.decorProp
    self.use_custom_color = can
    if can:
        col = self.col
        self.color = (col[0]**pw22, col[1]**pw22, col[2]**pw22)
class NodeColorNote(MntNodeRoot):
    bl_idname = 'MntNodeColorNote'
    bl_label = "Color note"
    bl_width_max = 256
    bl_width_min = 64
    bl_width_default = 140
    col: bpy.props.FloatVectorProperty(name="Color", size=3, soft_min=0, soft_max=1, subtype='COLOR', update=NcnUpdateCol)
    decorProp: bpy.props.BoolProperty(name="Decor Prop", default=True, update=NcnUpdateCol)
    decorHeight: bpy.props.IntProperty(name="Decor Height", default=3, min=2, max=6)
    nclass = 33#2
    def InitNode(self, context):
        self.col = (random.random(), random.random(), random.random()) #(0.628377, 0.849800, 0.916233)
    def DrawExtNode(self, context, colLy, prefs):
        AddNiceColorProp(colLy, self,'col')
        colLy.prop(self,'decorProp')
        colLy.prop(self,'decorHeight')
    def DrawNode(self, context, colLy, prefs):
        row = colLy.row()
        row.prop(self,'col', text="", emboss=not self.decorProp) #emboss==False для color prop -- это потрясающе!!
        #row.prop(self,'col', text="") if not self.decorProp else row.label() #Некликабельная версия.
        row.scale_y = 0.5*self.decorHeight

list_classes += [NodeColorNote]
AddToSacat([ (0,NodeColorNote) ], "Color", AtHomePoll)
list_tupleСlsToPublic += [(1, NodeColorNote)]
list_clsToChangeTag += [NodeColorNote]

dict_listSoldSkoLinks = {}

def RectRerouteWalker(skTar, skCur, isEve): #"Щепотка RANTO".
    if not skCur.is_output:#and skCur.node.type=='RETOUTE'
        skCur = skCur.node.outputs[0]
    for lk in dict_listSoldSkoLinks.get(skCur, []):
        lk.is_muted = isEve #Омг, почему в иви не работает?
        nd = lk.to_node
        if nd.type=='REROUTE':
            lk.to_socket.cache = skTar.cache
            lk.to_socket.node.outputs[0].cache = skTar.cache
            RectRerouteWalker(skTar, lk.to_socket, isEve)
        elif (lk.to_socket.bl_rna.properties.get('default_value'))and(lk.to_socket.bl_rna.properties['default_value'].is_array):
            try:
                lk.to_socket.default_value = (skTar.default_value[0], skTar.default_value[1], skTar.default_value[2], 1)
            except:
                pass #"Ну и хрен с тобой".
def NcnUpdatePublish(self, context): #А я-то надеялся, что Блендер может обрабатывать деревья с кастомными сокетами, если их bl_idname совпадают, или что-то похоже. Оказалось, что нет. Приходится засовывать вручную.
    isEve = bpy.context.scene.render.engine=='BLENDER_EEVEE' #В b4.1 без `bpy.` не работает.
    self.cache = (self.default_value[0]**pw22, self.default_value[1]**pw22, self.default_value[2]**pw22, 1)
    dict_listSoldSkoLinks.clear()
    for lk in self.id_data.links:
        dict_listSoldSkoLinks.setdefault(lk.from_socket, [])
        if (lk.is_valid)and(not lk.is_hidden):
            dict_listSoldSkoLinks[lk.from_socket].append(lk)
    for sk in self.node.outputs:
        if (sk.enabled)and(not sk.hide):
            RectRerouteWalker(sk, sk, isEve)

class NcnColSocket(bpy.types.NodeSocket):
    bl_idname = 'NcnColSocket'
    bl_label = "Color"
    default_value: bpy.props.FloatVectorProperty(name="Color", size=3, min=0, max=1, subtype='COLOR', update=NcnUpdatePublish)
    cache: bpy.props.FloatVectorProperty(name="Cache", size=4)
    def draw(self, context, layout, node, text):
        row = layout.row()
        row.prop(self,"default_value", text="")
        row.scale_y = 0.5*self.node.decorHeight
    def draw_color(self, context, node):
        return self.cache
    @classmethod
    def draw_color_simple(cls):
        return (0.8934110431855, 0.8934110431855, 0.43571415700134714, 1.0)

def NcnUpdateColCount(self, context):
    len = length(self.outputs)
    for cyc in range(len, self.colCount):
        self.outputs.new(NcnColSocket.bl_idname, "Color")
        self.outputs[-1].default_value = (random.random(), random.random(), random.random())
    for cyc in reversed(range(self.colCount, len)):
        self.outputs.remove(self.outputs[cyc])
class NodeColorNotepad(MntNodeRoot):
    bl_idname = 'MntNodeColorNotepad'
    bl_label = "Color Notepad"
    bl_width_max = 220
    bl_width_min = 40
    bl_width_default = 140
    colCount: bpy.props.IntProperty(name="Count", default=1, min=0, max=32, soft_min=1, soft_max=6, update=NcnUpdateColCount)
    decorHeight: bpy.props.IntProperty(name="Decor Height", default=2, min=2, max=4)
    nclass = 2 #Первый несуществующий, потому что '1' имеет обработку активного, и я хрен знает как оно работает.
    def InitNode(self, context):
        NcnUpdateColCount(self, context)
    def update(self):
        if self.outputs:
            NcnUpdatePublish(self.outputs[0], None)
    def DrawExtNode(self, context, colLy, prefs):
        colLy.prop(self,'decorHeight')
        colLy.prop(self,'colCount')

list_classes += [NcnColSocket]
list_classes += [NodeColorNotepad]
AddToSacat([ (1,NodeColorNotepad) ], "Color", AtHomePoll)
list_tupleСlsToPublic += [(2, NodeColorNotepad)]
list_clsToChangeTag += [NodeColorNotepad]

class NqleOp(bpy.types.Operator):
    bl_idname = 'mnt.node_op_nqe'
    bl_label = "NqleOp"
    bl_options = {'UNDO'}
    who: bpy.props.StringProperty()
    def execute(self, context):
        if self.who:
            ndRepr = eval(self.who)
            for ci in ndRepr.execs:
                ci.error = ""
                if ci.isActive:
                    try:
                        if ci.isTb:
                            if ci.tbPoi:
                                exec(ci.tbPoi.as_string(), globals(), locals())
                        elif ci.txtExec:
                            exec(ci.txtExec, globals(), locals())
                    except Exception as ex:
                        ci.error = str(ex)
        return {'FINISHED'}

def NqleUpdateResetSelfError(self, context):
    self.error = ""
def NqleUpdateResetErrors(self, context):
    for ci in self.execs:
        ci.error = ""

def NqleUpdateCount(self, context): #todo1 зашаблонить! #todo0 стоит ли защитить затирание данных?
    len = length(self.execs)
    for cyc in range(len, self.count):
        ci = self.execs.add()
        ci.name = str(cyc)
    for cyc in reversed(range(self.count, len)):
        self.execs.remove(cyc)
class NqleExecTxtTb(bpy.types.PropertyGroup):
    isActive: bpy.props.BoolProperty(name="Active", default=True, update=NqleUpdateResetSelfError)
    isTb: bpy.props.BoolProperty(name="Toggle", default=False, update=NqleUpdateResetSelfError)
    tbPoi: bpy.props.PointerProperty(name="Text Block", type=bpy.types.Text, update=NqleUpdateResetSelfError)
    txtExec: bpy.props.StringProperty(name="Exec", update=NqleUpdateResetSelfError)
    error: bpy.props.StringProperty(name="Error")

def NqleAddErr(where, inx, txt):
    row = where.row(align=True)
    if False:
        rowInx = row.row(align=True)
        rowInx.alignment = 'CENTER'
        rowInx.label(text=str(int(inx)+1)+":")
    row.label(text=txt, icon='ERROR')

class NodeQuickLayoutExec(MntNodeRoot):
    bl_idname = 'MntNodeQuickLayoutExec'
    bl_label = "Quick Layout Exec"
    bl_width_max = 2048
    bl_width_min = 64
    bl_width_default = 420
    execs: bpy.props.CollectionProperty(type=NqleExecTxtTb)
    count: bpy.props.IntProperty(name="Count of execs", min=0, max=32, soft_min=1, soft_max=6, default=1, update=NqleUpdateCount)
    method: bpy.props.EnumProperty(name="Method", default='LAYOUT', items=( ('LAYOUT',"As Layout",""), ('EXEC',"As Exec","") ), update=NqleUpdateResetErrors)
    isIgnoreErrors: bpy.props.BoolProperty(name="Ignore errors", default=False)
    isOnlyMatter: bpy.props.BoolProperty(name="Matter display only", default=False)
    decor: bpy.props.StringProperty(name="Decor")
    nclass = 8
    def draw_label(self):
        return "Quick "+("Layout" if self.method=='LAYOUT' else "Exec")
    def InitNode(self, context):
        self.count = 2
        self.execs[0].txtExec = "ly.prop(context.space_data.edit_tree.nodes.active, 'bl_idname')"
        self.execs[1].txtExec = "#bpy.ops.node.add_node('INVOKE_DEFAULT', type=context.node.execs[0].txtExec, use_transform=True)"
    def DrawExtNode(self, context, colLy, prefs):
        colLy.prop(self,'isOnlyMatter')
        colLy.row().prop(self,'method', expand=True)
        if self.method=='EXEC':
            AddNiceColorProp(colLy, self,'decor', align=True)
        colLy.prop(self,'count')
        colLy.prop(self,'isIgnoreErrors')
    def DrawNode(self, context, colLy, prefs):
        colListExs = colLy.column(align=True)
        canDisplayErrors = not self.isIgnoreErrors
        isLayMode = self.method=='LAYOUT'
        txt_alert = "exec() !"*prefs.allIsPlaceExecAlerts #todo рефакторить EvalAndAddPropExtended от сюда, int и передавать prefs.
        for ci in self.execs:
            if not self.isOnlyMatter:
                row = colListExs.row().row(align=True)
                rowEcAc = row.row(align=True)
                rowEcAc.prop(ci,'isActive', text="")
                rowEcAc.active = False #todo мб функцию для быстрого неактивного пропа.
                rowTgl = row.row(align=True)
                isTb = ci.isTb
                rowTgl.prop(ci,'isTb', text="", icon='GREASEPENCIL', emboss=True)#, invert_checkbox=isTb) #ADD  GREASEPENCIL
                rowTgl.active = False
                if canDisplayErrors:
                    row.alert = not not ci.error
                if (isLayMode)and(ci.isActive):
                    try:
                        if isTb:
                            if ci.tbPoi:
                                exec(ci.tbPoi.as_string(), globals(), locals()|{'ly':colLy})
                        elif ci.txtExec:
                            exec(ci.txtExec, globals(), locals()|{'ly':colLy})
                    except Exception as ex:
                        if canDisplayErrors:
                            NqleAddErr(colLy, ci.name, str(ex))
                            row.alert = True
                if isTb:
                    EvalAndAddPropExtended(row, ci,'tbPoi', "", txt_warning=txt_alert, alertWarn=True, canExec=False)
                else:
                    EvalAndAddPropExtended(row, ci,'txtExec', "", icon='SCRIPT', txt_warning=txt_alert, alertWarn=True, canExec=False)
        if not isLayMode:
            colLy.operator(NqleOp.bl_idname, text=self.decor if self.decor else "Exec").who = repr(self)
            if canDisplayErrors:
                for ci in self.execs:
                    if ci.error:
                        NqleAddErr(colLy, ci.name, ci.error)

#todo0 наверное стоит запариться с кешированием для exec'а.

list_classes += [NqleExecTxtTb, NqleOp]
list_classes += [NodeQuickLayoutExec]
AddToSacat([ (0,NodeQuickLayoutExec) ], "Script", AtHomePoll)
list_tupleСlsToPublic += [(5, NodeQuickLayoutExec)]
list_clsToChangeTag += [NodeQuickLayoutExec]

list_clsSolemn = []

def NsUpdateProcBg(self, context):
    def NsProcBg(hlState, alertState):
        if (alertState)and(any(self.alertColor)):
            dict_ndLastAlert[self] = alertState
            MnTimerUpdateSetAlertColor(self, None)
        elif self.propHlFromTheme:
            self.use_custom_color = (hlState)and(self.isHlFromTheme)
            props = self.propHlFromTheme.split(".")
            self.color = getattr(getattr(bpy.context.preferences.themes[0].user_interface, props[0]), props[1])[:3]
        else:
            self.use_custom_color = False
    exec(self.execBgState)

class MntNodeSolemn(MntNodeAlertness): #Они самое приятное, что я когда либо кодил.
    bl_width_max = 1024
    bl_width_min = 64
    bl_width_default = 253+math.pi #Потому что я так захотел; для "щепотки эстетики".
    #Пришлось делать "перехват" alertColor из class MntNodeAlertness, потому что иначе будут два timers.register(), и прочие прелести.
    alertColor: bpy.props.FloatVectorProperty(name="Alert color", default=(0.0, 0.0, 0.0), min=0, max=1, size=3, subtype='COLOR', update=NsUpdateProcBg)
    solemnName: bpy.props.StringProperty(name="Solemn Name", default="Ceremonial!")
    nclass = 8
    propHlFromTheme = ''
    def DrawExtPreChain(self, context, colLy):
        MntNodeAlertness.DrawExtPreChain(self, context, colLy)
        AddNiceColorProp(colLy, self,'solemnName', align=True)

class NodeSolemnBool(MntNodeSolemn):
    bl_idname = 'MntNodeSolemnBool'
    bl_label = "Solemn Bool"
    bool: bpy.props.BoolProperty(name="Bool", default=False, update=NsUpdateProcBg)
    alerting: bpy.props.BoolProperty(name="Alert trigger", default=False, update=NsUpdateProcBg)
    decor: bpy.props.IntProperty(name="Decor", default=1, min=0, max=7, soft_min=1, soft_max=3)
    isHlFromTheme: bpy.props.BoolProperty(name="Highlighting from theme", default=True, update=NsUpdateProcBg)
    propHlFromTheme = 'wcol_option.inner_sel'
    execBgState = "NsProcBg(self.bool, self.bool^self.alerting)" #О нет; но иначе 'match self.bl_idname: case'. Я выбрал exec(), как меньше из двух зол эстетики.
    def InitNode(self, context):
        self.bool = True
    def DrawExtNode(self, context, colLy, prefs):
        colLy.prop(self,'isHlFromTheme')
        colLy.prop(self,'alerting')
        colLy.prop(self,'decor')
    def DrawNode(self, context, colLy, prefs):
        decor = self.decor
        solemnName = self.solemnName
        colLy.prop(self,'bool', text=" " if (decor//2%2)and(not solemnName)and(not decor//4) else solemnName, icon=('CHECKBOX_HLT' if self.bool else 'CHECKBOX_DEHLT') if decor//2%2 else 'NONE', emboss=decor%2)
list_clsSolemn += [NodeSolemnBool]

class NodeSolemnFactor(MntNodeSolemn):
    bl_idname = 'MntNodeSolemnFactor'
    bl_label = "Solemn Factor"
    factor: bpy.props.FloatProperty(name="Factor", default=0.0, min=0, max=1, subtype='FACTOR', update=NsUpdateProcBg)
    alerting: bpy.props.IntProperty(name="Alert trigger", default=0, min=-1, max=1, update=NsUpdateProcBg)
    isHlFromTheme: bpy.props.BoolProperty(name="Highlighting from theme", default=True, update=NsUpdateProcBg)
    propHlFromTheme = 'wcol_numslider.item'
    execBgState = "NsProcBg(not self.factor==0.0, not( (self.factor==0.0)and(self.alerting<1)or(self.factor==1.0)and(self.alerting>-1) ))"
    def InitNode(self, context):
        self.factor = 0.5
    def DrawExtNode(self, context, colLy, prefs):
        colLy.prop(self,'isHlFromTheme')
        colLy.prop(self,'alerting')
    def DrawNode(self, context, colLy, prefs):
        colLy.prop(self, 'factor', text=self.solemnName)
list_clsSolemn += [NodeSolemnFactor]

class NodeSolemnInteger(MntNodeSolemn):
    bl_idname = 'MntNodeSolemnInteger'
    bl_label = "Solemn Integer"
    integer: bpy.props.IntProperty(name="Integer", default=0, update=NsUpdateProcBg)
    execBgState = "NsProcBg(self.integer, self.integer)"
    def DrawNode(self, context, colLy, prefs):
        colLy.prop(self, 'integer', text=self.solemnName)
list_clsSolemn += [NodeSolemnInteger]

class NodeSolemnFloat(MntNodeSolemn):
    bl_idname = 'MntNodeSolemnFloat'
    bl_label = "Solemn Float"
    float: bpy.props.FloatProperty(name="Float", default=0.0, step=10, update=NsUpdateProcBg)
    execBgState = "NsProcBg(self.float, self.float)"
    def DrawNode(self, context, colLy, prefs):
        colLy.prop(self, 'float', text=self.solemnName)
list_clsSolemn += [NodeSolemnFloat]

class NodeSolemnColor(MntNodeSolemn):
    bl_idname = 'MntNodeSolemnColor'
    bl_label = "Solemn Color"
    colour: bpy.props.FloatVectorProperty(name="Color", size=3, min=0, max=1, subtype='COLOR', update=NsUpdateProcBg) #Как ловко выкрутился от конфликта api, но с сохранением эстетики.
    decor: bpy.props.IntProperty(name="Decor", default=0, min=0, max=2)
    execBgState = "NsProcBg(any(self.colour), any(self.colour))"
    def InitNode(self, context):
        self.alertColor = (0.063010, 0.168269, 0.450786)
        self.colour = (0.166974, 0.293647, 0.587855)
        self.decor = 2
    def DrawExtNode(self, context, colLy, prefs):
        colLy.prop(self,'decor')
    def DrawNode(self, context, colLy, prefs):
        if not self.solemnName:
            colLy.prop(self,'colour', text="")
        else:
            decor = self.decor
            if not decor:
                colLy.prop(self,'colour', text=self.solemnName)
            elif decor==1:
                colLy.row(align=True).prop(self,'colour', text=self.solemnName)
            else:
                AddNiceColorProp(colLy, self,'colour', txt=self.solemnName)
list_clsSolemn += [NodeSolemnColor]

class NodeSolemnLayout(MntNodeSolemn):
    bl_idname = 'MntNodeSolemnLayout'
    bl_label = "Solemn Layout"
    txt_exec: bpy.props.StringProperty(name="Text exec")
    def InitNode(self, context):
        self.txt_exec = "ly.row().prop(context.scene.render, 'engine', expand=True)"
    def DrawNode(self, context, colLy, prefs):
        colLy.prop(self, 'txt_exec', text="", icon='SCRIPT')
        exec(self.txt_exec, globals(), locals()|{'ly':colLy})
list_clsSolemn += [NodeSolemnLayout]

if False:
    #Dynamic solemn:
    def NsUpdateNdsExec(self, context):
        text = self.txt_exec
        bpy.utils.unregister_class(NodeDynamicSolemnDyn)
        try:
            exec(execNodeDynamicSolemn.replace("#@", text))
        except:
            exec(execNodeDynamicSolemn)
        bpy.utils.register_class(NodeDynamicSolemnDyn)
        MnUpdateNclass(self)
    class NodeDynamicSolemnRoot(MntNodeSolemn):
        bl_idname = 'MntNodeDynamicSolemn'
        txt_exec: bpy.props.StringProperty(name="Exec", update=NsUpdateNdsExec)
        isOnlyMatter: bpy.props.BoolProperty(name="Matter display only", default=False, update=NsUpdateProcBg)
        def InitNode(self, context):
            self.txt_exec = "abc: bpy.props.FloatVectorProperty(name=\"Vec4\", size=5, subtype='COLOR')"
    #Получилось вяло, и не "сохранятеся". Неплохо было бы придумать, как сделать их разными для разных нод в рамках одного класса. Не могу допетрить, как работают классические "Custom Properties".
    class NodeDynamicSolemnMain(NodeDynamicSolemnRoot):
        bl_label = "Custom Solemn"
        bl_width_default = 317+math.pi
        def DrawNode(self, context, colLy, prefs):
            colLy.label(text="Dynamically, for all in class", icon="INFO")
            EvalAndAddPropExtended(colLy, self,'txt_exec', "", icon='SCRIPT', txt_warning="exec() !"*prefs.allIsPlaceExecAlerts, alertWarn=True, canDraw=not self.isOnlyMatter, canExec=False)
            for li in NodeDynamicSolemnDyn.__annotations__:
                if hasattr(self, li):
                    colLy.prop(self, li)
    execNodeDynamicSolemn = """
    global NodeDynamicSolemnDyn
    class NodeDynamicSolemnDyn(NodeDynamicSolemnMain):
        #@
        pass"""
    exec(execNodeDynamicSolemn)
    list_classes += [NodeDynamicSolemnDyn]
    list_clsToChangeTag += [NodeDynamicSolemnDyn]


list_classes += list_clsSolemn
for cyc, li in enumerate(list_clsSolemn):
    AddToSacat([(cyc,li)], "Solemn", AtHomePoll)
list_clsToChangeTag += list_clsSolemn

class NodeUvManager(MntNodeWithOnlyMatter):
    bl_idname = 'MntUvManager'
    bl_label = "UV Manager"
    bl_width_max = 2048
    bl_width_min = 256
    bl_width_default = 448
    filterMh: bpy.props.StringProperty(name="filterMh", default="")
    filterUv: bpy.props.StringProperty(name="filterUv", default="")
    isHierarchy: bpy.props.BoolProperty(name="Display as hierarchy", default=False)
    displayActiveRender: bpy.props.IntProperty(name="Display active render", default=0, min=0, max=2)
    nclass = 3
    def InitNode(self, context):
        self.filterMh = ".*"
        self.filterUv = ".*"
        #self.alertColor = (0.005556, 0.105280, 0.094881)
    def DrawExtNode(self, context, colLy, prefs):
        colLy.prop(self,'isHierarchy')
        colLy.prop(self,'displayActiveRender')
    def DrawNode(self, context, colLy, prefs):
        colFilters = colLy.column(align=True)
        isNotOnlyMatter = not self.isOnlyMatter
        if not(patrUv:=StencilAddFilterProp(self, prefs, colFilters.row(), prop='filterUv', ico='UV', canDraw=isNotOnlyMatter)):
            return
        if not(patrMh:=StencilAddFilterProp(self, prefs, colFilters, prop='filterMh', ico='MESH_DATA', canDraw=isNotOnlyMatter)):
            return
        colLy.box()
        scoUv = 0
        scoMh = 0
        totUv = 0
        displayActiveRender = self.displayActiveRender
        if self.isHierarchy:
            colList = colLy.column(align=True)
            for mh in bpy.data.meshes:
                if patrMh.search(mh.name):
                    len = length(mh.uv_layers)
                    totUv += len
                    if [True for uv in mh.uv_layers if patrUv.search(uv.name)]:
                        box = colList.row().box()
                        col = box.column(align=True)
                        col.row().prop(mh,'name', text="", icon='MESH_DATA')
                        row = col.row(align=True)
                        row.label(icon='BLANK1')
                        col = row.column(align=True)
                        can = (len>1)or(displayActiveRender!=1)
                        for uv in mh.uv_layers:
                            if patrUv.search(uv.name):
                                ico = 'RESTRICT_RENDER_OFF' if uv.active_render else 'RESTRICT_RENDER_ON'
                                row = col.row(align=True)
                                row.prop(uv,'name', text="", icon='UV')
                                if (can)and(displayActiveRender):
                                    row.prop(uv,'active_render', text="", icon=ico, emboss=False)
                                scoUv += 1
                    scoMh += 1
        else:
            rowList = colLy.row(align=True)
            colUv = rowList.column(align=True)
            colAc = rowList.column(align=True)
            colMh = rowList.row().column(align=True)
            for mh in bpy.data.meshes:
                if patrMh.search(mh.name):
                    can = (length(mh.uv_layers)>1)or(displayActiveRender!=1)
                    for uv in mh.uv_layers:
                        if patrUv.search(uv.name):
                            ico = 'RESTRICT_RENDER_OFF' if uv.active_render else 'RESTRICT_RENDER_ON'
                            colUv.prop(uv,'name', text="", icon='UV')
                            if displayActiveRender:
                                if can:
                                    colAc.prop(uv,'active_render', text="", icon=ico, emboss=False)
                                else:
                                    colAc.label(icon='BLANK1')
                            colMh.prop(mh,'name', text="", icon='MESH_DATA')
                            scoUv += 1
                        totUv += 1
                    scoMh += 1
        StencilTotalRow(prefs, colLy, ('MESH_DATA', scoMh, length(bpy.data.meshes)), " >> ", ('UV', scoUv, totUv), decor=1)
        self.ProcAlertState(scoUv)

list_classes += [NodeUvManager]
AddToSacat([ (0,NodeUvManager) ], "Managers", AtHomePoll)
list_clsToChangeTag += [NodeUvManager]

dict_editorIcos = {'ShaderNodeTree':    'NODE_MATERIAL',
                   'CompositorNodeTree':'NODE_COMPOSITING',
                   'GeometryNodeTree':  'GEOMETRY_NODES',
                   'TextureNodeTree':   'NODE_TEXTURE',
                   'NodeTreeUndefined': 'QUESTION' }

class NgdfSearch:
    def __init__(self):
        self.countDupli = 0
        self.countNodes = 0
        self.countLinks = 0
        self.list_ng = []

class NgdfDetector:
    def __init__(self):
        self.countFacts = 0
        self.list_all = []

dict_ngdfDetector = {}

class NgdfOp(bpy.types.Operator):
    bl_idname = 'mnt.node_op_ngdf'
    bl_label = "NamOp"
    who: bpy.props.StringProperty()
    opt: bpy.props.StringProperty()
    def execute(self, context):
        if self.who:
            ndRepr = eval(self.who)
            match self.opt:
                case 'FindRequest':
                    list_result = dict_ngdfDetector[ndRepr]
                    list_result.clear()
                    dict_ndlk = {}
                    for ng in bpy.data.node_groups:
                        #if ng.bl_idname==ManagersTree.bl_idname: continue
                        key = (length(ng.nodes), length(ng.links))
                        dict_ndlk.setdefault(key, [])
                        dict_ndlk[key].append(ng)
                    scoFound = 0
                    for di in dict_ndlk:
                        list_ng = dict_ndlk[di]
                        if length(list_ng)>1:
                            dict_matter = {}
                            for li in list_ng:
                                key = tuple(sorted([nd.bl_idname for nd in li.nodes]))
                                if not dict_matter.get(key, None):
                                    dict_matter[key] = []
                                dict_matter[key].append(li)
                            for di in dict_matter:
                                list_matter = dict_matter[di]
                                if length(list_matter)>1:
                                    list_result += list_matter
        return {'FINISHED'}

def NgdfAddItem(where, ng):
    def AddOp(where, enabled, ico, pressed, opt, who, txt=""):
        row = where.row(align=True)
        row.enabled = enabled
        op = row.operator(NgdfOp.bl_idname, text=txt, icon=ico, depress=pressed)
        return op
    row0 = where.row(align=True)
    if ng.users.numerator==0:
        row0.label(text="", icon='DRIVER_TRANSFORM')
    row0.prop(ng,'name', text="", icon=dict_editorIcos.get(ng.bl_idname,'NODETREE'))
    rowa = row0.row(align=True)
    rowa.prop(ng,'use_fake_user', text="")
    rowa.active = False
    AddOp(row0, True, 'TRASH', False, 'Del', ng.name)
class NodeNgDuplicateDetector(MntNodeAlertness):
    bl_idname = 'MntNodeNgDuplicateDetector'
    bl_label = "Nodegroups duplicate finder"
    bl_icon = 'DUPLICATE' #Как удобно.
    bl_width_max = 2048
    bl_width_min = 256
    bl_width_default = 512
    def DrawNode(self, context, colLy, prefs):
        dict_ngdfDetector.setdefault(self, NgdfDetector())
        colList = colLy.column(align=True)
        rowTotal = colList.row(align=True)
        AddThinSep(colList, 0.5)
        for li in dict_ngdfDetector[ndRepr].list_all:
            box = colList.row().box()
            colItem = box.column(align=True)
            row = colItem.row(align=True)
            row.label( text="+"+str(length(list_mat)-1)+" found: "+str(length(list_ng[0].nodes))+" nodes "+str(length(list_ng[0].links))+" links " )
            row.active = False
            for li in list_mat:
                NgdfAddItem(colItem, li)
        count = dict_ngdfDetector[ndRepr].countFacts
        if count:
            StencilTotalRow(prefs, rowTotal, ('DUPLICATE', count), decor=1)
        else:
            rowTotal.label(text="Clear!", icon='INFO')
        self.ProcAlertState(count)

#list_classes += [NgdfOp]
#list_classes += [NodeNgDuplicateDetector]
#AddToSacat([ (2,NodeNgDuplicateDetector) ], "Special", AtHomePoll)
#list_clsToChangeTag += [NodeNgDuplicateDetector]

def NjfTypeItems(self, context):
    if self.fieldType=='BOOLEAN':
        return ( ('AND',"And",""), ('OR',"Or","") )
    else:
        return ( ('MAX',"Maximum",""), ('ADD',"Addition",""), ('MIN',"Minimum","") )

def NjfUpdateType(self, context):
    for puts in [self.inputs, self.outputs]:
        for sk in puts:
            sk.enabled = sk.type==self.fieldType
    if (self.fieldType=='BOOLEAN')and(self.method==''):
        self.method = 'AND'
    #self.nclass = 4 if self.fieldType=='VECTOR' else 8
    #MnUpdateNclass(self)

class NodeJoinField(MntNodeRoot):
    bl_idname = 'MntNodeJoinField'
    bl_label = "Join Field"
    fieldType: bpy.props.EnumProperty(name="Type", default='VALUE', items=( ('VALUE',"Float",""), ('VECTOR',"Vector",""), ('BOOLEAN',"Boolean","") ), update=NjfUpdateType)
    method: bpy.props.EnumProperty(name="Method", default=0, items=NjfTypeItems)
    nclass = 8
    def draw_label(self):
        return "Join "+self.bl_rna.properties['fieldType'].enum_items[self.fieldType].name
    def InitNode(self, context):
        list_blids = ['NodeSocketFloat', 'NodeSocketVector', 'NodeSocketBool']
        for li in list_blids:
            self.outputs.new(li, "Value")
        for li in list_blids:
            sk = self.inputs.new(li, "Values")
            BNodeSocket.get_fields(sk).flag = 2048
            sk.hide_value = True
        self.fieldType = 'VALUE'
    def DrawNode(self, context, colLy, prefs):
        colLy.prop(self,'fieldType', text="")
        colLy.prop(self,'method', text="")

list_classes += [NodeJoinField]
AddToSacat([ (0,NodeJoinField) ], "Exotic", AtHomePoll)
list_clsToChangeTag += [NodeJoinField]


def NeTimerInit(nd):
    def GetAllCanonSkIds():
        list_result = []
        set_ignored = {'NodeSocket', 'NodeSocketStandard'}
        for li in dir(bpy.types):
            if (li.startswith('NodeSocket'))and(li not in set_ignored)and(length([True for ch in li if ord(ch) in range(65,91)])==3):
                list_result.append( (li, getattr(bpy.types, li).bl_rna.name.replace(" Node Socket", "")) )
        return list_result
    nd.doneExtend = True
    match nd.extendKey:
        case 'AllSks':
            for id, nm in GetAllCanonSkIds():
                nd.outputs.new(id, nm)
                nd.inputs.new(id, nm).hide_value = True
            nd.nodeLabel = "All sockets"
        case 'EveryoneMultiinputs':
            def AddMi(id, nm):
                sk = nd.inputs.new(id, nm)
                BNodeSocket.get_fields(sk).flag = 2048
                sk.hide_value = True
            for id, nm in GetAllCanonSkIds():
                AddMi(id, nm)
            AddMi('Undef', "Undef")
            nd.nodeLabel = "Multiinputs"
        case 'SkTests':
            def AddHideSk(puts, id, name):
                sk = puts.new(id, name)
                sk.hide_value = True
                return sk
            for puts in [nd.inputs, nd.outputs]:
                AddHideSk(puts, 'NodeSocketVector', "Canon")
                AddHideSk(puts, NstSocketTest0.bl_idname, "Black").rawcol = (0, 0, 0, 1)
                AddHideSk(puts, NstSocketTest0.bl_idname, "Gray").rawcol = (0.5, 0.5, 0.5, 1.0)
                AddHideSk(puts, NstSocketTest0.bl_idname, "Transparent").rawcol = (1.0, 0.5, 0.0, 0.0)
                AddHideSk(puts, NstSocketTest0.bl_idname, "Dc Dcs").rawcol = (1.0, 1.0, 0.5, 1.0)
                AddHideSk(puts, NstSocketTest0.bl_idname, "High1").rawcol = (2.0, 1.0, 0.5, 1.0)
                AddHideSk(puts, NstSocketTest0.bl_idname, "High2").rawcol = (2.0, 1.5, 1.0, 0.5)
                AddHideSk(puts, NstSocketTest1.bl_idname, "Neg").rawcol = (-1, -1, -1, 1)
                AddHideSk(puts, NstSocketTest1.bl_idname, "NegAl").rawcol = (0.125, 1, 0.0625, -1)
                AddHideSk(puts, NstSocketTest2.bl_idname, "Dcs").rawcol = (0.5, 0.5, 0.5, 0.5)
                AddHideSk(puts, NstSocketTest3.bl_idname, "Nothing")
                AddHideSk(puts, 'Undef', "Undef")
    
class NodeExtender(MntNodeRoot):
    bl_idname = 'MntNodeExtender'
    bl_label = "Node Extender"
    doneExtend: bpy.props.BoolProperty(name="DoneExtend", default=False)
    extendKey: bpy.props.StringProperty(name="ExtendKey", default="")
    nodeLabel: bpy.props.StringProperty(name="Node label", default="")
    nclass = 2
    def draw_label(self):
        return self.nodeLabel
    def DrawNode(self, context, colLy, prefs):
        if not self.doneExtend:
            bpy.app.timers.register(functools.partial(NeTimerInit, self))

list_classes += [NodeExtender]
AddToSacat([ (1,NodeExtender) ], "Self", AtHomePoll)
AddToSacat([ (1,NodeExtender, {'extendKey':repr('AllSks')}, "All sockets") ], "Exotic", AtHomePoll)
AddToSacat([ (2,NodeExtender, {'extendKey':repr('SkTests')}, "Socket test") ], "Exotic", AtHomePoll)
AddToSacat([ (3,NodeExtender, {'extendKey':repr('EveryoneMultiinputs')}, "Multiinputs") ], "Exotic", AtHomePoll)
list_clsToChangeTag += [NodeExtender]

class NstSocketTest(bpy.types.NodeSocket):
    bl_label = "Test"
    rawcol: bpy.props.FloatVectorProperty(name="Raw", size=4, default=(1,1,1,1), min=-1, max=2, subtype='COLOR')
    def draw(self, context, layout, node, text):
        layout.label(text=self.name)
class NstSocketTestDc(NstSocketTest):
    def draw_color(self, context, node):
        return self.rawcol
class NstSocketTestCs(NstSocketTest):
    @classmethod
    def draw_color_simple(cls):
        return (0.5, 0.5, 0.5, 0.5)
class NstSocketTest0(NstSocketTestDc, NstSocketTestCs):
    bl_idname = 'NstSocketTest0'
class NstSocketTest1(NstSocketTestDc):
    bl_idname = 'NstSocketTest1'
class NstSocketTest2(NstSocketTestCs):
    bl_idname = 'NstSocketTest2'
class NstSocketTest3(NstSocketTest):
    bl_idname = 'NstSocketTest3'

list_classes += [NstSocketTest0, NstSocketTest1, NstSocketTest2, NstSocketTest3]

def Prefs():
    return bpy.context.preferences.addons[thisAddonName].preferences
class AddonPrefs(AddonPrefs):
    debugLy: bpy.props.BoolProperty(name="Debug draw", default=False)
    allIsPlaceExecAlerts: bpy.props.BoolProperty(name="Place exec alerts", default=True)
    decorTotalRow: bpy.props.IntProperty(name="Decor Total Row", default=21, min=0, max=63)
    allIsBrightFilters: bpy.props.BoolProperty(name="Bright filters", default=True)
    def draw(self, context):
        colLy = self.layout.column()
        box = GetLabeledDoubleBox(colLy, "Main", active=True, alignment='CENTER')
        colBox = box.column(align=True)
        #colBox.column().box()
        colBox.prop(self,'debugLy')
        colBox.prop(self,'allIsPlaceExecAlerts')
        #colBox.column().box()
        AddThinSep(colBox, 0.5) #Немножко декора; оступы меж двумя галками складываются; а так же отступ от (потенциальной) коробки.
        colBox.prop(self,'decorTotalRow')
        colBox.prop(self,'allIsBrightFilters')
        for cls in list_clsToAddon:
            cls.DrawInAddon(cls, context, colLy, self)

list_classes += [AddonPrefs]

def DoRegOldBlids():
    class MntNodeOldBlids(MntNodeRoot):
        def DrawPreChain(self, context, colLy):
            for li in self.__annotations__:
                colLy.prop(self, li)
    # ===================================================================== FastNote
    class VrFastNote(MntNodeOldBlids):
        bl_idname = 'FastNote'
        bl_label = "FastNote"
        note: bpy.props.StringProperty(name="Note body", default="")
    bpy.utils.register_class(VrFastNote)
    # ===================================================================== Notepad
    class VrNotepadLine(bpy.types.PropertyGroup):
        txt_line: bpy.props.StringProperty(name="NpLTB", default="")
    bpy.utils.register_class(VrNotepadLine)
    class VrNotepad(MntNodeOldBlids):
        bl_idname = 'Notepad'
        bl_label = "Notepad"
        memo: bpy.props.CollectionProperty(type=VrNotepadLine)
        def DrawNode(self, context, colLy, prefs):
            for ci in self.memo:
                colLy.prop(ci,'txt_line', text="")
    bpy.utils.register_class(VrNotepad)
    # ===================================================================== ItemPropPyManager
    class VrTablePropFilter(bpy.types.PropertyGroup):
        txt_prop: bpy.props.StringProperty(name="Prop Id", default="")
        txt_filter: bpy.props.StringProperty(name="Prop Filter", default="")
    bpy.utils.register_class(VrTablePropFilter)
    class VrNodeItemPropPyManager(MntNodeOldBlids):
        bl_idname = 'ItemPropPyManager'
        bl_label = "Items Prop Manager"
        path:    bpy.props.StringProperty(name="Path",    default="")
        props:   bpy.props.StringProperty(name="Props",   default="")
        precomp: bpy.props.StringProperty(name="Precomp", default="")
        filters: bpy.props.CollectionProperty(type=VrTablePropFilter)
        def DrawNode(self, context, colLy, prefs):
            for ci in self.filters:
                colLy.prop(ci,'txt_prop')
                colLy.prop(ci,'txt_filter')
    bpy.utils.register_class(VrNodeItemPropPyManager)
    # ===================================================================== PropsNamePyViewer
    class VrNodePropsNameViewer(MntNodeOldBlids):
        bl_idname = 'PropsNamePyViewer'
        bl_label = "Props Name Viewer"
        path:   bpy.props.StringProperty(name="Path",   default="")
        filter: bpy.props.StringProperty(name="Filter", default="")
    bpy.utils.register_class(VrNodePropsNameViewer)
    # ===================================================================== ScriptItemRunner
    class VrNodeScriptItemRunner(MntNodeOldBlids):
        bl_idname = 'ScriptItemRunner'
        bl_label = "Script Item Runner"
        tbPoi: bpy.props.PointerProperty(name="Text Block", type=bpy.types.Text)
        path:    bpy.props.StringProperty(name="path",    default="")
        filter:  bpy.props.StringProperty(name="filter",  default="")
        asName:  bpy.props.StringProperty(name="asName",  default="")
        oneLine: bpy.props.StringProperty(name="oneLine", default="")
    bpy.utils.register_class(VrNodeScriptItemRunner)
    # ===================================================================== TextBlockTextFinder
    class VrNodeTextBlockTextFinder(MntNodeOldBlids):
        bl_idname = 'TextBlockTextFinder'
        bl_label = "Textblock LineText Finder"
        regex: bpy.props.StringProperty(name="RegEx", default="")
        tbPoi: bpy.props.PointerProperty(name="Text Block", type=bpy.types.Text)
        isDisplayAsProp: bpy.props.BoolProperty(name="Display as prop", default=True)
    bpy.utils.register_class(VrNodeTextBlockTextFinder)

class MntOpOldBlids(bpy.types.Operator):
    bl_idname = 'mnt.node_op_oldblids'
    bl_label = "OldBlids"
    bl_options = {'UNDO'}
    def execute(self, context):
        DoRegOldBlids()
        return {'FINISHED'}
list_classes += [MntOpOldBlids]

list_tupleСlsToPublic.sort(key=lambda a:a[0])

isDataOnRegisterDoneTgl = True

@bpy.app.handlers.persistent
def DataOnRegister(dummy, d):
    if isDataOnRegisterDoneTgl:
        MnUpdateAllNclassFromTree() #Пока что это наилучший вариант.

def register():
    bpy.app.handlers.load_post.append(DataOnRegister)
    for li in list_classes:
        bpy.utils.register_class(li)
    RegisterNodeCategories()
def unregister():
    for li in list_classes:
        bpy.utils.unregister_class(li)
    UnregisterNodeCategories()

if __name__=="__main__":
    register()
    MnUpdateAllNclassFromTree(False)
