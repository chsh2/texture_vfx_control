
bl_info = {
    "name" : "Texture VFX Control",
    "author" : "https://github.com/chsh2/",
    "description" : "Shader-based video playback control and composition VFXs",
    "blender" : (3, 3, 0),
    "version" : (0, 1, 0),
    "location" : "Node Editor",
    "warning" : "This addon is still in an early stage of development",
    "doc_url": "",
    "wiki_url": "",
    "tracker_url": "",
    "category" : "Node"
}

import bpy
from . import auto_load

auto_load.init()

class NODE_MT_add_tfx_submenu(bpy.types.Menu):
    bl_label = "Texture VFX Control"
    bl_idname = "NODE_MT_add_tfx_submenu"

    def draw(self, context):
        layout = self.layout
        layout.operator("node.tfx_add_playback_driver", icon='PLAY')
        layout.operator("node.tfx_grainy_blur", icon='SHADERFX')
        layout.operator("node.tfx_chroma_key", icon='SHADERFX')
        layout.operator("node.tfx_outline", icon='SHADERFX')
        layout.operator("node.tfx_append_node_groups", icon='NODE')

def menu_func(self, context):
    layout = self.layout
    layout.menu("NODE_MT_add_tfx_submenu", icon='SHADERFX')

def register():
    auto_load.register()
    bpy.utils.register_class(NODE_MT_add_tfx_submenu)
    bpy.types.NODE_MT_add.append(menu_func)
    bpy.types.VIEW3D_MT_object_quick_effects.append(menu_func)
    
def unregister():
    auto_load.unregister()
    bpy.utils.unregister_class(NODE_MT_add_tfx_submenu)
    bpy.types.NODE_MT_add.remove(menu_func)
    bpy.types.VIEW3D_MT_object_quick_effects.remove(menu_func)