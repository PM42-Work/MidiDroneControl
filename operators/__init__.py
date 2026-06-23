from . import sampler, injector

def register():
    sampler.register()
    injector.register()

def unregister():
    injector.unregister()
    sampler.unregister()