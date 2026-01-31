import bpy
from ..operators.playback_control_modal import is_modal_running

def draw_nla_header(self, context):
    if context.workspace.name == "Media Playback":
        self.layout.operator("tfx.playback_manager_modal", text="Video Editor Mode", icon='FILE_MOVIE', depress=is_modal_running())

class TFX_PT_panel_strip_properties(bpy.types.Panel):
    bl_idname = 'TFX_PT_panel_strip_properties'
    bl_label = "Video Strip"
    bl_space_type = "NLA_EDITOR"
    bl_region_type = "UI"
    bl_category = "TexFX"
    bl_context = "objectmode"
    bl_order = 2
    
    @classmethod
    def poll(cls, context):
        return (context.workspace.name == "Media Playback"
        and len(context.selected_nla_strips) > 0
        and context.selected_nla_strips[0].action is not None
        and "tfxMediaNodeGroup" in context.selected_nla_strips[0].action)

    def draw(self, context):
        strip = context.selected_nla_strips[0]
        layout = self.layout
        layout.label(text="Hide the video:")
        row = layout.row()
        row.enabled = is_modal_running()
        row.prop(strip.action, '["tfxHideBefore"]', text="Before Start")
        row.prop(strip.action, '["tfxHideAfter"]', text="After End")