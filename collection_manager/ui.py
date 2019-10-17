from bpy.types import (
    Operator,
    Panel,
    UIList,
    UI_UL_list,
    )

from .internals import *
from .operators import (
    excludeall_history,
    restrictselectall_history,
    hideall_history,
    disableviewall_history,
    disablerenderall_history,
    )


class CollectionManager(Operator):
    bl_label = "Collection Manager"
    bl_idname = "view3d.collection_manager"
    
    view_layer = ""
    
    def draw(self, context):
        layout = self.layout
        scn = context.scene
        
        if context.view_layer.name != self.view_layer:
            update_collection_tree(context)
            self.view_layer = context.view_layer.name
        
        title_row = layout.split(factor=0.5)
        main = title_row.row()
        view = title_row.row(align=True)
        view.alignment = 'RIGHT'
        
        main.label(text="Collection Manager")
        
        view.prop(context.view_layer, "use", text="")
        view.separator()
        
        window = context.window
        scene = window.scene
        view.template_search(
            window, "view_layer",
            scene, "view_layers",
            new="scene.view_layer_add",
            unlink="scene.view_layer_remove")
        
        layout.row().separator()
        layout.row().separator()
        
        filter_row = layout.row()
        filter_row.alignment = 'RIGHT'
        
        filter_row.popover(panel="COLLECTIONMANAGER_PT_restriction_toggles", text="", icon='FILTER')
        
        toggle_row = layout.split(factor=0.3)
        toggle_row.alignment = 'LEFT'
        
        sec1 = toggle_row.row()
        sec1.alignment = 'LEFT'
        sec1.enabled = False
        
        if len(expanded) > 0:
            text = "Collapse All Items"
        else:
            text = "Expand All Items"
        
        sec1.operator("view3d.expand_all_items", text=text)
        
        for laycol in collection_tree:
            if laycol["has_children"]:
                sec1.enabled = True
                break
        
        sec2 = toggle_row.row()
        sec2.alignment = 'RIGHT'
        
        if scn.show_exclude:
            depress = True if len(excludeall_history) else False
            sec2.operator("view3d.un_exclude_all_collections", text="", icon='CHECKBOX_HLT', depress=depress)
        
        if scn.show_selectable:
            depress = True if len(restrictselectall_history) else False
            sec2.operator("view3d.un_restrict_select_all_collections", text="", icon='RESTRICT_SELECT_OFF', depress=depress)
        
        if scn.show_hideviewport:
            depress = True if len(hideall_history) else False
            sec2.operator("view3d.un_hide_all_collections", text="", icon='HIDE_OFF', depress=depress)
        
        if scn.show_disableviewport:
            depress = True if len(disableviewall_history) else False
            sec2.operator("view3d.un_disable_viewport_all_collections", text="", icon='RESTRICT_VIEW_OFF', depress=depress)
        
        if scn.show_render:
            depress = True if len(disablerenderall_history) else False
            sec2.operator("view3d.un_disable_render_all_collections", text="", icon='RESTRICT_RENDER_OFF', depress=depress)
        
        layout.row().template_list("CM_UL_items", "", context.scene, "CMListCollection", context.scene, "CMListIndex", rows=15, sort_lock=True)
        
        addcollec_row = layout.row()
        addcollec_row.operator("view3d.add_collection", text="Add Collection", icon='COLLECTION_NEW').child = False
        
        addcollec_row.operator("view3d.add_collection", text="Add SubCollection", icon='COLLECTION_NEW').child = True
        
        
    def execute(self, context):
        wm = context.window_manager
        lvl = 0
        
        #expanded.clear()
        
        #excludeall_history.clear()
        #restrictselectall_history.clear()
        #hideall_history.clear()
        #disableviewall_history.clear()
        #disablerenderall_history.clear()
        
        
        context.scene.CMListIndex = 0
        update_property_group(context)
        
        if get_max_lvl() > 5:
            lvl = get_max_lvl() - 5
        
        if lvl > 25:
            lvl = 25
        
        self.view_layer = context.view_layer.name
        
        return wm.invoke_popup(self, width=(400+(lvl*20)))


class CM_UL_items(UIList):
    last_filter_value = ""
    
    def draw_item(self, context, layout, data, item, icon, active_data,active_propname, index):
        self.use_filter_show = True
        
        scn = context.scene
        laycol = layer_collections[item.name]
        collection = laycol["ptr"].collection
        
        row = layout.row(align=True)
        row.alignment = 'LEFT'
        
        # indent child items
        if laycol["lvl"] > 0:
            for x in range(laycol["lvl"]):
                row.label(icon='BLANK1')
        
        # add expander if collection has children to make UIList act like tree view
        if laycol["has_children"]:
            if laycol["expanded"]:
                prop = row.operator("view3d.expand_sublevel", text="", icon='DISCLOSURE_TRI_DOWN', emboss=False)
                prop.expand = False
                prop.name = item.name
                prop.index = index
                
            else:
                prop = row.operator("view3d.expand_sublevel", text="", icon='DISCLOSURE_TRI_RIGHT', emboss=False)
                prop.expand = True
                prop.name = item.name
                prop.index = index
                
        else:
            row.label(icon='BLANK1')
        
        
        row.label(icon='GROUP')
        
        row.prop(collection, "name", text="", expand=True)
        
        # used as a separator (actual separator not wide enough)
        row.label()
        
        # add set_collection op
        row_setcol = row.row()
        row_setcol.operator_context = 'INVOKE_DEFAULT'
        
        icon = 'MESH_CUBE'
        
        if len(context.selected_objects) > 0 and context.active_object:
            if context.active_object.name in collection.objects:
                icon = 'SNAP_VOLUME'
        else:
            row_setcol.enabled = False
        
        
        prop = row_setcol.operator("view3d.set_collection", text="", icon=icon, emboss=False)
        prop.collection_index = laycol["id"]
        prop.collection_name = item.name
        
        
        if scn.show_exclude:
            icon = 'CHECKBOX_DEHLT' if laycol["ptr"].exclude else 'CHECKBOX_HLT'
            row.operator("view3d.exclude_collection", text="", icon=icon, emboss=False).name = item.name
            
        if scn.show_selectable:
            icon = 'RESTRICT_SELECT_ON' if laycol["ptr"].collection.hide_select else 'RESTRICT_SELECT_OFF'
            row.operator("view3d.restrict_select_collection", text="", icon=icon, emboss=False).name = item.name
        
        if scn.show_hideviewport:
            icon = 'HIDE_ON' if laycol["ptr"].hide_viewport else 'HIDE_OFF'
            row.operator("view3d.hide_collection", text="", icon=icon, emboss=False).name = item.name
        
        if scn.show_disableviewport:
            icon = 'RESTRICT_VIEW_ON' if laycol["ptr"].collection.hide_viewport else 'RESTRICT_VIEW_OFF'
            row.operator("view3d.disable_viewport_collection", text="", icon=icon, emboss=False).name = item.name
        
        if scn.show_render:
            icon = 'RESTRICT_RENDER_ON' if laycol["ptr"].collection.hide_render else 'RESTRICT_RENDER_OFF'
            row.operator("view3d.disable_render_collection", text="", icon=icon, emboss=False).name = item.name
        
        
        row.operator("view3d.remove_collection", text="", icon='X', emboss=False).collection_name = item.name
    
    
    def filter_items(self, context, data, propname):
        flt_flags = []
        flt_neworder = []
        
        list_items = getattr(data, propname)
        
        if self.filter_name:
            flt_flags = UI_UL_list.filter_items_by_name(self.filter_name, self.bitflag_filter_item, list_items)
        
        else:
            flt_flags = [self.bitflag_filter_item] * len(list_items)
        
            for idx, item in enumerate(list_items):
                if not layer_collections[item.name]["visible"]:
                    flt_flags[idx] = 0
        
        return flt_flags, flt_neworder
    

    
    def invoke(self, context, event):
        pass


class CMRestrictionTogglesPanel(Panel):
    bl_label = "Restriction Toggles"
    bl_idname = "COLLECTIONMANAGER_PT_restriction_toggles"
    bl_space_type = 'VIEW_3D'
    bl_region_type = 'HEADER'
    
    def draw(self, context):
        
        layout = self.layout
        
        row = layout.row()
        
        row.prop(context.scene, "show_exclude", icon='CHECKBOX_HLT', icon_only=True)
        row.prop(context.scene, "show_selectable", icon='RESTRICT_SELECT_OFF', icon_only=True)
        row.prop(context.scene, "show_hideviewport", icon='HIDE_OFF', icon_only=True)
        row.prop(context.scene, "show_disableviewport", icon='RESTRICT_VIEW_OFF', icon_only=True)
        row.prop(context.scene, "show_render", icon='RESTRICT_RENDER_OFF', icon_only=True)
