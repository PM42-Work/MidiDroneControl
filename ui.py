import bpy
from .core import midi_engine

class MIDIDRONECONTROL_PT_panel(bpy.types.Panel):
    bl_label = "Midi Drone Control"
    bl_space_type = 'VIEW_3D'
    bl_region_type = 'UI'
    bl_category = "Midi Drone Control"

    def draw(self, context):
        layout = self.layout
        sc = context.scene

        if not sc.mdc_banks:
            layout.operator("mdc.init_banks", text="Initialize System", icon='SYSTEM')
            return

        box = layout.box()
        box.label(text="Setup & Routing", icon='PREFERENCES')
        row = box.row(align=True)
        row.prop(sc, "mdc_layer_mode", expand=True)
        if sc.mdc_layer_mode == 'MULTI': box.prop(sc, "mdc_target_layer", text="")

        icon_conn = 'LINKED' if midi_engine.is_listening else 'UNLINKED'
        text_conn = "Disconnect Controller" if midi_engine.is_listening else "Connect MIDI Controller"
        box.operator("mdc.toggle_midi", text=text_conn, icon=icon_conn)
        box.prop(sc, "mdc_midi_device", text="")
        
        row_patch = box.row(align=True)
        row_patch.operator("mdc.patch_shader", text="Patch Shader", icon='SHADING_RENDERED')
        row_patch.operator("mdc.cleanup_live", text="", icon='TRASH') # <--- Adds a trashcan icon next to it

        # The 3-State Machine
        layout.separator()
        row = layout.row(align=True)
        row.scale_y = 1.5
        
        icon_safe = 'CHECKBOX_HLT' if sc.mdc_state == 'SAFE' else 'CHECKBOX_DEHLT'
        row.prop_enum(sc, "mdc_state", 'SAFE', text="SAFE", icon=icon_safe)
        
        icon_busk = 'LIGHT_SUN' if sc.mdc_state == 'BUSK' else 'LIGHT_DATA'
        row.prop_enum(sc, "mdc_state", 'BUSK', text="BUSK", icon=icon_busk)
        
        icon_rec = 'REC' if sc.mdc_state == 'RECORD' else 'RADIOBUT_OFF'
        row.prop_enum(sc, "mdc_state", 'RECORD', text="RECORD", icon=icon_rec)

        layout.separator()
        layout.label(text="Busking Pads", icon='VIEW_ORTHO')
        
        bank = sc.mdc_banks[sc.mdc_bank_index]
        pad_layout = [[12, 13, 14, 15], [8, 9, 10, 11], [4, 5, 6, 7], [0, 1, 2, 3]]

        grid_box = layout.box()
        for row_indices in pad_layout:
            grid_row = grid_box.row(align=True)
            for idx in row_indices:
                if idx < len(bank.pads):
                    pad = bank.pads[idx]
                    col = grid_row.column(align=True)
                    has_data = pad.json_payload != "{}"
                    icon = 'PLAY_SOUND' if has_data else 'BLANK1'
                    col.scale_y = 1.5
                    op_trig = col.operator("mdc.trigger_pad", text=f"{idx+1}", icon=icon)
                    op_trig.pad_index = idx
                    col.scale_y = 0.5
                    op_samp = col.operator("mdc.sample_pad", text="REC")
                    op_samp.pad_index = idx

class MIDIDRONECONTROL_OT_init_banks(bpy.types.Operator):
    bl_idname = "mdc.init_banks"
    bl_label = "Init Banks"
    def execute(self, context):
        sc = context.scene
        if not sc.mdc_banks:
            b = sc.mdc_banks.add()
            b.name = "Bank 1"
            for i in range(16):
                p = b.pads.add()
                p.name = f"Pad {i+1}"
                p.midi_note = 36 + i 
        return {'FINISHED'}

classes = (MIDIDRONECONTROL_PT_panel, MIDIDRONECONTROL_OT_init_banks)
def register():
    for cls in classes: bpy.utils.register_class(cls)
def unregister():
    for cls in reversed(classes): bpy.utils.unregister_class(cls)