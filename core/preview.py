import bpy
import time
from . import memory

_cached_drones = []
_cached_layer_strings = {}

def update_busk_caches():
    """Call this when entering BUSK/RECORD mode to cache objects and strings"""
    global _cached_drones, _cached_layer_strings
    sc = bpy.context.scene
    
    # 1. Look exclusively at the layers loaded into RAM from our samples
    used_layers = set()
    for payload in memory.active_payloads.values():
        used_layers.add(payload.get("layer", "Layer_1"))
        
    if not used_layers:
        used_layers.add('Layer_1')
        
    _cached_layer_strings = {
        layer: (layer, f"{layer}_live") 
        for layer in used_layers
    }
    
    # 2. Cache the drones (Find EVERY object marked as a drone, animated or not)
    _cached_drones = []
    for obj in bpy.data.objects:
        if obj.type != 'MESH': continue
        if "md_sphere" in obj: 
            _cached_drones.append(obj)
    
    # 3. Create the 4D RGBA property on all found drones for the sampled layers
    for obj in _cached_drones:
        for layer, live_prop in _cached_layer_strings.values():
            if live_prop not in obj:
                obj[live_prop] = [0.0, 0.0, 0.0, 0.0]
                try: 
                    ui_data = obj.id_properties_ui(live_prop)
                    ui_data.update(subtype='COLOR')
                except Exception: 
                    pass

def live_preview_timer():
    try: sc = bpy.context.scene
    except AttributeError: return 0.016 
        
    fps = sc.render.fps / sc.render.fps_base
    interval = 1.0 / fps

    if sc.mdc_state == 'SAFE': return interval
        
    if not _cached_drones and sc.mdc_state in {'BUSK', 'RECORD'}:
        update_busk_caches()
        
    current_time = time.time()
    preview_cooldowns = memory.drone_cooldowns.copy()
    preview_values = {} 
    
    sorted_triggers = sorted(memory.live_busk_triggers, key=lambda x: x[1])
    for pad_idx, trigger_time, override_layer in sorted_triggers:
        baked_payload = memory.baked_payloads.get(pad_idx)
        if not baked_payload: continue
        
        target_layer = baked_payload.get("layer", override_layer)
        baked_drones = baked_payload.get("drones", {})
        
        for drone_name, drone_info in baked_drones.items():
            cooldown_key = (target_layer, drone_name)
            
            if cooldown_key in preview_cooldowns and current_time < preview_cooldowns[cooldown_key]:
                continue 
                
            local_max_frames = drone_info["max_offset"]
            preview_cooldowns[cooldown_key] = trigger_time + (local_max_frames / fps)
            time_offset_frames = int((current_time - trigger_time) * fps)
            
            if 0 <= time_offset_frames <= local_max_frames:
                if cooldown_key not in preview_values:
                    preview_values[cooldown_key] = {}
                for ch_idx, buffer_array in drone_info["channels"].items():
                    preview_values[cooldown_key][ch_idx] = buffer_array[time_offset_frames]

    needs_redraw = False
    for obj in _cached_drones:
        obj_name = obj.name
        updated = False
        
        for layer, live_prop in _cached_layer_strings.values():
            cooldown_key = (layer, obj_name)
            
            if cooldown_key in preview_values:
                # Active: Pack RGB with 1.0 Alpha!
                new_color = [0.0, 0.0, 0.0, 1.0] 
                for ch_idx, val in preview_values[cooldown_key].items():
                    if ch_idx < 3: new_color[ch_idx] = val
                    
                current_color = list(obj[live_prop])
                if len(current_color) < 4 or current_color[:4] != new_color:
                    obj[live_prop] = new_color
                    updated = True
            else:
                # Inactive: Set Alpha to 0.0
                current_color = list(obj[live_prop])
                if len(current_color) > 3 and current_color[3] != 0.0:
                    obj[live_prop] = [0.0, 0.0, 0.0, 0.0]
                    updated = True

        if updated: 
            obj.update_tag(refresh={'OBJECT'})
            needs_redraw = True

    if needs_redraw:
        for window in bpy.context.window_manager.windows:
            for area in window.screen.areas:
                if area.type == 'VIEW_3D': area.tag_redraw()

    return interval 

def register():
    if not bpy.app.timers.is_registered(live_preview_timer):
        bpy.app.timers.register(live_preview_timer, persistent=True)
def unregister():
    global _cached_drones
    _cached_drones.clear()
    if bpy.app.timers.is_registered(live_preview_timer):
        bpy.app.timers.unregister(live_preview_timer)