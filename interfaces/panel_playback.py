import bpy
from ..utils import node_utils

class TFX_PT_panel_playback_control(bpy.types.Panel):
    bl_idname = 'TFX_PT_panel_playback_control'
    bl_label = "Playback Control"
    bl_space_type = "VIEW_3D"
    bl_region_type = "UI"
    bl_category = "TexFX"
    bl_context = "objectmode"
    bl_order = 2
    
    @classmethod
    def poll(cls, context):
        image_node, _ = node_utils.get_active_image_node(check=True)
        return image_node and image_node.image and image_node.image.source in ('SEQUENCE', 'MOVIE')
    
    def draw(self, context):
        image_node, media_node_tree = node_utils.get_active_image_node()
        top_node = context.object.active_material.node_tree.nodes.active
        
        layout = self.layout
        if "tfxPlaybackControl" not in top_node.node_tree or top_node.node_tree["tfxPlaybackControl"] == 0:
            layout.operator("tfx.add_playback_driver", icon='ADD')
            
        elif top_node.node_tree["tfxPlaybackControl"] == 1:
            if "tfxPlayhead" in top_node.node_tree:
                layout.prop(top_node.node_tree, '["tfxPlayhead"]', text="Playhead")
            row = layout.row()
            row.operator("tfx.refresh_playback_drivers", text="Refresh", icon='FILE_REFRESH')
            row.operator("tfx.remove_playback_driver", text="Remove", icon='X')
        
        elif top_node.node_tree["tfxPlaybackControl"] == 2:
            layout.operator("tfx.open_playback_manager_workspace", icon='SEQ_SEQUENCER')
            row = layout.row()
            row.operator("tfx.refresh_playback_drivers", text="Refresh", icon='FILE_REFRESH')
            row.operator("tfx.remove_playback_driver", text="Remove", icon='X')