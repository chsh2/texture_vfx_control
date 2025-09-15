import bpy

def add_driver_variable(driver, subject, data_path, name, id_type='OBJECT', custom_property = True):
    var = driver.variables.new()
    var.name = name
    var.type = 'SINGLE_PROP'
    var.targets[0].id_type = id_type
    var.targets[0].id = subject
    var.targets[0].data_path = f'["{data_path}"]' if custom_property else data_path

def set_global_location_driver(tree, subject=None):
    if "TfxDriverObjLoc" not in tree.nodes:
        return
    node = tree.nodes["TfxDriverObjLoc"]
    for i,attr in enumerate(['LOC_X', 'LOC_Y', 'LOC_Z']):
        target = node.inputs[i]
        target.driver_remove('default_value')
        if subject is None:
            continue
        fc = target.driver_add('default_value')
        fc.driver.type = 'AVERAGE'
        var = fc.driver.variables.new()
        var.name = subject.name
        var.type = 'TRANSFORMS'
        var.targets[0].id = subject
        var.targets[0].transform_space = 'WORLD_SPACE'
        var.targets[0].transform_type = attr
        
def get_global_location_driver_id(tree):
    default_str = "(No Object Selected)"
    if "TfxDriverObjLoc" not in tree.nodes or not tree.animation_data:
        return default_str
    fc = tree.animation_data.drivers.find('nodes["TfxDriverObjLoc"].inputs[0].default_value')
    if not fc or len(fc.driver.variables) < 1:
        return default_str
    return f"Driver: {fc.driver.variables[0].name}"

def set_playhead_driver(tree, length, subject, id_type, datapath_playhead, datapath_duration, out=False):
    if "TfxParam" not in tree.nodes or "Group Output" not in tree.nodes["TfxParam"].node_tree.nodes:
        return
    node = tree.nodes["TfxParam"].node_tree.nodes["Group Output"]
    if not out and "In" in node.inputs:
        target = node.inputs["In"]
        expr = f"min(p*d/{length}, 1.0)"
    elif out and "Out" in node.inputs:
        target = node.inputs["Out"]
        expr = f"1.0-min((1-p)*d/{length}, 1.0)"
    else:
        return
    target.driver_remove('default_value')
    fc = target.driver_add('default_value')
    fc.driver.type = 'SCRIPTED'
    add_driver_variable(fc.driver, subject, datapath_playhead, 'p', id_type=id_type)
    add_driver_variable(fc.driver, subject, datapath_duration, 'd', id_type=id_type)
    fc.driver.expression = expr
    
def set_strip_driver(tree, length, subject, track_name, strip_name, out=False):
    if "TfxParam" not in tree.nodes or "Group Output" not in tree.nodes["TfxParam"].node_tree.nodes:
        return
    node = tree.nodes["TfxParam"].node_tree.nodes["Group Output"]
    if not out and "In" in node.inputs:
        target = node.inputs["In"]
        datapath = 'frame_start'
        expr = f"max(0.0,min((t-f)/{length}, 1.0))"
    elif out and "Out" in node.inputs:
        target = node.inputs["Out"]
        datapath = 'frame_end'
        expr = f"1.0-max(0.0,min((f-t)/{length}, 1.0))"
    else:
        return
    target.driver_remove('default_value')
    fc = target.driver_add('default_value')
    fc.driver.type = 'SCRIPTED'
    add_driver_variable(
        fc.driver, subject, 
        f'animation_data.nla_tracks["{track_name}"].strips["{strip_name}"].{datapath}', 
        'f', id_type='OBJECT', custom_property=False
    )
    add_driver_variable(
        fc.driver, bpy.context.scene, 
        'frame_current', 
        't', id_type='SCENE', custom_property=False
    )
    fc.driver.expression = expr    
 
def get_action_fcurves(action):
    if action is None:
        return None
    if bpy.app.version < (4, 5, 0):
        return action.fcurves
    else:
        return action.layers[0].strips[0].channelbag(action.slots[0]).fcurves 
    
def get_global_playback_manager():
    obj_name = "TfxPlaybackManager"
    if obj_name in bpy.data.objects:
        return bpy.data.objects[obj_name]
    else:
        new_obj = bpy.data.objects.new(obj_name, None)
        new_obj.hide_viewport = True
        bpy.context.scene.collection.objects.link(new_obj)
        return new_obj