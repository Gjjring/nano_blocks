import jcmwave
import os 
import numpy as np
keys = {}

keys['cd_width'] = 6
keys['cd_height'] = 5
keys['wg_width'] = 0.3
keys['wg_displacement_left'] = -1
keys['wg_displacement_right'] = 1
keys['wg_stub_length'] = 0.75
keys['boundary_id'] = 1
keys['vacuum_wavelength'] = 500e-9
keys['polygons'] = []
keys['dielectric_slc'] = 0.25/3.5
keys['air_slc'] = 0.25

"""
physical area of the user defined geometry is 1.0 to 4.0 micrometers high and
4 micrometers wide
"""

keys['in_port_fields_path'] = os.path.join("..", "1D", "project_results", "fieldbag.jcm")
jcmwave.geo(".", keys=keys)
jcmwave.solve(os.path.join("..", "1D", "project.jcmpt"), keys=keys)
results =jcmwave.solve("project.jcmpt", keys=keys)

print("upper left: {}".format(np.abs(results[3]['ModeCoefficients_Port1_Source'][0][0])))
print("upper right: {}".format(np.abs(results[3]['ModeCoefficients_Port3_Source'][0][0])))
print("lower right: {}".format(np.abs(results[3]['ModeCoefficients_Port2_Source'][0][0])))
