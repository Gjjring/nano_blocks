import jcmwave
import os 
keys = {}

keys['cd_width'] = 6
keys['cd_height'] = 5
keys['wg_width'] = 0.3
keys['wg_displacement_left'] = -1
keys['wg_displacement_right'] = 1
keys['wg_stub_length'] = 1.
keys['boundary_id'] = 1
keys['vacuum_wavelength'] = 500e-9
keys['polygons'] = []


"""
physical area of the user defined geometry is 1.0 to 4.0 micrometers high and
4 micrometers wide
"""

keys['in_port_fields_path'] = os.path.join("..", "1D", "project_results", "fieldbag.jcm")
jcmwave.geo(".", keys=keys)
jcmwave.solve(os.path.join("..", "1D", "project.jcmpt"), keys=keys)
jcmwave.solve("project.jcmpt", keys=keys)
