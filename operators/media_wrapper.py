import bpy
from bpy_extras.io_utils import ImportHelper
from ..utils import asset_manager, node_utils, media_utils

def mat_image_name_search_func(self, context, edit_text):
    """
    Find all image textures used in the active material. List their names as operator options
    """
    if not context.object.active_material or not context.object.active_material.node_tree:
        return []
    node_tree = context.object.active_material.node_tree
    return [node.image.name for node in node_tree.nodes if node.type == 'TEX_IMAGE' and node.image]
    
class WrapMediaOperator(bpy.types.Operator):
    """Convert an image texture in the active material to a node group under the control of this add-on"""
    bl_idname = "tfx.wrap_media"
    bl_label = "Convert a Texture to FX Node"
    bl_category = 'View'
    bl_options = {'REGISTER', 'UNDO'}
    
    image_name: bpy.props.StringProperty(
        name='Texture Media',
        description='Select an existing image/movie texture in the active material',
        default='',
        search=mat_image_name_search_func
    )

    def draw(self, context):
        layout = self.layout
        layout.prop(self, 'image_name')
        
    def invoke(self, context, event):
        self.image_name = ''
        return context.window_manager.invoke_props_dialog(self, width=500)
    
    def execute(self, context):
        # Create a new node group for this texture
        root_group = asset_manager.create_node_group_instance(None, 'tfx_texture')
        top_group = asset_manager.create_node_group_instance(None, 'tfx_interface')
        
        # Find all image texture nodes given the image name
        if not context.object.active_material or not context.object.active_material.node_tree:
            self.report({'ERROR'}, 'Active object has no material or node tree')
            return {'CANCELLED'}
        node_tree = context.object.active_material.node_tree
        tex_nodes = [node for node in node_tree.nodes if node.type == 'TEX_IMAGE' and node.image and node.image.name == self.image_name]
        
        if len(tex_nodes) < 1:
            return {'FINISHED'}
        
        for src_node in tex_nodes:
            # Place a new shader node
            dst_node = node_tree.nodes.new('ShaderNodeGroup')
            dst_node.node_tree = top_group
            dst_node.location = src_node.location
            #dst_node.width = src_node.width
            dst_node.label = src_node.label
            
            # Rewire the node graph
            for link in src_node.inputs['Vector'].links:
                node_tree.links.new(link.from_socket, dst_node.inputs['UV'])
            if len(dst_node.inputs['UV'].links) < 1:
                # The FX node group requires a UV map to work
                uv_node = node_tree.nodes.new('ShaderNodeUVMap')
                uv_node.location = (dst_node.location.x - 200, dst_node.location.y)
                node_tree.links.new(uv_node.outputs['UV'], dst_node.inputs['UV'])
            
            for link in src_node.outputs['Color'].links:
                node_tree.links.new(dst_node.outputs['Color'], link.to_socket)
            for link in src_node.outputs['Alpha'].links:
                node_tree.links.new(dst_node.outputs['Alpha'], link.to_socket)
            node_tree.nodes.active = dst_node
        
        # Set the image and related properties inside the FX node group
        top_group.nodes['TfxNext'].node_tree = root_group
        top_group.nodes['TfxRoot'].node_tree = root_group
        root_group.nodes['TfxMedia'].image = tex_nodes[0].image
        root_group.nodes['TfxMedia'].interpolation = tex_nodes[0].interpolation
        root_group.nodes['TfxMedia'].projection = tex_nodes[0].projection
        root_group.nodes['TfxMedia'].extension = tex_nodes[0].extension
        if tex_nodes[0].image.source in ('MOVIE', 'SEQUENCE'):
            src_image_user, dst_image_user = tex_nodes[0].image_user, root_group.nodes['TfxMedia'].image_user
            dst_image_user.frame_start = src_image_user.frame_start
            dst_image_user.frame_duration = src_image_user.frame_duration
            dst_image_user.frame_offset = src_image_user.frame_offset
            dst_image_user.use_auto_refresh = src_image_user.use_auto_refresh
            dst_image_user.use_cyclic = src_image_user.use_cyclic
        root_group.nodes['TfxRatio'].inputs[0].default_value = tex_nodes[0].image.size[0]
        root_group.nodes['TfxRatio'].inputs[1].default_value = tex_nodes[0].image.size[1]
        
        # Remove the original texture nodes
        for src_node in tex_nodes:
            node_tree.nodes.remove(src_node)
        
        return {'FINISHED'}
    
    
class ReplaceMediaOperator(bpy.types.Operator, ImportHelper):
    """For a node group under the add-on's control, replace its media file"""
    bl_idname = "tfx.replace_media"
    bl_label = "Replace Media File"
    bl_category = 'View'
    bl_options = {'REGISTER', 'UNDO'}
    
    directory: bpy.props.StringProperty(subtype='DIR_PATH')
    files: bpy.props.CollectionProperty(type=bpy.types.OperatorFileListElement)
    filepath = bpy.props.StringProperty(name="File Path", subtype='FILE_PATH')
    filter_folder: bpy.props.BoolProperty(default=True, options={'HIDDEN'})
    filter_image: bpy.props.BoolProperty(default=True, options={'HIDDEN'})
    filter_movie: bpy.props.BoolProperty(default=True, options={'HIDDEN'})
    
    def execute(self, context):
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
        
        image_node, node_tree = node_utils.get_active_image_node(check=True)
        if image_node is not None:
            image_node.image = target_image
            if target_image.source in ('MOVIE', 'SEQUENCE'):
                image_user = image_node.image_user
                image_user.frame_start = 1
                image_user.frame_duration = media_utils.get_media_duration(target_image)
                image_user.frame_offset = 0
                image_user.use_auto_refresh = True
                image_user.use_cyclic = True
            node_tree.nodes['TfxRatio'].inputs[0].default_value = target_image.size[0]
            node_tree.nodes['TfxRatio'].inputs[1].default_value = target_image.size[1]
        
        return {'FINISHED'}