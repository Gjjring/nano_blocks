# -*- coding: utf-8 -*-
"""
Created on Mon Dec 29 15:43:55 2025

@author: Phill
"""
import numpy as np
import matplotlib.pyplot as plt
from scipy.stats import qmc
from matplotlib.ticker import FuncFormatter
from numpy import ma
from matplotlib.patches import Rectangle, FancyArrowPatch, ArrowStyle
from matplotlib.colors import Normalize
from sklearn.gaussian_process import GaussianProcessRegressor
from sklearn.gaussian_process.kernels import ConstantKernel, RBF, Matern
from scipy.special import erfc
from scipy.stats import norm

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
        f = np.maximum(f, g)
        # print(f.shape)
    f = np.rint(f).astype(int)
    return f


def num_to_letter(x, pos):
    x = int(x)
    if x < 1:
        return ""
    elif x > 26:
        return ""
    return chr(ord('A') + x - 1)

class Landscape:

    def __init__(
            self,
            seed:int=10,
            board_resolution:int=8,
            n_peaks=1,
        ):
        self.seed = seed
        self.board_resolution=board_resolution
        self.n_peaks = n_peaks
        self.mask = None
        self.function_landscape = None
        self.X = None
        self.Y = None
        self.peaks = None
        self.current_pos = None
        self.current_gradients = None

        self.fig = None
        self.landscape_mesh = None
        self.text_annotations = [None]*board_resolution**2
        self.current_pos_rect = None
        self.grad_arrows = [None]*4
        self.surrogate_mesh = None
        self.current_hint_rect = None


    def create_landscape(self):
        rng = np.random.default_rng(self.seed)

        n_peaks = self.n_peaks

        peaks = rng.integers(low=0, high=self.board_resolution,
                     size=n_peaks*2).reshape(n_peaks,2)
        self.peaks = peaks
        # print(peaks)
        x = np.arange(self.board_resolution)
        X, Y = np.meshgrid(x, x, indexing='ij')
        f = np.zeros_like(X)
        self.X = X
        self.Y = Y

        #strengths = rng.integers(low=0, high=90, size=n_peaks)
        strengths = rng.normal(loc = 60., scale=10., size=n_peaks)
        strengths[0] = 100

        average_width = np.ones(2*n_peaks)*(6-n_peaks)*self.board_resolution*0.5

        widths = average_width + rng.normal(loc = 0., scale=self.board_resolution*0.2, size=n_peaks*2)
        widths = widths.reshape(n_peaks, 2)
        #widths = np.stack([widths, widths]).T

        print(f"strengths: {strengths}")
        print(f"widths: {widths}")




        R = np.stack([X.flatten(), Y.flatten()]).T

        f = multi_gaussian(R, strengths, peaks, widths).reshape(self.board_resolution, self.board_resolution)
        self.function_landscape = f

    def create_mask(self):
        self.mask = np.ones(self.function_landscape.shape, dtype=bool)

    def uncover(self, index):
        self.mask[index[0], index[1]] = False

    def cover(self, index):
        self.mask[index[0], index[1]] = True

    # def create_figure(self):
    #     plt.close("all")
    #     fig = plt.figure(figsize=(18,16))
    #     self.fig = fig

    @property
    def masked_landscape(self):
        f = self.function_landscape
        if self.mask is not None:
            return ma.masked_where(self.mask, f)
        else:
            raise RuntimeError("mask not yet set")

    def plot_landscape(self, fig):
        plt.figure(fig)

        f = self.function_landscape
        if self.mask is not None:
            f_masked = ma.masked_where(self.mask, f)
        else:
            f_masked = f
        ax = plt.gca()
        if self.landscape_mesh is None:
            self.landscape_mesh = plt.pcolormesh(self.X+1, self.Y+1, f_masked, cmap='turbo',
                           vmin=0, vmax=100, edgecolor='k', lw=0.1)
            plt.colorbar()
            ax.xaxis.set_major_formatter(FuncFormatter(num_to_letter))
        else:
            self.landscape_mesh.set_array(f_masked.ravel())

        # plt.xlim(-0.1, self.board_resolution+0.1)
        # plt.ylim(-0.1, self.board_resolution+0.1)

    def annotate_numbers(self):
        f = self.function_landscape


        for index in np.ndindex(f.shape):
            flat_index = np.ravel_multi_index(index, f.shape)
            val = f[index]
            x = self.X[index] + 1
            y = self.Y[index] + 1
            s = f"{val}"
            if self.text_annotations[flat_index] is None:
                text = plt.text(x, y, s,
                                ha='center', va='center',
                fontsize=22., visible=False)
                self.text_annotations[flat_index] = text

            if self.mask is not None:
                if self.mask[index]:
                    self.text_annotations[flat_index].set_visible(False)
                    continue

            print(f"index is: {index[0]}, {index[1]}, {flat_index}")


            # self.text_annotations[flat_index].x = x
            # self.text_annotations[flat_index].y = y
            # self.text_annotations[flat_index].s = f"{val}"
            # print(self.text_annotations[flat_index])
            # print(self.text_annotations[flat_index].__dict__)
            self.text_annotations[flat_index].set_visible(True)

            # print(self.text_annotations[flat_index])
            # plt.text(x, y, f"{val}",
            #          ha='center', va='center',
            #          fontsize=22.)

        self.fig.canvas.draw_idle()

    def set_current_pos(self, index):
        self.current_pos = index

    def highlight_current_pos(self):
        index = self.current_pos + np.ones(2, dtype=int)
        xy = index - np.array([0.5, 0.5])
        print(index)
        print(xy)
        if self.current_pos_rect is None:
            rect = Rectangle(xy, width=1.0, height=1.0, lw=5.,
                         edgecolor='white', fill=False, zorder=10)
            self.current_pos_rect = rect
            plt.gca().add_artist(rect)
        else:
            self.current_pos_rect.set_xy(xy)

    def calc_gradients(self):
        if self.current_pos is None:
            return
        index = self.current_pos
        gradients = np.full(4, fill_value=np.nan)
        f = self.function_landscape
        for ii, direction in enumerate(["north", "east", "south", "west"]):
            if direction == "north":
                neighbour = index + np.array([0, 1], dtype=int)
            elif direction == "east":
                neighbour = index + np.array([1, 0], dtype=int)
            elif direction == "south":
                neighbour = index + np.array([0, -1], dtype=int)
            elif direction == "west":
                neighbour = index + np.array([-1, 0], dtype=int)
            print(index, neighbour)
            if np.any(neighbour < 0):
                continue
            try:
                gradients[ii] = f[neighbour[0], neighbour[1]] - f[index[0], index[1]]
            except IndexError:
                pass
        self.current_gradients = gradients

    def init_gradient_plot(self):
        ax = plt.gca()
        for ii in range(4):
            text = f"{int(ii)}"
            # text = ax.text(0, 0, text,
            #         ha="center", va="center",
            #         size=15,
            #         visible=False,
            #         bbox=dict(boxstyle="rarrow,pad=0.3",
            #       fc="lightblue", ec="steelblue", lw=2))
            arrowstyle = ArrowStyle.Simple(head_length=15.0, head_width=50.0, tail_width=25.0)
            text = plt.text(0, 0, text, fontsize=18, visible=False, ha="center", va='center')
            arrow = FancyArrowPatch(posA=(0, 0), posB=(-1, -1), visible=False,
                                    arrowstyle=arrowstyle)
            plt.gca().add_artist(arrow)
            self.grad_arrows[ii] = [text, arrow]

    def update_gradient_plot(self):
        if self.current_gradients is None:
            return
        if self.current_pos is None:
            return
        ax = plt.gca()
        for ii, grad_val in enumerate(self.current_gradients):
            print(ii, grad_val)
            if np.isnan(grad_val):
                self.grad_arrows[ii][0].set_visible(False)
                self.grad_arrows[ii][1].set_visible(False)
                continue

            length = 0.5
            length_a = 0.25
            length_b = 0.75
            if ii == 0:
                pos = self.current_pos + length*np.array([0, 1.0]) + np.ones(2)
                posA = self.current_pos + length_a*np.array([0, 1.0]) + np.ones(2)
                posB = self.current_pos + length_b*np.array([0, 1.0]) + np.ones(2)
                boxstyle= "rarrow,pad=0.3"
            elif ii == 1:
                pos = self.current_pos + length*np.array([1.0, 0.]) + np.ones(2)
                posA = self.current_pos + length_a*np.array([1.0, 0.0]) + np.ones(2)
                posB = self.current_pos + length_b*np.array([1.0, 0.0]) + np.ones(2)
                boxstyle= "rarrow,pad=0.3"
                #rotation = 0.
            elif ii == 2:
                pos = self.current_pos + length*np.array([0.0, -1.]) + np.ones(2)
                posA = self.current_pos + length_a*np.array([0, -1.0]) + np.ones(2)
                posB = self.current_pos + length_b*np.array([0, -1.0]) + np.ones(2)
                boxstyle= "rarrow,pad=0.3"
            elif ii == 3:
                pos = self.current_pos + length*np.array([-1.0, 0.]) + np.ones(2)
                posA = self.current_pos + length_a*np.array([-1.0, 0.0]) + np.ones(2)
                posB = self.current_pos + length_b*np.array([-1.0, 0.0]) + np.ones(2)
                #rotation = 180.
                boxstyle= "larrow,pad=0.3"

            bbox=dict(
                boxstyle=boxstyle,
                fc="lightblue",
                ec="steelblue",
                lw=2
            )
            text = f"{int(grad_val)}"
            cmap = plt.cm.get_cmap('coolwarm')
            norm = Normalize(vmin=-10, vmax=10)
            color = cmap(norm(grad_val))
            self.grad_arrows[ii][0].set_position(pos)
            self.grad_arrows[ii][0].set_text(text)
            #self.grad_arrows[ii].set_bbox(bbox)
            self.grad_arrows[ii][0].set_visible(True)
            self.grad_arrows[ii][1].set_positions(posA, posB)
            self.grad_arrows[ii][1].set_visible(True)
            self.grad_arrows[ii][1].set_edgecolor("k")
            self.grad_arrows[ii][1].set_facecolor(color)
            # print(self.grad_arrows[ii][0])
            # print(self.grad_arrows[ii][1])
        self.fig.canvas.draw_idle()


    def plot_peak_positions(self, fig):
        plt.figure(fig)
        plt.scatter(self.peaks[:,0]+1, self.peaks[:, 1]+1)


        # print(design_points)
        # print(l_bounds)
        # print(u_bounds)
        # design_points = qmc.scale(design_points, l_bounds, u_bounds)

        # print(design_points)

    def init_surrogate_model(self):
        

        X = self.X
        Y = self.Y
        f_masked = self.masked_landscape.compressed()
        inv_mask = np.logical_not(self.mask)
        x_unmasked = X[inv_mask]
        y_unmasked = Y[inv_mask]
        R = np.stack([x_unmasked, y_unmasked]).T
        mean = np.mean(f_masked)
        
        surrogate = GaussianProcessRegressor(
            normalize_y=True,
            # kernel= (ConstantKernel(mean, constant_value_bounds="fixed") +
            #           ConstantKernel(mean, constant_value_bounds=(0.1, 10000.))*Matern(1.0, length_scale_bounds=(0.1, 1000.), nu=2.5)),
            kernel = Matern(1.0, length_scale_bounds=(0.1, 1000.), nu=2.5),
            random_state=self.seed,
            n_restarts_optimizer=0)
        
        surrogate.fit(R, f_masked)
        print(surrogate.kernel_)
        all_R = np.stack([X.flatten(), Y.flatten()]).T
        predictions, std = surrogate.predict(all_R, return_std=True)
        
        mean = predictions.reshape(X.shape)
        std = std.reshape(X.shape)*mean
        
        max_val = np.max(f_masked)
        if np.isclose(max_val, 100):
            hint = np.where(np.isclose(self.function_landscape, max_val))
            print(hint)
        else:        
            u = (mean-max_val)/std        
            cdf = norm.cdf(u)        
            ei = (mean-max_val)* cdf + std*norm.pdf(u)                
            hint = np.where(np.isclose(ei, np.max(ei)))
        hint = np.array([hint[0][0], hint[1][0]])
        self.current_hint =hint
        
        
        #print(predictions.shape)
        self.surrogate_predictions = mean
        

    def plot_surrogate(self, ax):
        plt.sca(ax)
        if self.surrogate_mesh is None:
            self.surrogate_mesh = plt.pcolormesh(self.X+1, self.Y+1, self.surrogate_predictions, cmap='turbo',
                           vmin=None, vmax=None, edgecolor='k', lw=0.1)
            plt.colorbar()
            ax.xaxis.set_major_formatter(FuncFormatter(num_to_letter))
        else:
            self.surrogate_mesh.set_array(self.surrogate_predictions.ravel())
            
    def plot_hint(self):
        index = self.current_hint + np.ones(2, dtype=int)
        xy = index - np.array([0.5, 0.5])
        
        if self.current_hint_rect is None:
            rect = Rectangle(xy, width=1.0, height=1.0, lw=5.,
                         edgecolor='purple', fill=False, zorder=10)
            self.current_pos_rect = rect
            plt.gca().add_artist(rect)
        else:
            self.current_hint_rect.set_xy(xy)
    


if __name__ == "__main__":
    ls = Landscape()
    ls.create_landscape()
    ls.create_mask()
    #ls.create_figure()
    
    plt.close("all")
    fig = plt.figure(figsize=(18,16))    
    
    ls.uncover([0, 0])    
    ls.uncover([2, 2])
    ls.uncover([1, 2])
    ls.uncover([3, 5])
    ls.uncover([4, 0])
    ls.uncover([7, 7])
    ls.uncover([7, 5])
    ls.uncover([5, 7])
    ls.uncover([0, 7])
    ls.uncover([7, 0])
    ls.uncover([5, 3])
    ls.uncover([2, 0])
    ls.uncover([3, 7])
    ls.uncover([6, 6])
    ls.uncover([0, 4])
    ls.uncover([5, 5])
    ls.uncover([3, 1])
    ls.uncover([6, 7])

    #ls.set_current_pos([7, 7])
    ls.plot_landscape(fig)
    ls.plot_peak_positions(fig)
    #ls.init_gradient_plot()
    #ls.annotate_numbers()
    #ls.cover([0, 0])
    #ls.plot_landscape()
    #ls.annotate_numbers()
    #ls.calc_gradients()
    #ls.update_gradient_plot()
    ls.init_surrogate_model()
    fig = plt.figure(figsize=(18,16))
    ax = plt.gca()
    ls.plot_surrogate(ax)
    print(ls.current_hint)
    ls.plot_hint()


    # ls.highlight_current_pos()
    # ls.set_current_pos([1, 1])
    # ls.highlight_current_pos()
    # del ls.current_pos_rect
    
    plt.show()
