import bpy
from ..utils import node_utils, asset_manager, anim_utils

class NewFxMenu(bpy.types.Menu):
    bl_label = "New Effect"
    bl_idname = "TFX_MT_new_effect"
    def draw(self, context):
        layout = self.layout
        layout.menu("TFX_MT_new_effect_by_category")
        layout.menu("TFX_MT_new_effect_by_name")
        layout.operator("wm.search_single_menu", text="Search...", icon='VIEWZOOM').menu_idname = "TFX_MT_new_effect_by_name"

        layout.separator(factor=0.5, type="LINE")
        for cat in asset_manager.template_fx_list:
            layout.menu(f'TFX_MT_new_effect_by_category_{cat["category"].lower().replace(" ", "_").replace("/", "_")}')

class NewFxByCategorySubMenu(bpy.types.Menu):
    bl_label = "All (By Category)"
    bl_idname = "TFX_MT_new_effect_by_category"
    def draw(self, context):
        layout = self.layout
        fx_info = asset_manager.template_fx_list
        for cat in fx_info:
            layout.label(text=f'<Category: {cat["category"]}>')
            for item in cat["effects"]:
                op = layout.operator("tfx.push_effect", text=item["name"])
                op.fx_group_name = f'tfx_effect_{item["node_name"]}'
                op.param_group_name = f'tfx_param_{item["node_name"]}'
                op.asset_file_name = item["file"]
            layout.separator(factor=0.25, type="LINE")

class NewFxByNameSubMenu(bpy.types.Menu):
    bl_label = "All (Alphabetical)"
    bl_idname = "TFX_MT_new_effect_by_name"
    def draw(self, context):
        layout = self.layout
        fx_info = asset_manager.template_fx_list
        items = [item for cat in fx_info for item in cat["effects"]]
        items.sort(key=lambda x: x["name"])
        for item in items:
            op = layout.operator("tfx.push_effect", text=item["name"])
            op.fx_group_name = f'tfx_effect_{item["node_name"]}'
            op.param_group_name = f'tfx_param_{item["node_name"]}'
            op.asset_file_name = item["file"]

class NewFxCategorySubMenuBase(bpy.types.Menu):
    bl_label = ""
    bl_idname = "TFX_MT_new_effect_by_category_base"
    category_name = ""
    def draw(self, context):
        layout = self.layout
        fx_info = asset_manager.template_fx_list
        for cat in fx_info:
            if cat["category"] == self.category_name:
                for item in cat["effects"]:
                    op = layout.operator("tfx.push_effect", text=item["name"])
                    op.fx_group_name = f'tfx_effect_{item["node_name"]}'
                    op.param_group_name = f'tfx_param_{item["node_name"]}'
                    op.asset_file_name = item["file"]
                break

fx_info = asset_manager.template_fx_list
for cat in fx_info:
    class_name = f'TFX_MT_new_effect_by_category_{cat["category"].lower().replace(" ", "_").replace("/", "_")}'
    menu_cls = type(
        class_name,
        (NewFxCategorySubMenuBase,),
        {
            "bl_label": cat["category"],
            "bl_idname": class_name,
            "category_name": cat["category"],
        }
    )
    bpy.utils.register_class(menu_cls)

class TFX_PT_panel_fx_chain(bpy.types.Panel):
    bl_idname = 'TFX_PT_panel_fx_chain'
    bl_label = "Effects Chain"
    bl_space_type = "VIEW_3D"
    bl_region_type = "UI"
    bl_category = "TexFX"
    bl_context = "objectmode"
    bl_order = 3
    
    @classmethod
    def poll(cls, context):
        return node_utils.is_active_node_tfx()
    
    def draw(self, context):
        chain = node_utils.get_effect_chain_nodes()
        layout = self.layout

        for i in range(len(chain)-1, 0, -1):
            tree, fx_name = chain[i]
            params = tree.nodes["TfxParam"].node_tree.nodes["Group Output"].inputs
            promoted_params = []
            if "tfxPromoted" in tree:
                promoted_params = tree["tfxPromoted"]

            header, body = layout.panel(tree.name)
            header.label(text=fx_name, icon='SHADERFX')
            header.prop(params["Bypass"], 'default_value', text='',
                        icon='HIDE_OFF' if not params["Bypass"].default_value else 'HIDE_ON')

            op = header.operator("tfx.swap_effect", text='', icon='TRIA_UP')
            op.depth = i
            op = header.operator("tfx.swap_effect", text='', icon='TRIA_DOWN')
            op.depth = i-1

            header.operator("tfx.pop_effect", text='', icon='X').depth = i

            if body:
                for p in promoted_params:
                    node = tree.nodes[p[0]]
                    attr = getattr(node, p[1])
                    if isinstance(attr, bpy.types.CurveMapping):
                        body.template_curve_mapping(node, p[1], type='COLOR' if len(attr.curves) > 1 else 'NONE')
                    elif isinstance(attr, bpy.types.ColorRamp):
                        body.template_color_ramp(node, p[1])
                    else:
                        body.prop(node, p[1])
                    
                for j,p in enumerate(params):
                    if j == 0:
                        continue
                    if p.name:
                        row = body.row()
                        row.prop(p, 'default_value', text=p.name)
                        if p.name == "Use Object Location" and p.default_value:
                            button_text = anim_utils.get_global_location_driver_id(tree)
                            row = body.row()
                            row.alignment = 'RIGHT'
                            row.operator("tfx.set_effect_location_driver", text=button_text, icon='LINKED').node_group_name = tree.name
                        if p.name in ("In", "Out"):
                            op = row.operator("tfx.set_transition_playback_driver", text='', icon='LINKED')
                            op.transition_type = p.name
                            op.node_group_name = tree.name
                        if p.name in ("Random Seed", "Phase"):
                            op = row.operator("tfx.set_effect_temporal_driver", text='', icon='LINKED')
                            op.param_name = p.name
                            op.node_group_name = tree.name
                            
            layout.separator(factor=0.25, type="LINE")
        
        layout.menu("TFX_MT_new_effect", icon='ADD')