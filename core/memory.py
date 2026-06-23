import json

# High-speed caches
active_payloads = {}
drone_cooldowns = {}

# Deferred Baking (Live Recording) Cache
recorded_triggers = []
was_playing = False
last_evaluated_frame = -1

def load_bank_to_cache(context):
    """Deserializes the current bank's JSON data into high-speed memory."""
    global active_payloads
    active_payloads.clear()
    
    sc = context.scene
    if not sc.mdc_banks or sc.mdc_bank_index >= len(sc.mdc_banks):
        return
        
    bank = sc.mdc_banks[sc.mdc_bank_index]
    for idx, pad in enumerate(bank.pads):
        if pad.json_payload and pad.json_payload != "{}":
            try:
                active_payloads[idx] = json.loads(pad.json_payload)
            except Exception as e:
                print(f"Midi Drone Control Error loading pad {idx}: {e}")

def clear_cooldowns():
    """Resets all drone locks."""
    global drone_cooldowns, last_evaluated_frame
    drone_cooldowns.clear()
    last_evaluated_frame = -1