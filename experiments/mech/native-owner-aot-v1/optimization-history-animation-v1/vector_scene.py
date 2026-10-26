"""A shared vector scene for SVG export and supersampled video frames."""
from __future__ import annotations

from pathlib import Path

from matplotlib.backends.backend_agg import FigureCanvasAgg
from matplotlib.figure import Figure
from matplotlib.font_manager import FontProperties
from matplotlib.lines import Line2D
from matplotlib.patches import Ellipse, FancyBboxPatch
from matplotlib.transforms import Bbox, TransformedBbox
import numpy as np
from PIL import Image


class VectorScene:
    def __init__(self, width: int, height: int, scale: int = 2):
        self.width, self.height, self.scale = width, height, scale
        self.fig = Figure(figsize=(width / 100, height / 100), dpi=100 * scale, facecolor="white")
        self.canvas = FigureCanvasAgg(self.fig)
        self.axes = self.fig.add_axes([0, 0, 1, 1], zorder=10)
        self.axes.set(xlim=(0, width), ylim=(height, 0))
        self.axes.set_axis_off()
        self.dynamic = False
        self.artists = []
        self.background = None
        self.layer = 0
        self.base_layer = 0

    def add(self, artist):
        self.layer += 1
        artist.set_zorder(self.layer)
        artist.set_animated(self.dynamic)
        if self.dynamic:
            self.artists.append(artist)
        return artist

    def line(self, points, fill, width=1, dashes=None, clip=None, gid=None):
        if len(points) == 4 and not isinstance(points[0], (tuple, list, np.ndarray)):
            points = [(points[0], points[1]), (points[2], points[3])]
        x, y = zip(*points)
        artist = Line2D(x, y, color=fill, linewidth=width * .72,
                        antialiased=True, solid_capstyle="round", solid_joinstyle="round",
                        dash_capstyle="round", gid=gid)
        if dashes is not None:
            artist.set_linestyle((0, [value * .72 for value in dashes]))
        self.axes.add_line(artist)
        if clip is not None:
            artist.set_clip_box(TransformedBbox(Bbox.from_extents(*clip), self.axes.transData))
        return self.add(artist)

    def ellipse(self, bounds, fill, outline=None, width=1, gid=None):
        left, top, right, bottom = bounds
        artist = Ellipse(((left + right) / 2, (top + bottom) / 2), right - left, bottom - top,
                         facecolor=fill, edgecolor=outline or "none", linewidth=width * .72,
                         antialiased=True, gid=gid)
        self.axes.add_patch(artist)
        return self.add(artist)

    def rounded_rectangle(self, bounds, radius, fill, outline, width=1):
        left, top, right, bottom = bounds
        artist = FancyBboxPatch((left, top), right - left, bottom - top,
                               boxstyle=f"round,pad=0,rounding_size={radius}",
                               facecolor=fill, edgecolor=outline, linewidth=width * .72,
                               antialiased=True)
        self.axes.add_patch(artist)
        return self.add(artist)

    def text(self, xy, value, size, color, bold, anchor, font_path):
        properties = FontProperties(fname=str(font_path), size=size * .72)
        artist = self.axes.text(*xy, value, color=color, fontproperties=properties,
                               horizontalalignment="right" if anchor.startswith("r") else "left",
                               verticalalignment="top", antialiased=True)
        return self.add(artist)

    @staticmethod
    def textlength(value, font):
        return font.getlength(value)

    def freeze(self):
        self.canvas.draw()
        self.background = self.canvas.copy_from_bbox(self.fig.bbox)
        self.base_layer = self.layer
        self.dynamic = True

    def begin(self):
        for artist in self.artists:
            artist.remove()
        self.artists.clear()
        self.layer = self.base_layer

    def image(self):
        self.canvas.restore_region(self.background)
        for artist in self.artists:
            self.axes.draw_artist(artist)
        pixels = np.asarray(self.canvas.buffer_rgba())[:, :, :3].copy()
        image = Image.fromarray(pixels)
        return image.resize((self.width, self.height), Image.Resampling.LANCZOS)

    def svg(self, path: Path, metadata, height=None):
        for artist in self.artists:
            artist.set_animated(False)
        try:
            bounds = None if height is None else Bbox.from_extents(
                0, (self.height - height) / 100, self.width / 100, self.height / 100)
            self.fig.savefig(path, format="svg", metadata=metadata, bbox_inches=bounds)
        finally:
            for artist in self.artists:
                artist.set_animated(True)
