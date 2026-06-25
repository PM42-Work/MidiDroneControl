bl_info = {
    "name": "Midi Drone Control",
    "author": "Raghuvansh Agarwal",
    "version": (1, 1, 0),
    "blender": (4, 3, 0),
    "location": "View3D > Sidebar > Midi Drone Control",
    "description": "MIDI-triggered sample pad for live drone light busking",
    "category": "3D View",
}

import bpy
import sys
import os
import platform
from bpy.props import EnumProperty, CollectionProperty, IntProperty

current_dir = os.path.dirname(os.path.realpath(__file__))
system_platform = platform.system().lower() 
dep_folder = "win" if system_platform == 'windows' else "mac" if system_platform == 'darwin' else "linux"
dep_path = os.path.join(current_dir, "dependencies", dep_folder)
if dep_path not in sys.path: 
    sys.path.insert(0, dep_path)

from . import properties, ui, core, operators

def get_layer_items(self, context):
    items = [('md_layer_1', "Baked Colours (md_layer_1)", "")]
    sc = context.scene
    if hasattr(sc, "adv_layers") and len(sc.adv_layers) > 0:
        for i, layer in enumerate(sc.adv_layers):
            items.append((f"Layer_{i+1}", f"Layer {i+1}: {layer.name}", ""))
    return items

def get_midi_devices(self, context):
    try:
        import rtmidi
        midi_in = rtmidi.MidiIn()
        ports = midi_in.get_ports()
        if not ports: return [('NONE', 'No MIDI Devices Found', '')]
        return [(str(i), port_name, "") for i, port_name in enumerate(ports)]
    except Exception: return [('NONE', 'Error Loading MIDI Library', '')]

def update_system_state(self, context):
    if self.mdc_state == 'RECORD':
        context.scene.sync_mode = 'AUDIO_SYNC'

    val = 0.0 if self.mdc_state == 'SAFE' else 1.0
    for mat in bpy.data.materials:
        if mat.node_tree:
            driver_node = mat.node_tree.nodes.get("MDC_State_Driver")
            if driver_node:
                driver_node.outputs[0].default_value = val

    if self.mdc_state in {'BUSK', 'RECORD'}:
        try:
            from .core import memory, preview
            memory.compile_dirty_pads()
            preview.update_busk_caches() # <--- Triggers the cache generation right here!
        except Exception as e:
            print(f"MDC Compiler Error: {e}")

def register():
    properties.register()
    core.register()
    operators.register()
    ui.register()

    sc = bpy.types.Scene
    sc.mdc_layer_mode = EnumProperty(name="Layer Mode", items=[('SINGLE', 'Single', ''), ('MULTI', 'Multi', '')], default='SINGLE')
    sc.mdc_target_layer = EnumProperty(name="Target Layer", items=get_layer_items)
    
    sc.mdc_state = EnumProperty(
        name="System State",
        items=[
            ('SAFE', 'Safe Mode (Playback)', ''),
            ('BUSK', 'Busk Mode (Live Preview)', ''),
            ('RECORD', 'Record Mode (Arm)', '')
        ],
        default='SAFE',
        update=update_system_state
    )
    
    sc.mdc_midi_device = EnumProperty(name="MIDI Input", items=get_midi_devices)
    sc.mdc_banks = CollectionProperty(type=properties.MidiDroneBankItem)
    sc.mdc_bank_index = IntProperty(default=0)

def unregister():
    ui.unregister()
    operators.unregister()
    core.unregister()
    properties.unregister()