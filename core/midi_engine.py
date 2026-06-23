import bpy
import queue
import threading
from . import memory

midi_queue = queue.Queue()
midi_backend_backend = None
is_listening = False

def midi_callback(message, data):
    msg = message[0]
    status = msg[0]
    if 144 <= status <= 159:
        note = msg[1]
        velocity = msg[2]
        
        if velocity > 0: 
            pad_idx = note - 36
            if 0 <= pad_idx < 16:
                midi_queue.put(pad_idx)

def poll_midi_queue():
    global midi_queue
    
    screen = bpy.context.screen
    if not screen and bpy.context.window_manager.windows:
        screen = bpy.context.window_manager.windows[0].screen
    is_playing = getattr(screen, "is_animation_playing", False) if screen else False
    
    sc = bpy.context.scene
    current_frame = sc.frame_current

    if memory.was_playing and not is_playing and sc.mdc_is_armed:
        if memory.recorded_triggers:
            bpy.ops.mdc.bake_triggers()
            
    memory.was_playing = is_playing

    while not midi_queue.empty():
        try:
            pad_idx = midi_queue.get_nowait()
            
            if sc.mdc_is_armed:
                # --- REMOVED THE TARGET LAYER SNAPSHOT HERE ---
                memory.recorded_triggers.append((pad_idx, current_frame))
                
                if not is_playing:
                    bpy.ops.mdc.bake_triggers()
                    
        except queue.Empty:
            break
        except Exception as e:
            print(f"Midi Drone Control Engine Error: {e}")
            
    return 0.01 

class MIDIDRONECONTROL_OT_toggle_midi(bpy.types.Operator):
    bl_idname = "mdc.toggle_midi"
    bl_label = "Connect MIDI"
    bl_description = "Start/Stop background MIDI system thread listening"
    
    def execute(self, context):
        global midi_backend_backend, is_listening
        sc = context.scene
        
        if is_listening:
            if midi_backend_backend:
                midi_backend_backend.close_port()
                midi_backend_backend = None
            bpy.app.timers.unregister(poll_midi_queue)
            is_listening = False
            self.report({'INFO'}, "MIDI Connection Severed.")
            return {'FINISHED'}
            
        try:
            import rtmidi
            midi_in = rtmidi.MidiIn()
            ports = midi_in.get_ports()
            
            if not ports:
                self.report({'ERROR'}, "No MIDI Hardware input ports detected!")
                return {'CANCELLED'}
                
            port_index = 0
            if sc.mdc_midi_device != 'NONE':
                try: port_index = int(sc.mdc_midi_device)
                except ValueError: pass
            
            midi_in.open_port(port_index)
            midi_in.set_callback(midi_callback)
            
            midi_backend_backend = midi_in
            is_listening = True
            
            memory.load_bank_to_cache(context)
            memory.clear_cooldowns()
            
            bpy.app.timers.register(poll_midi_queue, persistent=True)
            self.report({'INFO'}, f"Connected to MIDI Device: {ports[port_index]}")
            
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