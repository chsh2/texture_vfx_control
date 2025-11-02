import bpy
from bpy_extras.io_utils import ImportHelper, ExportHelper
import json
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



def generate_json_config():
    json_output = {"effects": []}
    chain = node_utils.get_effect_chain_nodes()
    for i,tree_info in enumerate(chain):
        if i == 0:
            continue
        if "TfxParam" not in tree_info[0].nodes:
            continue
        effect_json = {"name": tree_info[1], "parameters": {}, "node_attributes": []}

        params = tree_info[0].nodes["TfxParam"].node_tree.nodes["Group Output"].inputs
        for param in params:
            if not param.name:
                continue
            effect_json["parameters"][param.name] = {"type": param.type, "value": param.default_value}
        
        promoted_params = [] if "tfxPromoted" not in tree_info[0] else tree_info[0]["tfxPromoted"]
        for p in promoted_params:
            node = tree_info[0].nodes[p[0]]
            attr_value = getattr(node, p[1])
            v = None
            if isinstance(attr_value, str):
                v = attr_value
            elif isinstance(attr_value, bpy.types.ColorRamp):
                v = {
                    "elements": [], 
                    "interpolation": attr_value.interpolation,
                    "color_mode": attr_value.color_mode,
                    "hue_interpolation": attr_value.hue_interpolation,
                }
                for elem in attr_value.elements:
                    v["elements"].append({
                        "position": elem.position,
                        "color": [elem.color[0], elem.color[1], elem.color[2], elem.color[3]],
                    })
            elif isinstance(attr_value, bpy.types.CurveMapping):
                v = {"curves": []}
                for curve in attr_value.curves:
                    curve_data = {"points": []}
                    for point in curve.points:
                        curve_data["points"].append({
                            "location": [point.location[0], point.location[1]],
                            "handle_type": point.handle_type,
                        })
                    v["curves"].append(curve_data)
            else:
                continue
            effect_json["node_attributes"].append({"node": p[0], "attribute": p[1], "value": v})

        json_output["effects"].append(effect_json)

    json_output["effects"].reverse()
    return json.dumps(json_output, indent=4)

def apply_json_config(json_config):
    effects = json_config.get("effects", [])
    for effect in effects:
        fx = asset_manager.template_fx_lookup_map.get(effect["name"], None)
        if fx is None:
            continue
        node_name, file_name = fx["node_name"], fx["file"]
        bpy.ops.tfx.push_effect(
            fx_group_name=f'tfx_effect_{node_name}',
            param_group_name=f'tfx_param_{node_name}',
            asset_file_name=file_name
        )

    chain = node_utils.get_effect_chain_nodes()[:len(effects)+1]
    for config,tree_info in zip(effects, chain[:0:-1]):
        tree = tree_info[0]
        params = tree.nodes["TfxParam"].node_tree.nodes["Group Output"].inputs
        for param in params:
            if not param.name:
                continue
            if param.name in config["parameters"] and param.type == config["parameters"][param.name]["type"]:
                param.default_value = config["parameters"][param.name]["value"]
        
        for attr in config.get("node_attributes", []):
            node = tree.nodes[attr["node"]]
            if not hasattr(node, attr["attribute"]):
                continue
            attr_ref = getattr(node, attr["attribute"])
            v = attr["value"]
            if isinstance(attr_ref, str):
                setattr(node, attr["attribute"], v)
            elif isinstance(attr_ref, bpy.types.ColorRamp):
                attr_ref.interpolation = v.get("interpolation", 'LINEAR')
                attr_ref.color_mode = v.get("color_mode", 'RGB')
                attr_ref.hue_interpolation = v.get("hue_interpolation", 'NEAR')
                num_elems = len(attr_ref.elements)
                for e_idx,elem_data in enumerate(v.get("elements", [])):
                    if e_idx < num_elems:
                        elem = attr_ref.elements[e_idx]
                    else:
                        elem = attr_ref.elements.new(position=elem_data["position"])
                    elem.position = elem_data["position"]
                    elem.color = elem_data["color"]
            elif isinstance(attr_ref, bpy.types.CurveMapping):
                for curve,curve_data in zip(attr_ref.curves, v.get("curves", [])):
                    num_points = len(curve.points)
                    for p_idx,point_data in enumerate(curve_data.get("points", [])):
                        if p_idx < num_points:
                            point = curve.points[p_idx]
                        else:
                            point = curve.points.new(position=elem_data["location"][0],value=elem_data["location"][1])
                        point.location = point_data["location"]
                        point.handle_type = point_data.get("handle_type", 'AUTO')

class CopyEffectsChain(bpy.types.Operator):
    """Copy the effects chain configuration to clipboard as JSON"""
    bl_idname = "tfx.copy_effects_chain"
    bl_label = "Copy Effects Chain"
    bl_category = 'View'
    bl_options = {'REGISTER'}

    def execute(self, context):
        json_config = generate_json_config()
        context.window_manager.clipboard = json_config
        self.report({'INFO'}, "Effects chain configuration copied to clipboard.")
        return {'FINISHED'}

class PasteEffectsChain(bpy.types.Operator):
    """Add effects according to the JSON configuration from the clipboard"""
    bl_idname = "tfx.paste_effects_chain"
    bl_label = "Paste Effects Chain"
    bl_category = 'View'
    bl_options = {'REGISTER', 'UNDO'}

    def execute(self, context):
        json_config = context.window_manager.clipboard
        try:
            config = json.loads(json_config)
        except:
            self.report({'WARNING'}, "No configurations available in the clipboard.")
            return {'CANCELLED'}
        apply_json_config(config)
        return {'FINISHED'}

class SaveEffectsChain(bpy.types.Operator, ExportHelper):
    """Save the effects chain configuration to a preset file"""
    bl_idname = "tfx.save_effects_chain"
    bl_label = "Copy Effects Chain"
    bl_category = 'View'
    bl_options = {'PRESET'}

    filter_glob: bpy.props.StringProperty(
        default='*.json', 
        options={'HIDDEN'},
    )
    filename_ext='.json'

    def execute(self, context):
        json_config = generate_json_config()
        try:
            with open(self.filepath, 'w') as f:
                f.write(json_config)
            self.report({'INFO'}, f"Effects chain configuration saved to {self.filepath}.")
        except Exception as e:
            self.report({'WARNING'}, f"Failed to save configuration: {str(e)}")
            return {'CANCELLED'}
        return {'FINISHED'}

class LoadEffectsChain(bpy.types.Operator, ImportHelper):
    """Load effects chain configuration from a preset file"""
    bl_idname = "tfx.load_effects_chain"
    bl_label = "Load Effects Chain"
    bl_category = 'View'
    bl_options = {'REGISTER', 'UNDO', 'PRESET'}

    filter_glob: bpy.props.StringProperty(
        default='*.json', 
        options={'HIDDEN'},
    )
    
    def execute(self, context):
        try:
            with open(self.filepath, 'r') as f:
                json_config = f.read()
            config = json.loads(json_config)
        except Exception as e:
            self.report({'WARNING'}, f"Failed to load configuration: {str(e)}")
            return {'CANCELLED'}
        apply_json_config(config)
        return {'FINISHED'}