# -*- coding: utf-8 -*-
"""
Created on Mon Dec 29 15:43:55 2025

@author: Phill
"""
import numpy as np
# import matplotlib.pyplot as plt
from scipy.stats import qmc
# from matplotlib.ticker import FuncFormatter
from numpy import ma
# from matplotlib.patches import Rectangle, FancyArrowPatch, ArrowStyle
# from matplotlib.colors import Normalize
from sklearn.gaussian_process import GaussianProcessRegressor
from sklearn.gaussian_process.kernels import ConstantKernel, RBF, Matern
from scipy.special import erfc
from scipy.stats import norm
import plotly.express as px
import plotly.graph_objects as go
import plotly.colors as pc

def gaussian(X, a, b ,c):
    # print(X.shape)
    # print(b.shape)
    # print((X-b).shape)
    return a*np.exp(-(
        (X[:, 0]-b[0])**2/c[0]**2 +
        (X[:, 1]-b[1])**2/c[1]**2)
        )

def multi_gaussian(X, a, b, c):
    f = np.zeros(X.shape[0])
    # print(f.shape)
    for ii in range(a.size):
        g = gaussian(X, a[ii], b[ii, :], c[ii, :])
        #f = np.maximum(f, g)
        f += g
        # print(f.shape)
    f /= (np.max(f)/100)
    f = np.rint(f).astype(int)
    return f


def letter_ticks(n):
    return {
        "tickmode": "array",
        "tickvals": list(range(n)),
        "ticktext": [chr(ord("A") + i) for i in range(n)]
    }

# def num_to_letter(x, pos):
#     x = int(x)
#     if x < 1:
#         return ""
#     elif x > 26:
#         return ""
#     return chr(ord('A') + x - 1)

class Landscape:

    def __init__(
            self,
            seed:int=10,
            n_peaks:int=2,
            
            board_resolution:int=8,
        ):
        self.seed = seed
        self.n_peaks = n_peaks
        self.board_resolution=board_resolution
        self.mask = None
        self.function_landscape = None        
        self.X = None
        self.Y = None
        self.peaks = None
        self.current_pos = None
        self.current_gradients = None
        self.current_hint = None

        #self.fig = None
        #self.landscape_mesh = None
        #self.text_annotations = [None]*board_resolution**2
        #self.current_pos_rect = None
        #self.grad_arrows = [None]*4
        #self.surrogate_mesh = None
        #self.current_hint_rect = None


    def init_landscape(self):
        rng = np.random.default_rng(self.seed)
        n_peaks = self.n_peaks
        peaks = rng.integers(low=0, high=self.board_resolution,
                     size=n_peaks*2).reshape(n_peaks,2)
        # self.peaks = peaks
        # print(peaks)
        x = np.arange(self.board_resolution)
        X, Y = np.meshgrid(x, x, indexing='ij')
        f = np.zeros_like(X)
        self.X = X
        self.Y = Y

        strengths = rng.integers(low=0, high=90, size=n_peaks)
        strengths[0] = 100

        average_width = np.ones(2*n_peaks)*self.board_resolution*0.5

        widths = average_width + rng.normal(loc = 0., scale=self.board_resolution*0.2, size=n_peaks*2)
        widths = widths.reshape(n_peaks, 2)

        R = np.stack([X.flatten(), Y.flatten()]).T

        f = multi_gaussian(R, strengths, peaks, widths).reshape(self.board_resolution, self.board_resolution)
        self.function_landscape = f

    def init_mask(self):
        self.mask = np.ones(self.function_landscape.shape, dtype=bool)

    def uncover(self, index):
        self.mask[index[0], index[1]] = False

    def cover(self, index):
        self.mask[index[0], index[1]] = True
    
    @property
    def masked_landscape(self):
        f = self.function_landscape
        if self.mask is not None:
            return ma.masked_where(self.mask, f)
        else:
            raise RuntimeError("mask not yet set")
            

def convert_data_to_rgba(img, mask):    
    rgba = np.zeros((img.shape[0], img.shape[1], 3), dtype=np.uint8)
    for index in np.ndindex(img.shape):
        val = img[index]
        color_str =  pc.sample_colorscale("Turbo", val/100.)[0]
        color_codes = color_str.split("(")[1].split(")")[0].split(",")
        r = int(color_codes[0].strip())        
        g = int(color_codes[1].strip())        
        b = int(color_codes[2].strip())
        if mask[index]:
            r = 255
            g = 255
            b = 255
        # else:
            #alpha = 255
        
        rgba[index[0], index[1], :] = np.array([r, g, b])
    # print(rgba[:2, :2])
    return rgba
import time
class Landscape_Plotter():
    
    def __init__(self, landscape:Landscape):
        self.ls = landscape
        self.fig = None
        
        
    def update_plot(self):
        f = self.ls.function_landscape.copy().astype(float)
        mask = self.ls.mask.T
        print(mask[:2, :2])
        img = f
        rgba = convert_data_to_rgba(img, mask)
        
        labels_flat = []
        for index in np.ndindex(f.shape):
            if mask[index]:
                labels_flat.append("")
            else:
                labels_flat.append(f"{f[index]:.0f}")
        
        
        x_coords = np.arange(self.ls.board_resolution)
        y_coords = np.arange(1, self.ls.board_resolution+1)
        X, Y = np.meshgrid(x_coords, y_coords)
        
        # Flatten arrays
        X_flat = X.flatten()
        Y_flat = Y.flatten()
        #print(self.fig.data[2])
        # self.fig.data[1]['z'] = rgba        )
        #print(labels_flat)
        self.fig.update_traces(selector=1, patch={'z':rgba})       
        self.fig.update_traces(selector=2,
                               patch={
                                   'text':labels_flat}
                               )
        # self.fig.
        #print(self.fig.data[2])
        # self.fig.data[2]['text'] = labels_flat
        # self.fig.data[2]['x'] = X_flat
        # self.fig.data[2]['y'] = Y_flat
        self.fig.update_yaxes(
            autorange=True
        )                
        return self.fig        
     
    def east_arrow_coord(self, center):
        arrow_center = center + np.array([0.5, 0.])
        scale = 2.0
        x = np.array([
            arrow_center[0]-0.1*scale,
            arrow_center[0]+0.1*scale,
            arrow_center[0]+0.1*scale,
            arrow_center[0]+0.25*scale,
            arrow_center[0]+0.1*scale,
            arrow_center[0]+0.1*scale,
            arrow_center[0]-0.1*scale,
            arrow_center[0]-0.1*scale,
            ])
        
        y = np.array([
            arrow_center[1]-0.1*scale,
            arrow_center[1]-0.1*scale,
            arrow_center[1]+-0.15*scale,
            arrow_center[1],
            arrow_center[1]+0.15*scale,
            arrow_center[1]+0.1*scale,
            arrow_center[1]+0.1*scale,
            arrow_center[1]-0.1*scale,
            ])
        
        x_text = (arrow_center[0]+0.15,)
        y_text = (arrow_center[1],)
        
        return (x, y, x_text, y_text)
    
    def west_arrow_coord(self, center):
        arrow_center = center + np.array([-0.5, 0.])
        scale = 2.0
        x = np.array([
            arrow_center[0]+0.1*scale,
            arrow_center[0]-0.1*scale,
            arrow_center[0]-0.1*scale,
            arrow_center[0]-0.25*scale,
            arrow_center[0]-0.1*scale,
            arrow_center[0]-0.1*scale,
            arrow_center[0]+0.1*scale,
            arrow_center[0]+0.1*scale,
            ])[::-1]
        
        y = np.array([
            arrow_center[1]+0.1*scale,
            arrow_center[1]+0.1*scale,
            arrow_center[1]+0.15*scale,
            arrow_center[1],
            arrow_center[1]-0.15*scale,
            arrow_center[1]-0.1*scale,
            arrow_center[1]-0.1*scale,
            arrow_center[1]+0.1*scale,
            ])[::-1]
        
        x_text = (arrow_center[0]-0.15,)
        y_text = (arrow_center[1],)
        
        return (x, y, x_text, y_text)
    
    def north_arrow_coord(self, center):
        arrow_center = center + np.array([0.0, 0.5])
        scale = 2.0
        y = np.array([
            arrow_center[1]-0.1*scale,
            arrow_center[1]+0.1*scale,
            arrow_center[1]+0.1*scale,
            arrow_center[1]+0.25*scale,
            arrow_center[1]+0.1*scale,
            arrow_center[1]+0.1*scale,
            arrow_center[1]-0.1*scale,
            arrow_center[1]-0.1*scale,
            ])
        
        x = np.array([
            arrow_center[0]-0.1*scale,
            arrow_center[0]-0.1*scale,
            arrow_center[0]+-0.15*scale,
            arrow_center[0],
            arrow_center[0]+0.15*scale,
            arrow_center[0]+0.1*scale,
            arrow_center[0]+0.1*scale,
            arrow_center[0]-0.1*scale,
            ])
        
        x_text = (arrow_center[0],)
        y_text = (arrow_center[1]+0.15,)
        
        return (x, y, x_text, y_text)    
    
    def south_arrow_coord(self, center):
        arrow_center = center + np.array([0.0, -0.5])
        scale = 2.0
        y = np.array([
            arrow_center[1]+0.1*scale,
            arrow_center[1]-0.1*scale,
            arrow_center[1]-0.1*scale,
            arrow_center[1]-0.25*scale,
            arrow_center[1]-0.1*scale,
            arrow_center[1]-0.1*scale,
            arrow_center[1]+0.1*scale,
            arrow_center[1]+0.1*scale,
            ])
        
        x = np.array([
            arrow_center[0]+0.1*scale,
            arrow_center[0]+0.1*scale,
            arrow_center[0]+0.15*scale,
            arrow_center[0],
            arrow_center[0]-0.15*scale,
            arrow_center[0]-0.1*scale,
            arrow_center[0]-0.1*scale,
            arrow_center[0]+0.1*scale,
            ])
        
        x_text = (arrow_center[0],)
        y_text = (arrow_center[1]-0.15,)
        
        return (x, y, x_text, y_text)    
    
    def create_arrow(self):
        center = np.array([1.0, 2.0])
        #east
        for generator in [self.east_arrow_coord, self.north_arrow_coord,
                          self.south_arrow_coord, self.west_arrow_coord]:
            x, y, x_text, y_text = generator(center)
            
            
            self.fig.add_trace(
                go.Scatter(
                    x=x, y=y,
                    fill="toself",                
                    fillcolor="white",
                    line=dict(color="black"),
                    marker=dict(opacity=0.),
                    hoverinfo='skip',
                ),
            )
            
            self.fig.add_trace(
                go.Scatter(
                    x=x_text, y=y_text,
                    text=["7"],             
                    mode="text",
                    textfont=dict(color="black", size=16),
                    showlegend=False,                   
                    hoverinfo='skip',
                ),
            )
    
    def init_plot(self):
        f = np.zeros((self.ls.board_resolution, self.ls.board_resolution))
        mask = np.ones((self.ls.board_resolution, self.ls.board_resolution), dtype=bool)
        rgba = convert_data_to_rgba(f, mask)
        fig= go.Figure()
        fig.add_trace(
            go.Heatmap(
                z=f,
                colorscale="Turbo",
                showscale=True,
                hoverinfo='skip',
                y0=1,
                zmin=0,
                zmax=100,
                opacity=0  # make the heatmap invisible
            )
        )

        
        fig.add_trace(
            go.Image(
                z=rgba,
                colormodel="rgb",
                y0=1,
            )
        )
        
        letters = ["A", "B", "C", "D", "E", "F", "G", "H"]
        customdata = np.tile(letters, (8, 1))
        
        fig.update_traces(
            hovertemplate="X: %{customdata}<br>Y: %{y}<br><extra></extra>",
            customdata=customdata,
        )
        #f[mask] = -1.
            
        x_coords = np.arange(self.ls.board_resolution)
        y_coords = np.arange(1, self.ls.board_resolution+1)
        X, Y = np.meshgrid(x_coords, y_coords)
        
        # Flatten arrays
        X_flat = X.flatten()
        Y_flat = Y.flatten()
        labels_flat = []
        for index in np.ndindex(f.shape):
            if mask[index]:
                labels_flat.append("")
            else:
                labels_flat.append(f"{f[index]:.0f}")
        
        
        
        
        fig.add_trace(
            go.Scatter(
                x=X_flat,
                y=Y_flat,
                text=labels_flat,
                mode="text",
                textfont=dict(color="black", size=16),
                showlegend=False,
                hoverinfo='skip',
            )
        ) 
        
        # Gridlines 
        for y in range(self.ls.board_resolution+1):
            fig.add_shape(
                type="line",
                x0=0-0.5, x1=self.ls.board_resolution-0.5,
                y0=y+0.5, y1=y+0.5,
                line=dict(color="black", width=2)
            )
        
        # Add grid lines (vertical)
        for x in range(self.ls.board_resolution+1):
            fig.add_shape(
                type="line",
                x0=x-0.5, x1=x-0.5,
                y0=0+0.5, y1=self.ls.board_resolution+0.5,
                line=dict(color="black", width=2)
            )
            
        fig.update_layout(
            xaxis=letter_ticks(self.ls.board_resolution),            
            width=700,
            height=700
        )        
        
        self.fig = fig
        
        self.create_arrow()
        self.fig.update_layout(showlegend=False)
        return fig
        
        
        
        # fig = px.imshow(
        #     img=str_data,
        #     origin="lower",
        #     color_continuous_scale="Turbo",
        #     zmin=0,
        #     zmax=100,
        #     text_auto=True,
        #     # hovertemplate='x:%{x:.3f}y:%{y:.3f}',
        # )   
        
        fig.update_xaxes(tickfont=dict(size=18))
        fig.update_yaxes(tickfont=dict(size=18))

    
    

        # def west_arrow_coord(self, center):
        #     arrow_center = center + np.array([-0.5, 0.])
        #     scale = 2.0
        #     x = np.array([
        #         arrow_center[0]+0.1*scale,
        #         arrow_center[0]-0.1*scale,
        #         arrow_center[0]-0.1*scale,
        #         arrow_center[0]-0.25*scale,
        #         arrow_center[0]-0.1*scale,
        #         arrow_center[0]-0.1*scale,
        #         arrow_center[0]+0.1*scale,
        #         arrow_center[0]+0.1*scale,
        #         ])[::-1]
            
        #     y = np.array([
        #         arrow_center[1]+0.1*scale,
        #         arrow_center[1]+0.1*scale,
        #         arrow_center[1]+0.15*scale,
        #         arrow_center[1],
        #         arrow_center[1]-0.15*scale,
        #         arrow_center[1]-0.1*scale,
        #         arrow_center[1]-0.1*scale,
        #         arrow_center[1]+0.1*scale,
        #         ])[::-1]
            
        #     x_text = (arrow_center[0]-0.15,)
        #     y_text = (arrow_center[1],)
            
        #     return (x, y, x_text, y_text)
        
        # def north_arrow_coord(self, center):
        #     arrow_center = center + np.array([0.0, 0.5])
        #     scale = 2.0
        #     y = np.array([
        #         arrow_center[1]-0.1*scale,
        #         arrow_center[1]+0.1*scale,
        #         arrow_center[1]+0.1*scale,
        #         arrow_center[1]+0.25*scale,
        #         arrow_center[1]+0.1*scale,
        #         arrow_center[1]+0.1*scale,
        #         arrow_center[1]-0.1*scale,
        #         arrow_center[1]-0.1*scale,
        #         ])
            
        #     x = np.array([
        #         arrow_center[0]-0.1*scale,
        #         arrow_center[0]-0.1*scale,
        #         arrow_center[0]+-0.15*scale,
        #         arrow_center[0],
        #         arrow_center[0]+0.15*scale,
        #         arrow_center[0]+0.1*scale,
        #         arrow_center[0]+0.1*scale,
        #         arrow_center[0]-0.1*scale,
        #         ])
            
        #     x_text = (arrow_center[0],)
        #     y_text = (arrow_center[1]+0.15,)
            
        #     return (x, y, x_text, y_text)    
        
        # def south_arrow_coord(self, center):
        #     arrow_center = center + np.array([0.0, -0.5])
        #     scale = 2.0
        #     y = np.array([
        #         arrow_center[1]+0.1*scale,
        #         arrow_center[1]-0.1*scale,
        #         arrow_center[1]-0.1*scale,
        #         arrow_center[1]-0.25*scale,
        #         arrow_center[1]-0.1*scale,
        #         arrow_center[1]-0.1*scale,
        #         arrow_center[1]+0.1*scale,
        #         arrow_center[1]+0.1*scale,
        #         ])
            
        #     x = np.array([
        #         arrow_center[0]+0.1*scale,
        #         arrow_center[0]+0.1*scale,
        #         arrow_center[0]+0.15*scale,
        #         arrow_center[0],
        #         arrow_center[0]-0.15*scale,
        #         arrow_center[0]-0.1*scale,
        #         arrow_center[0]-0.1*scale,
        #         arrow_center[0]+0.1*scale,
        #         ])
            
        #     x_text = (arrow_center[0],)
        #     y_text = (arrow_center[1]-0.15,)
            
        #     return (x, y, x_text, y_text)    