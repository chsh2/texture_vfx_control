import bpy
from collections import defaultdict

def list_tfx_node_groups(material):
    """
    Return a map of all textures converted by its add-on and their node groups
    """
    tex_groups_map = defaultdict(list)
    active_tex_name = ''
    
    node_tree = material.node_tree
    if node_tree is None:
        return {}, ''
    
    group_nodes = [node for node in node_tree.nodes if node.type == 'GROUP' and node.node_tree]
    for group_node in group_nodes:
            target_image = None
            if "TfxMedia" in group_node.node_tree.nodes:
                target_image = group_node.node_tree.nodes["TfxMedia"].image
            elif "TfxRoot" in group_node.node_tree.nodes:
                inner_node_tree = group_node.node_tree.nodes["TfxRoot"].node_tree
                target_image = inner_node_tree.nodes["TfxMedia"].image
            if target_image:
                tex_groups_map[target_image.name].append(group_node)
                if group_node == node_tree.nodes.active:
                    active_tex_name = target_image.name
                    
    return tex_groups_map, active_tex_name

def is_active_node_tfx():
    """
    Determine if the active node should be controlled by this add-on
    """
    context = bpy.context
    if (context.object is None) or (context.object.active_material is None) or (context.object.active_material.node_tree is None):
        return False
    node_tree = context.object.active_material.node_tree
    if (node_tree.nodes.active is None) or (node_tree.nodes.active.type != 'GROUP') or (node_tree.nodes.active.node_tree is None):
        return False
    active_node_tree = node_tree.nodes.active.node_tree
    if "tfxName" not in active_node_tree:
        return False
    return True

def get_active_image_node(check=False):
    if check and not is_active_node_tfx():
        return None, None
    active_node_tree = bpy.context.object.active_material.node_tree.nodes.active.node_tree
    if "TfxMedia" in active_node_tree.nodes:
        return active_node_tree.nodes["TfxMedia"], active_node_tree
    elif "TfxRoot" in active_node_tree.nodes:
        inner_node_tree = active_node_tree.nodes["TfxRoot"].node_tree
        return inner_node_tree.nodes["TfxMedia"], inner_node_tree
    return None, None

def get_effect_chain_nodes(check=False):
    if check and not is_active_node_tfx():
        return []
    res = []
    node_tree = bpy.context.object.active_material.node_tree.nodes.active.node_tree
    while "TfxNext" in node_tree.nodes and "tfxName" in node_tree:
        res.append((node_tree, node_tree["tfxName"]))
        node_tree = node_tree.nodes["TfxNext"].node_tree
    return res
    
    