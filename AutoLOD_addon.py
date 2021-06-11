import bpy
import math
from bpy.props import PointerProperty

# ---------- ---------- Addon infos ---------- ----------

# bl_info = {
#    "name": "AutoLODs",
#    "author": "Josué Raad",
#    "version": (1, 0),
#    "blender": (2, 80, 0),
#    "location": "View3D > Tools > LODs",
#    "description": "Allow to create and apply LODs based on the distance from camera",
#    "warning": "",
#    "doc_url": "",
#    "category": "Object",
#}

# ---------- ---------- Global definitions ---------- ----------

lod_modifier_name = "lod_modifier"

# ---------- ---------- Properties ---------- ----------

# create a property in the scene. Later i have an interface to draw it. todo
# And in the add modifier ops I check if the prop is not null

bpy.types.Scene.lod_target = PointerProperty(
    type=bpy.types.Object, name="lod target", description="The object to compute lod distance from")

bpy.types.Scene.agressivity = bpy.props.FloatProperty(
    name="agressivity", description="controlls the agressivity of the lods, higher values will result in more decimation", default=1, min=0.0)

bpy.types.Scene.lod_bias = bpy.props.IntProperty(
    name="lod bias", description="The bias of the lods, positives values will increase the lod level, while negative will decrease it", default=0, min=-4, max=4)

bpy.types.Scene.lod_start_dist = bpy.props.FloatProperty(
    name="lod start distance", description="Lods will tart generating after this distance", default=10, min=0, subtype='DISTANCE')

bpy.types.Scene.lod_ratio_multiplier = bpy.props.FloatProperty(
    name="lod ratio multiplier", description="Decimation ratio multiplier", default=1, min=0, max=1, subtype='FACTOR')

bpy.types.Scene.lod_max_level = bpy.props.IntProperty(
    name="lod max level", description="The maximum level of lod", default=6, min=0)

bpy.types.Object.is_lod = bpy.props.BoolProperty(
    name="is lod", description="is the object a lod", default=False)

# ---------- ---------- Utilitary functions ---------- ----------


def get_distance(object1, object2):
    """compute the distance between 2 objects"""
    return (object1.location - object2.location).length

# ----------


def objects_dont_share_data(objects):
    """returns True if no selcted objects shares the same data"""
    for object in objects:
        if object.data.users != 1:
            return False
    return True

# ----------


def get_all_lod_objects():
    """Returns a list of all LODs object in the current file"""
    output = []
    for object in bpy.data.objects:
        if object.is_lod:
            output.append(object)
    return output


# ---------- ---------- Utils fuinction for Operators ---------- ----------


def remove_all_lods(objects):
    """iterates on the selected objects and removes the lod modifier"""
    for object in objects:
        remove_decimate(object)

# ----------


def remove_decimate(object):
    old_modifier = object.modifiers.get(lod_modifier_name)
    if old_modifier is not None:
        object.modifiers.remove(old_modifier)
    object.is_lod = False

# ----------


def get_lod_target():
    scene = bpy.context.scene

    if scene.lod_target is None:
        # the active camera is used when there is no target
        scene.lod_target = scene.camera

    return scene.lod_target

# ----------


def add_decimate_modifiers(objects):
    """Add a decimate modifier, the decimation depends on the computed lod level"""
    target = get_lod_target()
    for object in objects:
        add_decimate_single(object, target)  # then add a new one

# ----------


def add_decimate_single(object, target):
    remove_decimate(object)  # we first remove old lod modifiers

    lod_modifier = object.modifiers.new(lod_modifier_name, "DECIMATE")

    if (lod_modifier is None):  # we can't add lod to the object (not a mesh)
        return None

    lod_level = get_lod_level(get_distance(object, target))
    ratio = bpy.context.scene.lod_ratio_multiplier
    set_lod_decimation(lod_modifier, lod_level, ratio)
    object.is_lod = True
    return lod_modifier

# ----------


def set_lod_decimation(lod_modifier, lod_level, ratio):
    """set the decimation based on the lod level"""
    if lod_level > 0:  # only lods level above 0 create lods
        # here we compute the actual decimation from the lod level.
        lod_modifier.ratio = 1 / 2**lod_level * ratio

# ----------


def get_lod_level(distance):
    """compute the LOD level based on the distance and Scene properties"""
    scene = bpy.context.scene
    lod_bias = scene.lod_bias
    start_dist = scene.lod_start_dist
    max_level = scene.lod_max_level
    agressivity = scene.agressivity

    distance -= start_dist

    if distance < 0 or agressivity == 0:  # if the object is bellow the min distance or lods are disabled
        return -1

    # the lod level formula.
    log_val = math.log(distance + 1, 4 / agressivity + 1)
    # the '4' is a magic number to have better results with the default agressivity of 1.0

    lod_level = (log_val).__trunc__()  # the lod level is an integer

    if lod_level > max_level:
        return max_level

    return lod_level + lod_bias

# ----------


def apply_all_lods(objects):
    backup_active = bpy.context.object
    for object in objects:
        bpy.context.view_layer.objects.active = object
        bpy.ops.object.modifier_apply(modifier=lod_modifier_name)
        object.is_lod = False
    bpy.context.view_layer.objects.active = backup_active

# ----------


# ---------- ---------- Operators ---------- ----------


class ExportLodOperatorObj(bpy.types.Operator):
    """Exports Lods for the selected object, in .obj format"""
    bl_idname = "object.export_lod_obj"
    bl_label = "Export LOD (.obj)"
    bl_option = {'REGISTER', 'UNDO'}

    @classmethod
    def poll(cls, context):
        return context.active_object is not None

    def execute(self, context):
        active_object = context.object

        if active_object.type != 'MESH':
            return

        is_lod = active_object.is_lod

        lod_max_level = context.scene.lod_max_level
        lod_modifier = add_decimate_single(active_object, active_object)

        for i in range(lod_max_level + 1):
            set_lod_decimation(lod_modifier, i, 1)
            path = bpy.path.abspath("//") + active_object.name + "_lod" + str(i) + ".obj"
            bpy.ops.export_scene.obj(filepath=path, use_selection=True, use_mesh_modifiers=True)

        if is_lod:
            add_decimate_single(active_object, get_lod_target())
        else:
            remove_decimate(active_object)

        return {'FINISHED'}


# ----------

class ApplyAllLodOperator(bpy.types.Operator):
    """Apply LODs for all objects that have LODs (apply lods for all lod objects)"""
    bl_idname = "object.apply_all_lod"
    bl_label = "Apply All LODs (!)"
    bl_option = {'REGISTER', 'UNDO'}

    @classmethod
    def poll(cls, context):
        # we don't want to execute this operator if some objects are sharing mesh data.
        return objects_dont_share_data(get_all_lod_objects())

    def execute(self, context):
        apply_all_lods(get_all_lod_objects())
        bpy.ops.ed.undo_push()
        return {'FINISHED'}

# ----------


class ApplyLodOperator(bpy.types.Operator):
    """Apply the lods to the object"""
    bl_idname = "object.apply_lod"
    bl_label = "Apply LODs"
    bl_option = {'REGISTER', 'UNDO'}

    @classmethod
    def poll(cls, context):
        # we don't want to execute this operator if select objects are sharing mesh data.
        return (context.active_object is not None) and (objects_dont_share_data(context.selected_objects))

    def execute(self, context):
        return self.apply_all_lods(context)

    def apply_all_lods(self, context):
        apply_all_lods(context.selected_objects)
        bpy.ops.ed.undo_push()
        return {'FINISHED'}

# ----------


class RemoveLodOperator(bpy.types.Operator):
    """Removes the lods modifier from the selected objects"""
    bl_idname = "object.remove_lod"
    bl_label = "Remove Lods"
    bl_option = {'REGISTER', 'UNDO'}

    @classmethod
    def poll(cls, context):
        return context.active_object is not None

    def execute(self, context):
        remove_all_lods(context.selected_objects)
        bpy.ops.ed.undo_push()
        return {'FINISHED'}


# ----------


class RemoveAllLodOperator(bpy.types.Operator):
    """Removes the lods modifier from all objects"""
    bl_idname = "object.remove_all_lod"
    bl_label = "Remove All Lods"
    bl_option = {'REGISTER', 'UNDO'}

    @classmethod
    def poll(cls, context):
        return context.active_object is not None

    def execute(self, context):
        remove_all_lods(get_all_lod_objects())
        bpy.ops.ed.undo_push()
        return {'FINISHED'}

# ----------


class UpdateLodOperator(bpy.types.Operator):
    """Add a lod modifier for the selected objects"""
    bl_idname = "object.update_lod"
    bl_label = "Update All Lods"
    bl_option = {'REGISTER', 'UNDO'}

    @classmethod
    def poll(cls, context):
        return context.active_object is not None

    def execute(self, context):
        return self.update_lods()

    def update_lods(self):
        add_decimate_modifiers(get_all_lod_objects())
        bpy.ops.ed.undo_push()
        return {'FINISHED'}

# ----------


class SetLodOperator(bpy.types.Operator):
    """Add a lod modifier for the selected objects"""
    bl_idname = "object.set_lod"
    bl_label = "Set Lods"
    bl_option = {'REGISTER', 'UNDO'}

    @classmethod
    def poll(cls, context):
        return context.active_object is not None

    def execute(self, context):
        return self.add_lods(context)

    def add_lods(self, context):
        add_decimate_modifiers(context.selected_objects)
        bpy.ops.ed.undo_push()
        return {'FINISHED'}

# ----------


# ---------- ---------- UI ---------- ----------

def draw_lod_panel(scene, layout):

    draw_properties(scene, layout)

    layout.separator()
    draw_local_ops(layout)

    layout.separator()
    draw_global_ops(layout)

    layout.separator()
    draw_export_op(layout)

# ----------


def draw_local_ops(layout):
    layout.label(text="Operations on selected object(s):")

    box = layout.box()
    box.scale_y = 2

    box.operator(SetLodOperator.bl_idname)
    box.operator(RemoveLodOperator.bl_idname)

    if ApplyLodOperator.poll(bpy.context):
        box.operator(ApplyLodOperator.bl_idname)
    else:
        box.label(
            text="Some objects share mesh, create separate users before apply")

# ----------


def draw_properties(scene, layout):
    layout.label(text="LOD Properties :")

    box = layout.box()

    box.prop(scene, "lod_target")
    box.prop(scene, "agressivity")
    box.prop(scene, "lod_max_level")
    box.prop(scene, "lod_bias", text="LOD bias")
    box.prop(scene, "lod_start_dist")
    box.prop(scene, "lod_ratio_multiplier")

# ----------


def draw_global_ops(layout):
    layout.label(text="Operations on all objects :")

    box = layout.box()
    box.scale_y = 2

    box.operator(ApplyAllLodOperator.bl_idname)
    box.operator(UpdateLodOperator.bl_idname)
    box.operator(RemoveAllLodOperator.bl_idname)

# ----------


def draw_export_op(layout):
    layout.label(text="Export :")

    box = layout.box()
    box.scale_y = 2

    box.operator(ExportLodOperatorObj
                 .bl_idname)

# ----------


class LOD_PT_lod_panel_scene(bpy.types.Panel):
    bl_label = "LODs"
    bl_category = "LOD Panel"
    bl_space_type = 'PROPERTIES'
    bl_region_type = 'WINDOW'
    bl_context = "scene"

    def draw(self, context):
        draw_lod_panel(context.scene, self.layout)

# ----------


class LOD_PT_lod_panel_view_3D(bpy.types.Panel):
    bl_label = "LODs"
    bl_space_type = 'VIEW_3D'
    bl_region_type = 'UI'
    bl_category = "LODs"

    def draw(self, context):
        draw_lod_panel(context.scene, self.layout)

# ----------


# ---------- ---------- Register & Unregister ---------- ----------


def register():
    bpy.utils.register_class(SetLodOperator)
    bpy.utils.register_class(RemoveLodOperator)
    bpy.utils.register_class(ApplyLodOperator)

    bpy.utils.register_class(LOD_PT_lod_panel_scene)
    bpy.utils.register_class(LOD_PT_lod_panel_view_3D)

    bpy.utils.register_class(ApplyAllLodOperator)
    bpy.utils.register_class(UpdateLodOperator)
    bpy.utils.register_class(RemoveAllLodOperator)

    bpy.utils.register_class(ExportLodOperatorObj)


def unregister():
    bpy.utils.unregister_class(SetLodOperator)
    bpy.utils.unregister_class(RemoveLodOperator)
    bpy.utils.unregister_class(ApplyLodOperator)

    bpy.utils.unregister_class(LOD_PT_lod_panel_scene)
    bpy.utils.unregister_class(LOD_PT_lod_panel_view_3D)

    bpy.utils.unregister_class(ApplyAllLodOperator)
    bpy.utils.unregister_class(UpdateLodOperator)
    bpy.utils.unregister_class(RemoveAllLodOperator)

    bpy.utils.unregister_class(ExportLodOperatorObj)


if __name__ == "__main__":
    register()
