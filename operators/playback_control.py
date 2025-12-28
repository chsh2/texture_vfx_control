import bpy
from ..utils import media_utils, anim_utils, node_utils, asset_manager

class AddPlaybackDriverOperator(bpy.types.Operator):
    """Set up a driver to control the playback of image sequence/movie texture"""
    bl_idname = "tfx.add_playback_driver"
    bl_label = "Add Playback Controller"
    bl_category = 'View'
    bl_options = {'REGISTER', 'UNDO'}
    
    trim_media: bpy.props.BoolProperty(
        name='Trim Media',
        default=False,
        description='Only play a selected frame range from the movie/sequence'
    )
    first_frame: bpy.props.IntProperty(
        name='First Frame',
        description='The first frame from the movie/sequence to be played',
        default=1, min=1, max=65535
    )
    last_frame: bpy.props.IntProperty(
        name='Last Frame',
        description='The last frame from the movie/sequence to be played',
        default=65535, min=1, max=65535
    )
    controller: bpy.props.EnumProperty(
        name='Controller',
        items=[ ('LOCAL', 'Local Keyframes', 'Keyframes will be stored in the shader node group that contains the media'),
                ('GLOBAL', 'Global Manager (Beta)', 'All keyframes will be stored in an object named "TfxPlaybackManager" as an NLA strip')],
        default='LOCAL',
        description='Determine to set keyframes inside the material node group itself or inside another object'
    )
    add_keyframes: bpy.props.BoolProperty(
        name='Add Keyframes',
        default=True,
        description='Add keyframes automatically to realize some basic playback modes'
    )
    playback_loops: bpy.props.IntProperty(
        name='Loop',
        description='Number of repeated playbacks',
        default=1, min=1
    )
    playback_rate: bpy.props.FloatProperty(
        name='Playback Rate',
        description='Speed up or slow down the playback',
        default=1, min=0.05, soft_max=5
    ) 
    playback_reversed: bpy.props.BoolProperty(
        name='Reverse',
        default=False,
        description='Play the video in another direction'
    ) 
    playback_pingpong: bpy.props.BoolProperty(
        name='Ping-Pong',
        default=False,
        description='Change the direction of playback in every loop'
    )
    fit_scene_fps: bpy.props.BoolProperty(
        name='Fit Scene FPS',
        default=True,
        description='When the media FPS is different from the scene FPS, adjust the playback speed accordingly'
    )
    
    def draw(self, context):
        layout = self.layout
        
        row = layout.box().row()
        message = f'Frames: {self._frame_duration}'
        row.label(text=message, icon='INFO')
        if self._source == 'MOVIE':
            message = f'FPS: {self._fps:.2f}'
            row.label(text=message)
            
        layout.prop(self, "trim_media")
        if self.trim_media:
            row = layout.box().row()
            row.prop(self, "first_frame")
            row.prop(self, "last_frame")
            
        layout.prop(self, "controller")
        if self.controller == 'LOCAL':
            layout.prop(self, "add_keyframes")
        if self.add_keyframes or self.controller == 'GLOBAL':
            box = layout.box() 
            box.prop(self, 'playback_rate')
            box.prop(self, 'playback_loops')
            row = box.row()
            row.prop(self, "playback_reversed")
            row.prop(self, "playback_pingpong")
            if self._source == 'MOVIE':
                box.prop(self, "fit_scene_fps")
        
    def invoke(self, context, event):
        image_node, _ = node_utils.get_active_image_node()
        self._source = image_node.image.source
        self._frame_duration = media_utils.get_media_duration(image_node.image)
        self._fps = media_utils.get_media_fps(image_node.image)
        self.first_frame = 1
        self.last_frame = self._frame_duration
        return context.window_manager.invoke_props_dialog(self, width=300)
    
    def execute(self, context):
        image_node, media_node_tree = node_utils.get_active_image_node()
        top_node = context.object.active_material.node_tree.nodes.active
        
        # Get information from media and user input
        media_duration = media_utils.get_media_duration(image_node.image)
        media_fps = media_utils.get_media_fps(image_node.image)
        scene_fps = context.scene.render.fps / context.scene.render.fps_base
        
        if self.last_frame < self.first_frame:
            self.last_frame = self.first_frame
            
        first_frame = min(self.first_frame, media_duration) if self.trim_media else 1
        frame_duration = min(self.last_frame, media_duration) - first_frame + 1 if self.trim_media else media_duration
        
        # Disable default control
        image_node.image_user.frame_duration = 65535
        image_node.image_user.frame_start = 1
        
        # Set up custom properties
        suffix = media_node_tree.name[len("tfx_texture_"):]
        if self.controller == 'LOCAL':
            datapath_start = 'tfxFirstFrame'
            datapath_duration = 'tfxFrameDuration'
            datapath_playhead = 'tfxPlayhead'
            subject = top_node.node_tree
            id_type = 'NODETREE'
            top_node.node_tree["tfxPlaybackControl"] = int(1)
        else:
            datapath_start = f'tfxFirstFrame_{suffix}'
            datapath_duration = f'tfxFrameDuration_{suffix}'
            datapath_playhead = f'tfxPlayhead_{suffix}'
            subject = anim_utils.get_global_playback_manager()
            id_type = 'OBJECT'
            top_node.node_tree["tfxPlaybackControl"] = int(2)
        subject[datapath_duration] = frame_duration
        subject[datapath_start] = first_frame
        subject[datapath_playhead] = 0.0
        ui = subject.id_properties_ui(datapath_playhead)
        ui.update(soft_min=0.0, soft_max=1.0, subtype='FACTOR')
        
        # Set up the driver
        image_node.image_user.driver_remove('frame_offset')
        fc = image_node.image_user.driver_add('frame_offset')
        fc.driver.type = 'SCRIPTED'
        anim_utils.add_driver_variable(fc.driver, subject, datapath_start, 's', id_type=id_type)
        anim_utils.add_driver_variable(fc.driver, subject, datapath_playhead, 'p', id_type=id_type)
        anim_utils.add_driver_variable(fc.driver, subject, datapath_duration, 'd', id_type=id_type)
        anim_utils.add_driver_variable(fc.driver, bpy.context.scene, 'frame_current', 't', id_type='SCENE', custom_property=False)
        fc.driver.expression = "int(min(max(floor(p*d)+s-t, s-t), s+d-t-1))"
        
        # Remove existing keyframes
        if subject.animation_data and subject.animation_data.action:
            fcurves = anim_utils.get_action_fcurves(subject.animation_data.action)
            fc = fcurves.find(f'["{datapath_playhead}"]')
            if fc:
                fcurves.remove(fc)

        # Insert new keyframes   
        if self.add_keyframes or self.controller == 'GLOBAL':            
            frame_current = bpy.context.scene.frame_current
            next_keyframe = frame_current
            pingpong = False
            
            playback_rate = self.playback_rate if not self.controller == 'GLOBAL' else 1
            num_loops = self.playback_loops if not self.controller == 'GLOBAL' else int(1+self.playback_pingpong)
            playback_reversed = self.playback_reversed if not self.controller == 'GLOBAL' else False
            
            if self.fit_scene_fps:
                playback_rate = playback_rate * media_fps / scene_fps
            for _ in range(num_loops):
                # Set start frame
                subject[datapath_playhead] = float(playback_reversed ^ pingpong)
                subject.keyframe_insert(f'["{datapath_playhead}"]')
                # Set end frame
                next_keyframe += max(1, round( (frame_duration-1.0) / playback_rate) )
                bpy.context.scene.frame_set(next_keyframe)
                subject[datapath_playhead] = 1.0 - float(playback_reversed ^ pingpong)
                subject.keyframe_insert(f'["{datapath_playhead}"]')
                next_keyframe += 1
                bpy.context.scene.frame_set(next_keyframe)
                
                if self.playback_pingpong:
                    pingpong = not pingpong
                    
            fcurves = anim_utils.get_action_fcurves(subject.animation_data.action)
            for fcurve in fcurves:
                if fcurve.data_path == f'["{datapath_playhead}"]':
                    for point in fcurve.keyframe_points:
                        point.interpolation = 'LINEAR'
            bpy.context.scene.frame_set(frame_current)
        
        # Convert keyframes to NLA strip
        if self.controller == 'GLOBAL':
            track = subject.animation_data.nla_tracks.new()
            strip = track.strips.new("tmp", context.scene.frame_current, subject.animation_data.action)
            track.name = image_node.image.name
            strip.name = image_node.image.name
            strip.use_reverse = self.playback_reversed
            strip.scale = 1.0 / self.playback_rate
            strip.repeat = self.playback_loops / (1.0 + self.playback_pingpong)
            subject.animation_data.action = None
        
        bpy.ops.tfx.refresh_playback_drivers()
        return {'FINISHED'}
    
    
class RemovePlaybackDriverOperator(bpy.types.Operator):
    """Set up a driver to control the playback of image sequence/movie texture"""
    bl_idname = "tfx.remove_playback_driver"
    bl_label = "Remove Playback Controller"
    bl_category = 'View'
    bl_options = {'REGISTER', 'UNDO'}
    
    def invoke(self, context, event):
        return context.window_manager.invoke_props_dialog(self)
    
    def execute(self, context):
        image_node, media_node_tree = node_utils.get_active_image_node()
        top_node = context.object.active_material.node_tree.nodes.active
        media_duration = media_utils.get_media_duration(image_node.image)
        
        image_node.image_user.driver_remove('frame_offset')
        image_node.image_user.frame_duration = media_duration
        image_node.image_user.frame_start = 1
        image_node.image_user.frame_offset = 0
        
        if top_node.node_tree["tfxPlaybackControl"] == 1:
            subject = top_node.node_tree
            if subject.animation_data and subject.animation_data.action:
                fcurves = anim_utils.get_action_fcurves(subject.animation_data.action)
                fc = fcurves.find('["tfxPlayhead"]')
                if fc:
                    fcurves.remove(fc)
            for key in ["tfxFirstFrame", "tfxFrameDuration", "tfxPlayhead", "tfxPlaybackControl"]:
                if key in subject:
                    del subject[key]
        
        elif top_node.node_tree["tfxPlaybackControl"] == 2:
            subject = anim_utils.get_global_playback_manager()
            suffix = media_node_tree.name[len("tfx_texture_"):]
            for key in [f"tfxFirstFrame_{suffix}", f"tfxFrameDuration_{suffix}", f"tfxPlayhead_{suffix}"]:
                if key in subject:
                    del subject[key]
            
            if subject.animation_data:
                tracks_to_remove = []
                for track in subject.animation_data.nla_tracks:
                    for strip in track.strips:
                        if strip.action:
                            fcurves = anim_utils.get_action_fcurves(strip.action)
                            for fc in fcurves:
                                if fc.data_path == f'["tfxPlayhead_{suffix}"]':
                                    tracks_to_remove.append(track)
                                    break
                            else:
                                continue
                            break
                for track in tracks_to_remove:
                    subject.animation_data.nla_tracks.remove(track)
                
            del top_node.node_tree["tfxPlaybackControl"]
                
        return {'FINISHED'}
    
class OpenGlobalManagerWorkspaceOperator(bpy.types.Operator):
    """Switch to a workspace to adjust animations of the global playback manager"""
    bl_idname = "tfx.open_playback_manager_workspace"
    bl_label = "Open Global Manager"
    bl_category = 'View'
    bl_options = {'REGISTER', 'UNDO'}
    
    def execute(self, context):
        workspace_name = "Media Playback"
        if workspace_name in bpy.data.workspaces:
            bpy.context.window.workspace = bpy.data.workspaces[workspace_name]
        else:
            bpy.ops.workspace.append_activate(idname=workspace_name, filepath=asset_manager.basic_template_filepath)

        return {'FINISHED'}
    
class RefreshDriversOperator(bpy.types.Operator):
    """Use this operator to manually refresh all related drivers, in case the playback control does not work"""
    bl_idname = "tfx.refresh_playback_drivers"
    bl_label = "Refresh Playback Drivers"
    bl_category = 'View'
    bl_options = {'REGISTER', 'UNDO'}
    
    def execute(self, context):
        image_node, media_node_tree = node_utils.get_active_image_node()
        if media_node_tree.animation_data:
            for fc in media_node_tree.animation_data.drivers:
                tmp = fc.driver.expression
                fc.driver.expression = tmp
        return {'FINISHED'}