import bpy
from random import randrange

# File:             GenerateParticleAssembly.py
# Date:             08.25.2019
# Version:          Blender 2.8
#
# This script creates particle objects at each vertex of an emitter object.
#
# Instructions:
#   1. Model emitter object w/ vertices at desired particle locations.
#   2. Model particle object.
#   3. Name "Particle" and "Emitter" objects accordingly.
#   4. Run script!


PARTICLE_NAME = "Particle"
EMITTER_NAME = "Emitter"


def create_particle_at_vertex(source_particle, vertex):
    
    # Create Particle Object
    new_particle = bpy.data.objects.new(
        name=(source_particle.name+".{:03d}").format(0),
        object_data=source_particle.data.copy()
    )
        
    # Position Object At Vertex
    new_particle.location = vertex.co
    
    # Add Object to Scene
    bpy.context.collection.objects.link(new_particle)
    
    return new_particle


# Main Program
def main():
   
    # Declare Local Variables
    source_particle = bpy.data.objects[PARTICLE_NAME]
    source_emitter = bpy.data.objects[EMITTER_NAME]
    new_particles = []
    
    # Create Particles
    for vertex in source_emitter.data.vertices:
        new_particles.append(create_particle_at_vertex(source_particle, vertex))
    

if __name__ == '__main__':
    main()