import bpy
import json

class MIDIDRONECONTROL_OT_sample_pad(bpy.types.Operator):
    bl_idname = "mdc.sample_pad"
    bl_label = "Sample Selected Keyframes"
    bl_description = "Capture selected keyframes from chosen layer and write to this pad"
    
    pad_index: bpy.props.IntProperty()

    def execute(self, context):
        sc = context.scene
        selected_drones = [obj for obj in context.selected_objects if obj.animation_data and obj.animation_data.action]
        
        if not selected_drones:
            self.report({'WARNING'}, "No objects with animation data selected!")
            return {'CANCELLED'}
            
        target_layer = sc.mdc_target_layer if sc.mdc_layer_mode == 'MULTI' else "md_layer_1"
        
        # Step 1: Find Global Time Zero across all selected items
        all_selected_frames = []
        sampled_data = {}
        
        for obj in selected_drones:
            action = obj.animation_data.action
            obj_data = {}
            
            for fcurve in action.fcurves:
                # Target the correct custom property or layer path
                if target_layer not in fcurve.data_path:
                    continue
                    
                selected_keys = [kp for kp in fcurve.keyframe_points if kp.select_control_point]
                if not selected_keys:
                    continue
                    
                array_index = fcurve.array_index
                if array_index not in obj_data:
                    obj_data[array_index] = []
                    
                for kp in selected_keys:
                    all_selected_frames.append(kp.co.x)
                    # Store as [frame, value]
                    obj_data[array_index].append([kp.co.x, kp.co.y])
            
            if obj_data:
                sampled_data[obj.name] = obj_data

        if not all_selected_frames:
            self.report({'WARNING'}, "No selected keyframe points found in the timeline!")
            return {'CANCELLED'}
            
        global_time_zero = min(all_selected_frames)
        max_duration = 0
        
        # Step 2: Normalize timelines relative to Global Time Zero
        normalized_payload = {}
        for drone_name, channels in sampled_data.items():
            normalized_payload[drone_name] = {}
            for array_idx, keys in channels.items():
                norm_keys = []
                for frame, val in keys:
                    time_offset = frame - global_time_zero
                    norm_keys.append([time_offset, val])
                    if time_offset > max_duration:
                        max_duration = time_offset
                normalized_payload[drone_name][str(array_idx)] = norm_keys

        # Step 3: Write out to Blender persistent storage
        bank = sc.mdc_banks[sc.mdc_bank_index]
        pad = bank.pads[self.pad_index]
        pad.json_payload = json.dumps(normalized_payload)
        pad.name = f"Cue ({len(normalized_payload)} Drones)"
        
        # Sync immediately with our active memory cache
        from ..core import memory
        memory.load_bank_to_cache(context)
        
        self.report({'INFO'}, f"Sampled {len(normalized_payload)} drones to Pad {self.pad_index + 1} (Len: {int(max_duration)}f)")
        return {'FINISHED'}

def register():
    bpy.utils.register_class(MIDIDRONECONTROL_OT_sample_pad)

def unregister():
    bpy.utils.unregister_class(MIDIDRONECONTROL_OT_sample_pad)