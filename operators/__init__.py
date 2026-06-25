from . import sampler, injector, shader_patcher, cleanup

def register():
    sampler.register()
    injector.register()
    shader_patcher.register()
    cleanup.register()

def unregister():
    shader_patcher.unregister()
    injector.unregister()
    sampler.unregister()
    cleanup.unregister()