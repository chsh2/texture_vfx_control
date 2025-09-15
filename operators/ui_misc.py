import bpy
from ..utils import node_utils

class SetNodeActiveOperator(bpy.types.Operator):
    """Set a texture node group active for user interactions"""
    bl_idname = "tfx.set_node_active"
    bl_label = "Set Shader Node Active By Texture Name"
    bl_category = 'View'
    bl_options = {'REGISTER', 'INTERNAL'}
    
    image_name: bpy.props.StringProperty(default='')
    
    def execute(self, context):
        if (context.object is None) or (context.object.active_material is None):
            return {'CANCELLED'}
        
        tex_groups_map, _ = node_utils.list_tfx_node_groups(context.object.active_material)
        if self.image_name in tex_groups_map:
            context.object.active_material.node_tree.nodes.active = tex_groups_map[self.image_name][0]
            return {'FINISHED'}
                
        return {'FINISHED'}
