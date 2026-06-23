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

        # Ensure we have at least one bank initialized
        if not sc.mdc_banks:
            layout.operator("mdc.init_banks", text="Initialize System", icon='SYSTEM')
            return

        # 1. Setup & Routing
        box = layout.box()
        box.label(text="Setup & Routing", icon='PREFERENCES')
        
        row = box.row(align=True)
        row.prop(sc, "mdc_layer_mode", expand=True)
        
        if sc.mdc_layer_mode == 'MULTI':
            box.prop(sc, "mdc_target_layer", text="")


        icon_conn = 'TRIA_DOWN' if midi_engine.is_listening else 'WIRE'
        text_conn = "Disconnect Controller" if midi_engine.is_listening else "Connect MIDI Controller"
        box.operator("mdc.toggle_midi", text=text_conn, icon=icon_conn)
            
        box.prop(sc, "mdc_midi_device", text="")



        # 2. Master Arm (Big Button)
        row = layout.row()
        row.scale_y = 1.5
        if sc.mdc_is_armed:
            row.prop(sc, "mdc_is_armed", text="ARMED (RECORDING)", icon='REC', toggle=True)
        else:
            row.prop(sc, "mdc_is_armed", text="SAFE (PLAYBACK ONLY)", icon='TRIA_RIGHT', toggle=True)

        # 3. The 4x4 Grid
        layout.separator()
        layout.label(text="Busking Pads", icon='VIEW_ORTHO')
        
        bank = sc.mdc_banks[sc.mdc_bank_index]
        
        # MPC Style: Row 4 (Top) down to Row 1 (Bottom)
        pad_layout = [
            [12, 13, 14, 15], # Row 4 (Top)
            [8, 9, 10, 11],   # Row 3
            [4, 5, 6, 7],     # Row 2
            [0, 1, 2, 3]      # Row 1 (Bottom)
        ]

        grid_box = layout.box()
        for row_indices in pad_layout:
            grid_row = grid_box.row(align=True)
            for idx in row_indices:
                if idx < len(bank.pads):
                    pad = bank.pads[idx]
                    
                    # Pad Cell
                    col = grid_row.column(align=True)
                    
                    # Dynamic naming/icon based on if it has data
                    has_data = pad.json_payload != "{}"
                    icon = 'PLAY_SOUND' if has_data else 'BLANK1'
                    
                    # Trigger Button (Big)
                    col.scale_y = 1.5
                    op_trig = col.operator("mdc.trigger_pad", text=f"{idx+1}", icon=icon)
                    op_trig.pad_index = idx
                    
                    # Sample Button (Small)
                    col.scale_y = 0.5
                    op_samp = col.operator("mdc.sample_pad", text="REC")
                    op_samp.pad_index = idx

# A helper operator just to initialize the memory structures on first load
class MIDIDRONECONTROL_OT_init_banks(bpy.types.Operator):
    bl_idname = "mdc.init_banks"
    bl_label = "Init Banks"
    
    def execute(self, context):
        sc = context.scene
        if not sc.mdc_banks:
            b = sc.mdc_banks.add()
            b.name = "Bank 1"
            # Add exactly 16 pads
            for i in range(16):
                p = b.pads.add()
                p.name = f"Pad {i+1}"
                p.midi_note = 36 + i # C1 mapping
        return {'FINISHED'}

classes = (MIDIDRONECONTROL_PT_panel, MIDIDRONECONTROL_OT_init_banks)

def register():
    for cls in classes:
        bpy.utils.register_class(cls)

def unregister():
    for cls in reversed(classes):
        bpy.utils.unregister_class(cls)