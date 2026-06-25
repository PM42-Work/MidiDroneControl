import json

active_payloads = {}
baked_payloads = {}
dirty_pads = {}

drone_cooldowns = {}
recorded_triggers = []
live_busk_triggers = []

was_playing = False
last_evaluated_frame = -1

def evaluate_keys(keys, time_offset):
    if not keys: return 0.0
    if time_offset <= keys[0][0]: return keys[0][1]
    if time_offset >= keys[-1][0]: return keys[-1][1]
    for i in range(len(keys) - 1):
        k1, k2 = keys[i], keys[i+1]
        if k1[0] <= time_offset <= k2[0]:
            span = k2[0] - k1[0]
            return k2[1] if span == 0 else k1[1] + ((time_offset - k1[0]) / span) * (k2[1] - k1[1])
    return 0.0

def load_bank_to_cache(context):
    global active_payloads, dirty_pads
    active_payloads.clear()
    
    sc = context.scene
    if not sc.mdc_banks or sc.mdc_bank_index >= len(sc.mdc_banks): return
        
    bank = sc.mdc_banks[sc.mdc_bank_index]
    for idx, pad in enumerate(bank.pads):
        if pad.json_payload and pad.json_payload != "{}":
            try: 
                active_payloads[idx] = json.loads(pad.json_payload)
                dirty_pads[idx] = True
            except Exception as e: print(f"MDC Load Error: {e}")

def compile_dirty_pads():
    global active_payloads, baked_payloads, dirty_pads
    
    for idx, payload in active_payloads.items():
        if not dirty_pads.get(idx, True): continue
            
        target_layer = payload.get("layer", "Layer_1")
        drone_data = payload.get("drones", {})
        
        baked_drones = {}
        for drone_name, channels in drone_data.items():
            local_max = int(max([keys[-1][0] for keys in channels.values() if keys], default=0))
            
            baked_channels = {}
            for ch_str, keys in channels.items():
                ch_idx = int(ch_str)
                if ch_idx > 2: continue 
                
                buffer = [0.0] * (local_max + 1)
                for f in range(local_max + 1):
                    buffer[f] = evaluate_keys(keys, f)
                baked_channels[ch_idx] = buffer
                
            baked_drones[drone_name] = {
                "max_offset": local_max,
                "channels": baked_channels
            }
            
        baked_payloads[idx] = {"layer": target_layer, "drones": baked_drones}
        dirty_pads[idx] = False

def clear_cooldowns():
    global drone_cooldowns, last_evaluated_frame
    drone_cooldowns.clear()
    last_evaluated_frame = -1