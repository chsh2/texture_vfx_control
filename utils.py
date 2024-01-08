import bpy
import os

def get_target_node(node_tree, 
                    filter = lambda node: (node.type == 'TEX_IMAGE' and node.image)
                    ):
    """
    Find the shader node to perform operations.
    First, check the active node. If it is not qualified, search through all nodes to find the first eligible one
    """
    nodes = node_tree.nodes
    if nodes.active and filter(nodes.active):
        return nodes.active, node_tree
    # Search recursively for node groups
    elif nodes.active and nodes.active.type=='GROUP' and nodes.active.node_tree:
        return get_target_node(nodes.active.node_tree, filter)
    else:
        for node in nodes:
            if filter(node):
                return node, node_tree
    return None, None

def copy_driver(src, dst):
    """
    Copy all attributes of the source driver to an empty destination driver
    """
    dst.type = src.type
    for src_var in src.variables:
        dst_var = dst.variables.new()
        dst_var.name = src_var.name
        dst_var.type = src_var.type
        dst_var.targets[0].id_type = src_var.targets[0].id_type
        dst_var.targets[0].id = src_var.targets[0].id
        dst_var.targets[0].data_path = src_var.targets[0].data_path
    dst.expression = src.expression

def get_library_blend_file():
    file_name = 'res/assets.blend'
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