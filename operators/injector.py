import bpy
import numpy as np
import time
from ..core import memory

class MIDIDRONECONTROL_OT_trigger_pad(bpy.types.Operator):
    bl_idname = "mdc.trigger_pad"
    bl_label = "Trigger Pad"
    pad_index: bpy.props.IntProperty()

    def execute(self, context):
        sc = context.scene
        state = sc.mdc_state
        if state == 'SAFE': return {'FINISHED'}
            
        screen = context.screen
        if not screen and context.window_manager.windows:
            screen = context.window_manager.windows[0].screen
        is_playing = getattr(screen, "is_animation_playing", False) if screen else False
        
        target_layer = sc.mdc_target_layer if sc.mdc_layer_mode == 'MULTI' else "md_layer_1"
        
        memory.live_busk_triggers.append((self.pad_index, time.time(), target_layer))
        
        if state == 'RECORD':
            memory.recorded_triggers.append((self.pad_index, sc.frame_current, target_layer))
            if not is_playing:
                bpy.ops.mdc.bake_triggers()
                memory.live_busk_triggers.clear()
            
        return {'FINISHED'}

class MIDIDRONECONTROL_OT_bake_triggers(bpy.types.Operator):
    bl_idname = "mdc.bake_triggers"
    bl_label = "Bake Recorded Triggers"
    
    def execute(self, context):
        sc = context.scene
        if not memory.recorded_triggers: return {'FINISHED'}
            
        memory.recorded_triggers.sort(key=lambda x: x[1])
        memory.clear_cooldowns()
        
        drones_to_update = {} 
        chunk_masks = {} 

        for pad_idx, trigger_frame, trigger_layer in memory.recorded_triggers:
            payload = memory.active_payloads.get(pad_idx)
            if not payload: continue
            
            target_layer = payload.get("layer", trigger_layer)
            drone_data = payload.get("drones", payload) 
            
            for drone_name, channels in drone_data.items():
                cooldown_key = (target_layer, drone_name)
                if cooldown_key in memory.drone_cooldowns and trigger_frame < memory.drone_cooldowns[cooldown_key]:
                    continue
                        
                if cooldown_key not in drones_to_update:
                    drones_to_update[cooldown_key] = {0: [], 1: [], 2: []}
                    chunk_masks[cooldown_key] = []
                    
                local_max_offset = 0
                for array_idx_str, keys in channels.items():
                    array_idx = int(array_idx_str)
                    for offset_frame, value in keys:
                        target_f = trigger_frame + offset_frame
                        drones_to_update[cooldown_key][array_idx].append([target_f, value])
                        if offset_frame > local_max_offset: local_max_offset = offset_frame
                            
                chunk_masks[cooldown_key].append((trigger_frame, trigger_frame + local_max_offset))
                memory.drone_cooldowns[cooldown_key] = trigger_frame + local_max_offset

        for (target_layer, drone_name), channels in drones_to_update.items():
            obj = bpy.data.objects.get(drone_name)
            if not obj: continue
            
            if not obj.animation_data: obj.animation_data_create()
            if not obj.animation_data.action: obj.animation_data.action = bpy.data.actions.new(name=f"{drone_name}_Action")
            action = obj.animation_data.action
            
            for array_idx, new_keys in channels.items():
                if not new_keys: continue
                
                data_path = f'["{target_layer}"]'
                fcurve = action.fcurves.find(data_path, index=array_idx)
                if not fcurve: fcurve = action.fcurves.new(data_path, index=array_idx)
                
                keys_np = np.array(new_keys, dtype=np.float32)
                keys_np = keys_np[keys_np[:, 0].argsort()]
                
                num_existing = len(fcurve.keyframe_points)
                if num_existing > 0:
                    coords = np.zeros(num_existing * 2, dtype=np.float32)
                    fcurve.keyframe_points.foreach_get('co', coords)
                    existing_pts = coords.reshape((num_existing, 2))
                    
                    mask = np.ones(len(existing_pts), dtype=bool)
                    for start_f, end_f in chunk_masks[(target_layer, drone_name)]:
                        in_chunk = (existing_pts[:, 0] >= start_f) & (existing_pts[:, 0] <= end_f)
                        mask &= ~in_chunk
                    existing_pts = existing_pts[mask]
                else: existing_pts = np.empty((0, 2), dtype=np.float32)
                    
                combined_pts = np.vstack((existing_pts, keys_np))
                combined_pts = combined_pts[combined_pts[:, 0].argsort()]
                
                fcurve.keyframe_points.clear() 
                fcurve.keyframe_points.add(len(combined_pts))
                fcurve.keyframe_points.foreach_set('co', combined_pts.flatten())
                fcurve.update()
                
                bool_arr = [False] * len(combined_pts)
                fcurve.keyframe_points.foreach_set('select_control_point', bool_arr)
                fcurve.keyframe_points.foreach_set('select_left_handle', bool_arr)
                fcurve.keyframe_points.foreach_set('select_right_handle', bool_arr)

        memory.recorded_triggers.clear()
        
        if context.area: context.area.tag_redraw()
        else:
            for window in context.window_manager.windows:
                for area in window.screen.areas:
                    if area.type in {'VIEW_3D', 'DOPESHEET_EDITOR', 'GRAPH_EDITOR'}: area.tag_redraw()
                        
        return {'FINISHED'}

def register():
    bpy.utils.register_class(MIDIDRONECONTROL_OT_trigger_pad)
    bpy.utils.register_class(MIDIDRONECONTROL_OT_bake_triggers)

def unregister():
    bpy.utils.unregister_class(MIDIDRONECONTROL_OT_bake_triggers)
    bpy.utils.unregister_class(MIDIDRONECONTROL_OT_trigger_pad)