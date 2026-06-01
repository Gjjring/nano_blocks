# -*- coding: utf-8 -*-
"""
Created on Mon Dec 29 15:43:55 2025

@author: Phill
"""
import numpy as np
# import matplotlib.pyplot as plt
from scipy.stats import qmc
import matplotlib.cm as cm
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
import string 
def gaussian(X, a, b ,c):
    # print(X.shape)
    # print(b.shape)
    # print((X-b).shape)
    return a*np.exp(-(
        (X[:, 0]-b[0])**2/(2*c[0]**2) +
        (X[:, 1]-b[1])**2/(2*c[1]**2))
        )

def mpl_to_plotly(cmap, n=256):
    return [
        [i/(n-1), f"rgb({int(r*255)},{int(g*255)},{int(b*255)})"]
        for i, (r, g, b, _) in enumerate(cmap(np.linspace(0, 1, n)))
    ]

def gaussian_grad(X, a, b ,c, dim_index):
    # print(X.shape)
    # print(b.shape)
    # print((X-b).shape)
    g = gaussian(X, a, b, c)
    
    if dim_index == 0:
        df = -((X[:,0]-b[0])/c[0]**2)*g
    else:
        df = -((X[:,1]-b[1])/c[1]**2)*g
    return df

def gaussian_with_grad(X, a, b, c):
    g = gaussian(X, a, b, c)
    dg = []
    for index in range(2):
        df = -((X[:, index]-b[index])/c[index]**2)*g
        dg.append(df)
    return (g, dg)

def multi_gaussian_with_grad(X, a, b, c):
    f = np.zeros(X.shape[0])
    df = np.zeros((X.shape[0], 2))
    # print(f.shape)
    for ii in range(a.size):
        print(a[ii], b[ii, :], c[ii, :])
        g, dg = gaussian_with_grad(X, a[ii], b[ii, :], c[ii, :])
        print(np.max(g))
        
        #f = np.maximum(f, g)
        f += g
        df[:, 0] += dg[0]
        df[:, 1] += dg[1]
        # print(f.shape)
    
    norm_factor = (np.max(f)/100)
    f /= norm_factor
    #f -= np.min(f)
    df /= norm_factor
    #f = np.round(f).astype(int)
    return f, df

# def multi_gaussian_grad(X, a, b, c):
#     df = np.zeros((X.shape[0], 2))
#     # print(f.shape)
#     for ii in range(a.size):
#         for jj, dim in enumerate(['x', 'y']):
#             g = gaussian_grad(X, a[ii], b[ii, :], c[ii, :], dim)
#             #f = np.maximum(f, g)
#             df[..., jj] += g
#             # print(f.shape)
#     df /= (np.max(f)/100)
    
#     return f

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
            n_peaks:int=1,
            
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
        self.previous_pos = None
        self.current_gradients = None
        self.current_hint = None
        self.mask_editable = True
        self.current_hint = None        
        self.surrogate_predictions = None
        self.hint_function = None
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
        l_bounds = (0, 0)
        u_bounds = (self.board_resolution, self.board_resolution)
        sobol = qmc.Sobol(2, seed=self.seed)
        peaks = sobol.integers(self.board_resolution, n=n_peaks)
        print(peaks)
        #peaks = qmc.scale(design_points, l_bounds, u_bounds)
        # peaks = rng.integers(low=0, high=self.board_resolution,
        #              size=n_peaks*2).reshape(n_peaks,2)
        
        self.peaks = peaks
        # print(f"peaks: {peaks}")
        x = np.arange(self.board_resolution)
        X, Y = np.meshgrid(x, x, indexing='ij')
        f = np.zeros_like(X)
        self.X = X
        self.Y = Y

        # strengths = rng.integers(low=0, high=90, size=n_peaks)
        # strengths[0] = 100

        # average_width = np.ones(2*n_peaks)*self.board_resolution*0.5    

        # widths = average_width + rng.normal(loc = 0., scale=self.board_resolution*0.2, size=n_peaks*2)
        # widths = np.clip(widths, a_min=2.0, a_max=None)
        # widths = widths.reshape(n_peaks, 2)
        # print(f"widths: {widths}")
        
        
        strengths = rng.normal(loc = 80., scale=10., size=n_peaks)
        strengths = np.clip(strengths, a_min=70., a_max=90.)
        strengths[0] = 100

        
        #print(f"average_width, {average_width}")
        factor=  np.sqrt(7-n_peaks)
        if n_peaks == 1:
            average_width = np.ones(2*n_peaks)*factor*self.board_resolution/8.
            # print(f"average width: {average_width}")
            widths = average_width + rng.normal(loc = 0., scale=average_width/5., size=n_peaks*2)
            widths = widths.reshape(1, 2)
        else:
            if n_peaks < 5:
                n_wide = 1
            else:
                n_wide = 2            
            widths = np.zeros((n_peaks, 2))
            narrow_width = factor*self.board_resolution/16.
            wide_width = factor*self.board_resolution/8.            
            # print(f"narrow width: {narrow_width}, wide width: {wide_width}")
            
            width_sizes = np.ones(n_peaks, dtype=bool)
            width_sizes[:n_wide] = False
            rng.shuffle(width_sizes)
            
            for i_peak in range(n_peaks):                
                #if i_peak == 1:
                if not width_sizes[i_peak]:
                    widths[i_peak, :] = wide_width + rng.normal(loc = 0., scale=wide_width/5.0, size=2)
                else:
                    widths[i_peak, :] = narrow_width + rng.normal(loc = 0., scale=narrow_width/5.0, size=2)
        widths = np.clip(widths, a_min=2.0, a_max=None)
        #widths = widths.reshape(n_peaks, 2)

        # print(f"strengths: {strengths}")
        # print(f"widths: {widths}")
        

        R = np.stack([X.flatten(), Y.flatten()]).T
        f, grad_f = multi_gaussian_with_grad(R, strengths, peaks, widths)
        f = f.reshape(self.board_resolution, self.board_resolution)
        grad_f = grad_f.reshape(self.board_resolution, self.board_resolution, 2)
        #f = multi_gaussian(R, strengths, peaks, widths).reshape(self.board_resolution, self.board_resolution)
        #grad_f = multi_gaussian_grad(R, strengths, peaks, widths).reshape(self.board_resolution, self.board_resolution)
        self.function_landscape = f
        self.gradient_landspace = grad_f

    def init_mask(self):
        self.mask = np.ones(self.function_landscape.shape, dtype=bool)
        self.mask_editable = True

    def uncover(self, index):
        if self.mask_editable:
            self.mask[index[0], index[1]] = False
            #self.init_surrogate_model()

    def cover(self, index):
        if self.mask_editable:
            self.mask[index[0], index[1]] = True
    
    def remove_mask(self):
        self.mask = np.zeros(self.function_landscape.shape, dtype=bool)
        self.mask_editable = False
    
    @property
    def masked_landscape(self):
        f = self.function_landscape
        if self.mask is not None:
            return ma.masked_where(self.mask.T, f)
        else:
            raise RuntimeError("mask not yet set")
            
    def calc_gradients(self):
        if self.current_pos is None:
            return
        index = self.current_pos
        
        gradients = self.gradient_landspace[index[1], index[0], ::-1]
        # print("function: {}".format(self.function_landscape[index[1], index[0]]))
        # print("gradients: {}".format(gradients))
        self.current_gradients = gradients
        
    def init_surrogate_model(self):
        print("##### init surrogate model called ####")

        X = self.X
        Y = self.Y
        f_masked = self.masked_landscape.compressed()
        if f_masked.size > 0:        
            inv_mask = np.logical_not(self.mask).T
            x_unmasked = X[inv_mask]
            y_unmasked = Y[inv_mask]
            R = np.stack([x_unmasked, y_unmasked]).T
            mean = np.mean(f_masked)
            print(f"f_masked.size: {f_masked.size}")
            print(f_masked)            
            for row in range(R.shape[0]):
                print(R[row,: ], print(f_masked[row]))
                
                
            
            
            surrogate = GaussianProcessRegressor(
                normalize_y=True,
                # kernel= (ConstantKernel(mean, constant_value_bounds="fixed") +
                #           ConstantKernel(mean, constant_value_bounds=(0.1, 10000.))*Matern(1.0, length_scale_bounds=(0.1, 1000.), nu=2.5)),
                kernel = Matern(1.0, length_scale_bounds=(0.1, 1000.), nu=2.5),
                # kernel = ConstantKernel(mean, constant_value_bounds=(0.1, 10000.))*Matern(1.0, length_scale_bounds=(0.1, 1000.), nu=2.5),
                random_state=self.seed,
                n_restarts_optimizer=0)
            
            surrogate.fit(R, f_masked)
            print(surrogate.kernel_)
            all_R = np.stack([X.flatten(), Y.flatten()]).T
            predictions, std = surrogate.predict(all_R, return_std=True)
            print(np.max(predictions))
            
            mean = predictions.reshape(X.shape)
            std = std.reshape(X.shape)*mean
            
            max_val = int(np.max(np.round(f_masked)))
            if max_val == 100:
                hint = np.where(np.isclose(self.function_landscape, max_val))
                #print(hint)
                self.hint_function = np.ones(self.function_landscape.shape)*100
            else:
                Z1 = -1*(mean-max_val)/std        
                Z2 = -1*(mean-100)/std
                cdf1 = norm.cdf(Z1)        
                pdf1 = norm.pdf(Z1)
                
                cdf2 = norm.cdf(Z2)        
                pdf2 = norm.pdf(Z2)
                ei = (mean-max_val)* (cdf2-cdf1) + std*(pdf1-pdf2)
                
                if np.max(mean) > 80.:
                    acq_func = np.copy(mean)
                    acq_func[inv_mask] = 0
                else:
                    z = (100 - mean) / std
                    if np.max(std) < 1e-5:
                        acq_func = np.zeros_like(mean)
                    else:
                        acq_func = np.exp(-0.5 * z**2) / std
                    
                
                
                # ei = (mean-max_val)* (cdf1) + std*(pdf1)
                # hint = np.where(np.isclose(ei, np.max(ei)))
                
                if np.max(acq_func) < 1.:
                    print("random hint")
                    x_masked = X[self.mask.T]
                    y_masked = Y[self.mask.T]
                    R = np.stack([x_masked, y_masked]).T
                    rows = list(range(R.shape[0]))
                    row = np.random.choice(rows)
                    
                    hint = [[R[row, 0]],[R[row, 1]]]
                else:
                    hint = np.where(np.isclose(acq_func, np.max(acq_func)))
                
                print(f"max ei: {np.max(ei)}")
                # target = 100
                # eps = 1                
                # scores = norm.cdf((target+eps-mean)/std) - norm.cdf((target-eps-mean)/std)
                #best_idx = unsampled_idx[np.argmax(scores)]                
                #print(f"max scores: {np.max(scores)}")
                
                # if np.max(scores) < 1.:
                #     x_masked = X[self.mask.T]
                #     y_masked = Y[self.mask.T]
                #     R = np.stack([x_masked, y_masked]).T
                #     rows = list(range(R.shape[0]))
                #     row = np.random.choice(rows)
                    
                #     hint = [[R[row, 0]],[R[row, 1]]]
                # else:
                # hint = np.where(np.isclose(scores, np.max(scores)))
                self.hint_function = acq_func
            hint = np.array([hint[0][0], hint[1][0]])
            self.current_hint =hint
            
            
            #print(predictions.shape)
            # print(np.max(mean))
            
            self.surrogate_predictions = mean
            

def convert_data_to_rgba(mask):    
    rgba = np.zeros((mask.shape[0], mask.shape[1], 4), dtype=np.uint8)
    r = 255
    g = 255
    b = 255
    for index in np.ndindex(mask.shape):
        
        
        if mask[index]:
            alpha = 255         
        else:
            alpha = 0
        
        rgba[index[0], index[1], :] = np.array([r, g, b, alpha])
    # print(rgba[:2, :2])
    return rgba
import time







class Landscape_Plotter():
    
    def __init__(self, landscape:Landscape):
        self.ls = landscape
        self.fig = None
        self.compass_fig = None
        self.ml_fig = None
        
        
    def update_landscape(self):
        f = np.round(self.ls.function_landscape.copy().astype(float))
        #print(self.fig.data[0])
        self.fig.update_traces(
            selector=0,
            z=f,
        )
        self.update_peak_pos()
        return self.fig
    
    # def update_landscape(self):
    #     f = self.ls.function_landscape.copy().astype(float)
    #     #print(self.fig.data[0])
    #     self.fig.update_traces(
    #         selector=0,
    #         z=f,
    #     )
    #     self.update_peak_pos()
    #     return self.fig
    
    def update_current_pos(self, xy):
        self.ls.current_pos = xy
        y0 = 1
        x0 = 0
        x = np.arange(x0, self.ls.board_resolution+x0)
        y = np.arange(y0, self.ls.board_resolution+y0)
        X, Y = np.meshgrid(x, y, indexing='ij')
        
        
        if self.ls.previous_pos is not None:
            x = X[self.ls.previous_pos[0], self.ls.previous_pos[1]]
            y = Y[self.ls.previous_pos[0], self.ls.previous_pos[1]]
            selector={'x0':x-0.5, 'y0':y-0.5}
            self.fig.update_shapes(
                selector=selector,
                line=dict(
                    color="black",
                    width=2,
                ),
                fillcolor=None,
            )
        
        x = X[xy[0], xy[1]]
        y = Y[xy[0], xy[1]]
        selector={'x0':x-0.5, 'y0':y-0.5}
        self.fig.update_shapes(
            selector=selector,
            line=dict(
                color=pc.qualitative.Plotly[0],
                width=4,                
            ),
        )
        shapes = list(self.fig['layout']['shapes'])
        got_it = False
        for ishape, shape in enumerate(shapes):
            if shape["line"] is not None:
                if shape['line']['color'] == pc.qualitative.Plotly[0]:
                    got_it = True
                    break
        if got_it:            
            shapes.append(shapes.pop(ishape))
            self.fig['layout']['shapes'] =tuple(shapes)
                    
        self.ls.previous_pos = self.ls.current_pos
        return self.fig
        
    def update_mask(self, xy):
        if not self.ls.mask_editable:
            return self.fig
        mask = self.ls.mask
        #rgba = convert_data_to_rgba(mask)
        
        new_value = not mask[xy[0], xy[1]]
        self.ls.mask[xy[0], xy[1]] = new_value
        
        
        y0 = 1
        x0 = 0
        x = np.arange(x0, self.ls.board_resolution+x0)
        y = np.arange(y0, self.ls.board_resolution+y0)
        X, Y = np.meshgrid(x, y, indexing='ij')
        
        x = X[xy[0], xy[1]]
        y = Y[xy[0], xy[1]]
        selector={'x0':x-0.5, 'y0':y-0.5}
        if new_value:
            self.fig.update_shapes(selector=selector, fillcolor="white")
        else:
            self.fig.update_shapes(selector=selector, fillcolor=None)
        
        # for index in np.ndindex(mask.shape):            
        #     x = X[index]
        #     y = Y[index]
        #     selector={'x0':x-0.5, 'y0':y-0.5}
        #     if mask[index]:
        #         self.fig.update_shapes(selector=selector, fillcolor="white")
        #     else:
        #         self.fig.update_shapes(selector=selector, fillcolor=None)
            
        
        # self.fig.update_traces(selector=0, opacity=0.)
        # self.fig.update_traces(selector=1, patch={'z':rgba})
         # self.fig.update_traces(selector=0, opacity=1.)
        return self.fig
    
         
    def reset_mask(self):
        print("start reset_mask")
        mask = self.ls.mask
        
        
        y0 = 1
        x0 = 0
        
        x = np.arange(x0, self.ls.board_resolution+x0)
        y = np.arange(y0, self.ls.board_resolution+y0)
        X, Y = np.meshgrid(x, y, indexing='ij')
        
        for index in np.ndindex(mask.shape):            
            x = X[index]
            y = Y[index]
            selector={'x0':x-0.5, 'y0':y-0.5}
            if mask[index]:
                self.fig.update_shapes(
                    selector=selector,
                    fillcolor="white",
                    line=dict(
                        color="black",
                        width=2,
                    ),
                )
            else:
                self.fig.update_shapes(
                    selector=selector,
                    fillcolor=None,
                    line=dict(
                        color="black",
                        width=2,
                    ),
                )
        self.ls.previous_pos = None
        print("end reset_mask")
        return self.fig
    
    def plot_peak_pos(self):        
        self.fig.add_trace(
            go.Scatter(
                x=self.ls.peaks[:, 1],
                y=self.ls.peaks[:, 0]+1,
                marker={'color':"black"},
                showlegend=False,
                mode='markers',
                hoverinfo='skip',
            )
        )
        
    def update_peak_pos(self):
        
        self.fig.update_traces(
            selector=1,
            x=self.ls.peaks[:, 1],
            y=self.ls.peaks[:, 0]+1,
            
        )
        
        # self.fig.add_trace(
        #     go.Scatter(
        #         x=self.ls.peaks[:, 0],
        #         y=self.ls.peaks[:, 1],
        #         marker={'color':"white"},
        #         showlegend=False,
        #         hoverinfo='skip',
        #     )
        # )
    
    def init_plot(self):
        print("start init_plot")
        f = np.zeros((self.ls.board_resolution, self.ls.board_resolution))
        mask = self.ls.mask
        #mask = np.ones((self.ls.board_resolution, self.ls.board_resolution), dtype=bool).T
        #mask[0, 0] = False
        #rgba = convert_data_to_rgba(mask)
        #print(rgba[:2, :2])
        #fig= go.Figure()
        
        #letters = ["A", "B", "C", "D", "E", "F", "G", "H"]
        letters = list(string.ascii_uppercase[:self.ls.board_resolution])
        customdata = np.tile(letters, (self.ls.board_resolution, 1))
        
               
        terrain = mpl_to_plotly(cm.get_cmap("terrain"))
        
        fig = px.imshow(
                img=f,
                origin="lower",
                #x=letters,
                y=np.arange(1, self.ls.board_resolution+1),
                color_continuous_scale =terrain,
                #hoverinfo='skip',
                text_auto=True,
                #y0=1,
                zmin=0,
                zmax=100,
                #hovertemplate="X: %{x}<br>Y: %{y}<br><extra></extra>",
                # customdata=customdata,
            )
        self.fig = fig
        y0 = 1
        x0 = 0
        x = np.arange(x0, self.ls.board_resolution+x0)
        y = np.arange(y0, self.ls.board_resolution+y0)
        X, Y = np.meshgrid(x, y, indexing='ij')
        
        for index in np.ndindex(mask.shape):
            x = X[index]
            y = Y[index]
            if mask[index]:
                shape = fig.add_shape(type="rect",
                    x0=x-0.5, y0=y-0.5, x1=x+0.5, y1=y+0.5,                    
                    fillcolor="white",
                    line=dict(
                        color="black",
                        width=2,
                    ),
                )
            else:
                shape = fig.add_shape(type="rect",
                    x0=x-0.5, y0=y-0.5, x1=x+0.5, y1=y+0.5,                    
                    fillcolor=None,
                    line=dict(
                        color="black",
                        width=2,
                    ),
                )
        self.plot_peak_pos()
            
        
        # fig.add_trace(
        #     go.Image(
        #         z=rgba,                
        #         colormodel="rgba",
        #         hoverinfo="skip",
        #         y0=1,
        #         zorder=10,
        #         # x0=0,
        #     )
        # )
        
        
        
        fig.update_traces(
            hovertemplate="X: %{customdata}<br>Y: %{y}<br><extra></extra>",
            customdata=customdata,
        )
        #f[mask] = -1.
            
        # x_coords = np.arange(self.ls.board_resolution)
        # y_coords = np.arange(1, self.ls.board_resolution+1)
        # X, Y = np.meshgrid(x_coords, y_coords)
        
        # # Flatten arrays
        # X_flat = X.flatten()
        # Y_flat = Y.flatten()
        # labels_flat = []
        # for index in np.ndindex(f.shape):
        #     if mask[index]:
        #         labels_flat.append("")
        #     else:
        #         labels_flat.append(f"{f[index]:.0f}")
        
        
        
        
        # fig.add_trace(
        #     go.Scatter(
        #         x=X_flat,
        #         y=Y_flat,
        #         text=labels_flat,
        #         mode="text",
        #         textfont=dict(color="black", size=16),
        #         showlegend=False,
        #         hoverinfo='skip',
        #     )
        # ) 
        
        # Gridlines 
        # for y in range(self.ls.board_resolution+1):
        #     fig.add_shape(
        #         type="line",
        #         x0=0-0.5, x1=self.ls.board_resolution-0.5,
        #         y0=y+0.5, y1=y+0.5,
        #         line=dict(color="black", width=2)
        #     )
        
        # # Add grid lines (vertical)
        # for x in range(self.ls.board_resolution+1):
        #     fig.add_shape(
        #         type="line",
        #         x0=x-0.5, x1=x-0.5,
        #         y0=0+0.5, y1=self.ls.board_resolution+0.5,
        #         line=dict(color="black", width=2)
        #     )
            
        fig.update_layout(
            xaxis=letter_ticks(self.ls.board_resolution),            
            width=700,
            height=700
        )        
        fig.update_layout(paper_bgcolor="#d9e3f1")
        # self.fig = fig
        
        # self.create_arrow()
        # self.fig.update_layout(showlegend=False)
        fig.update_xaxes(tickfont=dict(size=18))
        fig.update_yaxes(
            tickfont=dict(size=18)
            
        )
        fig.update_xaxes(
            {'range': (-0.5, self.ls.board_resolution-0.5),
             'autorange': False,
             'fixedrange':True,
             }
        )     
        fig.update_yaxes(
             {'range': (0.5, self.ls.board_resolution+0.5),
              'autorange': False,
              'fixedrange':True,
              }
         )
        
        #      'showticklabels':False,
        #      'showgrid':False,
        #      'showline':False,
        #      'zeroline':False,
        #      }
        # )
        
        
        print("end init_plot")
        return fig
    
    
    def init_ml_plot(self):
        f = np.zeros((self.ls.board_resolution, self.ls.board_resolution))
        
        #letters = ["A", "B", "C", "D", "E", "F", "G", "H"]
        letters = list(string.ascii_uppercase[:self.ls.board_resolution])
        customdata = np.tile(letters, (self.ls.board_resolution, 1))
        
               
        terrain = mpl_to_plotly(cm.get_cmap("terrain"))
        
        fig = px.imshow(
                img=f,
                origin="lower",
                y=np.arange(1, self.ls.board_resolution+1),
                color_continuous_scale =terrain,        
                text_auto=True,
                zmin=0,
                zmax=100,
            )
        self.ml_fig = fig
        
        shape = fig.add_shape(type="rect",
            x0=-1.5, y0=-1.5, x1=-0.5, y1=-0.5,                    
            fillcolor=None,
            line=dict(
                color="purple",
                width=2,
            ),
        )
        
        fig.update_traces(
            hovertemplate="X: %{customdata}<br>Y: %{y}<br><extra></extra>",
            customdata=customdata,
        )        
            
        fig.update_layout(
            xaxis=letter_ticks(self.ls.board_resolution),            
            width=700,
            height=700
        )        
        fig.update_layout(paper_bgcolor="#d9e3f1")        
        fig.update_xaxes(tickfont=dict(size=18))
        fig.update_yaxes(
            tickfont=dict(size=18)            
        )
        
        fig.update_yaxes(
            {'range': (0.5, self.ls.board_resolution+0.5),
             'autorange': False,
             'fixedrange':True,
             }
        )       
        
        fig.update_xaxes(
            {'range': (-0.5, self.ls.board_resolution-0.5),
             'autorange': False,
             'fixedrange':True,
             }
        )       
        
        return fig    
    
    def update_ml_plot(self):
        if self.ls.surrogate_predictions is not None:
            f = np.round(self.ls.surrogate_predictions)
            #f = np.round(self.ls.hint_function)
            print(f"predictions max {np.max(f)}")
            #print(f"predictions:{f}")
            self.ml_fig.update_traces(
                selector=0,
                z=f,
            )
        if self.ls.current_hint is not None:
            
            x = self.ls.current_hint[1] 
            y = self.ls.current_hint[0] + 1
            
            selector = 0
            print(f"setting hint to pos: {x, y}")
            #print(self.)
            self.ml_fig.update_shapes(selector=selector,
                                   x0=x-0.5, y0=y-0.5, x1=x+0.5, y1=y+0.5)
            
        return self.ml_fig
        
    def east_arrow_coord(self, scale):
        arrow_center = np.array([0.0, 0.])
        #scale = 2.0
        scale1 = scale
        scale2 = 1.0
        
        head_begin = 0.1*scale1
        
        x = np.array([
            #tail
            arrow_center[0]-0.2*scale,
            arrow_center[0]+head_begin,
            arrow_center[0]+head_begin,
            arrow_center[0]+head_begin+0.1,
            arrow_center[0]+head_begin,
            arrow_center[0]+head_begin,
            arrow_center[0]-0.2*scale,
            arrow_center[0]-0.2*scale,
            ])
        scale1 = scale#
        scale2 = 0.5#
        head_width = scale2
        y = np.array([
            arrow_center[1]-0.08*scale2,
            arrow_center[1]-0.08*scale2,
            arrow_center[1]+-0.15*scale2,
            arrow_center[1],
            arrow_center[1]+0.15*scale2,
            arrow_center[1]+0.08*scale2,
            arrow_center[1]+0.08*scale2,
            arrow_center[1]-0.08*scale2,
            ])        
        
        return (x, y)
    

    
    def plot_gradient_compass(self):
        print("plot_gradient_compass")
        if self.ls.current_gradients is None:
            fig= go.Figure(
                )
        else:
            fig= go.Figure()
            
            scale = np.linalg.norm(self.ls.current_gradients)
            
            angle = -1*np.arctan2(
                self.ls.current_gradients[1],
                self.ls.current_gradients[0]
                )
            print(self.ls.current_gradients)
            #angle = np.radians(-45.)
            print(np.degrees(angle))
            self.create_arrow(fig, angle, scale)
      
            
        fig.update_layout(            
            width=400,
            height=400,
        )        
        fig.update_xaxes(
            {'range': (-0.5, 0.5),
             'autorange': False,
             'showticklabels':False,
             'showgrid':False,
             'showline':False,
             'zeroline':False,
             'fixedrange':True,
             }
        )
        fig.update_yaxes(
            {'range': (-0.5, 0.5),
             'autorange': False,
             'showticklabels':False,
             'showgrid':False,
             'showline':False,
             'zeroline':False,
             'fixedrange':True,
             }
        )
        fig.update
        fig.update_layout(paper_bgcolor="#d9e3f1")
        self.compass_fig = fig
        return fig
    
    def rotation_matrix(self, angle, size):
        R = np.array(
            [[np.cos(angle), np.sin(angle)],
             [-np.sin(angle), np.cos(angle)]]
        )
        R = np.tile(R, (size, 1, 1))
        return R
    
    def create_arrow(self, fig, angle, scale):
        center = np.array([0.0, 0.0])
        #east        
        scale = np.min([2.0, scale/5.])
        
        x, y = self.east_arrow_coord(scale)
        # print(x)
        # print(y)
        
        
        coords = np.stack([x, y]).T
        # print(coords)
        rotation = self.rotation_matrix(angle, coords.shape[0])
        
        #coords_rotated = np.squeeze(rotation @ coords[..., None])
        coords_rotated = np.einsum('nij,nj->ni', rotation, coords)
        # coords_rotated = coords
        print(coords_rotated.shape)
        
        fig.add_trace(
            go.Scatter(
                x=coords_rotated[:, 0],
                y=coords_rotated[:, 1],
                fill="toself",
                fillcolor="white",
                line=dict(color="black"),
                marker=dict(opacity=0.),
                hoverinfo='skip',
                zorder=100,
            ),
        )        
        
            
                
                
                
        
            
            
        
    