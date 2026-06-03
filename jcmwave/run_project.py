import jcmwave
import os
import numpy as np
keys = {}

keys['cd_width'] = 6
keys['cd_height'] = 5
keys['vacuum_wavelength'] = 500e-9
keys['polygons'] = []
keys['dielectric_slc'] = 0.25/3.5
keys['air_slc'] = 0.25

angles = np.arange(0, 360, 15)
r1 = 0.2
r2 = 0.3

vertices = []
for i, angle in enumerate(angles):
    if i % 2 == 0:
        r = r1
    else:
        r = r2
    x = r*np.cos(np.radians(angle))
    y = r*np.sin(np.radians(angle))
    vertices.append([x, y])

keys['polygons'] =[
    (np.array(vertices), 0)
]

"""
physical area of the user defined geometry is 1.0 to 4.0 micrometers high and
4 micrometers wide
"""

jcmwave.solve("project.jcmpt", keys=keys)
