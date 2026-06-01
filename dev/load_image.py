# -*- coding: utf-8 -*-
"""
Created on Wed Feb  7 20:02:35 2024

@author: Phill
"""
import os
#from scipy.ndimage import 
import skimage as ski
import numpy as np
import matplotlib.pyplot as plt
import imageio.v3 as imageio
import shapely
import jcmwave
#from descartes import PolygonPatch

from matplotlib.path import Path
from matplotlib.patches import PathPatch
from matplotlib.collections import PatchCollection

import cv2


# Plots a Polygon to pyplot `ax`
def plot_polygon(ax, poly, **kwargs):
    path = Path.make_compound_path(
        Path(np.asarray(poly.exterior.coords)[:, :2]),
        *[Path(np.asarray(ring.coords)[:, :2]) for ring in poly.interiors])

    patch = PathPatch(path, **kwargs)
    collection = PatchCollection([patch], **kwargs)
    
    ax.add_collection(collection, autolim=True)
    ax.autoscale_view()
    return collection

#file_path = "img001.jpg"
#img = imageio.imread(file_path)
camera = cv2.VideoCapture(0)

return_value, img = camera.read()


# Display the resulting frame 

print(return_value)
cv2.imshow('frame', img) 
plt.close("all")

plt.figure()
plt.imshow(img)
plt.title("Image")
#img = img[:, 400:]

target_color = img[45, 100, :]
plt.figure()
plt.title("Cropped Image")
plt.imshow(img)

#gray_image = ski.color.rgb2gray(img)
#gray_image = img[:, :, 2]

#plt.figure()
#plt.imshow(gray_image, cmap='Greys_r')

# blur the image to denoise
blurred_image = ski.filters.gaussian(img, sigma=1.0)

plt.figure()
plt.title("Blurred Image")
plt.imshow(blurred_image)

hsv_image = ski.color.rgb2hsv(blurred_image)
hsv_target_color = ski.color.rgb2hsv(target_color)

# show the histogram of the blurred image
#histogram, bin_edges = np.histogram(blurred_image, bins=256, range=(0.0, 1.0))
#fig, ax = plt.subplots()
#plt.plot(bin_edges[0:-1], histogram)
#plt.title("Graylevel histogram")
#plt.xlabel("gray value")
#plt.ylabel("pixel count")
#plt.xlim(0, 1.0)

#t = ski.filters.threshold_otsu(blurred_image)
#'print("Found automatic threshold t = {}.".format(t))

# create a binary mask with the threshold found by Otsu's method
#binary_mask = blurred_image > t
hsv_lower = np.array([0.15, 0.1, 0.1])
hsv_higher = np.array([0.40, 1.0, 1.0])
binary_mask = cv2.inRange(hsv_image, hsv_lower, hsv_higher)

binary_mask = ski.filters.gaussian(binary_mask, sigma=3.0)


edge = 20
half_edge = int(edge/2)
ix, iy = binary_mask.shape
new_mask = np.zeros((ix+edge, iy+edge), dtype=np.bool8)
new_mask[half_edge:-half_edge, half_edge:-half_edge] = binary_mask

#new_mask = np.logical_not(new_mask)

fig, ax = plt.subplots()
plt.imshow(new_mask, cmap="gray")
plt.title("Masked Image")
#ix = np.arange(binary_mask.shape[0])
#iy = np.arange(binary_mask.shape[1])
    
#IX, IY = np.meshgrid(ix, iy, indexing='ij')

#IX = IX[binary_mask].flatten()
#IY = IY[binary_mask].flatten()
keys = {}
keys['cd_width'] = new_mask.shape[1]
keys['cd_height'] = new_mask.shape[0]
keys['polygons'] = []

def order_lexicographically(points, start=0.0, return_sort_indices=False):
    angle = np.angle( (points[:,0]+1j*points[:,1])*np.exp(1j*(np.pi+1e-3+start)))
    angle = np.round(angle, 3)
    radius = np.linalg.norm(points, axis=1)
    angle[np.isclose(radius, 0.)] = -np.pi
    sort_indices = np.lexsort((radius, angle))
    #sort_indices = np.argsort(angle)
    all_data = np.round(np.vstack([points.T, angle, radius]).T, 3)
    #pp = pprint.PrettyPrinter(indent=4, width=120)
    #pp.pprint("x, y, z, angle, radius")
    #pp.pprint(all_data)
    #pp.pprint("x, y, z, angle, radius")
    #pp.pprint(all_data[sort_indices, :])
    if return_sort_indices:
        return points[sort_indices, :], sort_indices
    else:
        return points[sort_indices, :]

if True:
    ax = plt.gca()
    BLUE = '#6699cc'
    #on_pixels = np.vstack([IX, IY]).T.tolist()
    contours = ski.measure.find_contours(new_mask.T, 0.5)
    for contour in contours:
        p = shapely.Polygon(contour)
        if p.area > 1000:
            big_poly = p
            #patch1 = PolygonPatch(p, fc=BLUE, ec=BLUE, alpha=0.5, zorder=2)
            #ax.add_patch(patch1)
            #plot_polygon(ax, p)
            
            p2 = p.simplify(10.)
            
            plot_polygon(ax, p2, facecolor='red')
            c = np.array(p2.exterior.coords)
            c = c[:-1, :]
            plt.scatter(c[:,0], c[:,1], c='green')
            c[:, 1] = keys['cd_height']-c[:, 1]
            mid_point = np.tile(np.mean(c, axis=0), c.shape[0]).reshape(c.shape)
            
            c -= mid_point 
            c = order_lexicographically(c)
            c += mid_point
            
            print(c)
            keys['polygons'].append(c)
            
    
        #coords = ski.measure.approximate_polygon(contour, tolerance=2.5)
        #plt.plot(coords[:, 1], coords[:, 0], '-r', linewidth=2)
        #coords2 = approximate_polygon(contour, tolerance=39.5)
        #ax2.plot(coords2[:, 1], coords2[:, 0], '-g', linewidth=2)
        #print("Number of coordinates:", len(contour), len(coords), len(coords2))
    
    camera.release()
    cv2.destroyAllWindows()
    
    #mp = shapely.MultiPoint(on_pixels)
    
    #ch = mp.convex_hull

jcmwave.geo(project_dir=".", keys=keys)