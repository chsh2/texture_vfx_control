import bpy
import os

def get_library_blend_file():
    file_name = '../res/assets.blend'
    script_file = os.path.realpath(__file__)
    directory = os.path.dirname(script_file)
    file_path = os.path.join(directory, file_name)
    return file_path

def append_node_group(node_group_name):
    if node_group_name in bpy.data.node_groups:
        return bpy.data.node_groups[node_group_name]

    mode = bpy.context.mode
    bpy.ops.object.mode_set(mode='OBJECT')    
    file_path = get_library_blend_file()
    inner_path = 'NodeTree'
    bpy.ops.wm.append(
        filepath=os.path.join(file_path, inner_path, node_group_name),
        directory=os.path.join(file_path, inner_path),
        filename=node_group_name
    )    
    bpy.ops.object.mode_set(mode=mode)
    return bpy.data.node_groups[node_group_name]