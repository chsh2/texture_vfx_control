import bpy
from .utils import append_node_group, get_target_node, copy_driver

def add_node_group(node_tree, name, location=(0,0)) -> bpy.types.ShaderNodeGroup:
    node = node_tree.nodes.new('ShaderNodeGroup')
    node.node_tree = append_node_group(name)
    node.location = location
    return node

def add_uv_input(node_tree, location=(0,0)) -> bpy.types.ShaderNodeUVMap:
    node = node_tree.nodes.new('ShaderNodeUVMap')
    node.location = location
    return node    

def get_fx_chain_info(tex_node, fx_types=['tfx_ChromaKey']):
    """
    Return all FX nodes attached to a texture node, as well as links among them.
    Also return the final output color and alpha sockets.
    """
    node_chain = [tex_node]
    inside_links = set()
    output_color_links = []
    output_alpha_links = []
    output_color_socket, output_alpha_socket = None, None
    
    # Find all FX nodes connected to the texture through the color socket
    p = 0
    while p < len(node_chain):
        node:bpy.types.Node = node_chain[p]
        for output in node.outputs:
            if output.name in ['Image', 'Color']:
                for link in output.links:
                    if link.to_node.type == 'GROUP' \
                      and link.to_node.node_tree.name in fx_types \
                      and link.to_node not in node_chain:
                        node_chain.append(link.to_node)
                output_color_socket = output
            elif output.name == 'Alpha':
                output_alpha_socket = output
        p += 1

    # Get link information from all nodes in the chain
    for node in node_chain:
        for output in node.outputs:
            for link in output.links:
                # Link inside the chain
                if link.from_node in node_chain and link.to_node in node_chain:
                    link_info = (node_chain.index(link.from_node), link.from_socket.name,
                                 node_chain.index(link.to_node), link.to_socket.name)
                    inside_links.add(link_info)
                # Output link
                elif link.from_node in node_chain:
                    if output.name in ['Image', 'Color']:
                        output_color_links.append(link)
                    elif output.name == 'Alpha':
                        output_alpha_links.append(link)
    return node_chain, inside_links, output_color_links, output_alpha_links, output_color_socket, output_alpha_socket
            
def duplicate_tex_and_fx_nodes(node_tree, tex_node, node_chain, inside_links):
    """
    Generate 4 copies of a texture node (and some FX nodes following it) for edge detection purpose
    """
    tags = ['V-', 'V+', 'U-', 'U+']
    offset_alpha_outputs = {tag:None for tag in tags}
    offset_nodes ={tag:None for tag in tags}
    
    for i,tag in enumerate(tags):
        expected_name = f'{tex_node.name}.{tag}'
        # Skip duplicating if the node already exists. Get its output socket instead
        if expected_name in node_tree.nodes:
            _, _, _, _, _, offset_output = get_fx_chain_info(node_tree.nodes[expected_name])
            offset_nodes[tag] = node_tree.nodes[expected_name]
            offset_alpha_outputs[tag] = offset_output
        else:
            # Duplicate the texture node
            offset_nodes[tag] = node_tree.nodes.new('ShaderNodeTexImage')
            offset_nodes[tag].name = f'{tex_node.name}.{tag}'
            offset_nodes[tag].hide = True
            offset_nodes[tag].location = (tex_node.location[0], tex_node.location[1]+50*(i+1))
            offset_nodes[tag].image = tex_node.image
            offset_nodes[tag].projection = tex_node.projection
            offset_nodes[tag].extension = tex_node.extension
            offset_nodes[tag].image_user.frame_duration = tex_node.image_user.frame_duration
            offset_nodes[tag].image_user.frame_start = tex_node.image_user.frame_start
            offset_nodes[tag].image_user.frame_offset = tex_node.image_user.frame_offset
            offset_nodes[tag].image_user.use_auto_refresh = tex_node.image_user.use_auto_refresh
            offset_nodes[tag].image_user.use_cyclic = tex_node.image_user.use_cyclic
            offset_alpha_outputs[tag] = offset_nodes[tag].outputs['Alpha']
            # Check if there is a playback driver
            if node_tree.animation_data:
                for driver in node_tree.animation_data.drivers:
                    if driver.data_path in [f'nodes["{tex_node.name}"].image_user.frame_offset', f"nodes['{tex_node.name}'].image_user.frame_offset"]:
                        new_driver = offset_nodes[tag].image_user.driver_add('frame_offset')
                        copy_driver(driver.driver, new_driver.driver)
            # Duplicate each FX node
            offset_fx_chain = [offset_nodes[tag]]
            for fx_node in node_chain:
                if fx_node == tex_node:
                    continue
                offset_fx_node = node_tree.nodes.new('ShaderNodeGroup')
                offset_fx_node.name = f'{fx_node.name}.{tag}'
                offset_fx_node.hide = True
                offset_fx_node.location = (fx_node.location[0], fx_node.location[1]+50*(i+1))
                offset_fx_node.node_tree = fx_node.node_tree
                for j in range(len(offset_fx_node.inputs)):
                    offset_fx_node.inputs[j].default_value = fx_node.inputs[j].default_value
                for output in offset_fx_node.outputs:
                    if output.name == 'Alpha':
                        offset_alpha_outputs[tag] = output
                offset_fx_chain.append(offset_fx_node)
            # Set up links in the same way as the original FX chain
            for link_info in inside_links:
                node_tree.links.new(offset_fx_chain[link_info[0]].outputs[link_info[1]],
                                    offset_fx_chain[link_info[2]].inputs[link_info[3]])
    offset_uv_inputs ={tag:offset_nodes[tag].inputs['Vector'] for tag in tags}
    return offset_uv_inputs, offset_alpha_outputs

class AppendNodeGroupsOperator(bpy.types.Operator):
    """Append all preset shader node groups of the add-on to the current file"""
    bl_idname = "node.tfx_append_node_groups"
    bl_label = "Append VFX Node Groups"
    bl_category = 'View'
    bl_options = {'REGISTER', 'UNDO'}  
    
    def execute(self, context):
        available_node_groups = [#'tfx_RGBtoUV', 
                                 'tfx_ChromaKey',
                                 'tfx_GrainyBlur',
                                 'tfx_OutlinePre',
                                 'tfx_OutlinePost']
        for group in available_node_groups:
            append_node_group(group)
        
        return {'FINISHED'}
    
class GrainyBlurOperator(bpy.types.Operator):
    """Apply grainy blur effect to the selected texture"""
    bl_idname = "node.tfx_grainy_blur"
    bl_label = "Effect: Grainy Blur"
    bl_category = 'View'
    bl_options = {'REGISTER', 'UNDO'}      

    strength: bpy.props.FloatProperty(
        name='Strength',
        default=0.02, min=0, max=0.1
    )     
    def draw(self, context):
        layout = self.layout
        layout.prop(self, 'strength')

    def invoke(self, context, event):
        return context.window_manager.invoke_props_dialog(self)
            
    def execute(self, context):
        obj = context.object
        mat_idx = obj.active_material_index
        mat:bpy.types.Material = obj.material_slots[mat_idx].material
        
        # Process the active node if possible, otherwise find the first node that qualifies
        tex_node, target_node_tree = get_target_node(mat.node_tree, 
                                                     filter=lambda node: (node.type == 'TEX_IMAGE' and node.image))
        if not tex_node:
            self.report({"WARNING"}, "Cannot find any eligible texture node to perform the operation.")
            return {'FINISHED'}
        
        # Find the input UV. Create a new node if there is none
        uv_input_node = None
        uv_socket = None
        if len(tex_node.inputs[0].links) > 0:
            link = tex_node.inputs[0].links[0]
            uv_input_node = link.from_node
            uv_socket = link.from_socket
            target_node_tree.links.remove(link)
        else:
            uv_input_node = add_uv_input(target_node_tree, location=(tex_node.location[0] - 250, 
                                                            tex_node.location[1]))
            uv_socket = uv_input_node.outputs['UV']
            
        # Set up the FX node: between UV and texture
        blur_node = add_node_group(target_node_tree, 'tfx_GrainyBlur', 
                                   location=(tex_node.location[0] - 150, 
                                             tex_node.location[1]))
        target_node_tree.links.new(blur_node.outputs['UV'], tex_node.inputs[0])
        target_node_tree.links.new(uv_socket, blur_node.inputs['UV'])
        blur_node.inputs['Factor'].default_value = self.strength
        
        return {'FINISHED'}
    
class ChromaKeyOperator(bpy.types.Operator):
    """Apply chroma key effect to the selected texture"""
    bl_idname = "node.tfx_chroma_key"
    bl_label = "Effect: Chroma Key"
    bl_category = 'View'
    bl_options = {'REGISTER', 'UNDO'}    
      
    key_color: bpy.props.FloatVectorProperty(
            name = "Key Color",
            subtype = "COLOR",
            default = (.0,.0,1.0,1.0),
            min = 0.0, max = 1.0, size = 4,
            description='Color of the background to remove',
    )
    color_space: bpy.props.EnumProperty(
            name='Color Space',
            items=[('YUV', 'YUV', ''),
                    ('RGB', 'RGB', '')],
            default='YUV'
    ) 
    threshold: bpy.props.FloatProperty(
        name='Threshold',
        default=0.4, min=0, max=1
    )
    smoothness: bpy.props.FloatProperty(
        name='Smoothness',
        default=0.08, min=0, max=1,
        description='Smoothness of the output alpha channel',
    )
    spill: bpy.props.FloatProperty(
        name='Spill',
        default=0.1, min=0, max=1,
        description='Reduce the color spill of the foreground',
    )    
    
    def draw(self, context):
        layout = self.layout
        layout.prop(self, 'key_color')
        layout.prop(self, 'color_space')
        layout.prop(self, 'threshold')
        layout.prop(self, 'smoothness')
        layout.prop(self, 'spill')

    def invoke(self, context, event):
        return context.window_manager.invoke_props_dialog(self)
            
    def execute(self, context):
        obj = context.object
        mat_idx = obj.active_material_index
        mat:bpy.types.Material = obj.material_slots[mat_idx].material
        if mat.blend_method == 'OPAQUE':
            mat.blend_method = 'BLEND'
            
        # Process the active node if possible, otherwise find the first node that qualifies
        tex_node, target_node_tree = get_target_node(mat.node_tree, 
                                                     filter=lambda node: (node.type == 'TEX_IMAGE' and node.image))
        if not tex_node:
            self.report({"WARNING"}, "Cannot find any eligible texture node to perform the operation.")
            return {'FINISHED'}
        
        # Find sockets of output color and alpha; can be multiple ones
        output_sockets = {'Color':[], 'Alpha':[]}
        for key in output_sockets:
            for link in tex_node.outputs[key].links:
                output_sockets[key].append(link.to_socket)
                target_node_tree.links.remove(link)
        
        # Set up the FX node after the texture node
        matte_node = add_node_group(target_node_tree, 'tfx_ChromaKey', 
                                   location=(tex_node.location[0] + 150, 
                                             tex_node.location[1]))
        target_node_tree.links.new(tex_node.outputs[0], matte_node.inputs['Image'])
        for socket in output_sockets['Color']:
            target_node_tree.links.new(matte_node.outputs['Image'], socket)
        for socket in output_sockets['Alpha']:
            target_node_tree.links.new(matte_node.outputs['Alpha'], socket)            
        matte_node.inputs['Key Color'].default_value = self.key_color
        matte_node.inputs['Threshold'].default_value = self.threshold
        matte_node.inputs['Smoothness'].default_value = self.smoothness
        matte_node.inputs['Spill'].default_value = self.spill
        matte_node.inputs['RGB-YUV'].default_value = float(self.color_space == 'YUV')
        
        return {'FINISHED'}

class OutlineOperator(bpy.types.Operator):
    """Apply outline effect to the selected texture"""
    bl_idname = "node.tfx_outline"
    bl_label = "Effect: Outline"
    bl_category = 'View'
    bl_options = {'REGISTER', 'UNDO'}    

    outline_color: bpy.props.FloatVectorProperty(
            name = "Outline Color",
            subtype = "COLOR",
            default = (1.0,1.0,.0,1.0),
            min = 0.0, max = 1.0, size = 4,
    )
    outline_size: bpy.props.FloatVectorProperty(
            name = "Size",
            default = (0.5, 0.5),
            min = 0, soft_max = 5, size = 2, step = 1
    )
    outline_outer: bpy.props.BoolProperty(
            name = "Outer Contour",
            default = True
    )
    outline_inner: bpy.props.BoolProperty(
            name = "Inner Contour",
            default = False
    )
    blur_strength: bpy.props.FloatProperty(
        name='Blur',
        default=0, min=0, max=0.1, step=1
    )
              
    def draw(self, context):
        layout = self.layout
        layout.prop(self, 'outline_color')
        layout.prop(self, 'outline_size')
        layout.prop(self, 'outline_outer')
        layout.prop(self, 'outline_inner')
        layout.prop(self, 'blur_strength')
        
    def invoke(self, context, event):
        return context.window_manager.invoke_props_dialog(self)
            
    def execute(self, context):
        obj = context.object
        mat_idx = obj.active_material_index
        mat:bpy.types.Material = obj.material_slots[mat_idx].material
            
        # Process the active node if possible, otherwise find the first node that qualifies
        tex_node, target_node_tree = get_target_node(mat.node_tree, 
                                                     filter=lambda node: (node.type == 'TEX_IMAGE' and node.image))
        if not tex_node:
            self.report({"WARNING"}, "Cannot find any eligible texture node to perform the operation.")
            return {'FINISHED'}
        
        # Duplicate nodes for edge detection
        node_chain, inside_links, output_color_links, output_alpha_links, \
            output_color_socket, output_alpha_socket = get_fx_chain_info(tex_node)
        offset_uv_inputs, offset_alpha_outputs \
            = duplicate_tex_and_fx_nodes(target_node_tree, tex_node, node_chain, inside_links)

        # Find the input UV. Create a new node if there is none
        uv_input_node = None
        uv_socket = None
        if len(tex_node.inputs[0].links) > 0:
            link = tex_node.inputs[0].links[0]
            uv_input_node = link.from_node
            uv_socket = link.from_socket
            target_node_tree.links.remove(link)
        else:
            uv_input_node = add_uv_input(target_node_tree, location=(tex_node.location[0] - 400, 
                                                            tex_node.location[1]))
            uv_socket = uv_input_node.outputs['UV']
            
        # Add blur effect to the outline only
        if self.blur_strength > 0:
            blur_node = add_node_group(target_node_tree, 'tfx_GrainyBlur', 
                                    location=(tex_node.location[0] - 300, 
                                                tex_node.location[1]))
            blur_node.inputs['Factor'].default_value = self.blur_strength
            target_node_tree.links.new(uv_socket, blur_node.inputs['UV'])
            uv_socket = blur_node.outputs['UV']
        
        # Set up FX nodes: both before and after the texture node
        pre_node = add_node_group(target_node_tree, 'tfx_OutlinePre', 
                                   location=(tex_node.location[0] - 200, 
                                             tex_node.location[1]))
        post_node = add_node_group(target_node_tree, 'tfx_OutlinePost', 
                                   location=(node_chain[-1].location[0] + 200, 
                                             node_chain[-1].location[1]))
        target_node_tree.links.new(uv_socket, pre_node.inputs['UV'])
        for tag in ['U+', 'U-', 'V+', 'V-']:
            target_node_tree.links.new(pre_node.outputs[tag], offset_uv_inputs[tag])
            target_node_tree.links.new(offset_alpha_outputs[tag], post_node.inputs[tag])
        target_node_tree.links.new(output_color_socket, post_node.inputs['Image'])
        target_node_tree.links.new(output_alpha_socket, post_node.inputs['Alpha'])
        pre_node.inputs['U_Offset'].default_value = self.outline_size[0] / 100.0
        pre_node.inputs['V_Offset'].default_value = self.outline_size[1] / 100.0
        post_node.inputs['Color'].default_value = self.outline_color
        post_node.inputs['Inner'].default_value = float(self.outline_inner)
        post_node.inputs['Outer'].default_value = float(self.outline_outer)
        
        # Reconnect output sockets
        for link in output_color_links:
            target_node_tree.links.new(post_node.outputs['Image'], link.to_socket)
        for link in output_alpha_links:
            target_node_tree.links.new(post_node.outputs['Alpha'], link.to_socket)
        
        return {'FINISHED'}
    
