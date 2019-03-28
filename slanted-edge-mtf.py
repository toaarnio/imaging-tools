#!/usr/bin/python3 -B

import os                        # built-in module
import sys                       # built-in module
import time                      # built-in module
import json                      # built-in module
import pprint                    # built-in module
import cv2                       # pip install opencv-python
import imgio                     # pip install imgio
import numpy as np               # pip install numpy
import scipy.signal              # pip install scipy
import scipy.ndimage.morphology  # pip install scipy
import matplotlib.pyplot as pp   # pip install matplotlib
import matplotlib.widgets        # pip install matplotlib
import argv                      # local import


DEBUG = False

EDGE_WIDTH = 99
MIN_ROI_WIDTH = EDGE_WIDTH
MIN_ROI_HEIGHT = EDGE_WIDTH
MIN_ROI_SIZE = (MIN_ROI_HEIGHT, MIN_ROI_WIDTH)


DEFAULT_CONFIG = {
    "roi-center": [],  # [miny, maxy, minx, maxx]
    "roi-top-left": [],
    "roi-top-right": [],
    "roi-bottom-left": [],
    "roi-bottom-right": [],
    "edge-width": EDGE_WIDTH,
    "edge-min-angle": 78,
    "edge-max-angle": 88,
}


class MTFResults(object):

    def __init__(self, corner):
        self.corner = corner         # center|top-left|...
        self.esf = None              # Edge Spread Function
        self.lsf = None              # Line Spread Function
        self.lsfs = None             # smoothed LSF
        self.mtf = None              # FFT of raw LSF
        self.mtfs = None             # FFT of smoothed LSF
        self.mtf50 = None            # MTF50 in cycles/pixel
        self.mtf20 = None            # MTF20 in cycles/pixel
        self.edge_straight = None    # straightened edge region
        self.edge_region = None      # edge region source pixels
        self.edge_mask = None        # edge region binary mask
        self.edge_coords = None      # edge y-coords & x-coords
        self.edge_coeffs = None      # edge coeffs: y = ax + b
        self.edge_angle = None       # edge angle in degrees
        self.edge_yspan = None       # edge length in pixels
        self.success = False         # True|False

    def report(self):
        if self.success:
            print("-" * 60)
            print("Results for {} region:".format(self.corner))
            print("  Edge angle: {:.1f} degrees".format(self.edge_angle))
            print("  Edge height: {} pixels".format(self.edge_yspan))
            print("  MTF50: {:.3f} cycles/pixel = {:.1f} pixels/cycle".format(self.mtf50, 1.0 / self.mtf50))
            print("  MTF20: {:.3f} cycles/pixel = {:.1f} pixels/cycle".format(self.mtf20, 1.0 / self.mtf20))
        else:
            print("-" * 60)
            print("MTF calculation for {} region failed.".format(self.corner))


def mtf(config, results, filename):
    print("Configuration:")
    pprint.pprint(config, indent=2)
    min_angle = config["edge-min-angle"]
    max_angle = config["edge-max-angle"]
    edge_width = config["edge-width"]

    # read source image, convert to grayscale, normalize [black, white] = [0, 1]
    basename = os.path.basename(filename)
    image = imread(filename)
    imgh, imgw = image.shape

    # plot source image - selected regions will be overlaid later
    fig, axis = pp.subplots(num="image", nrows=1, ncols=1, squeeze=True, figsize=(17,9), dpi=110)
    fig.canvas.set_window_title("slanted-edge-mtf: Selected regions")
    axis.imshow(image)
    pp.title(basename)
    pp.show(block=False)

    for idx, res in enumerate(results):

        # extract region of interest
        prefix = "{} edge detection failed".format(res.corner)  # prepended to all error messages
        key = "roi-{}".format(res.corner)
        roi = np.array(config[key])
        if roi is None or len(roi) == 0:
            print("{} region not specified, skipping...".format(res.corner))
            continue
        roi_valid = np.all((roi >= 0) & (roi < [imgh, imgh, imgw, imgw]))
        enforce(roi_valid, "{0}: Selected region {1} is exceeding image boundaries ({3} x {2})."
                .format(prefix, roi, *image.shape))
        region = image[roi[0]:roi[1], roi[2]:roi[3]]
        roih, roiw = region.shape
        roi_valid = np.all(region.shape > MIN_ROI_SIZE)
        enforce(roi_valid, "{0}: Selected region must be at least {2} x {1} pixels; was {4} x {3}."
                .format(prefix, *MIN_ROI_SIZE, *region.shape))
        axis.add_patch(pp.Rectangle((roi[2], roi[0]), roiw, roih, edgecolor="red", facecolor="none"))

        # detect edge pixels
        otsu_map = otsu(region)                               # generate binary mask: 0=black, 1=white
        otsu_filt = morpho(otsu_map)                          # filter out small non-contiguous regions
        otsu_edges = canny(otsu_filt)                         # detect edges; there should be only one
        edge_coords = np.nonzero(otsu_edges)                  # get (x, y) coordinates of edge pixels
        edge_y_span = len(np.unique(edge_coords[0]))          # get number of scanlines intersected
        plot_edge([region, otsu_map, otsu_filt, otsu_edges])  # plot edge images if in debug mode
        enforce(edge_y_span > MIN_ROI_HEIGHT, "{}: Edge must have at least {} scanlines; had {}."
                .format(prefix, MIN_ROI_HEIGHT, edge_y_span))

        # fit a straight line through the detected edge
        edge_coeffs = np.polyfit(*reversed(edge_coords), deg=1)
        plot_edge([region, otsu_map, otsu_filt, otsu_edges], edge_coeffs, "{}".format(res.corner))
        edge_angle = np.abs(np.rad2deg(np.arctan(edge_coeffs[0])))
        enforce(min_angle < edge_angle < max_angle, "{}: Edge angle must be [{}, {}] degrees; was {:.1f}."
                .format(prefix, min_angle, max_angle, edge_angle))
        prompt("Review the {} edge plots, then press Enter to continue.".format(res.corner.lower()))

        # extract EDGE_WIDTH pixels from each scanline, centered on the detected edge
        px = np.poly1d(edge_coeffs, variable="x")  # y = ax + b  <==> x = (y - b) / a
        py = np.poly1d([1.0 / px.c[0], -px.c[1] / px.c[0]], variable="y")
        xp = np.polyval(py, np.arange(0, roih))  # ideal edge position on each scanline
        xpi = xp.round().astype(np.int32)
        xfirst = xpi - edge_width // 2
        xlast = xpi + edge_width // 2
        valid_rows = (xfirst >= 0) & (xlast < roiw)
        xfirst = xfirst[valid_rows]
        xlast = xlast[valid_rows]
        enforce(np.sum(valid_rows) >= MIN_ROI_HEIGHT, "{}: Edge must have at least {} valid scanlines; had {}."
                .format(prefix, MIN_ROI_HEIGHT, np.sum(valid_rows)))
        xmin = np.min(xfirst)
        xmax = np.max(xlast)
        xfirst -= xmin
        xlast -= xmin
        crop = region[valid_rows, xmin:xmax+1]
        roih, roiw = crop.shape
        edge_straight = np.zeros((roih, edge_width), dtype=np.float32)
        edge_straight[:] = [crop[y, xfirst[y]:xlast[y]+1] for y in range(roih)]

        # store results
        res.edge_straight = edge_straight
        res.edge_region = region
        res.edge_mask = otsu_filt
        res.edge_coeffs = edge_coeffs
        res.edge_angle = edge_angle
        res.edge_yspan = roih

    pp.close("edges")

    for idx, res in enumerate(results):
        if res.edge_straight is not None:
            # compute Edge Spread Function (ESF), Line Spread Function (LSF), and filtered LSF
            edge = res.edge_straight
            res.esf = esf = np.mean(edge, axis=0)
            res.lsf = lsf = np.gradient(esf)
            res.lsfs = lsfs = scipy.signal.wiener(lsf, 7)
            plot_curves([edge], [esf, lsf, lsfs], ["Edge Profile", "LSF", "Filtered LSF"], res.corner)
            prompt("Review the {} ESF & LSF curves, then press Enter to continue.".format(res.corner))
            # compute filtered & unfiltered MTF
            res.mtf = mtf = fft(lsf)
            res.mtfs = mtfs = fft(lsfs)
            # compute MTF50 & MTF20 from filtered MTF
            x_mtf = np.linspace(0, 1, len(mtf))
            res.mtf50 = mtf50 = np.interp(0.5, mtfs[::-1], x_mtf[::-1])
            res.mtf20 = mtf20 = np.interp(0.2, mtfs[::-1], x_mtf[::-1])
            res.success = True

    pp.close("curves")

    for idx, res in enumerate(results):
        if res.success:
            label = "{}: MTF50 = {:.3f} cycles/pixel = {:.1f} pixels/cycle".format(res.corner, res.mtf50, 1.0 / res.mtf50)
            plot_mtf(res.mtfs, res.mtf50, res.mtf20, label=label, color=pp.cm.cool(idx / 4))
            if DEBUG:  # plot the unfiltered MTF only in debug mode
                plot_mtf(res.mtf, res.mtf50, res.mtf20, color=pp.cm.cool(idx / 4), linestyle=":", linewidth=0.5)

    roi_filename = "MTF-{}-ROI.png".format(basename)
    lsf_filename = "MTF-{}-LSF.png".format(basename)
    mtf_filename = "MTF-{}-MTF.png".format(basename)
    pp.title("MTF - {}".format(basename))
    pp.show(block=False)
    pp.figure("mtf")
    pp.savefig(mtf_filename)
    pp.figure("image")
    pp.savefig(roi_filename)
    success = np.all([res.success for res in results])
    return success


def imread(filename, verbose=True):
    image, maxval = imgio.imread(filename, verbose=verbose)
    image = np.dot(image, [0.2125, 0.7154, 0.0721])  # RGB => Luminance
    image = image / maxval
    image = normalize(image)
    return image


def normalize(image):
    black = np.percentile(image, 0.1)
    white = np.percentile(image, 99.9)
    image = (image - black) / (white - black)
    image = np.clip(image, 0, 1)
    return image


def otsu(image):
    # Otsu's binary thresholding
    image = cv2.GaussianBlur(image, (5, 5), 0)  # simple noise removal
    image = (image * 255).astype(np.uint8)      # [0, 1] => [0, 255]
    otsu_thr, otsu_map = cv2.threshold(image, 0, 255, cv2.THRESH_OTSU)
    return otsu_map


def morpho(mask):
    # morphological filtering of binary mask: 3 x (erosion + dilation)
    structure = np.ones((3,3))  # 8-connected structure
    mask = scipy.ndimage.morphology.binary_opening(mask, structure, iterations=3)
    return mask


def canny(image):
    # Canny edge detection
    image = (image * 255).astype(np.uint8)  # [0, 1] => [0, 255]
    edge_map = cv2.Canny(image, image.min(), image.max(), apertureSize=3, L2gradient=True)
    return edge_map


def fft(lsf):
    # FFT of line spread function
    fft = np.fft.fft(lsf, 1024)  # even 256 would be enough
    fft = fft[:len(fft) // 2]    # drop duplicate half
    fft = np.abs(fft)            # |a + bi| = sqrt(a² + b²)
    fft = fft / fft.max()        # normalize to [0, 1]
    return fft


def plot_mtf(mtf, mtf50, mtf20, **kwargs):
    fig = pp.figure(num="mtf", figsize=(17,9), dpi=110)
    fig.canvas.set_window_title("slanted-edge-mtf: MTF curves")
    pp.grid(linestyle=":")
    pp.xlim([0, 0.75])
    pp.ylim([0, 1])
    pp.xticks(np.arange(0, 0.76, 0.05))
    pp.yticks(np.arange(0, 1.01, 0.05))
    pp.plot(np.linspace(0, 1, len(mtf)), mtf, **kwargs)
    pp.axvline(x=0.5, linestyle=":", linewidth=0.1, color="red")
    pp.axhline(y=0.5, linestyle=":", linewidth=0.1, color="red")
    pp.text(0.505, 0.75, "Nyquist limit", color="red", rotation="vertical")
    pp.text(0.650, 0.51, "MTF50", color="red")
    kwargs["linestyle"] = "--"
    pp.xlabel("cycles/pixel")
    pp.ylabel("MTF")
    pp.legend()


def plot_curves(images, curves, titles, suptitle):
    if DEBUG:
        ncols = len(curves) + len(images)
        fig, axes = pp.subplots(num="curves", nrows=1, ncols=ncols, squeeze=False, clear=True, figsize=(17,9), dpi=110)
        fig.canvas.set_window_title("slanted-edge-mtf: {} ESF & LSF curves".format(suptitle))
        axes = axes.flatten()
        for i, img in enumerate(images):
            axes[i].imshow(img)
            axes[i].axvline(img.shape[1] / 2, color="red", linewidth=0.7)
            axes[i].set_title(suptitle)
        axes = axes[len(images):]
        for ax, curve, title in zip(axes, curves, titles):
            ax.grid(which="both", linestyle=":")
            ax.plot(curve * 255)
            ax.axvline(img.shape[1] / 2, color="red", linewidth=0.7)
            ax.set_title(title)
            ax.set_xlabel("pixel")
            ax.set_ylabel("DN")
        pp.tight_layout()
        pp.show(block=False)


def plot_edge(images, edge_coeffs=None, suptitle=None):
    # plots the given list of images on separate subplots, then optionally overlays each
    # subplot with a red line representing the given linear edge equation (y = ax + b)
    if DEBUG:
        ncols = len(images)
        roih, roiw = images[0].shape
        fig, axes = pp.subplots(num="edges", nrows=1, ncols=ncols, sharey=True, squeeze=False, clear=True, figsize=(17,9), dpi=110)
        fig.canvas.set_window_title("slanted-edge-mtf: {} edge detection".format(suptitle))
        axes = np.array(fig.axes)
        axes = axes.flatten()
        for ax, img in zip(axes, images):
            ax.imshow(img, cmap="gray")
            ax.xaxis.tick_top()
            if edge_coeffs is not None:
                p = np.poly1d(edge_coeffs)
                xp = np.linspace(0, roiw, roiw * 4)
                yp = p(xp)
                inside = (0 <= yp) & (yp < roih)
                xp_roi = xp[inside]
                yp_roi = yp[inside]
                ax.plot(xp_roi, yp_roi, color="red", scalex=False, scaley=False)
        pp.tight_layout()
        pp.show(block=False)


def prompt(message):
    if DEBUG:
        input(message)


def enforce(expression, message_if_false):
    if not expression:
        print(message_if_false)
        prompt("Processing failed. Press Enter to quit...")
        sys.exit(1)


class ROI_selector(object):

    def __init__(self, filename):
        self.image = imread(filename, verbose=False)

    def run(self, corner):
        self.fig, self.ax = pp.subplots(num="selector", figsize=(17,9), dpi=110)
        self.fig.canvas.set_window_title("slanted-edge-mtf: Edge Region Selector")
        self.ax.imshow(self.image, cmap="gray")
        rs = matplotlib.widgets.RectangleSelector(self.ax,
                                                  self.box_select_callback,
                                                  drawtype="box",
                                                  useblit=True,
                                                  button=[1],
                                                  minspanx=MIN_ROI_WIDTH,
                                                  minspany=MIN_ROI_HEIGHT,
                                                  spancoords="data",
                                                  interactive=True)
        pp.connect("key_press_event", self.event_exit_callback)
        pp.title("Select {} edge region, then press Enter".format(corner.upper()))
        pp.show(block=True)
        return list(self.roi)

    def box_select_callback(self, eclick, erelease):
        x1, y1 = eclick.xdata, eclick.ydata
        x2, y2 = erelease.xdata, erelease.ydata
        self.roi = np.array([y1, y2, x1, x2]).round().astype(np.uint32)

    def event_exit_callback(self, event):
        if event.key in ["enter", "esc"]:
            pp.close("selector")


def load_json(filename):
    with open(filename, "r") as f:
        config = json.load(f)
    return config


def save_json(filename, config):
    with open(filename, "w") as f:
        config_str = pprint.pformat(config, indent=2, width=120)
        config_str = config_str.replace('\'', '"')  # python dict => json
        f.write(config_str)


def load_config(json_file):
    if json_file is not None:
        enforce(os.path.exists(json_file), "Config file {} does not exist.".format(json_file))
        print("Loading configuration from {}.".format(json_file))
        config = load_json(json_file)
    else:
        print("JSON config file not specified (see --help), reverting to interactive mode.")
        config = DEFAULT_CONFIG
    return config


def save_config(json_file, config):
    if json_file is not None:
        print("Saving current config to {}.".format(json_file))
        save_json(json_file, config)


def main():
    global DEBUG
    DEBUG = argv.exists("--debug")
    quiet = argv.exists("--quiet")
    json_in = argv.stringval("--load", default=None)
    json_out = argv.stringval("--save", default=None)
    corners = ["center", "top-left", "top-right", "bottom-left", "bottom-right"]
    roi = argv.stringval("--roi", default="center", accepted=corners+["all"])
    showHelp = argv.exists("--help")
    argv.exitIfAnyUnparsedOptions()
    if showHelp or len(sys.argv) < 2:
        print("Usage: slanted-edge-mtf.py [options] image.{ppm|png|jpg}")
        print()
        print("  options:")
        print("    --load config.json              load configuration from JSON file")
        print("    --save config.json              save current config to JSON file")
        print("    --roi all|center|top-left|...   region to analyze; default = center")
        print("    --quiet                         silent mode, do not show any graphs")
        print("    --debug                         plot extra graphs for diagnostics")
        print("    --help                          show this help message")
        print()
        print("  interactive mode:")
        print("    mouse left + move               select region containing a slanted edge")
        print("    enter/esc                       confirm selected region, start processing")
        print()
        sys.exit(-1)

    filename = sys.argv[1]
    enforce(os.path.exists(filename), "Image file {} does not exist.".format(filename))

    config = load_config(json_in)

    selected_rois = corners if roi == "all" else [roi]
    ignored_rois = set(corners) - set(selected_rois)
    for corner in ignored_rois:
        key = "roi-{}".format(corner)  # 'top-left' => 'roi-top-left'
        config[key] = []

    if json_in is None:
        selector = ROI_selector(filename)
        for roi_name in selected_rois:
            key = "roi-{}".format(roi_name)  # 'top-left' => 'roi-top-left'
            config[key] = selector.run(roi_name)

    print("=" * 40, os.path.basename(filename), "=" * 40)
    results = [MTFResults(roi_name) for roi_name in selected_rois]
    success = mtf(config, results, filename)
    print("Success." if success else "Failed.")
    for res in results:
        res.report()

    if DEBUG or not quiet:
        input("Press Enter to quit...")

    pp.close("all")

    save_config(json_out, config)

    sys.exit(0 if success else 1)


if __name__ == "__main__":
    main()
