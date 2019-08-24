import bpy

# File:             ParticleSystemToAnimatedObjects.py
# Date:             08.21.2019
# Version:          Blender 2.8
# Original Script:  https://blender.stackexchange.com/questions/4956/convert-particle-system-to-animated-meshes
#
# This script is converts a Blender particle system into individually keyframed objects.
# While the original script was for an earlier version of the API, this version has been
# updated to work in Blender 2.8.
#
# Instructions:
#   1. Select Particle Object
#   2. Shift-Select Emitter Object (Object w/ Particle System)
#   3. Run Script


KEYFRAME_LOCATION = True
KEYFRAME_ROTATION = True
KEYFRAME_SCALE = True


# Duplicate the given object for every particle and return the duplicates.
def create_objects_for_particles(particle_system, object):
    mesh = object.data
    object_list = []

    for index, _ in enumerate(particle_system.particles):
        mesh_copy = mesh.copy() # Perform deep copy of particle object
        duplicate = bpy.data.objects.new(name="particle.{:03d}".format(index),object_data=mesh_copy)
        bpy.context.collection.objects.link(duplicate)
        object_list.append(duplicate)

    return object_list

# Match and keyframe the objects to the particles for every frame in the  given range.
def match_and_keyframe_objects(ps, object_list, start_frame, end_frame):
    for frame in range(start_frame, end_frame + 1):
        bpy.context.scene.frame_set(frame)
        for particle, object in zip(ps.particles, object_list):
            match_object_to_particle(particle, object)
            add_keyframes_to_object(object)

# Match the location, rotation, scale and visibility of the object to the particle.
def match_object_to_particle(particle, object):
    location = particle.location
    rotation = particle.rotation
    size = particle.size
    visibility = True
    object.location = location
    # Set rotation mode to quaternion to match particle rotation.
    object.rotation_mode = 'QUATERNION'
    object.rotation_quaternion = rotation
    object.scale = (size, size, size)

# Keyframe location, rotation, and scale
def add_keyframes_to_object(object):
    if KEYFRAME_LOCATION:
        object.keyframe_insert("location")
    if KEYFRAME_ROTATION:
        object.keyframe_insert("rotation_quaternion")
    if KEYFRAME_SCALE:
        object.keyframe_insert("scale")

# Main program
def main():
   
    # Get emitter object
    emitter = bpy.context.object
   
    # Get particle object
    object = [obj for obj in bpy.context.selected_objects if obj != emitter][0]
   
    # Get particle system
    dg = bpy.context.evaluated_depsgraph_get()
    ob = bpy.context.object.evaluated_get(dg)
    particle_system = ob.particle_systems.active
   
    # Get animation bounds
    start_frame = bpy.context.scene.frame_start
    end_frame = bpy.context.scene.frame_end

    # Convert particles to objects
    object_list = create_objects_for_particles(particle_system, object)
    match_and_keyframe_objects(particle_system, object_list, start_frame, end_frame)

if __name__ == '__main__':
    main()