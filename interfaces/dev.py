import bpy
from rna_prop_ui import PropertyPanel

"""
Show the default custom properties panel for shader node groups to edit metadata required by this add-on.
"""

#class NODE_PT_custom_props(PropertyPanel, bpy.types.Panel):
#    bl_label = "Custom Properties"
#    bl_space_type = 'NODE_EDITOR'
#    bl_region_type = 'UI'
#    bl_category = "Node"
#    _context_path = "space_data.edit_tree.nodes.active"
#    _property_type = bpy.types.Node
#    
#    @classmethod
#    def poll(cls, context):
#        space_data = context.space_data
#        return space_data.edit_tree and space_data.edit_tree.nodes.active

class NODE_TREE_PT_custom_props(PropertyPanel, bpy.types.Panel):
    bl_label = "Custom Properties"
    bl_space_type = 'NODE_EDITOR'
    bl_region_type = 'UI'
    bl_category = "Group"
    _context_path = "space_data.edit_tree"
    _property_type = bpy.types.NodeTree
    
    @classmethod
    def poll(cls, context):
        return context.space_data.edit_tree