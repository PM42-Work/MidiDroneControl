bl_info = {
    "name": "Midi Drone Control",
    "author": "Raghuvansh Agarwal",
    "version": (1, 0, 0),
    "blender": (4, 3, 0),
    "location": "View3D > Sidebar > Midi Drone Control",
    "description": "MIDI-triggered sample pad for live drone light busking",
    "category": "3D View",
}

import bpy
import sys
import os
import platform
from bpy.props import BoolProperty, EnumProperty, CollectionProperty, IntProperty

# Add dependencies path so Blender can find our MIDI libraries (rtmidi/mido)
current_dir = os.path.dirname(os.path.realpath(__file__))
system_platform = platform.system().lower() 
dep_folder = "win" if system_platform == 'windows' else "mac" if system_platform == 'darwin' else "linux"
dep_path = os.path.join(current_dir, "dependencies", dep_folder)
if dep_path not in sys.path: 
    sys.path.insert(0, dep_path)

# Import our modules
from . import properties, ui, core, operators

def get_layer_items(self, context):
    # This defaults to the standard base layer. 
    # If you have Advanced Lighting Control active, we can later hook this 
    # into sc.adv_layers to read dynamically!
    return [('md_layer_1', "Base Layer (md_layer_1)", "")]

def register():
    # 1. Register module classes
    properties.register()
    core.register()
    operators.register()
    ui.register()

    # 2. Register Scene-level properties
    sc = bpy.types.Scene
    
    # UI State Properties
    sc.mdc_layer_mode = EnumProperty(
        name="Layer Mode",
        items=[('SINGLE', 'Single Layer', ''), ('MULTI', 'Multi Layer', '')],
        default='SINGLE'
    )
    
    sc.mdc_target_layer = EnumProperty(
        name="Target Layer", 
        items=get_layer_items
    )
    
    sc.mdc_is_armed = BoolProperty(
        name="Armed", 
        default=False,
        description="When active, MIDI pads will write to the timeline."
    )
    
    # MIDI Device Dropdown 
    sc.mdc_midi_device = EnumProperty(
        name="MIDI Input",
        items=[('NONE', 'No Device Found', '')],
        default='NONE'
    )

    # Persistent JSON Memory Banks
    sc.mdc_banks = CollectionProperty(type=properties.MidiDroneBankItem)
    sc.mdc_bank_index = IntProperty(default=0)

def unregister():
    # 1. Unregister classes in reverse order
    ui.unregister()
    operators.unregister()
    core.unregister()
    properties.unregister()
    
    # Scene properties are automatically cleared by Blender on unregister/reload