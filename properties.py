import bpy
from bpy.props import StringProperty, IntProperty, CollectionProperty

class MidiDronePadItem(bpy.types.PropertyGroup):
    name: StringProperty(name="Pad Name", default="Empty")
    midi_note: IntProperty(name="MIDI Note", default=36) # Default to C1
    json_payload: StringProperty(name="Payload", default="{}")

class MidiDroneBankItem(bpy.types.PropertyGroup):
    name: StringProperty(name="Bank Name", default="Bank 1")
    pads: CollectionProperty(type=MidiDronePadItem)

classes = (MidiDronePadItem, MidiDroneBankItem)

def register():
    for cls in classes:
        bpy.utils.register_class(cls)

def unregister():
    for cls in reversed(classes):
        bpy.utils.unregister_class(cls)