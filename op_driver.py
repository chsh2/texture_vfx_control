import bpy
from .utils import get_target_node

def add_driver_variable(driver, id, data_path, name):
    var = driver.variables.new()
    var.name = name
    var.type = 'SINGLE_PROP'
    var.targets[0].id = id
    var.targets[0].data_path = f'["{data_path}"]'

class AddTexturePlaybackDriverOperator(bpy.types.Operator):
    """Map the playback of a movie/sequence texture to a custom float property by adding a driver to the offset value"""
    bl_idname = "node.tfx_add_playback_driver"
    bl_label = "Add Texture Playback Driver"
    bl_category = 'View'
    bl_options = {'REGISTER', 'UNDO'}  

    start: bpy.props.IntProperty(
        name='First Frame',
        description='The first frame from the movie/sequence to be played. Determine automatically when set to -1 or 0',
        default=-1, min=-1
    )
    duration: bpy.props.IntProperty(
        name='Duration',
        description='Number of frames from the movie/sequence to be played. Determine automatically when set to -1 or 0',
        default=-1, min=-1
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
        
    def draw(self, context):
        layout = self.layout
        layout.label(text='Video Frames to Play:')
        box1 = layout.box() 
        box1.prop(self, 'start')
        box1.prop(self, 'duration')
        layout.prop(self, "add_keyframes")
        if self.add_keyframes:
            box2 = layout.box() 
            box2.prop(self, 'playback_rate')
            box2.prop(self, 'playback_loops')
            row = box2.row()
            row.prop(self, "playback_reversed")
            row.prop(self, "playback_pingpong")

    def invoke(self, context, event):
        return context.window_manager.invoke_props_dialog(self)
            
    def execute(self, context):
        obj = context.object
        mat_idx = obj.active_material_index
        mat = obj.material_slots[mat_idx].material
        
        # Process the active node if possible, otherwise find the first node that qualifies
        tex_node, target_node_tree = get_target_node(mat.node_tree, 
                                        filter=lambda node: (node.type == 'TEX_IMAGE' and node.image and
                                                             (node.image.source == 'MOVIE' or node.image.source == 'SEQUENCE')))
        if not tex_node:
            self.report({"WARNING"}, "Cannot find any eligible texture node to perform the operation.")
            return {'FINISHED'}
            
        tex_name = tex_node.image.name
        datapath_start = f'frame_start_{tex_name}'
        datapath_duration = f'frame_duration_{tex_name}'
        datapath_playhead = f'playhead_{tex_name}'
        
        # Get the playback frame range from multiple sources
        frame_duration = self.duration if self.duration > 0 else \
                        obj[datapath_duration] if datapath_duration in obj else \
                        tex_node.image_user.frame_duration
        frame_start = self.start if self.start > 0 else \
                      obj[datapath_start] if datapath_start in obj else \
                      tex_node.image_user.frame_start
        
        # Set custom properties as inputs of the driver
        obj[datapath_duration] = frame_duration
        obj[datapath_start] = frame_start
        obj[datapath_playhead] = 0.0
        ui = obj.id_properties_ui(datapath_playhead)
        ui.update(soft_min=0.0, soft_max=1.0)
        
        def add_driver_to_node(node):
            # Must modify the original attributes of the texture node, otherwise cannot play correctly
            node.image_user.frame_duration = 65535
            node.image_user.frame_start = 1

            # Add a new driver and fill it with the expression
            node.image_user.driver_remove('frame_offset')
            playback_driver = node.image_user.driver_add('frame_offset')
            playback_driver.driver.type = 'SCRIPTED'
            add_driver_variable(playback_driver.driver, obj, datapath_start, 's')
            add_driver_variable(playback_driver.driver, obj, datapath_playhead, 'p')
            add_driver_variable(playback_driver.driver, obj, datapath_duration, 'd')
            
            scene_var = playback_driver.driver.variables.new()
            scene_var.name = 't'
            scene_var.type = 'SINGLE_PROP'
            scene_var.targets[0].id_type = 'SCENE'
            scene_var.targets[0].id = bpy.context.scene
            scene_var.targets[0].data_path = 'frame_current'  
            
            playback_driver.driver.expression = 'min(max(floor(p*d)+s-t, s-t), s+d-t-1)'
            
            # Remove existing keyframes
            if obj.animation_data:
                fcurves = obj.animation_data.action.fcurves
                for fcurve in fcurves:
                    if fcurve.data_path == f'["{datapath_playhead}"]':
                        fcurve.keyframe_points.clear()

            # Insert new keyframes   
            if self.add_keyframes:            
                frame_current = bpy.context.scene.frame_current
                pingpong = False
                for _ in range(self.playback_loops):
                    # Set start frame
                    obj[datapath_playhead] = float(self.playback_reversed ^ pingpong)
                    obj.keyframe_insert(f'["{datapath_playhead}"]')
                    # Set end frame
                    bpy.context.scene.frame_current += max(1, round( (frame_duration-1.0) / self.playback_rate) )
                    obj[datapath_playhead] = 1.0 - float(self.playback_reversed ^ pingpong)
                    obj.keyframe_insert(f'["{datapath_playhead}"]')
                    bpy.context.scene.frame_current += 1
                    
                    if self.playback_pingpong:
                        pingpong = not pingpong
                        
                fcurves = obj.animation_data.action.fcurves
                for fcurve in fcurves:
                    if fcurve.data_path == f'["{datapath_playhead}"]':
                        for point in fcurve.keyframe_points:
                            point.interpolation = 'LINEAR'
                bpy.context.scene.frame_current = frame_current
            
            # Refresh the driver to put it into effect
            playback_driver.driver.expression = playback_driver.driver.expression
        
        add_driver_to_node(tex_node)
        # Set the same driver to derivative nodes
        for tag in ['V-', 'V+', 'U-', 'U+']:
            expected_name = f'{tex_node.name}.{tag}'
            if expected_name in target_node_tree.nodes:
                add_driver_to_node(target_node_tree.nodes[expected_name])
        
        return {'FINISHED'}