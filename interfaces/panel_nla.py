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
    bl_order = 0
    
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
        row = layout.box().row()
        row.enabled = is_modal_running()
        row.prop(strip.action, '["tfxHideBefore"]', text="Before Start")
        row.prop(strip.action, '["tfxHideAfter"]', text="After End")
        layout.label(text="Transition:")
        box = layout.box()
        box.prop(strip.action, '["tfxInLength"]', text="In Frames")
        box.prop(strip.action, '["tfxOutLength"]', text="Out Frames")
        layout.label(text="Playing Mode:")
        box = layout.box()
        box.enabled = is_modal_running()
        box.prop(strip, "scale")
        box.prop(strip, "repeat")
        box.prop(strip, "use_reverse")
        box = box.box()
        box.label(text="Extend (Hold Last/First Frame):")
        row = box.row()
        row.label(text="Start:")
        row.prop(strip, "action_frame_start", text="")
        row.label(text=f" / {strip.action.frame_range[0]:.0f}")
        row = box.row()
        row.label(text="End:")
        row.prop(strip, "action_frame_end", text="")
        row.label(text=f" / {strip.action.frame_range[1]:.0f}")
        row = box.row()
        row.operator("nla.action_sync_length", text="Reset", icon="FILE_REFRESH")
        layout.operator("tfx.append_media")

class TFX_PT_panel_editor_settings(bpy.types.Panel):
    bl_idname = 'TFX_PT_panel_editor_settings'
    bl_label = "Editor Settings"
    bl_space_type = "NLA_EDITOR"
    bl_region_type = "UI"
    bl_category = "TexFX"
    bl_context = "objectmode"
    bl_order = 1
    
    @classmethod
    def poll(cls, context):
        return context.workspace.name == "Media Playback"

    def draw(self, context):
        layout = self.layout
        layout.label(text="Synchronize keyframes:")
        box = layout.box()
        box.prop(context.scene, 'tfx_editor_sync_frames_fx')
        box.prop(context.scene, 'tfx_editor_sync_obj_properties')
        box.prop(context.scene, 'tfx_editor_sync_mat_properties')