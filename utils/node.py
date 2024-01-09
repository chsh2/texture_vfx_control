import bpy
from ..utils.asset import append_node_group

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

def add_node_group(node_tree, name, location=(0,0)) -> bpy.types.ShaderNodeGroup:
    node = node_tree.nodes.new('ShaderNodeGroup')
    node.node_tree = append_node_group(name)
    node.location = location
    return node

def add_uv_input(node_tree, location=(0,0)) -> bpy.types.ShaderNodeUVMap:
    node = node_tree.nodes.new('ShaderNodeUVMap')
    node.location = location
    return node   