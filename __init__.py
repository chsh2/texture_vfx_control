bl_info = {
    "name" : "Texture VFX Control",
    "author" : "https://github.com/chsh2/texture_vfx_control",
    "description" : "Playback and VFX management for media textures to provide a video-editor-like experience in the 3D space",
    "blender" : (4, 2, 0),
    "version" : (1, 0, 0),
    "warning" : "This addon is still in an early stage of development",
    "doc_url": "",
    "wiki_url": "",
    "tracker_url": "https://github.com/chsh2/texture_vfx_control/issues",
    "category" : "Node"
}

import bpy
from . import auto_load

auto_load.init()

def register():
    auto_load.register()
    
def unregister():
    auto_load.unregister()