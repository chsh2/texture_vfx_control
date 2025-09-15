import bpy
from ..utils import node_utils

class TFX_PT_panel_media_selection(bpy.types.Panel):
    bl_idname = 'TFX_PT_panel_media_selection'
    bl_label = "Media Selection"
    bl_space_type = "VIEW_3D"
    bl_region_type = "UI"
    bl_category = "TexFX"
    bl_context = "objectmode"
    bl_order = 0
    
    @classmethod
    def poll(cls, context):
        return (context.object is not None) and (context.object.active_material is not None) and (context.object.active_material.node_tree is not None)
    
    def draw(self, context):
        layout = self.layout
        tex_groups_map, active_name = node_utils.list_tfx_node_groups(context.object.active_material)
        
        for name in tex_groups_map:
            layout.operator("tfx.set_node_active", text=name, icon='FILE_IMAGE', depress=(active_name==name)).image_name = name
        layout.separator(factor=0.25, type="LINE")
        layout.operator("tfx.wrap_media", icon='ADD')
        
class TFX_PT_panel_media_properties(bpy.types.Panel):
    bl_idname = 'TFX_PT_panel_media_properties'
    bl_label = "Media Properties"
    bl_space_type = "VIEW_3D"
    bl_region_type = "UI"
    bl_category = "TexFX"
    bl_context = "objectmode"
    bl_options = {'DEFAULT_CLOSED'}
    bl_order = 1
    
    @classmethod
    def poll(cls, context):
        return node_utils.is_active_node_tfx()
    
    def draw(self, context):
        image_node, _ = node_utils.get_active_image_node()
        layout = self.layout
        
        layout.operator("tfx.replace_media", icon='FILEBROWSER')
        if image_node.image is not None:
            source_type = 'Movie' if image_node.image.source == 'MOVIE' else 'Sequence' if image_node.image.source == 'SEQUENCE' else 'Single Image'
            layout.label(text=f"{source_type}, {image_node.image.size[0]} x {image_node.image.size[1]}", icon='INFO')
            row = layout.row()
            row.label(text="Interpolation:")
            row.prop(image_node, 'interpolation', text='')
            row = layout.row()
            row.label(text="Extension:")
            row.prop(image_node, 'extension', text='')
            row = layout.row()
            row.label(text="Color Space:")
            row.prop(image_node.image.colorspace_settings, 'name', text='')
            row = layout.row()
            row.label(text="Alpha Mode:")
            row.prop(image_node.image, 'alpha_mode', text='')