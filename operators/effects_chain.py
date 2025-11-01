import bpy
from ..utils import asset_manager, node_utils, anim_utils

"""
Effects chain structure:
[Material] -> [Top (Interface Node Group)] -> [FX1 Node Group] -> [FX2 Node Group] -> ... -> [Root (Media Node Group)]
Top (depth==0) and Root (depth==-1) are not allowed to be popped/swapped.
"""

def set_next_depth(current_tree, next_tree):
    current_tree.nodes['TfxNext'].node_tree = next_tree
    i = 1
    while f'TfxNext.{i:03}' in current_tree.nodes:
        current_tree.nodes[f'TfxNext.{i:03}'].node_tree = next_tree
        i += 1

class PushEffectOperator(bpy.types.Operator):
    """Add a new effect to the media"""
    bl_idname = "tfx.push_effect"
    bl_label = "New Effect"
    bl_category = 'View'
    bl_options = {'REGISTER', 'UNDO'}
    
    fx_group_name: bpy.props.StringProperty(default='')
    param_group_name: bpy.props.StringProperty(default='')
    asset_file_name: bpy.props.StringProperty(default='')
    
    def execute(self, context):
        if not node_utils.is_active_node_tfx():
            return {'CANCELLED'}
        fx_node_group = asset_manager.create_node_group_instance(self.asset_file_name, self.fx_group_name)
        param_node_group = asset_manager.create_node_group_instance(self.asset_file_name, self.param_group_name)
        fx_node_group.nodes['TfxParam'].node_tree = param_node_group

        top_node = context.object.active_material.node_tree.nodes.active
        inner_node_tree = top_node.node_tree.nodes['TfxNext'].node_tree
        
        set_next_depth(top_node.node_tree, fx_node_group)
        set_next_depth(fx_node_group, inner_node_tree)

        if 'TfxRoot' in inner_node_tree.nodes:
            fx_node_group.nodes['TfxRoot'].node_tree = inner_node_tree.nodes['TfxRoot'].node_tree
        else:
            fx_node_group.nodes['TfxRoot'].node_tree = inner_node_tree
        
        return {'FINISHED'}

class PopEffectOperator(bpy.types.Operator):
    """Remove an effect from the chain"""
    bl_idname = "tfx.pop_effect"
    bl_label = "Remove Effect"
    bl_category = 'View'
    bl_options = {'REGISTER', 'UNDO'}

    depth: bpy.props.IntProperty()

    def execute(self, context):
        if not node_utils.is_active_node_tfx():
            return {'CANCELLED'}
        active_node = context.object.active_material.node_tree.nodes.active
        
        # Other cases
        chain = node_utils.get_effect_chain_nodes()
        if self.depth >= len(chain) or self.depth <= 0:
            return {'CANCELLED'}
        set_next_depth(chain[self.depth-1][0], chain[self.depth][0].nodes["TfxNext"].node_tree)

        return {'FINISHED'}
    
class SwapEffectOperator(bpy.types.Operator):
    """Reorder two adjacent effects in the chain"""
    bl_idname = "tfx.swap_effect"
    bl_label = "Swap Effect"
    bl_category = 'View'
    bl_options = {'REGISTER', 'UNDO'}

    depth: bpy.props.IntProperty() # Swap effects at depth and depth+1

    def execute(self, context):
        if not node_utils.is_active_node_tfx():
            return {'CANCELLED'}
        active_node = context.object.active_material.node_tree.nodes.active

        chain = node_utils.get_effect_chain_nodes()
        if self.depth >= len(chain)-1 or self.depth <= 0:
            return {'CANCELLED'}

        # Step 1: depth->depth+1 ==> depth->depth+2
        set_next_depth(chain[self.depth][0], chain[self.depth+1][0].nodes["TfxNext"].node_tree)

        # Step 2: depth-1->depth ==> depth-1->depth+1
        if self.depth > 0:
            set_next_depth(chain[self.depth-1][0], chain[self.depth+1][0])
        else:
            outer_nodes = [node for node in context.object.active_material.node_tree.nodes if node.type == 'GROUP' and node.node_tree == active_node.node_tree]
            for outer_node in outer_nodes:
                outer_node.node_tree = chain[self.depth+1][0]

        # Step 3: depth+1->depth+2 ==> depth+1->depth
        set_next_depth(chain[self.depth+1][0], chain[self.depth][0])

        return {'FINISHED'}
    
class SetEffectLocationDriverOperator(bpy.types.Operator):
    """Select an object to use its global location as a reference for the effect"""
    bl_idname = "tfx.set_effect_location_driver"
    bl_label = "Set Effect Location Driver"
    bl_category = 'View'
    bl_options = {'REGISTER', 'UNDO'}
    
    obj_name: bpy.props.StringProperty(
        name='Object',
        description='Select an object to use its global location as a reference',
        default='',
        search=lambda self, context, edit_text: [obj.name for obj in context.scene.objects]
    )
    node_group_name: bpy.props.StringProperty()
    
    def draw(self, context):
        layout = self.layout
        layout.prop(self, "obj_name", icon='OBJECT_DATA')
    
    def invoke(self, context, event):
        self.obj_name = ''
        return context.window_manager.invoke_props_dialog(self)
    
    def execute(self, context):
        if self.node_group_name not in bpy.data.node_groups:
            return {'CANCELLED'}
        
        tree = bpy.data.node_groups[self.node_group_name]
        subject = None
        if self.obj_name in bpy.data.objects:
            subject = bpy.data.objects[self.obj_name]
        
        anim_utils.set_global_location_driver(tree, subject)
        
        return {'FINISHED'}
    
class SetEffectTemporalDriverOperator(bpy.types.Operator):
    """Set speed of an animated effect by driving it using the scene frame"""
    bl_idname = "tfx.set_effect_temporal_driver"
    bl_label = "Set Effect Temporal Driver"
    bl_category = 'View'
    bl_options = {'REGISTER', 'UNDO'}
    
    node_group_name: bpy.props.StringProperty()
    param_name: bpy.props.StringProperty()
    length: bpy.props.IntProperty(
        name='Length',
        description='Frame duration of the effect animation',
        default=10, min=1, soft_max=128
    )
    offset: bpy.props.IntProperty(
        name='Offset',
        description='Frame offset of the effect animation',
        default=0, soft_min=-128, soft_max=128
    )

    def draw(self, context):
        layout = self.layout
        hint_text = {
            'Random Seed': "Frames per Seed:",
            'Phase': "Frames per Cycle:",
        }.get(self.param_name, "Frames")
        row = layout.row()
        row.label(text=hint_text)
        row.prop(self, "length", text="")
        row = layout.row()
        row.label(text="Frame Offset:")
        row.prop(self, "offset", text="")
    
    def invoke(self, context, event):
        return context.window_manager.invoke_props_dialog(self)

    def execute(self, context):
        if self.node_group_name not in bpy.data.node_groups:
            return {'CANCELLED'}
        from math import pi

        tree = bpy.data.node_groups[self.node_group_name]
        rate = 1.0
        if self.param_name == 'Random Seed':
            rate = 1.0 / self.length
        elif self.param_name == 'Phase':
            rate = 2.0 * pi / self.length
        anim_utils.set_linear_temporal_driver(tree, self.param_name, rate, self.offset)
        
        return {'FINISHED'}

class SetTransitionPlaybackDriverOperator(bpy.types.Operator):
    """Bind a transition effect to the video playhead or an action strip"""
    bl_idname = "tfx.set_transition_playback_driver"
    bl_label = "Set Transition Playback Driver"
    bl_category = 'View'
    bl_options = {'REGISTER', 'UNDO'}
    
    node_group_name: bpy.props.StringProperty()
    bind_to: bpy.props.EnumProperty(
        items=[ ('PLAYHEAD', 'Playhead', ''),
                ('STRIP', 'NLA Track Strip', '')],
        default='PLAYHEAD',
    )
    transition_type: bpy.props.EnumProperty(
        items=[ ('In', '', ''),
                ('Out', '', '')],
        default='In',
    )
    length: bpy.props.IntProperty(
        name='Length',
        description='Frame duration of the transition effect',
        default=10, min=1, soft_max=128
    )
    
    def draw(self, context):
        layout = self.layout
        #layout.prop(self, 'bind_to')
        layout.prop(self, "length")
    
    def invoke(self, context, event):
        top_node = context.object.active_material.node_tree.nodes.active
        if "tfxPlaybackControl" not in top_node.node_tree:
            self.report({'INFO'}, "The media does not have a playback controller.")
            return {'CANCELLED'}
        return context.window_manager.invoke_props_dialog(self)
    
    def execute(self, context):
        param_tree = bpy.data.node_groups[self.node_group_name]
        top_node = context.object.active_material.node_tree.nodes.active
        image_node, media_node_tree = node_utils.get_active_image_node()
        suffix = media_node_tree.name[len("tfx_texture_"):]
        
        if self.bind_to == 'PLAYHEAD':
            if top_node.node_tree["tfxPlaybackControl"] == 1:
                datapath_duration = 'tfxFrameDuration'
                datapath_playhead = 'tfxPlayhead'
                subject = top_node.node_tree
                id_type = 'NODETREE'
            else:
                datapath_duration = f'tfxFrameDuration_{suffix}'
                datapath_playhead = f'tfxPlayhead_{suffix}'
                subject = anim_utils.get_global_playback_manager()
                id_type = 'OBJECT'
            anim_utils.set_playhead_driver(
                param_tree, self.length, subject, id_type, datapath_playhead, datapath_duration, self.transition_type == 'Out'
            )
        else:
            subject = anim_utils.get_global_playback_manager()
            track_name, strip_name = None, None
            if subject and subject.animation_data:
                for track in subject.animation_data.nla_tracks:
                    for strip in track.strips:
                        if strip.action:
                            fcurves = anim_utils.get_action_fcurves(strip.action)
                            for fc in fcurves:
                                if fc.data_path == f'["tfxPlayhead_{suffix}"]':
                                    track_name = track.name
                                    strip_name = strip.name
                                    break
                            else:
                                continue
                            break
            if track_name is None:
                self.report({'INFO'}, "The media does not have any action strips.")
                return {'CANCELLED'}
            anim_utils.set_strip_driver(
                param_tree, self.length, subject, track_name, strip_name, self.transition_type == 'Out'
            )
                
        return {'FINISHED'}