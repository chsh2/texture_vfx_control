import bpy
from bpy_extras.io_utils import ImportHelper
from mathutils import Vector
from ..utils import anim_utils, media_utils

_is_playback_manager_modal_running = False
def is_modal_running():
    global _is_playback_manager_modal_running
    return _is_playback_manager_modal_running

def protect_nla_tracks():
    if is_modal_running():
        return

    key = "tfxPlaybackManager"
    subjects = []
    for scene in bpy.data.scenes:
        if key in scene and scene[key].name in scene.objects:
            subjects.append(scene[key])

    for subject in subjects:
        if subject.animation_data is not None:
            for track in subject.animation_data.nla_tracks:
                track.lock = True

class StripMode:
    LOOP = 1
    EXTEND = 2
    PINGPONG = 3

class StripState:
    def __init__(self, strip, hide_before=False, hide_after=False):
        self.strip = strip
        self.frame_start = strip.frame_start
        self.frame_end = strip.frame_end
        self.hide_before = hide_before
        self.hide_after = hide_after
        self.scale = strip.scale
        self.select = strip.select

def select_objects_by_strips(context):
    if context.selected_nla_strips is None:
        return
    for obj in context.selected_objects:
        obj.select_set(False)
    objs = [o for o in context.scene.objects if o.data and hasattr(o.data, "materials")]
    media_node_groups = set()
    for strip in context.selected_nla_strips:
        if strip.action and "tfxMediaNodeGroup" in strip.action:
            media_node_groups.add(strip.action["tfxMediaNodeGroup"].name)
    for obj in objs:
        for slot in obj.material_slots:
            mat = slot.material
            if mat and mat.node_tree:
                group_nodes = [node for node in mat.node_tree.nodes if node.type == 'GROUP' and node.node_tree]
                for group_node in group_nodes:
                    if 'TfxRoot' in group_node.node_tree.nodes:
                        inner_node_tree = group_node.node_tree.nodes['TfxRoot'].node_tree
                        if inner_node_tree.name in media_node_groups:
                            mat.node_tree.nodes.active = group_node
                            obj.active_material_index = slot.slot_index
                            obj.select_set(True)
                            context.view_layer.objects.active = obj
                            break

def set_strip_visibility(strip_state):
    strip = strip_state.strip
    subjects = []
    if strip.action and "tfxMediaNodeGroup" in strip.action:
        for mat in bpy.data.materials:
            if mat.node_tree:
                group_nodes = [node for node in mat.node_tree.nodes if node.type == 'GROUP' and node.node_tree]
                for group_node in group_nodes:
                    if 'TfxRoot' in group_node.node_tree.nodes:
                        inner_node_tree = group_node.node_tree.nodes['TfxRoot'].node_tree
                        if inner_node_tree.name == strip.action["tfxMediaNodeGroup"].name:
                            subjects.append((mat.node_tree, group_node))
    for subject, group_node in subjects:
        datapath = f'nodes["{group_node.name}"].inputs[1].default_value'
        if subject.animation_data and subject.animation_data.action:
            fcurves = anim_utils.get_action_fcurves(subject.animation_data.action)
            fc = fcurves.find(datapath)
            if fc:
                fcurves.remove(fc)
        frame_current = bpy.context.scene.frame_current
        if strip_state.hide_before:
            bpy.context.scene.frame_set(int(strip_state.frame_start - 1))
            group_node.inputs[1].default_value = True
            subject.keyframe_insert(datapath)
            bpy.context.scene.frame_set(int(strip_state.frame_start))
            group_node.inputs[1].default_value = False
            subject.keyframe_insert(datapath)
        if strip_state.hide_after:
            bpy.context.scene.frame_set(int(strip_state.frame_end))
            group_node.inputs[1].default_value = False
            subject.keyframe_insert(datapath)
            bpy.context.scene.frame_set(int(strip_state.frame_end + 1))
            group_node.inputs[1].default_value = True
            subject.keyframe_insert(datapath)
        bpy.context.scene.frame_set(frame_current)

def get_strip_flags(strip, fc):
    flags = set()
    if strip.action is None or "tfxMediaNodeGroup" not in strip.action:
        return flags
    if abs(strip.repeat - 1.0) > 1e-6:
        flags.add(StripMode.LOOP)
    if abs(strip.action_frame_end - strip.action.frame_range[1]) + abs(strip.action_frame_start - strip.action.frame_range[0]) > 1e-6:
        flags.add(StripMode.EXTEND)
    if len(fc.keyframe_points) != 2:
        flags.add(StripMode.PINGPONG)
    return flags

def trim_strip(strip, trim_type, frame_delta):
    if strip.action is None or "tfxMediaNodeGroup" not in strip.action:
        return False

    media_node_group = strip.action["tfxMediaNodeGroup"]
    media_ub = media_utils.get_media_duration(media_node_group.nodes['TfxMedia'].image)
    suffix = media_node_group.name.split('_')[-1]
    manager = anim_utils.get_global_playback_manager()
    fcurves = anim_utils.get_action_fcurves(strip.action)
    fc = fcurves.find(f'["tfxPlayhead_{suffix}"]')
    flags = get_strip_flags(strip, fc)

    if StripMode.EXTEND in flags:
        if trim_type == 2:
            if not strip.use_reverse:
                strip.action_frame_end += frame_delta / strip.scale
            else:
                strip.action_frame_start -= frame_delta / strip.scale
        if trim_type == 1:
            if not strip.use_reverse:
                strip.action_frame_start += frame_delta / strip.scale
            else:
                strip.action_frame_end -= frame_delta / strip.scale
            strip.action_frame_end = max(strip.action_frame_end, strip.action_frame_start + 1)
            strip.frame_start += frame_delta
            strip.frame_end += frame_delta
        return True
    
    if StripMode.LOOP in flags or StripMode.PINGPONG in flags:
        if trim_type == 2:
            strip.repeat += frame_delta / (strip.frame_end - strip.frame_start) * strip.repeat
            strip.repeat = max(0.1, strip.repeat)
        return True

    if trim_type == 2:
        frame_delta = max(frame_delta, strip.frame_start - strip.frame_end + 1)
    if trim_type == 1:
        frame_delta = min(frame_delta, strip.frame_end - strip.frame_start - 1)
    frame_delta = round(frame_delta / strip.scale) * strip.scale
    if strip.use_reverse:
        frame_delta = -frame_delta
    if (trim_type == 2 and not strip.use_reverse) or (trim_type == 1 and strip.use_reverse):
        current_ub = manager[f'tfxFirstFrame_{suffix}'] + manager[f'tfxFrameDuration_{suffix}'] - 1
        frame_delta = min(frame_delta, (media_ub - current_ub) * strip.scale)
        manager[f'tfxFrameDuration_{suffix}'] += int(frame_delta / strip.scale)
    if (trim_type == 1 and not strip.use_reverse) or (trim_type == 2 and strip.use_reverse):
        current_lb = manager[f'tfxFirstFrame_{suffix}']
        frame_delta = max(frame_delta, (1 - current_lb) * strip.scale)
        manager[f'tfxFirstFrame_{suffix}'] += int(frame_delta / strip.scale)
        manager[f'tfxFrameDuration_{suffix}'] -= int(frame_delta / strip.scale)  

    fc.keyframe_points[-1].co.x = fc.keyframe_points[0].co.x + manager[f'tfxFrameDuration_{suffix}'] - 1
    fc.update()
    strip.action_frame_end = strip.action.frame_range[1]
    if strip.use_reverse:
        frame_delta = -frame_delta
    if trim_type == 1:
        strip.frame_start += frame_delta
        strip.frame_end += frame_delta
    return True

def remap_keyframes(old_state, new_state, use_left_pivot=True):
    strip = new_state.strip
    if strip.action is None or "tfxMediaNodeGroup" not in strip.action:
        return False
    strip.action["tfxStripStart"] = new_state.frame_start
    strip.action["tfxStripEnd"] = new_state.frame_end
    strip.action.update_tag()

    media_node_group = strip.action["tfxMediaNodeGroup"]
    fc_to_remap = []

    groups_to_map = set()
    for group in bpy.data.node_groups:
        if "TfxRoot" in group.nodes and group.nodes["TfxRoot"].type == 'GROUP' and group.nodes["TfxRoot"].node_tree == media_node_group:
            groups_to_map.add(group.name)
            if "tfxName" in group and group["tfxName"] == "Interface":
                continue
            if bpy.context.scene.tfx_editor_sync_frames_fx:
                if group.animation_data and group.animation_data.action:
                    fcurves = anim_utils.get_action_fcurves(group.animation_data.action)
                    fc_to_remap += [f for f in fcurves]
                if "TfxParam" in group.nodes and group.nodes["TfxParam"].node_tree:
                    param_group = group.nodes["TfxParam"].node_tree
                    if param_group.animation_data and param_group.animation_data.action:
                        fcurves = anim_utils.get_action_fcurves(param_group.animation_data.action)
                        fc_to_remap += [f for f in fcurves]

    mats_to_map = set()
    if bpy.context.scene.tfx_editor_sync_obj_properties or bpy.context.scene.tfx_editor_sync_mat_properties:
        for mat in bpy.data.materials:
            if mat.node_tree:
                group_nodes = [node for node in mat.node_tree.nodes if node.type == 'GROUP' and node.node_tree]
                for group_node in group_nodes:
                    if group_node.node_tree.name in groups_to_map:
                        mats_to_map.add(mat.name)
                        if bpy.context.scene.tfx_editor_sync_mat_properties and mat.node_tree.animation_data and mat.node_tree.animation_data.action:
                            fcurves = anim_utils.get_action_fcurves(mat.node_tree.animation_data.action)
                            fc_to_remap += [f for f in fcurves]
                        break
    
    if bpy.context.scene.tfx_editor_sync_obj_properties:
        for obj in bpy.data.objects:
            if obj.data and hasattr(obj.data, "materials"):
                for slot in obj.material_slots:
                    mat = slot.material
                    if mat and mat.name in mats_to_map:
                        if obj.animation_data and obj.animation_data.action:
                            fcurves = anim_utils.get_action_fcurves(obj.animation_data.action)
                            fc_to_remap += [f for f in fcurves]
                        break

    scale_factor = new_state.scale / old_state.scale
    for fc in fc_to_remap:
        for kp in fc.keyframe_points:
            if use_left_pivot:
                kp.co.x = new_state.frame_start + (kp.co.x - old_state.frame_start) * scale_factor
            else:
                kp.co.x = new_state.frame_end - (old_state.frame_end - kp.co.x) * scale_factor
        fc.update()
    return True

class PlaybackManagerModalOperator(bpy.types.Operator):
    """Custom UI for editing multiple video strips in the NLA editor"""
    bl_idname = "tfx.playback_manager_modal"
    bl_label = "Playback Manager Modal"
    bl_category = 'View'
    bl_options = {'REGISTER', 'INTERNAL'}

    _area = None
    _workspace = None
    _dragging_type = 0
    _trim_mode = False
    _dragging_mode = False
    _dragging_start_frame = -1
    _dragging_end_frame = -1
    _strips_state = {}

    def update_state(self, context):
        new_state = {}
        selection_changed = False
        state_changed = {}

        subject = anim_utils.get_global_playback_manager()
        if subject.animation_data is None:
            return selection_changed, state_changed
        for track in subject.animation_data.nla_tracks:
            to_purge = []
            # For now, only one strip is allows for one media node group
            for i,strip in enumerate(track.strips):
                if strip.action is None or "tfxMediaNodeGroup" not in strip.action:
                    to_purge.append(strip)
                    continue
                node_group = strip.action["tfxMediaNodeGroup"]
                if node_group.name in new_state:
                    to_purge.append(strip)
                    continue
                new_state[node_group.name] = StripState(
                    strip,
                    hide_before=strip.action.get("tfxHideBefore", False),
                    hide_after=strip.action.get("tfxHideAfter", False)
                )

            for strip in to_purge:
                track.strips.remove(strip)
        
        for key, strip_state in new_state.items():
            if key not in self._strips_state:
                state_changed[key] = None
            else:
                if (self._strips_state[key].frame_start != strip_state.frame_start or
                    self._strips_state[key].frame_end != strip_state.frame_end or
                    self._strips_state[key].hide_before != strip_state.hide_before or
                    self._strips_state[key].hide_after != strip_state.hide_after or
                    self._strips_state[key].scale != strip_state.scale):
                    state_changed[key] = self._strips_state[key]
                if self._strips_state[key].select != strip_state.select:
                    selection_changed = True

        self._strips_state = new_state
        return selection_changed, state_changed

    def cleanup(self):
        global _is_playback_manager_modal_running
        _is_playback_manager_modal_running = False
        protect_nla_tracks()
        return {'CANCELLED'}

    def invoke(self, context, event):
        global _is_playback_manager_modal_running
        if _is_playback_manager_modal_running:
            return self.cleanup()

        self._workspace = context.workspace
        self._scene = context.scene

        context.window_manager.modal_handler_add(self)
        _is_playback_manager_modal_running = True
        _, state_changed = self.update_state(context)
        for key in state_changed:
            set_strip_visibility(self._strips_state[key])

        subject = anim_utils.get_global_playback_manager()
        if subject.animation_data:
            for track in subject.animation_data.nla_tracks:
                track.lock = False

        return {'RUNNING_MODAL'}

    def modal(self, context, event):
        global _is_playback_manager_modal_running
        if not _is_playback_manager_modal_running or context.window.workspace != self._workspace or context.scene != self._scene:
            return self.cleanup()

        if context.area is None or context.area.type != 'NLA_EDITOR':
            return {'PASS_THROUGH'}

        if event.type == 'LEFTMOUSE' and event.value == 'PRESS':
            v2d = context.region.view2d
            self._dragging_type = 0
            dragging_handler_size = 6
            for strip in context.selected_nla_strips:
                x1 = v2d.view_to_region(strip.frame_start, 0, clip=False)[0]
                x2 = v2d.view_to_region(strip.frame_end, 0, clip=False)[0]
                if abs(event.mouse_region_x - x2) < dragging_handler_size:
                    self._dragging_start_frame = strip.frame_end
                    self._dragging_type = 2
                    break
                elif abs(event.mouse_region_x - x1) < dragging_handler_size:
                    self._dragging_start_frame = strip.frame_start
                    self._dragging_type = 1
                    break
            
        refresh_needed = False
        if event.type == 'LEFTMOUSE' and event.value == 'CLICK_DRAG':
            if self._dragging_type != 0:
                self._trim_mode = True
                context.window.cursor_set('KNIFE')
                return {'RUNNING_MODAL'}
            else:
                self._dragging_mode = True
                
        if self._trim_mode and event.type == 'LEFTMOUSE' and event.value == 'RELEASE':
            self._trim_mode = False
            context.window.cursor_set('DEFAULT')
            v2d = context.region.view2d
            self._dragging_end_frame = v2d.region_to_view(event.mouse_region_x, 0)[0]
            frame_delta = self._dragging_end_frame - self._dragging_start_frame
            for strip in context.selected_nla_strips:
                trim_strip(strip, self._dragging_type, frame_delta)

        if self._dragging_mode and event.type == 'MOUSEMOVE':
            self._dragging_mode = False
            refresh_needed = True

        if event.type in ('LEFTMOUSE', 'RET', 'TAB') and event.value == 'RELEASE':
            refresh_needed = True

        if refresh_needed:
            selection_changed, state_changed = self.update_state(context)
            if selection_changed:
                select_objects_by_strips(context)
            for key, old_state in state_changed.items():
                if old_state is not None:
                    remap_keyframes(old_state, self._strips_state[key], use_left_pivot=(self._dragging_type != 1))
            for key in state_changed:
                set_strip_visibility(self._strips_state[key])
            if len(state_changed) > 0:
                bpy.context.view_layer.update()

        return {'PASS_THROUGH'}

class AppendMediaOperator(bpy.types.Operator, ImportHelper):
    """Insert another media after the currently selected strip. Mesh, material and related settings will be inherited from the current strip"""
    bl_idname = "tfx.append_media"
    bl_label = "Append Media"
    bl_category = 'View'
    bl_options = {'REGISTER', 'UNDO'}

    directory: bpy.props.StringProperty(subtype='DIR_PATH')
    files: bpy.props.CollectionProperty(type=bpy.types.OperatorFileListElement)
    filepath = bpy.props.StringProperty(name="File Path", subtype='FILE_PATH')
    filter_folder: bpy.props.BoolProperty(default=True, options={'HIDDEN'})
    filter_image: bpy.props.BoolProperty(default=True, options={'HIDDEN'})
    filter_movie: bpy.props.BoolProperty(default=True, options={'HIDDEN'})
    delta_location: bpy.props.FloatVectorProperty(
        default = (1e-4, 1e-4, 1e-4),
        name = "Location Offset",
        description='Apply a small offset to the location of the object, since completely overlapping objects may lead to display errors',
    )

    def draw(self, context):
        layout = self.layout
        layout.label(text="Location Offset:")
        layout.prop(self, "delta_location", text="")

    def execute(self, context):
        if context.selected_nla_strips is None:
            return {'CANCELLED'}
        nla_strips = [s for s in context.selected_nla_strips if s.action and "tfxMediaNodeGroup" in s.action]
        if len(nla_strips) < 1:
            return {'CANCELLED'}
        for strip in nla_strips:
            strip.select = False
        src_strip = nla_strips[0]
        src_media_node_group = src_strip.action["tfxMediaNodeGroup"]

        # Find the object and material to duplicate
        objs = [o for o in context.scene.objects if o.data and hasattr(o.data, "materials")]
        src_obj = None
        src_slot_idx = -1
        node_to_replace = None
        for obj in objs:
            for i,slot in enumerate(obj.material_slots):
                mat = slot.material
                if mat and mat.node_tree:
                    group_nodes = [node for node in mat.node_tree.nodes if node.type == 'GROUP' and node.node_tree]
                    for group_node in group_nodes:
                        if 'TfxRoot' in group_node.node_tree.nodes:
                            inner_node_tree = group_node.node_tree.nodes['TfxRoot'].node_tree
                            if inner_node_tree.name == src_media_node_group.name:
                                node_to_replace = group_node.name
                                src_obj = obj
                                src_slot_idx = i
                                break
                if src_obj is not None:
                    break
            if src_obj is not None:
                break

        # Use the native operator to load files, which can detect movie or sequence automatically
        files_dict = [{"name": f.name} for f in self.files]
        images_pre = {img.name: img for img in bpy.data.images}
        bpy.ops.image.open(
            filepath=self.filepath,
            directory=self.directory, 
            files=files_dict, 
            relative_path=True,
            use_sequence_detection=True, use_udim_detecting=True
        )
        images_post = {img.name: img for img in bpy.data.images}
        
        # The user may import multiple files, but only one can be loaded in the node group
        target_image = None
        for name in images_post:
            if name not in images_pre:
                target_image = images_post[name]
                break
        for item in files_dict:
            if item["name"] in images_post:
                target_image = images_post[item["name"]]
                break
        if target_image is None:
            self.report({'ERROR'}, 'Failed to load new media file')
            return {'CANCELLED'}

        # Duplicate object, mesh, material and replace the media node
        context.scene.frame_set(int(src_strip.frame_end + 1))
        dst_obj = bpy.data.objects.new(target_image.name, src_obj.data.copy())
        dst_obj.data.name = target_image.name
        context.collection.objects.link(dst_obj)

        dst_obj.parent_type = src_obj.parent_type
        dst_obj.parent = src_obj.parent
        dst_obj.parent_bone = src_obj.parent_bone
        dst_obj.parent_vertices = src_obj.parent_vertices
        
        dst_obj.location = src_obj.location
        dst_obj.rotation_mode = src_obj.rotation_mode
        dst_obj.rotation_euler = src_obj.rotation_euler
        dst_obj.rotation_quaternion = src_obj.rotation_quaternion
        dst_obj.rotation_axis_angle = src_obj.rotation_axis_angle
        dst_obj.scale = src_obj.scale

        dst_obj.delta_location = src_obj.delta_location + Vector(self.delta_location)
        dst_obj.delta_scale = src_obj.delta_scale
        dst_obj.delta_rotation_euler = src_obj.delta_rotation_euler
        dst_obj.delta_rotation_quaternion = src_obj.delta_rotation_quaternion

        slot = dst_obj.material_slots[src_slot_idx]
        slot.material = slot.material.copy()
        slot.material.name = target_image.name
        node_tree = slot.material.node_tree
        node_tree.animation_data_clear()
        src_node = node_tree.nodes[node_to_replace]
        dst_node = node_tree.nodes.new("ShaderNodeTexImage")
        dst_node.location = src_node.location
        for link in src_node.inputs['UV'].links:
            node_tree.links.new(link.from_socket, dst_node.inputs['Vector'])      
        for link in src_node.outputs['Color'].links:
            node_tree.links.new(dst_node.outputs['Color'], link.to_socket)
        for link in src_node.outputs['Alpha'].links:
            node_tree.links.new(dst_node.outputs['Alpha'], link.to_socket)
        node_tree.nodes.active = dst_node
        node_tree.nodes.remove(src_node)

        dst_node.image = target_image
        dst_node.interpolation = src_media_node_group.nodes['TfxMedia'].interpolation
        dst_node.projection = src_media_node_group.nodes['TfxMedia'].projection
        dst_node.extension = src_media_node_group.nodes['TfxMedia'].extension
        if target_image.source in ('MOVIE', 'SEQUENCE'):
            dst_node.image_user.use_auto_refresh = True
            dst_node.image_user.use_cyclic = True

        # Convert the media with other add-on operators
        for obj in context.selected_objects:
                obj.select_set(False)
        context.view_layer.objects.active = dst_obj
        bpy.ops.tfx.wrap_media(image_name=target_image.name)
        bpy.ops.tfx.add_playback_driver(controller='GLOBAL')

        return {'FINISHED'}
