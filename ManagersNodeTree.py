bl_info = {'name':"ManagersNodeTree", 'author':"ugorek",
           'version':(2,0,7), 'blender':(4,0,0), #2023.11.22
           'description':"For .blend and other high level management.",
           'location':"NodeTreeEditor",
           'warning':"Имеет неизведанным образом ненулевой риск (ненулевого) повреждения данных. Будьте аккуратны и делайте бэкапы.",
           'category':"System",
           'wiki_url':"https://github.com/ugorek000/ManagersNodeTree/wiki", 'tracker_url':"https://github.com/ugorek000/ManagersNodeTree/issues"}
thisAddonName = bl_info['name']

from builtins import len as length
import bpy, re
import math
import nodeitems_utils

pw22 = 1/2.2

list_classes = []
list_clsToDrawAdn = []

class AddonPrefs(bpy.types.AddonPreferences):
    bl_idname = thisAddonName

dict_ndLastAlert = {}


def GetDicsIco(tgl):
    return 'DISCLOSURE_TRI_DOWN' if tgl else 'DISCLOSURE_TRI_RIGHT'
#def GetCheckIco(tgl):
#    return 'CHECKBOX_HLT' if tgl else 'CHECKBOX_DEHLT'

#def GetIcoFromObj(ob):
#    txt = ob.type.upper()
#    return {'MESH':'OBJECT'}.get(txt, txt)+'_DATA'

def AddToRegAndAddToSacat(list_ofClass, placeToInx, txtName, txtPoll):
    for li in list_ofClass:
        list_classes.append(li[1])
    AddToSacat(list_ofClass, placeToInx, txtName, txtPoll)

class ManagersTree(bpy.types.NodeTree):
    """For .blend and other high level management"""
    bl_idname = 'ManagersNodeTree'
    bl_label = "Managers Node Tree"
    bl_icon = 'FILE_BLEND'

list_classes += [ManagersTree]

class MntPadDraw(): #todo1 протестить что если без.
    def DrawExtNode(self,context,colLy):pass
    def DrawNode(self,context,colLy):pass
    def DrawExtPreChain(self,context,colLy):pass
    def DrawPreChain(self,context,colLy):pass
class MntPreChainBase(bpy.types.Node, MntPadDraw):
    def draw_buttons_ext(self, context, layout):
        colLy = layout.column()
        self.DrawExtPreChain(context, colLy)
        self.DrawExtNode(context, colLy)
    def draw_buttons(self, context, layout):
        colLy = layout.column()
        self.DrawPreChain(context, colLy)
        self.DrawNode(context, colLy)
class MntNodeRoot(MntPreChainBase):
    def DrawExtPreChain(self, context, colLy):
        colLy.prop(self,'width', text="Node width", slider=True)
    def DrawPreChain(self, context, colLy):
        AddThinSep(colLy, .1) #!.
def UpdateAlertColor(self, context):
    self.use_custom_color = (dict_ndLastAlert[self])and(any(self.alertColor))
    col = self.alertColor
    self.color = (col[0]**pw22, col[1]**pw22, col[2]**pw22)
class MntNodeAlertness(MntNodeRoot, MntPreChainBase):
    alertColor: bpy.props.FloatVectorProperty(name="Alert color", default=(0.0, 0.0, 0.0), min=0, max=1, size=3, subtype='COLOR', update=UpdateAlertColor)
    def DrawExtPreChain(self, context, colLy):
        MntNodeRoot.DrawExtPreChain(self, context, colLy)
        colLy.row().prop(self,'alertColor')
    def DrawPreChain(self, context, colLy):
        dict_ndLastAlert.setdefault(self, False)
        MntNodeRoot.DrawPreChain(self, context, colLy)
    def ProcAlertState(self, dataState):
        alertState = not not dataState
        if alertState!=dict_ndLastAlert[self]:
            dict_ndLastAlert[self] = alertState
            bpy.app.timers.register(functools.partial(UpdateAlertColor, self, None))

class AnyPoll(nodeitems_utils.NodeCategory): #Ждёт своего часа; наверное. todo
    @classmethod
    def poll(cls, context):
        return True
class IsManagerNodeTreePoll(nodeitems_utils.NodeCategory):
    @classmethod
    def poll(cls, context):
        return context.space_data.tree_type==ManagersTree.bl_idname
class IsNotManagerNodeTreePoll(nodeitems_utils.NodeCategory):
    @classmethod
    def poll(cls, context):
        return context.space_data.tree_type!=ManagersTree.bl_idname

dict_tupleShiftAList = {}

def AddToSacat(list_ofClass, placeToInx, txtName, txtPoll): #"Sacat" = "ShiftA Category".
    if dict_tupleShiftAList.get(txtName, None) is None:
        dict_tupleShiftAList[txtName] = [placeToInx, txtPoll, []]
    dict_tupleShiftAList[txtName][2] += [(li[0], li[1].bl_idname) for li in list_ofClass]

def RegisterNodeCategories():
    list_nodeCategories = []
    for cyc, li in enumerate(sorted( dict_tupleShiftAList.items(), key=lambda a: a[1][0] )):
        Poll = eval(li[1][1])
        txt = li[0]
        list_items = sorted(li[1][2], key=lambda a: a[0])
        list_nodeCategories.append(Poll(txt.replace(" ", ""), #Заметка: так же не должно оканчиваться на "_".
                                        txt.replace("_", ""),
                                        items=[nodeitems_utils.NodeItem(li[1]) for li in list_items]))
    try:
        nodeitems_utils.register_node_categories('CUSTOM_NODES', list_nodeCategories)
    except:
        nodeitems_utils.unregister_node_categories('CUSTOM_NODES')
        nodeitems_utils.register_node_categories('CUSTOM_NODES', list_nodeCategories)
def UnregisterNodeCategories():
    nodeitems_utils.unregister_node_categories('CUSTOM_NODES')


def PlacePropColor(where, who, prop):
    row = where.row()
    rowLabel = row.row()
    rowLabel.alignment = 'LEFT'
    rowLabel.label(text=who.bl_rna.properties[prop].name+":")
    row.alignment = 'EXPAND'
    row.prop(who, prop, text="")

def ToggleRegMnnPanel(self, context):
    if self.aMnnPanel:
        bpy.utils.register_class(PanelManagerNodesNode)
    else:
        bpy.utils.unregister_class(PanelManagerNodesNode)
class PanelManagerNodesNode(bpy.types.Panel):
    bl_idname = 'UU_PT_ManagerNodesNode'
    bl_label = "ManagerNodes Node"
    bl_space_type = 'NODE_EDITOR'
    bl_region_type = 'UI'
    bl_order = 256
    @classmethod
    def poll(cls, context):
        return context.space_data.tree_type==ManagersTree.bl_idname #!.
    def draw(self, context):
        colLy = self.layout.column()
        tree = context.space_data.edit_tree
        aNd = tree.nodes.active
        if aNd:
            colNd = GetLabeledDoubleBox(colLy, aNd.bl_label, 'NODE').column()#align=True)
            colNd.prop(aNd,'width', text="Node width", slider=True)
            if hasattr(aNd,'alertColor'):
                PlacePropColor(colNd.row(), aNd,'alertColor')
            if hasattr(context.active_node, "DrawExtNode"):
                aNd.DrawExtNode(context, colLy)
        else:
            AddBoxLabelDir(colLy, "", 'NODE', active=False)

def AddThinSep(where, scaleY=0.25, scaleX=1.0):
    row = where.row(align=True)
    row.separator()
    row.scale_x = scaleX
    row.scale_y = scaleY

#def AddDiscProp(where, who, prop, txt=None, emb=True):
#    tgl = getattr(who, prop)
#    where.prop(who, prop, icon='DISCLOSURE_TRI_DOWN' if tgl else 'DISCLOSURE_TRI_RIGHT', invert_checkbox=tgl, text=txt, emboss=emb)
#    return tgl

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

#def AddLabelBoxIco(where, txt, tgl=True, icon='NONE', isAddThinSep=False): #Выглядит красиво, но кривит внешний контекст!
#    isHasIcon = icon!='NONE'
#    if isHasIcon:
#        row = where.row()
#        row.scale_y = 1.05
#        row.ui_units_y = 0.0000001 #todo ??
#        row.label(icon=icon)
#        row.active = False
#    box = where.box()
#    box.scale_y = .55
#    row = box.row()
#    row.active = tgl
#    row.label(text=txt*(not isHasIcon), icon='BLANK1' if isHasIcon else 'NONE')
#    if isAddThinSep:
#        where.separator()

#def AddEpicLabel(where, txt, cou=3, tgl=False, isBoxBg=True):
#    def Inner(where):
#        colRoot = where.column(align=True)
#        colRoot.active = tgl
#        rowMatter = (colRoot.box() if isBoxBg else colRoot).row()
#        rowMatter.alignment = 'CENTER'
#        rowMatter.label(text=txt)
#        rowMatter.scale_y = 0.5*(cou-isBoxBg)
#    rowRoot = where.column(align=True)
#    colMain = rowRoot.column(align=True)
#    colMain.alignment = 'CENTER'
#    colMain.box()
#    rowMiddle = colMain.row(align=True)
#    colBox = rowMiddle.column(align=True)
#    for cyc in range(cou):
#        colBox.box()
#    colCenter = rowMiddle.column(align=True)
#    rowCenter = colCenter.row(align=True)
#    Inner(colCenter)
#    colBox = rowMiddle.column(align=True)
#    for cyc in range(cou):
#        colBox.box()
#    colMain.box()

def GetNodeBoxDiscl(where, who, prop, self):
    return GenDisclLabeledDoubleBox(where, who, prop, self.bl_label+" Node")
    return GenDisclLabeledDoubleBox(where, who, prop, "Node "+self.bl_label) #todo1

#todo1: уникальных к своим.

def AddWarningLabel(where, text, alert=False):
    rowLabel = where.row(align=True)
    rowIco = rowLabel.row(align=True)
    rowIco.active = False
    rowIco.alert = alert
    rowIco.label(icon='ERROR')
    rowLabel.alignment = 'LEFT'
    rowLabel.label(text=" "+text)
def EvalAndAddPropExtended(where, who, prop, txt_eval, locals=None, txt="", fixWidth=48, txt_warning="", alertWarn=False, icon='NONE'):
    col = where.column(align=True)
    row = col.row(align=True)
    rowOther = row.row(align=True)
    rowOther.alignment = 'LEFT'
    rowProp = rowOther.row(align=True)
    rowProp.prop(who, prop, text=txt, icon=icon)
    rowProp.ui_units_x = fixWidth
    if txt_warning:
        AddWarningLabel(rowOther, txt_warning, alert=alertWarn)
    try:
        result = eval(txt_eval if txt_eval else 'None', globals(), locals)
        return True, result
    except Exception as ex:
        col.label(text=str(ex), icon='ERROR')
        return False, None
def StencilAddFilterProp(self, where, prop='filter', ico=None): #todo1: пронести путь prefs'ов во все.
    row0 = where.row(align=True)
    row0.active = Prefs().allIsBrightFilters
    if ico:
        row1 = row0.row(align=True)
        row1.label(icon=ico)
        row1.active = False
    evaled = EvalAndAddPropExtended(row0, self, prop, f"re.compile(var)", locals={'var':getattr(self, prop)}, icon='SORTBYEXT')
    return evaled[1] if evaled[0] else None


def StencilTotalRow(where, *tupleDataIcos, decor=0):
    box = GetLbBoxRaw(where.row() if decor else where)
    rowMain = box.row(align=True)
    decorTotalRow = Prefs().decorTotalRow
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
    isCanonTotal = length(tupleDataIcos)==2
    type_tuple = type(())
    for cyc, dt in enumerate(tupleDataIcos):
        isTuple = type(dt)==type_tuple
        rowIco = rowTheme.row(align=True)
        rowIco.label(icon=dt[0] if isTuple else 'RADIOBUT_ON') #RADIOBUT_ON  SNAP_FACE
        rowIco.active = decorTotalRow//2%2
        AddThinSep(rowIco, 1, 0.5)
        rowData = rowTheme.row(align=True)
        rowData.alignment = 'LEFT'
        rowData.label(text=str(dt[1] if isTuple else dt))
        rowData.active = decorTotalRow%2
        if (isCanonTotal)and(cyc==0)and(decorTotalRow//4%2):
            rowDiv = rowTheme.row(align=True)
            rowDiv.alignment = 'LEFT'
            rowDiv.label(text="/")
            rowDiv.active = False
    if decor==1:
        rowMain.label()

class OpManagersNodeTree(bpy.types.Operator):
    bl_idname = 'uu.node_op_mnt_managersnodetree'
    bl_label = "Op Managers Node Tree"
    bl_options = {'UNDO'}
    who: bpy.props.StringProperty()
    def execute(self, context):
        if self.who:
            ndTar = eval(self.who)
            loc = ndTar.location.copy()
            tree = context.space_data.edit_tree
            for nd in reversed(tree.nodes):
                nd.location -= loc
                nd.location = (math.floor(nd.location.x/20-0.5)*20, math.floor(nd.location.y/20-0.5)*20)
                nd.select = False
            #tree.nodes.active = ndTar
            #ndTar.select = True
        return {'FINISHED'}
class NodeManagersNodeTree(MntNodeRoot):
    bl_idname = 'MntNodeManagersNodeTree'
    bl_label = "Managers Node Tree"
    bl_width_max = 768
    bl_width_min = 128
    bl_width_default = 256
    @classmethod
    def poll(cls, tree):
        return tree.bl_idname==ManagersTree.bl_idname
    def DrawExtNode(self, context, colLy):
        colLy.operator(OpManagersNodeTree.bl_idname, text="Offset nodes to world origin").who = repr(self)
        if not context.preferences.use_preferences_save:
            colLy.operator('wm.save_userpref', text="Save Preferences"+" *"*context.preferences.is_dirty)
    def DrawNode(self, context, colLy):
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
    @classmethod
    def poll(cls, tree):
        return tree.bl_idname==ManagersTree.bl_idname
    def draw_buttons_ext(self, context, layout):
        layout.prop(self,'width', text="Node width", slider=True)

list_classes += [OpManagersNodeTree] #todo наверное к своим поближе.
AddToRegAndAddToSacat([ (0,NodeManagersNodeTree), (1,NodeDummy) ], 9, "Self", 'IsManagerNodeTreePoll')

class NodeQuickNote(MntNodeAlertness):
    bl_idname = 'MntNodeQuickNote'
    bl_label = "Quick note"
    bl_width_max = 2048
    bl_width_min = 64
    bl_width_default = 256
    note: bpy.props.StringProperty(name="Note body", default="")
    def DrawNode(self, context, layout):
        layout.prop(self,'note', text="")
        self.ProcAlertState(self.note)

AddToRegAndAddToSacat([ (0,NodeQuickNote) ], 9, "Text", 'IsManagerNodeTreePoll')

class NnOp(bpy.types.Operator):
    bl_idname = 'uu.node_op_nn'
    bl_label = "NamOp"
    bl_options = {'UNDO'}
    opt: bpy.props.StringProperty()
    who: bpy.props.StringProperty()
    def execute(self, context):
        if self.who:
            ndRepr = eval(self.who)
            match self.opt:
                case 'CollapseEmpties':
                    warpTo = -1
                    memo = ndRepr.memo
                    for cyc, line in enumerate(ndRepr.memo):
                        if line.body:
                            if warpTo>-1:
                                memo[warpTo].body = memo[cyc].body
                                memo[warpTo].name = memo[cyc].name
                                memo[cyc].body = ""
                                warpTo += 1
                        elif warpTo==-1:
                            warpTo = cyc
                    for cyc in reversed(range(warpTo, length(memo))):
                        memo.remove(cyc)
                    context.area.tag_redraw()
        return {'FINISHED'}

list_classes += [NnOp]

def UpdateNodeNotepadLines(self, context):
    len = length(self.memo)
    for cyc in range(len, self.linesCount):
        ci = self.memo.add()
        ci.name = str(cyc)
    for cyc in reversed(range(self.linesCount, len)):
        self.memo.remove(cyc)
class NotepadLine(bpy.types.PropertyGroup): #todo префиксы прилизать у всех.
    body: bpy.props.StringProperty(name="NpLTB", default="")

def NnSetOp(op, opt, who):
    op.opt = opt
    op.who = who
class NodeNotepad(MntNodeAlertness):
    bl_idname = 'MntNodeNotepad'
    bl_label = "Notepad"
    bl_width_max = 2048
    bl_width_min = 140
    bl_width_default = 384
    linesCount: bpy.props.IntProperty(name="Count of lines", min=0, max=256, soft_max=32, default=5, update=UpdateNodeNotepadLines)
    memo: bpy.props.CollectionProperty(type=NotepadLine)
    def init(self, context):
        self.linesCount = 5 #Заметка: UpdateNodeNotepadLines().
    def DrawInAddon(self, context, colLy):
        prefs = Prefs()
        if colBox:=GetNodeBoxDiscl(colLy, prefs,'disclMnNn', self):
            colProps = colBox.column(align=True)
            colProps.prop(prefs,'nnDecorMemo')
            colProps.prop(prefs,'nnDecorLinesCount')
    def DrawExtNode(self, context, colLy):
        colLy.prop(self,'linesCount')
        self.DrawInAddon(context, colLy)
        colLy.label(text="Operators:")
        NnSetOp(colLy.operator(NnOp.bl_idname, text="Collapse empty lines"), 'CollapseEmpties', repr(self))
    def DrawNode(self, context, colLy):
        prefs = Prefs()
        nnDecorLinesCount = prefs.nnDecorLinesCount-1
        decorNum = prefs.nnDecorMemo//4%4
        decorBody = prefs.nnDecorMemo%4
        if prefs.nnDecorLinesCount:
            rowProp = colLy.row()
            if nnDecorLinesCount//2%2:
                rowProp.alignment = 'LEFT'
                rowProp.scale_x = 1.2
            rowProp.prop(self,'linesCount')
            rowProp.active = nnDecorLinesCount%2
        colNotepad = colLy.column(align=decorBody<2)
        len = length(str(self.linesCount-1))
        canAlert = any(self.alertColor)
        alertAcc = False
        for cyc, line in enumerate(self.memo):
            rowLine = colNotepad.row(align=True)
            if decorNum:
                rowNum = rowLine.row(align=True)
                rowNum.alignment = 'CENTER'
                rowNum.active = decorNum>1
                rowNum.label(text=str(cyc).zfill(len)+":")
            rowBody = (rowLine.row() if decorBody else rowLine).row(align=True)
            rowBody.prop(line,'body', text="")
            if canAlert:
                alertAcc |= not not line.body
        if canAlert:
            self.ProcAlertState(alertAcc)

list_classes += [NotepadLine]
AddToRegAndAddToSacat([ (1,NodeNotepad) ], 9, "Text", 'IsManagerNodeTreePoll')

class AddonPrefs(AddonPrefs):
    disclMnNn: bpy.props.BoolProperty(name="DisclMnNn", default=False)
    nnDecorLinesCount: bpy.props.IntProperty(name="Decor Lines count", default=3, min=0, max=4)
    nnDecorMemo: bpy.props.IntProperty(name="Decor Memo", default=4, min=0, max=11)

list_clsToDrawAdn.append(NodeNotepad)

#    def GenName(num): todo4 к Nsr
#        txt = ""
#        while num>0:
#            txt = chr(97+num%26)+txt
#            num //= 26
#        return txt
#    isDisplayLineNames: bpy.props.BoolProperty(name="Place line names", default=False)

#aaaa = [0,0] todo
#        aaa = colLy.column() ##############
#        import time
#        tm = time.time()
#        aaaa[1] *= aaaa[0]
#        aaaa[0] += 1
#        aaaa[1] += time.time()-tm
#        aaaa[1] /= aaaa[0]

def AddTableOfProps(self, where, data, list_props, colSpec=None): #todo: бардак!
    def Eix(ix):
        if niptIsPlaceDebug:
            return " {"+str(ix)+"}"
        return ""
    #Пайка:
    isShowFilterErrors = self.isShowFilterErrors
    prefs = Prefs()
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
    else:
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
        list_props[cyc] = ("."*(not not txt_path)+txt_path, txt_prop, ix, txt_error)
    if niptIsPlaceDebug:
        colTable.label(text="debug1:  "+str(list_props))
    #Узнать наличие дубликатов:
    isHaveDuplicates = length(list_props)!=length(set(list_props))
    #Преобразовать
    list_table = [ [None, li[0], li[1], li[2], li[3]] for li in list_props if li]
    if niptIsPlaceDebug:
        colTable.label(text="debug2:  "+str(list_table))
    try:
        for dt in data: #Нужно, чтобы отображение ошибки неитерируемости не дублировалось.
            break
        #Создать начала столбцов для таблицы:
        len = length(list_table)
        for cyc, (colWhere, propPath, propName, propIndx, txtError) in enumerate(list_table):
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
                    row.prop(self.filters[cyc],'txt_filter', text="", icon='SCRIPT') ##SCRIPT  SORTBYEXT
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
            (colSpec if colSpec else colTable) . label(text=str(ex)+Eix(2), icon='ERROR') #Отображать в перезаписываемой или по "хронологии".
            return
        sco = 0 #Если нужно будет возвращать, то вынести за пределы большого try, (но не помню почему).
        for dt in data:
            #isHaveDuplicates -- для переключения в режим "или".
            #list_table -- Если список props пустой, будет Total max/max. Поэтому False здесь, чтобы было Total 0.
            can = (not isHaveDuplicates)and(not not list_table)
            dict_errors = {}
            isBright = True
            for cyc, (colWhere, propPath, propName, propIndx, txtError) in enumerate(list_table):
                try:
                    if txtError: #Не проверять, чтобы все строки не помечались как содержащие ошибку в этом столбце.
                        continue
                    pr = eval("dt"+propPath)
                    isErrorInProp = True
                    val = getattr(pr, propName)
                    isErrorInProp = False
                    txt = self.filters[cyc].txt_filter
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
                for colWhere, propPath, propName, propIndx, txtError in list_table:
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
                            row.label(text="Prop value is None"+Eix(4), icon='ERROR') #todo: подадекватить и мб переосмыслить
                sco += 1
        if decorTable//2%2:
            colTable.separator()
            colTable.box()
        if decorTotal:
            colTotal = colTotalTop if decorTotal>0 else colTotalBottom
            StencilTotalRow(colTotal, ('RADIOBUT_OFF', sco), length(data), ('RNA', length(list_props)))
        self.ProcAlertState(sco)
    except Exception as ex:
        colMain.label(text=str(ex)+Eix(5), icon='ERROR')
        colMain.box()
    return list_props

def SplitPropTxtToList(txt_props):
    return [li for li in re.findall("[^;,]+", txt_props.replace(" ", ""))]
def UpdateNodeTableFilters(self, context):
    dict_saveToRestore = dict([(li.txt_prop, li.txt_filter) for li in self.filters.values()])
    self.filters.clear()
    for li in SplitPropTxtToList(self.props):
        ci = self.filters.add()
        ci.txt_prop = li #Todo: Имена могут быть одинаковыми!
        ci.txt_filter = dict_saveToRestore.get(li,"True")

class TablePropFilter(bpy.types.PropertyGroup):
    txt_prop: bpy.props.StringProperty(name="Prop Id", default="")
    txt_filter: bpy.props.StringProperty(name="Prop Filter", default="")

def AddPathNodePropEval(self, where, isPlaceExecAlerts):
    evaled = EvalAndAddPropExtended(where, self,'path', self.path, icon='ZOOM_ALL', txt_warning="eval() !"*isPlaceExecAlerts)
    if not self.path:
        where.label(text="Input expected", icon='INFO')
        return None
    if evaled[0]:
        matter = evaled[1]
        if not matter:
            where.label(text="Data is None", icon='INFO')
            return None #todo0: стоит ли всё отрубать?
    else:
        return None
    return matter
class NodeItemPropsTable(MntNodeAlertness):
    bl_idname = 'MntNodeItemPropsTable'
    bl_label = "Item-Props Table"
    bl_icon = 'PROPERTIES' #Можно было и 'SPREADSHEET', но этот нод изначадбнл был создан по нужде высокоуровневого менеджмента.
    bl_width_max = 4096
    bl_width_min = 256
    bl_width_default = 640
    path:    bpy.props.StringProperty(name="Path",    default="")
    props:   bpy.props.StringProperty(name="Props",   default="", update=UpdateNodeTableFilters)
    precomp: bpy.props.StringProperty(name="Precomp", default="")
    filters: bpy.props.CollectionProperty(type=TablePropFilter)
    isShowFilterErrors: bpy.props.BoolProperty(name="Show rows with errors", default=True)
    def init(self, context):
        self.path = "bpy.data.objects"
        self.props = "name, data; data.use_fake_user"
        self.precomp = "patr = re.compile(\".*\"); #precompiler here"
        self.filters[0].txt_filter = "patr.search(val)"
        self.filters[1].txt_filter = "re.search(\".*\", val.name)"
    def DrawInAddon(self, context, colLy):
        prefs = Prefs()
        if colBox:=GetNodeBoxDiscl(colLy, prefs,'disclMnNipt', self):
            colProps = colBox.column(align=True)
            colProps.prop(prefs,'niptIsBrightTableLabels')
            colProps.prop(prefs,'niptIsBrightFilterErrors')
            colProps.prop(prefs,'niptDecorTable')
            colProps.prop(prefs,'niptDecorTotal')
            colProps.prop(prefs,'niptIsPlaceDebug')
    def DrawExtNode(self, context, colLy):
        colLy.prop(self,'isShowFilterErrors')
        self.DrawInAddon(context, colLy)
    def DrawNode(self, context, colLy):
        colNodeProps = colLy.column(align=True)
        isPlaceExecAlerts = Prefs().allIsPlaceExecAlerts
        if data:=AddPathNodePropEval(self, colNodeProps, isPlaceExecAlerts):
            EvalAndAddPropExtended(colNodeProps.column(), self,'props', "", icon='RNA', txt_warning="eval() !"*isPlaceExecAlerts)
            EvalAndAddPropExtended(colNodeProps, self,'precomp', "", icon='SCRIPT', txt_warning="exec() !"*isPlaceExecAlerts, alertWarn=True)
            list_props = SplitPropTxtToList(self.props.replace(",",";"))
            AddTableOfProps(self, colLy, data, list_props, colSpec=colNodeProps)

list_classes += [TablePropFilter]
AddToRegAndAddToSacat([ (0,NodeItemPropsTable) ], 3, "Rna", 'IsManagerNodeTreePoll') #RNA #todo5

class AddonPrefs(AddonPrefs):
    disclMnNipt: bpy.props.BoolProperty(name="DisclMnNipt", default=False)
    niptIsBrightTableLabels: bpy.props.BoolProperty(name="Bright table labels", default=False)
    niptIsBrightFilterErrors: bpy.props.BoolProperty(name="Bright filter errors", default=False)
    niptDecorTable: bpy.props.IntProperty(name="Decor Table", default=6, min=0, max=7)
    niptDecorTotal: bpy.props.IntProperty(name="Decor Total", default=1, min=-1, max=1)
    niptIsPlaceDebug: bpy.props.BoolProperty(name="Place debug", default=False)

list_clsToDrawAdn.append(NodeItemPropsTable)

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
    def init(self, context):
        self.path = "bpy.context.space_data.edit_tree.nodes.active"
        self.filter = "re.search(\"\", val.identifier)"
    def DrawInAddon(self, context, colLy):
        prefs = Prefs()
        if colBox:=GetNodeBoxDiscl(colLy, prefs,'disclMnNpnv', self):
            colProps = colBox.column(align=True)
            colProps.prop(prefs,'npnvIsBrightTableLabels')
            colProps.prop(prefs,'npnvDecorTable')
            colProps.prop(prefs,'npnvDecorTotal')
    def DrawExtNode(self, context, colLy):
        colLy.prop(self,'isShowIdentifier')
        self.DrawInAddon(context, colLy)
    def DrawNode(self, context, colLy):
        colNodeProps = colLy.column(align=True)
        isShowIdentifier = self.isShowIdentifier
        prefs = Prefs()
        isPlaceExecAlerts = prefs.allIsPlaceExecAlerts
        isBrightFilters = prefs.allIsBrightFilters
        isBrightTableLabels = prefs.npnvIsBrightTableLabels
        decorTable = prefs.npnvDecorTable
        decorTotal = prefs.npnvDecorTotal
        ##
        if target:=AddPathNodePropEval(self, colNodeProps, isPlaceExecAlerts):
            AddThinSep(colLy, .2)
            row = colLy.row()
            row.prop(self,'filter', text="", icon='SCRIPT')
            row.active = isBrightFilters
            if isPlaceExecAlerts:
                AddWarningLabel(row, "eval() !")
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
                        if (li.type=='BOOLEAN'):
                            spl.row().prop(target, li.identifier)
                        else:
                            spl.row(align=li.identifier.startswith('matrix')).prop(target, li.identifier, text="")
                        sco += 1
                if decorTable%2:
                    colList.box()
                if decorTotal:
                    colTotal = colTotalTop if decorTotal>0 else colTotalBottom
                    StencilTotalRow(colTotal, ('RNA', sco), length(target.bl_rna.properties))
            except Exception as ex:
                colLy.label(text=str(ex), icon='ERROR')

AddToRegAndAddToSacat([ (1,NodePropsNameViewer) ], 3, "Rna", 'IsManagerNodeTreePoll')

class AddonPrefs(AddonPrefs):
    disclMnNpnv: bpy.props.BoolProperty(name="DisclMnNpnv", default=False)
    npnvIsBrightTableLabels: bpy.props.BoolProperty(name="Bright table labels", default=False)
    npnvDecorTable: bpy.props.IntProperty(name="Decor Table", default=3, min=0, max=7)
    npnvDecorTotal: bpy.props.IntProperty(name="Decor Total", default=1, min=-1, max=1)

list_clsToDrawAdn.append(NodePropsNameViewer)

import addon_utils, os, functools

def GetAddonsList():
    return [(mod, addon_utils.module_bl_info(mod)) for mod in addon_utils.modules(refresh=False)]

class NamOp(bpy.types.Operator):
    bl_idname = 'uu.node_op_nam'
    bl_label = "NamOp"
    opt: bpy.props.StringProperty()
    who: bpy.props.StringProperty()
    tar: bpy.props.StringProperty()
    def execute(self, context):
        if self.who:
            ndRepr = eval(self.who)
            dict_tgl = eval(ndRepr.togglersStrEval)
            match self.opt:
                case 'Discl':
                    if dict_tgl.get(self.tar):
                        del dict_tgl[self.tar]
                    else:
                        dict_tgl[self.tar] = 1
                case 'ToggleAll':
                    if dict_tgl:
                        dict_tgl.clear()
                    else:
                        for li in GetAddonsList():
                            dict_tgl[li[0].__name__] = 1
                    context.area.tag_redraw()
            ndRepr.togglersStrEval = repr(dict_tgl)
        return {'FINISHED'}

list_classes += [NamOp]

def NamItemsAddonFilter(self, context):
    list_items = [ ('All', "All", ""), ('User',"User","") ]
    set_unique = set()
    for md in addon_utils.modules(refresh=False):
        blinfo = addon_utils.module_bl_info(md)
        set_unique.add(blinfo['category'])
    list_items.extend( [(cat,cat,"") for cat in sorted(set_unique)] )
    return list_items

#todo1 сделать длинные тексты desc warn, и открытие папки file -- кликабельными операторами.

def NamSetOp(op, opt, who, tar=""):
    op.opt = opt
    op.who = who
    op.tar = tar
def AddAnBlInfoFromOrder(where, mod, blinfo, txt_order="dlfavw"):
    def AddAnBlInfoLine(where, label, txt):
        row0 = where.row(align=True)
        row1 = row0.row(align=True)
        row1.alignment = 'CENTER'
        row1.label(text=label)
        row1.active = False
        row0.label(text=txt)
    for ch in txt_order:
        target = [di for di in blinfo if di[0]==ch]
        target = target[0] if target else "hi"
        LCheck = lambda txt: (target==txt)and(blinfo[txt])
        if (mod)and(ch=="f"):     AddAnBlInfoLine(where, "File:",        mod.__file__)
        if LCheck('description'): AddAnBlInfoLine(where, "Description:", blinfo['description'])
        if LCheck('location'):    AddAnBlInfoLine(where, "Location:",    blinfo['location'])
        if LCheck('author'):      AddAnBlInfoLine(where, "Author:",      blinfo['author'])
        if LCheck('version'):     AddAnBlInfoLine(where, "Version:",     ".".join(str(li) for li in blinfo['version']))
        if LCheck('warning'):
            row0 = where.row(align=True)
            row1 = row0.row(align=True)
            #row1.alert = True
            row1.label(icon='ERROR')
            row1.active = False
            AddAnBlInfoLine(row0, "Warning:", blinfo['warning'])
class NodeAddonsManager(MntNodeAlertness):
    bl_idname = 'MntNodeAddonsManager'
    bl_label = "Addons Manager"
    #bl_icon = 'PLUGIN'
    bl_width_max = 2048
    bl_width_min = 256
    bl_width_default = 512
    filter: bpy.props.StringProperty(name="filter", default="")
    togglersStrEval: bpy.props.StringProperty(default="{}")
    enum_filterByCat: bpy.props.EnumProperty(name="Filter by category", items=NamItemsAddonFilter)
    isShowDisabledAddons: bpy.props.BoolProperty(name="Disabled addons", default=False)
    def init(self, context):
        self.filter = ".*"
    def DrawInAddon(self, context, colLy):
        prefs = Prefs()
        if colBox:=GetNodeBoxDiscl(colLy, prefs,'disclMnNam', self):
            colProps = colBox.column(align=True)
            colProps.prop(prefs,'namItemsAlignment')
            colProps.prop(prefs,'namIsSelfPraise')
            colProps.prop(prefs,'namDecorTable')
            colProps.prop(prefs,'namDecorItems')
            colProps.prop(prefs,'namDecorPrefsLabel')
            colProps.prop(prefs,'namDecorTotal')
            colProps.prop(prefs,'namIsShowButtons')
    def DrawExtNode(self, context, colLy):
        self.DrawInAddon(context, colLy)
        colLy.label(text="Operators:")
        NamSetOp(colLy.operator(NamOp.bl_idname, text="Toggle disclosures"), 'ToggleAll', repr(self))
    def DrawNode(self, context, colLy):
        prefs = Prefs()
        namDecorTable = prefs.namDecorTable
        #Quartet (1+3):
        row = colLy.row(align=True)
        row.row().operator('wm.save_userpref', text="Save Preferences"+(" *" if context.preferences.is_dirty else ""))
        row.prop(self,'enum_filterByCat', text="")
        row.row().operator('preferences.addon_install', text="Install...", icon='IMPORT')
        row.operator('preferences.addon_refresh', text="Refresh", icon='FILE_REFRESH')
        AddThinSep(colLy)
        #Filter:
        if not(patr:=StencilAddFilterProp(self, colLy)):
            return
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
        colTotalBottom = colTheme.column(align=True)
        #Prepare ly:
        dict_usedExt = {ext.module for ext in bpy.context.preferences.addons}
        tuple_userDirs = ( *[os.path.join(li,"addons") for li in bpy.utils.script_paths_pref()], bpy.utils.user_resource('SCRIPTS', path="addons") )
        tuple_userDirs = tuple(p for p in tuple_userDirs if p)
        list_addons = GetAddonsList()
        #Prepare for:
        max = length(list_addons)
        set_modNames = {li[0].__name__ for li in list_addons}
        set_missingMods = {di for di in dict_usedExt if di not in  set_modNames}
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
        dict_togglers = eval(self.togglersStrEval)
        try:
            #Matter:
            list_userAddonPaths = []
            entryTgl = False
            for cyc, (mod, blinfo) in enumerate(sorted(list_addons, key=lambda li: li[0].__name__ in dict_usedExt, reverse=True)):
                modName = mod.__name__
                scoTot += 1
                if cyc==len:
                    colShowDis = colAddons.row().column(align=True) #Второй .row() для namItemsAlignment==0.
                    entryTgl = True
                if (cyc>=len)and(not isSda):
                    can = False
                if (catf!="All")and(catf!=blinfo['category'])and not( (catf=="User")and(mod.__file__.startswith(tuple_userDirs)) ):
                    continue
                if not patr.search(blinfo['name']):
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
                isEnabled = modName in dict_usedExt #context.preferences.addons.get(modName, False)
                rowRecord = (colAddons.row() if namItemsAlignment>1 else colAddons).row().row(align=True) #Второй .row() для меж-record скругления при namDecorItems==0 и namItemsAlignment<4.
                #Disclosure:
                rowDiscl = rowRecord.row(align=True)
                isDiscl = dict_togglers.get(modName, False)
                NamSetOp(rowDiscl.operator(NamOp.bl_idname, text="", icon='DISCLOSURE_TRI_'+('DOWN' if isDiscl else 'RIGHT'), depress=isDiscl), 'Discl', repr(self), modName)
                rowDiscl.scale_x = 2.0
                rowDiscl.active = not isDiscl
                #Toggle addon register:
                rowEnabled = rowRecord.row(align=True)
                if modName==thisAddonName:
                    rowEnabled.operator(NamOp.bl_idname, text="", icon='CHECKBOX_HLT')
                else:
                    ico = 'CHECKBOX_HLT' if isEnabled else 'CHECKBOX_DEHLT'
                    rowEnabled.operator('preferences.addon_disable' if isEnabled else 'preferences.addon_enable', text="", icon=ico).module = modName
                AddThinSep(rowRecord, 1.0, .5)
                #Addon name:
                colAddon = rowRecord.column(align=True)
                rowAddon = colAddon.row(align=True)
                isSelfAddonMarker = blinfo['name']==bl_info['name']
                if (prefs.namIsSelfPraise)and(blinfo['author']=="ugorek"):
                    rowIsMyAddonMarker = rowAddon.row(align=True)
                    rowIsMyAddonMarker.active = False
                    rowIsMyAddonMarker.alert = isSelfAddonMarker# or True #MONKEY
                    rowIsMyAddonMarker.label(icon='SOLO_ON' if isSelfAddonMarker else 'SOLO_OFF') #FONTPREVIEW  SNAP_FACE  MONKEY  SOLO_ON  SOLO_OFF
                box = rowAddon.box()
                box.scale_y = 0.5
                rowLabel = box.row(align=True)
                rowName = rowLabel.row(align=True)
                rowName.alert = (isSelfAddonMarker)and(prefs.namIsSelfPraise)
                rowName.label(text=blinfo['name'])#, icon='PLUGIN')
                rowAddon.alert = False
                rowName.active = isEnabled
                if isDiscl:
                    namDecorItems = prefs.namDecorItems
                    box = (colAddon.row() if namDecorItems%2 else colAddon).box()
                    colAnBlInfo = box.column(align=True)
                    AddAnBlInfoFromOrder(colAnBlInfo, mod, blinfo, "avdlwf")
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
                                        colAddons.label(text=modName+" has error", icon='ERROR')
                                    del apClass.layout
                                colAddon.separator()
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
                            op.id = ("Name: %s %s\n" "Author: %s\n")%(blinfo['name'], str(blinfo['version']), blinfo['author'])
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
            StencilTotalRow(colTot, ('PLUGIN', scoDisp), scoTot, decor=(1+(1+dec)%2)) #todo0 наверное стоит сделать "вкл, выкл, отображется, всего".
            if dec>2:
                AddThinSep(rowSep, 0.25*(1+(dec-3)//2))
            if namDecorTable//4%2:
                AddThinSep(colSep)
                colSep.box()
                AddThinSep(colSep)
        if namDecorTable//2%2:
            colLy.box()
        self.ProcAlertState(scoDisp)

AddToRegAndAddToSacat([ (99,NodeAddonsManager) ], 2, "Managers", 'IsManagerNodeTreePoll')

class AddonPrefs(AddonPrefs):
    disclMnNam: bpy.props.BoolProperty(name="DisclMnNam", default=False)
    namItemsAlignment: bpy.props.IntProperty(name="Alignment between elements", default=4, min=0, max=5)
    namIsSelfPraise: bpy.props.BoolProperty(name="Self-praise", default=True)
    namDecorTable: bpy.props.IntProperty(name="Decor Table", default=1, min=0, max=15)
    namDecorItems: bpy.props.IntProperty(name="Decor Items", default=2, min=0, max=3)
    namDecorPrefsLabel: bpy.props.IntProperty(name="Decor Prefs label", default=2, min=-3, max=3)
    namDecorTotal: bpy.props.IntProperty(name="Decor Total", default=2, min=-7, max=7)
    namIsShowButtons: bpy.props.BoolProperty(name="Forcibly show buttons", default=False)

list_clsToDrawAdn.append(NodeAddonsManager)

#Todo: кнопка-варп сразу в тб в том же пространстве или по всем
#todo0: отрендерить текст чтобы узнать его ширину

class TtfResult:
    def __init__(self, inx, ln, txt):
        self.inx = inx
        self.ln = ln
        self.txt = txt
class TtfSearch:
    def __init__(self, tbRef, zlen):
        self.tbRef = tbRef
        self.zlen = zlen
        self.list_result = []
class TtfFinder:
    def __init__(self):
        self.lastTimeRaw = 0
        self.list_search = []

dict_nttfSearchCache = {}

import time

def TtfDoNdSearch(ndTar):
    dict_nttfSearchCache[ndTar].list_search.clear()
    try:
        patr = re.compile(ndTar.regex)
    except:
        return
    list_tbs = bpy.data.texts
    if ndTar.tbPoi:
        list_tbs = [tb for tb in bpy.data.texts if tb!=ndTar.tbPoi] if ndTar.isReverseTbPoi else [ndTar.tbPoi]
    if getattr(bpy.types.Text,'order', False):
        list_tbs.sort(key=lambda a: a.order)
    for tb in list_tbs:
        ttfSr = TtfSearch(tb, length(str(length(tb.lines))))
        for cyc, ln in enumerate(tb.lines):
            rex = patr.search(ln.body)
            if rex:
                ttfSr.list_result.append(TtfResult(cyc, ln, rex.group(0)))
        dict_nttfSearchCache[ndTar].list_search.append(ttfSr)
    dict_nttfSearchCache[ndTar].lastTimeRaw = time.time()

def TtfUpdateRegex(self, context):
    TtfDoNdSearch(self)

class NodeTextblockTextFinder(MntNodeAlertness):
    bl_idname = 'MntNodeTextblockTextFinder'
    bl_label = "Textblock Text Finder"
    bl_width_max = 2048
    bl_width_min = 256
    bl_width_default = 448
    tbPoi: bpy.props.PointerProperty(name="Text Block", type=bpy.types.Text, update=TtfUpdateRegex)
    regex: bpy.props.StringProperty(name="RegEx", default="", update=TtfUpdateRegex)
    isReverseTbPoi: bpy.props.BoolProperty(name="Reverse search", default=False, update=TtfUpdateRegex)
    isDisplayAsProp: bpy.props.BoolProperty(name="Display as prop", default=True)
    linesScaleY: bpy.props.FloatProperty(name="Lines scale Y", min=.4, max=1.5, default=.85)
    decorResults: bpy.props.IntProperty(name="Decor Results", default=3, min=0, max=7)
    def draw_label(self):
        #А так же поместить и само выражение.
        return "Textblock LineText Finder  /"+self.regex+"/" #"–"
    def init(self, context):
        self.regex = "^ *#\w+.+"
        if tb:=bpy.data.texts.get(".Compiled"):
            self.tbPoi = tb
            self.isReverseTbPoi = True
    def DrawInAddon(self, context, colLy):
        prefs = Prefs()
        if colBox:=GetNodeBoxDiscl(colLy, prefs,'disclMnNttf', self):
            colProps = colBox.column(align=True)
            colProps.prop(prefs,'nttfItemsAlignment')
            colProps.prop(prefs,'nttfDecorTable')
            colProps.prop(prefs,'nttfDecorTotal')
    def DrawExtNode(self, context, colLy):
        colLy.prop(self,'linesScaleY')
        colLy.prop(self,'isDisplayAsProp')
        colLy.prop(self,'decorResults')
        self.DrawInAddon(context, colLy)
    def DrawNode(self, context, colLy):
        dict_nttfSearchCache.setdefault(self, TtfFinder())
        if time.time()-dict_nttfSearchCache[self].lastTimeRaw>1.0:
            TtfDoNdSearch(self)
        isDisplayAsProp = self.isDisplayAsProp
        decorResults = self.decorResults
        prefs = Prefs()
        nttfItemsAlignment = prefs.nttfItemsAlignment
        nttfDecorTable = prefs.nttfDecorTable
        nttfDecorTotal = prefs.nttfDecorTotal
        rowTbPoi = colLy.row(align=True)
        rowLabel = rowTbPoi.row(align=True)
        rowLabel.alignment = 'CENTER'
        rowLabel.label(text="Search in:")
        rowReverse = rowTbPoi.row(align=True)
        rowReverse.prop(self,'isReverseTbPoi', text="", icon='ARROW_LEFTRIGHT')
        rowReverse.active = False
        rowTbPoi.prop(self,'tbPoi', text="")
        if patr:=StencilAddFilterProp(self, colLy, prop='regex'):
            if nttfDecorTable//2%2:
                colLy.box()
            colTotalTop = colLy.column(align=True)
            colFounds = colLy.column(align=True)
            colTotalBottom = colLy.column(align=True)
            scoDisp = 0
            scoTotAll = 0
            set_dataTb = {tb for tb in bpy.data.texts}
            list_search = dict_nttfSearchCache[self].list_search
            for fdsr in reversed(list_search):
                if fdsr.tbRef not in set_dataTb:
                    list_search.remove(fdsr)
            for fdsr in list_search:
                if fdsr.list_result:
                    box = colFounds.row().box()
                    colTb = box.column(align=True)
                    row = colTb.row()
                    row.alert = decorResults//4%2
                    row.prop(fdsr.tbRef,'name', text="", icon='TEXT')
                    row.active = decorResults%2
                    colList = colTb.column(align=True)
                    colList.scale_y = self.linesScaleY
                    for li in fdsr.list_result:
                        rowResult = (colList.row() if nttfItemsAlignment else colList).row(align=True)
                        rowInx = rowResult.row(align=True)
                        rowInx.alignment = 'CENTER'
                        rowInx.active = False
                        rowInx.label(text=str(li.inx).zfill(fdsr.zlen)+":")
                        if isDisplayAsProp:
                            rowResult.prop(li.ln,'body', text="")
                        else:
                            rowResult.label(text=li.txt)
                        rowResult.active = decorResults//2%2
                        scoDisp += 1
                scoTotAll += length(fdsr.tbRef.lines)
            if nttfDecorTable%2:
                colLy.box()
            if nttfDecorTotal:
                StencilTotalRow(colTotalTop if nttfDecorTotal>0 else colTotalBottom, ('PRESET', scoDisp), ('ALIGN_JUSTIFY', scoTotAll), decor=1) #RADIOBUT_OFF  PRESET  TRACKER
            self.ProcAlertState(scoDisp)

#todo у всех .setdefault(self, None)

AddToRegAndAddToSacat([ (2,NodeTextblockTextFinder) ], 8, "Text", 'IsManagerNodeTreePoll')

class AddonPrefs(AddonPrefs):
    disclMnNttf: bpy.props.BoolProperty(name="DisclMnNttf", default=False)
    nttfItemsAlignment: bpy.props.BoolProperty(name="Alignment between elements", default=False)
    nttfDecorTable: bpy.props.IntProperty(name="Decor Table", default=2, min=0, max=3)
    nttfDecorTotal: bpy.props.IntProperty(name="Decor Total", default=1, min=-1, max=1)

list_clsToDrawAdn.append(NodeTextblockTextFinder)

#def AddAllAnnot(where, self): #Не используется.
#    colList = where.column()
#    try:
#        colProps = colList.column(align=True)
#        if hasattr(self,'__annotations__'):
#            for k in self.__annotations__.keys():
#                colProps.row().prop(self, k)
#    except Exception as ex:
#        colList.label(text=str(ex), icon='ERROR')

def Prefs():
    return bpy.context.preferences.addons[thisAddonName].preferences
class AddonPrefs(AddonPrefs):
    aMnnPanel: bpy.props.BoolProperty(name=PanelManagerNodesNode.bl_label+" Panel", default=True, update=ToggleRegMnnPanel)
    allIsPlaceExecAlerts: bpy.props.BoolProperty(name="Place exec alerts", default=True)
    decorTotalRow: bpy.props.IntProperty(name="Decor Total Row", default=21, min=0, max=63)
    allIsBrightFilters: bpy.props.BoolProperty(name="Bright filters", default=True)
#    isHideOnlyOne: bpy.props.BoolProperty(name="Hide if only one", default=True)
    def draw(self, context):
        colLy = self.layout.column()
        box = GetLabeledDoubleBox(colLy, "Main", active=True, alignment='CENTER')
        colBox = box.column(align=True)
        colBox.prop(self,'aMnnPanel')
        #colBox.column().box()
        colBox.prop(self,'allIsPlaceExecAlerts')
        #colBox.column().box()
        AddThinSep(colBox, 0.5) #Омг, странно.
        colBox.prop(self,'decorTotalRow')
        colBox.prop(self,'allIsBrightFilters')
        for cls in list_clsToDrawAdn:
            cls.DrawInAddon(cls, context, colLy)

list_classes += [AddonPrefs]

def register():
    for li in list_classes:
        bpy.utils.register_class(li)
    if Prefs().aMnnPanel:
        bpy.utils.register_class(PanelManagerNodesNode)
    RegisterNodeCategories()
def unregister():
    for li in list_classes:
        bpy.utils.unregister_class(li)
    UnregisterNodeCategories()

if __name__=="__main__":
    register()
