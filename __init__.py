bl_info = {
    "name" : "(Dev) Texture VFX Control",
    "author" : "https://github.com/chsh2/texture_vfx_control",
    "description" : "Shader-based video playback control and composition VFXs",
    "blender" : (4, 2, 0),
    "version" : (1, 0, 0),
    "location" : "View3D > Object > Quick Effects, or Shader Editor > Add",
    "warning" : "This addon is still in an early stage of development",
    "doc_url": "",
    "wiki_url": "",
    "tracker_url": "",
    "category" : "Node"
}

import bpy
from . import auto_load

auto_load.init()

def register():
    auto_load.register()
    
def unregister():
    auto_load.unregister()