import bpy
import queue
import threading
from . import memory

# Thread safe event communication queue
midi_queue = queue.Queue()
midi_backend_backend = None
is_listening = False

def midi_callback(message, data):
    """Background thread callback executing when any hardware MIDI button is pressed."""
    msg = message[0]
    # Status byte 144 is Note On (Channel 1 default), status bytes 144-159 cover all channels
    status = msg[0]
    if 144 <= status <= 159:
        note = msg[1]
        velocity = msg[2]
        
        if velocity > 0: # Note On
            # Sequential mapping starting at C1 (Note 36)
            pad_idx = note - 36
            if 0 <= pad_idx < 16:
                midi_queue.put(pad_idx)

def poll_midi_queue():
    """Runs inside Blender's main loop at 100Hz to process events safely."""
    global midi_queue
    while not midi_queue.empty():
        try:
            pad_idx = midi_queue.get_nowait()
            # Direct execution inside Blender main context
            bpy.ops.mdc.trigger_pad(pad_index=pad_idx)
        except queue.Empty:
            break
        except Exception as e:
            print(f"Midi Drone Control Engine Error: {e}")
            
    return 0.01 # Keep polling every 10 milliseconds

class MIDIDRONECONTROL_OT_toggle_midi(bpy.types.Operator):
    bl_idname = "mdc.toggle_midi"
    bl_label = "Connect MIDI"
    bl_description = "Start/Stop background MIDI system thread listening"
    
    def execute(self, context):
        global midi_backend_backend, is_listening
        sc = context.scene
        
        if is_listening:
            # Shutdown
            if midi_backend_backend:
                midi_backend_backend.close_port()
                midi_backend_backend = None
            bpy.app.timers.unregister(poll_midi_queue)
            is_listening = False
            self.report({'INFO'}, "MIDI Connection Severed.")
            return {'FINISHED'}
            
        # Startup
        try:
            import rtmidi
            midi_in = rtmidi.MidiIn()
            ports = midi_in.get_ports()
            
            if not ports:
                self.report({'ERROR'}, "No MIDI Hardware input ports detected!")
                return {'CANCELLED'}
                
            # Pick first available active port
            midi_in.open_port(0)
            midi_in.set_callback(midi_callback)
            
            midi_backend_backend = midi_in
            is_listening = True
            
            # Warm up RAM cache
            memory.load_bank_to_cache(context)
            memory.clear_cooldowns()
            
            # Hook listener callback directly into Blender loop
            bpy.app.timers.register(poll_midi_queue, persistent=True)
            self.report({'INFO'}, f"Connected to MIDI Device: {ports[0]}")
            
        except ImportError:
            self.report({'ERROR'}, "MIDI library dependencies not found! Package with script first.")
            return {'CANCELLED'}
        except Exception as e:
            self.report({'ERROR'}, f"Failed to open connection: {e}")
            return {'CANCELLED'}
            
        return {'FINISHED'}

def register():
    bpy.utils.register_class(MIDIDRONECONTROL_OT_toggle_midi)

def unregister():
    global midi_backend_backend, is_listening
    if is_listening:
        if midi_backend_backend:
            midi_backend_backend.close_port()
        bpy.app.timers.unregister(poll_midi_queue)
    bpy.utils.unregister_class(MIDIDRONECONTROL_OT_toggle_midi)