#!/usr/bin/python3 -B

"""
A collection of miscellaneous camera related calculations.

MIT License

Copyright (c) 2018 Vitali Samurov

Permission is hereby granted, free of charge, to any person obtaining a copy
of this software and associated documentation files (the "Software"), to deal
in the Software without restriction, including without limitation the rights
to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
copies of the Software, and to permit persons to whom the Software is
furnished to do so, subject to the following conditions:

The above copyright notice and this permission notice shall be included in all
copies or substantial portions of the Software.


THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
SOFTWARE.

# Example:
# python3 cameracalc.py -v IMG_16M 1/2.3_INCH 3.8 2.4 100 IMG_UHD4K 1500 Test

"""
import sys                          # built-in module
import math                         # built-in module
import numpy as np                  # pip install numpy
import matplotlib.pyplot as pp      # pip install matplotlib
import matplotlib.lines as ln       # pip install matplotlib
import argparse                     # pip install argparse

################### Configuration section START
PROGRAM_VERSION = '0.51'            # Script version
KELL_FACTOR = 0.8                   # Bandwidth limitation parameter of a sampled image
SENSOR_35MM_DIAGONAL = 43.27        # Diagonal of full-frame (35mm) sensor, mm
LENS_VALUE_AT_FAR = 300             # Lens position value at FAR
OBJECT_DISTANCE_AT_FAR_MM = 2000    # Object distance, corresponding to FAR
LENS_VALUE_AT_NEAR = 750            # Lens position value at NEAR
OBJECT_DISTANCE_AT_NEAR_MM = 100    # Object distance, corresponding to NEAR

IMAGE_FORMAT = {
    'IMG_HD720':    [1280, 720],    # [width, height] # Effective pixels
    'IMG_HD1080':   [1920, 1080],
    'IMG_3M':       [2304, 1296],
    'IMG_4M':       [2592, 1520],
    'IMG_5M':       [2592, 1944],
    'IMG_6M':       [3072, 2160],
    'IMG_8M':       [3264, 2448],
    'IMG_3Kx3K':    [3000, 3000],
    'IMG_10K':      [3648, 2736],
    'IMG_UHD4K':    [3840, 2160],
    'IMG_12M':      [4000, 3000],
    'IMG_16M':      [4608, 3456],
    'IMG_20M':      [5184, 3888],
}

SENSOR_SIZE = {
    '1/3.6_INCH':   [4.0, 3.0],     # [width, height] # Effective size, mm
    '1/3.2_INCH':   [4.54, 3.42],
    '1/3_INCH':     [4.8, 3.6],
    '1/2.9_INCH':   [5.04, 3.77],
    '1/2.7_INCH':   [5.37, 4.29],
    '1/2.5_INCH':   [5.76, 4.29],
    '1/2.4_INCH':   [5.92, 4.57],
    '1/2.3_INCH':   [6.16, 4.62],
    '1/2_INCH':     [6.4, 4.8],
    '1/1.8_INCH':   [7.18, 5.32],
    '2/3_INCH':     [8.8, 6.6],
    '1_INCH':       [12.8, 9.6],
    'M4/3':         [17.3, 13.0],
    'APS-C':        [22.2, 14.8],
    'FULL_FRAME':   [36.0, 24.0],
}
################### Configuration section END

WIDTH_INDX = 0
HEIGHT_INDX = 1

class Configuration(object):
    def __init__(self, res, ssize, flen, fnum, minfd, cr, maxod, capt):
        self.kell_factor = KELL_FACTOR
        self.a35mm_diag = SENSOR_35MM_DIAGONAL
        self.lens_value_far = LENS_VALUE_AT_FAR
        self.object_distance_far_mm = OBJECT_DISTANCE_AT_FAR_MM
        self.lens_value_near = LENS_VALUE_AT_NEAR
        self.object_distance_near_mm = OBJECT_DISTANCE_AT_NEAR_MM
        self.resolution = IMAGE_FORMAT[res]
        self.sensor_size = SENSOR_SIZE[ssize]
        self.eff_mpix = self.resolution[WIDTH_INDX] * self.resolution[HEIGHT_INDX] / 1000000
        self.focal_len = float(flen)
        self.fnumber = float(fnum)
        self.min_focus_distance = int(minfd)
        self.target_crop = cr
        self.crop_resolution = IMAGE_FORMAT[cr]
        self.max_object_distance = int(maxod)
        self.fig_caption = capt

class Calculation(object):
    def __init__(self, cfg):
        self.cfgs = cfg

    def get_35mm_equivalent(self):
        sensor_width = self.cfgs.sensor_size[WIDTH_INDX]
        sensor_height = self.cfgs.sensor_size[HEIGHT_INDX]
        sensor_diag = math.sqrt(sensor_width**2 + sensor_height**2)
        lens_f_length_35mm = self.cfgs.focal_len * self.cfgs.a35mm_diag/sensor_diag
        return lens_f_length_35mm

    def get_sampling_freq_px_per_mm(self):
        sampl_freq = self.cfgs.resolution[WIDTH_INDX] / self.cfgs.sensor_size[WIDTH_INDX]
        return sampl_freq

    def get_pixel_pitch_um(self, sampl_freq):
        return 1000.0 / sampl_freq

    def get_nyquist_limit(self, sampl_freq):
        return 0.5 * self.cfgs.kell_factor * sampl_freq

    def get_circle_of_confusion_mm(self, nyquist_limit):
        return 1.0 / nyquist_limit

    def get_sensor_crop_size(self, crop_factor_h, crop_factor_v):
        crop_width_mm = self.cfgs.sensor_size[WIDTH_INDX] / crop_factor_h
        crop_height_mm = self.cfgs.sensor_size[HEIGHT_INDX] / crop_factor_v
        crop_diag_mm = math.sqrt(crop_width_mm**2 + crop_height_mm**2)
        return (crop_width_mm, crop_height_mm, crop_diag_mm)

    def get_sensor_crop_factor(self):
        hor_crop_factor = \
            self.cfgs.resolution[WIDTH_INDX] / self.cfgs.crop_resolution[WIDTH_INDX]

        ver_crop_factor = \
            self.cfgs.resolution[HEIGHT_INDX] / self.cfgs.crop_resolution[HEIGHT_INDX]

        return (hor_crop_factor, ver_crop_factor)

    def get_35mm_equivalent_crop(self, sensor_diag_cr):
        lens_f_length_35mm_crop = self.cfgs.focal_len * self.cfgs.a35mm_diag / sensor_diag_cr
        return lens_f_length_35mm_crop

    def get_angles_of_view_effective(self):
        hor_aov_eff = \
            np.rad2deg((2 * (math.atan(self.cfgs.sensor_size[WIDTH_INDX] / (2 * self.cfgs.focal_len)))))

        ver_aov_eff = \
            np.rad2deg((2 * (math.atan(self.cfgs.sensor_size[HEIGHT_INDX] / (2 * self.cfgs.focal_len)))))

        sensor_diag = math.sqrt(self.cfgs.sensor_size[WIDTH_INDX]**2 + self.cfgs.sensor_size[HEIGHT_INDX]**2)
        dia_aov_eff = \
            np.rad2deg((2 * (math.atan(sensor_diag / (2 * self.cfgs.focal_len)))))

        return (hor_aov_eff, ver_aov_eff, dia_aov_eff)

    def get_angles_of_view_cropped(self, h_crop_factor, v_crop_factor):
        sensor_width_crop_mm = self.cfgs.sensor_size[WIDTH_INDX] / h_crop_factor
        sensor_height_crop_mm = self.cfgs.sensor_size[HEIGHT_INDX] / v_crop_factor
        sensor_diag_crop_mm = math.sqrt(sensor_width_crop_mm**2 + sensor_height_crop_mm**2)
        hor_aov_cr = \
            np.rad2deg((2 * (math.atan(sensor_width_crop_mm / (2 * self.cfgs.focal_len)))))

        ver_aov_cr = \
            np.rad2deg((2 * (math.atan(sensor_height_crop_mm / (2 * self.cfgs.focal_len)))))

        diag_aov_cr = \
            np.rad2deg((2 * (math.atan(sensor_diag_crop_mm / (2 * self.cfgs.focal_len)))))
        return (hor_aov_cr, ver_aov_cr, diag_aov_cr)

    def get_hyperfocal(self, c_of_c_mm):
        flen = self.cfgs.focal_len
        fnum = self.cfgs.fnumber
        hyp_dist = flen + (flen**2) / (fnum * c_of_c_mm)
        return hyp_dist

    def get_near_dof_at_hyperfocal(self, hyperfocal):
        odof_n_hyp = round((hyperfocal**2) / (hyperfocal * 2))
        return odof_n_hyp

    def get_main_image_distances(self, hyperfocal):
        flen = self.cfgs.focal_len
        id_inf = flen
        id_hyp = 1.0 / (1.0 / flen - 1.0 / hyperfocal)
        id_1_meter = 1.0 / (1.0 / flen - 1.0 / 1000)
        id_macro = 1.0 / (1.0 / flen - 1.0 / self.cfgs.object_distance_near_mm)
        return (id_inf, id_hyp, id_1_meter, id_macro)

    def get_lens_position(self, object_distance):
        flen = self.cfgs.focal_len
        image_distance = 1.0 / (1.0 / flen - 1.0 / object_distance)
        x1 = 1.0 / (1.0 / flen - 1.0 / self.cfgs.object_distance_far_mm)
        y1 = self.cfgs.lens_value_far
        x0 = 1.0 / (1.0 / flen - 1.0 / self.cfgs.object_distance_near_mm)
        y0 = self.cfgs.lens_value_near
        lens_pos = int(0.5 + (y0 + (image_distance - x0)*(y1 - y0) / (x1 - x0)))
        return lens_pos

    def get_optics_values(self, hyperfocal):
        flen = self.cfgs.focal_len
        x1 = 1.0 / (1.0 / flen - 1.0 / self.cfgs.object_distance_far_mm)
        y1 = self.cfgs.lens_value_far
        x0 = 1.0 / (1.0 / flen - 1.0 / self.cfgs.object_distance_near_mm)
        y0 = self.cfgs.lens_value_near
        self.i_d_inf = 1.0 / (1.0 / flen - 1.0 / 65535)
        self.i_d_hyp = 1.0 / (1.0 / flen - 1.0 / hyperfocal)
        self.i_d_200cm = 1.0 / (1.0 / flen - 1.0 / 2000)
        self.i_d_150cm = 1.0 / (1.0 / flen - 1.0 / 1500)
        self.i_d_120cm = 1.0 / (1.0 / flen - 1.0 / 1200)
        self.i_d_100cm = 1.0 / (1.0 / flen - 1.0 / 1000)
        self.i_d_70cm = 1.0 / (1.0 / flen - 1.0 / 700)
        self.i_d_50cm = 1.0 / (1.0 / flen - 1.0 / 500)
        infl = int(0.5 + (y0 + (self.i_d_inf - x0)*(y1 - y0) / (x1 - x0)))
        hypl = int(0.5 + (y0 + (self.i_d_hyp - x0)*(y1 - y0) / (x1 - x0)))
        cm200l = int(0.5 + (y0 + (self.i_d_200cm - x0)*(y1 - y0) / (x1 - x0)))
        cm150l = int(0.5 + (y0 + (self.i_d_150cm - x0)*(y1 - y0) / (x1 - x0)))
        cm120l = int(0.5 + (y0 + (self.i_d_120cm - x0)*(y1 - y0) / (x1 - x0)))
        cm100l = int(0.5 + (y0 + (self.i_d_100cm - x0)*(y1 - y0) / (x1 - x0)))
        cm70l = int(0.5 + (y0 + (self.i_d_70cm - x0)*(y1 - y0) / (x1 - x0)))
        cm50l = int(0.5 + (y0 + (self.i_d_50cm - x0)*(y1 - y0) / (x1 - x0)))
        cm40l, cm20l, cm10l = -1, -1, -1
        self.i_d_10cm, self.i_d_20cm, self.i_d_40cm = -1, -1, -1

        if(self.cfgs.min_focus_distance <= 100):
            self.i_d_10cm = 1.0 / (1.0 / flen - 1.0 / 100)
            cm10l = int(0.5 + (y0 + (self.i_d_10cm - x0)*(y1 - y0) / (x1 - x0)))

        if(self.cfgs.min_focus_distance <= 200):
            self.i_d_20cm = 1.0 / (1.0 / flen - 1.0 / 200)
            cm20l = int(0.5 + (y0 + (self.i_d_20cm - x0)*(y1 - y0) / (x1 - x0)))

        if(self.cfgs.min_focus_distance <= 400):
            self.i_d_40cm = 1.0 / (1.0 / flen - 1.0 / 400)
            cm40l = int(0.5 + (y0 + (self.i_d_40cm - x0)*(y1 - y0) / (x1 - x0)))

        # Calculate DOF arrays
        od = np.array([0])
        id = np.array([0])
        idof_n = np.array([0])          # DOF near
        idof_f = np.array([0])          # DOF far

        for i in range(int(self.cfgs.object_distance_near_mm), int(self.cfgs.max_object_distance)):
            od = np.append(od, i)
            id_cur = 1.0 / (1.0 / flen - 1.0 / i)
            id = np.append(id, id_cur)
            odof_n_cur = int(((hyperfocal * i)/(hyperfocal + i)) + 0.5)
            idof_n_cur = 1.0 / (1.0 / flen - 1.0 / odof_n_cur)
            idof_n = np.append(idof_n, idof_n_cur)
            odof_f_cur = int(((hyperfocal * i)/(hyperfocal - i)) + 0.5)
            idof_f_cur = 1.0 / (1.0 / flen - 1.0 / odof_f_cur)
            idof_f = np.append(idof_f, idof_f_cur)

        od = np.delete(od, 0)
        id = np.delete(id, 0)
        idof_n = np.delete(idof_n, 0)
        idof_f = np.delete(idof_f, 0)
        return (infl,hypl,cm200l,cm150l,cm120l,cm100l,cm70l,cm50l,cm40l,cm20l,cm10l,od,id,idof_n,idof_f)


class Plots(object):
    def __init__(self, cfg, calc, fig_full_w_pixels):
        self.cfgs = cfg
        self.calcs = calc
        self.fig_full_x = fig_full_w_pixels
        self.fig_full_y = self.fig_full_x * cfg.resolution[HEIGHT_INDX] / cfg.resolution[WIDTH_INDX]
        self.fig_crop_x = self.fig_full_x * cfg.crop_resolution[WIDTH_INDX] / cfg.resolution[WIDTH_INDX]
        self.fig_crop_y = self.fig_full_y * cfg.crop_resolution[HEIGHT_INDX] / cfg.resolution[HEIGHT_INDX]
        self.crop_off_x = (self.fig_full_x - self.fig_crop_x) / 2
        self.crop_off_y = (self.fig_full_y - self.fig_crop_y) / 2

    def draw_crops(self):
        pp.figure('Sensor resolutions (%s)' % self.cfgs.fig_caption)
        full_rect = pp.Rectangle((0, 0), self.fig_full_x, self.fig_full_y, edgecolor = 'b', fill = None)
        crop_rect = pp.Rectangle((self.crop_off_x, self.crop_off_y), self.fig_crop_x, self.fig_crop_y, edgecolor = 'r', fill = None)
        pp.gca().add_patch(full_rect)
        pp.gca().add_patch(crop_rect)
        full_x = self.cfgs.resolution[WIDTH_INDX]
        full_y = self.cfgs.resolution[HEIGHT_INDX]
        eff_mp = self.cfgs.eff_mpix
        crop_x = self.cfgs.crop_resolution[WIDTH_INDX]
        crop_y = self.cfgs.crop_resolution[HEIGHT_INDX]
        crop_mp = crop_x * crop_y / 1000000
        pp.text(1, 1, 'Full: %d x %d (%.1f MP)' % (full_x, full_y, round(eff_mp, 1)), fontsize = 'xx-small', color = 'b')
        x = self.fig_crop_x / 3
        y = self.crop_off_y + 1
        pp.text(1, 1, 'Full: %d x %d (%.1f MP)' % (full_x, full_y, round(eff_mp, 1)), fontsize = 'xx-small', color = 'b')
        pp.text(x, y, 'Crop: %d x %d (%.1f MP)' % (crop_x, crop_y, round(crop_mp, 1)), fontsize = 'xx-small', color = 'r')
        pp.axis('scaled')
        pp.axis('off')

    def draw_dof_curves(self, od, id, idofn, idoff, hyper):
        f2 = pp.figure('Depth-of-field curves (%s)' % self.cfgs.fig_caption)
        pp.plot(id, od, label = 'Focus')
        pp.plot(idofn, od, label = 'Far DOF')
        pp.plot(idoff, od, label = 'Near DOF')
        pp.grid(b = True, which = 'both', linestyle = '-')
        pp.xlabel('Image distance, mm')
        pp.ylabel('Object distance, mm')
        nextPosY = 0
        nextPosYstep = 60
        font_size = 'x-small'

        if (self.calcs.i_d_10cm != -1):
            od = 100
            odof_f_10cm = int(((hyper * od)/(hyper - od)) + 0.5)
            line10cm = ln.Line2D([self.calcs.i_d_10cm, self.calcs.i_d_10cm], [0, odof_f_10cm], lw = 1, color = 'cyan')
            pp.gca().add_line(line10cm)
            lens_pos = self.calcs.get_lens_position(od)
            pp.text(self.calcs.i_d_10cm, odof_f_10cm + 5, '10cm LP: %d' % lens_pos, fontsize = font_size, color = 'r')

        if (self.calcs.i_d_20cm != -1):
            od = 200
            odof_f_20cm = int(((hyper * od)/(hyper - od)) + 0.5)
            line20cm = ln.Line2D([self.calcs.i_d_20cm, self.calcs.i_d_20cm], [0, odof_f_20cm], lw = 1, color = 'cyan')
            pp.gca().add_line(line20cm)
            lens_pos = self.calcs.get_lens_position(od)
            pp.text(self.calcs.i_d_20cm, odof_f_20cm + 5, '20cm LP: %d' % lens_pos, fontsize = font_size, color = 'r')

        if (self.calcs.i_d_40cm != -1):
            od = 400
            odof_f_40cm = int(((hyper * od)/(hyper - od)) + 0.5)
            line40cm = ln.Line2D([self.calcs.i_d_40cm, self.calcs.i_d_40cm], [0, odof_f_40cm], lw = 1, color = 'cyan')
            pp.gca().add_line(line40cm)
            lens_pos = self.calcs.get_lens_position(od)
            pp.text(self.calcs.i_d_40cm, odof_f_40cm + 5, '40cm LP: %d' % lens_pos, fontsize = font_size, color = 'r')

        od = 500
        odof_f_50cm = int(((hyper * od)/(hyper - od)) + 0.5)
        line50cm = ln.Line2D([self.calcs.i_d_50cm, self.calcs.i_d_50cm], [0, odof_f_50cm], lw = 1, color = 'cyan')
        pp.gca().add_line(line50cm)
        lens_pos = self.calcs.get_lens_position(od)
        pp.text(self.calcs.i_d_50cm, odof_f_50cm + 5, '50cm LP: %d' % lens_pos, fontsize = font_size, color = 'r')

        od = 700
        odof_f_70cm = int(((hyper * od)/(hyper - od)) + 0.5)
        if (odof_f_70cm > self.cfgs.max_object_distance):
            odof_f_70cm = self.cfgs.max_object_distance - 5
            nextPosY += nextPosYstep

        line70cm = ln.Line2D([self.calcs.i_d_70cm, self.calcs.i_d_70cm], [0, odof_f_70cm - nextPosY], lw = 1, color = 'cyan')
        pp.gca().add_line(line70cm)
        lens_pos = self.calcs.get_lens_position(od)
        pp.text(self.calcs.i_d_70cm, odof_f_70cm + 5 - nextPosY, '70cm LP: %d' % lens_pos, fontsize = font_size, color = 'r')

        od = 1000
        odof_f_100cm = int(((hyper * od)/(hyper - od)) + 0.5)
        if (odof_f_100cm > self.cfgs.max_object_distance):
            odof_f_100cm = self.cfgs.max_object_distance - 5
            nextPosY += nextPosYstep

        line100cm = ln.Line2D([self.calcs.i_d_100cm, self.calcs.i_d_100cm], [0, odof_f_100cm - nextPosY], lw = 1, color = 'cyan')
        pp.gca().add_line(line100cm)
        lens_pos = self.calcs.get_lens_position(od)
        pp.text(self.calcs.i_d_100cm, odof_f_100cm + 5 - nextPosY, '100cm LP: %d' % lens_pos, fontsize = font_size, color = 'r')

        od = 1200
        odof_f_120cm = int(((hyper * od)/(hyper - od)) + 0.5)
        if (odof_f_120cm > self.cfgs.max_object_distance):
            odof_f_120cm = self.cfgs.max_object_distance - 5
            nextPosY += nextPosYstep

        line120cm = ln.Line2D([self.calcs.i_d_120cm, self.calcs.i_d_120cm], [0, odof_f_120cm - nextPosY], lw = 1, color = 'cyan')
        pp.gca().add_line(line120cm)
        lens_pos = self.calcs.get_lens_position(od)
        pp.text(self.calcs.i_d_120cm, odof_f_120cm + 5 - nextPosY, '120cm LP: %d' % lens_pos, fontsize = font_size, color = 'r')

        od = 1500
        if (od < hyper):
            odof_f_150cm = int(((hyper * od)/(hyper - od)) + 0.5)
        else:
            odof_f_150cm = 65536

        if (odof_f_150cm > self.cfgs.max_object_distance):
            odof_f_150cm = self.cfgs.max_object_distance - 5
            nextPosY += nextPosYstep

        line150cm = ln.Line2D([self.calcs.i_d_150cm, self.calcs.i_d_150cm], [0, odof_f_150cm - nextPosY], lw = 1, color = 'cyan')
        pp.gca().add_line(line150cm)
        lens_pos = self.calcs.get_lens_position(od)
        pp.text(self.calcs.i_d_150cm, odof_f_150cm + 5 - nextPosY, '150cm LP: %d' % lens_pos, fontsize = font_size, color = 'r')

        od = 2000
        if (od < hyper):
            odof_f_200cm = int(((hyper * od)/(hyper - od)) + 0.5)
        else:
            odof_f_200cm = 65536

        if (odof_f_200cm > self.cfgs.max_object_distance):
            odof_f_200cm = self.cfgs.max_object_distance - 5
            nextPosY += nextPosYstep

        line200cm = ln.Line2D([self.calcs.i_d_200cm, self.calcs.i_d_200cm], [0, odof_f_200cm - nextPosY], lw = 1, color = 'cyan')
        pp.gca().add_line(line200cm)
        lens_pos = self.calcs.get_lens_position(od)
        pp.text(self.calcs.i_d_200cm, odof_f_200cm + 5 - nextPosY, '200cm LP: %d' % lens_pos, fontsize = font_size, color = 'r')

        od = hyper
        odof_f_hyp = self.cfgs.max_object_distance - 5
        nextPosY += nextPosYstep
        lineHyper = ln.Line2D([self.calcs.i_d_hyp, self.calcs.i_d_hyp], [0, odof_f_hyp - nextPosY], lw = 1, color = 'cyan')
        pp.gca().add_line(lineHyper)
        lens_pos = self.calcs.get_lens_position(od)
        pp.text(self.calcs.i_d_hyp, odof_f_hyp + 5 - nextPosY, 'HYPER LP: %d' % lens_pos, fontsize = font_size, color = 'r')

        od = 65535
        odof_f_inf = self.cfgs.max_object_distance - 5
        nextPosY += nextPosYstep
        lineInf = ln.Line2D([self.calcs.i_d_inf, self.calcs.i_d_inf], [0, odof_f_inf - nextPosY], lw = 1, color = 'cyan')
        pp.gca().add_line(lineInf)
        lens_pos = self.calcs.get_lens_position(od)
        pp.text(self.calcs.i_d_inf, odof_f_inf + 5 - nextPosY, 'INF LP: %d' % lens_pos, fontsize = font_size, color = 'r')

        pp.text(self.calcs.i_d_inf, 70, 'Ver: %s' % PROGRAM_VERSION, fontsize = 'x-small', color = 'black')
        pp.legend()

    def show_figures(self):
        pp.show()

def msg(name = None):
    out_str = '\nlist of image formats (pixels):\n'
    for x in IMAGE_FORMAT:
        out_str += '  ' + x + ': ' + str(IMAGE_FORMAT[x]) + '\n'

    out_str += '\nlist of sensor sizes (mm):\n'
    for x in SENSOR_SIZE:
        out_str += '  ' + x + ': ' + str(SENSOR_SIZE[x]) + '\n'

    out_str += '\ncommand line parameters:'
    out_str += '\n  cameracalc.py [-h] [-v] Res Size FLen Fnum MinFDist Crop MaxObDist Caption\n'
    return out_str


def main():
    print('Camera Calculator, ver %s\n' % PROGRAM_VERSION)
    parser = argparse.ArgumentParser(usage = msg())
    parser.add_argument('Res',
        help = 'effective resolution of the sensor, (e.g. IMG_12M)')

    parser.add_argument('Size',
        help = 'size of sensor\'s effective area, mm (e.g. 1/2.3_INCH)')

    parser.add_argument('FLen',
        help = 'lens focal length, mm')

    parser.add_argument('FNum',
        help = 'lens aperture, F-number')

    parser.add_argument('MinFDist',
        help = 'minimum focusing distance, lens is capable to focus, mm')

    parser.add_argument('Crop',
        help = 'target crop from native sensor resolution, (e.g. IMG_UHD4K)')

    parser.add_argument('MaxObDist',
        help = 'maximum object distance for the Lens DOF figure, mm')

    parser.add_argument('Caption',
        help = 'figure caption string')

    parser.add_argument('-v', '--verbose',
        help = 'increase output verbosity',
        action = 'store_true')

    args = parser.parse_args()

    if (int(args.MinFDist) > 500):
        print('Calculator is limited to minimum focusing distance <= 500 mm!')
        sys.exit()

    if args.verbose:
        verbosity_flag = True
    else:
        verbosity_flag = False

    # Create configuration object
    config = Configuration(
        args.Res,
        args.Size,
        args.FLen,
        args.FNum,
        args.MinFDist,
        args.Crop,
        args.MaxObDist,
        args.Caption)

    if verbosity_flag:
        print('--- Parameters:')
        print('Resolution:', args.Res, config.resolution)
        print('Sensor size:', args.Size, config.sensor_size)
        print('Focal length:', config.focal_len)
        print('F-number:', config.fnumber)
        print('Min focusing distance:', config.min_focus_distance)
        print('Target crop:', args.Crop, config.crop_resolution)
        print('Max object distance:', config.max_object_distance)
        print('Figures caption:', config.fig_caption)

    # Create calculation object
    calc = Calculation(config)
    sampl_freq_px_per_mm = calc.get_sampling_freq_px_per_mm()
    pixel_pitch_um = calc.get_pixel_pitch_um(sampl_freq_px_per_mm)
    nyquist_limit_lp_per_mm = calc.get_nyquist_limit(sampl_freq_px_per_mm)
    focal_35mm = calc.get_35mm_equivalent()
    c_o_c_mm = calc.get_circle_of_confusion_mm(nyquist_limit_lp_per_mm)
    (hor_crop_factor, ver_crop_factor) = calc.get_sensor_crop_factor()
    (cr_h_mm, cr_v_mm, cr_d_mm) = calc.get_sensor_crop_size(hor_crop_factor, ver_crop_factor)
    focal_35mm_crop = calc.get_35mm_equivalent_crop(cr_d_mm)
    (h_aov_eff, v_aov_eff, d_aov_eff) = calc.get_angles_of_view_effective()
    (h_aov_cr, v_aov_cr, d_aov_cr) = calc.get_angles_of_view_cropped(hor_crop_factor, ver_crop_factor)
    hyperfocal = calc.get_hyperfocal(c_o_c_mm)
    near_dof_hyp = calc.get_near_dof_at_hyperfocal(hyperfocal)
    (i_d_inf, i_d_hyp, i_d_1m, i_d_macro) = calc.get_main_image_distances(hyperfocal)
    (linf,lhyp,l200cm,l150cm,l120cm,l100cm,l70cm,l50cm,l40cm,l20cm,l10cm,o_d,i_d,idof_n,idof_f) = calc.get_optics_values(hyperfocal)

    print('\n--- Calculations:')
    print('Focal lenght 35 mm equivalent, mm:', round(focal_35mm, 1))
    print('Sensor effective pixels: %d x %d (MPix: %.2f)' % \
        (config.resolution[WIDTH_INDX], \
        config.resolution[HEIGHT_INDX], \
        round(config.eff_mpix, 2)))

    print('Pixel pitch, um: %.2f' % round(pixel_pitch_um, 2))
    print('Sampling frequency, px/mm: %.2f' % round(sampl_freq_px_per_mm, 2))
    print('Sensor Nyquist limit, lp/mm: %.2f (kell factor: %.1f)' % \
        (round(nyquist_limit_lp_per_mm, 2), config.kell_factor))

    print('Circle of confusion, mm: %.4f' % round(c_o_c_mm, 4))
    print('%s horizontal crop-factor: %.2f' % \
        (args.Crop, round(hor_crop_factor, 2)))

    print('%s vertical crop-factor: %.2f' % \
        (args.Crop, round(ver_crop_factor, 2)))

    print('%s crop width, mm: %.2f' % \
        (args.Crop, round(cr_h_mm, 2)))

    print('%s crop height, mm: %.2f' % \
        (args.Crop, round(cr_v_mm, 2)))

    print('%s crop diagonal, mm: %.2f' % \
        (args.Crop, round(cr_d_mm, 2)))

    print('Horizontal Angle-Of-View (effective), deg: %.1f' % round(h_aov_eff, 1))
    print('Vertical Angle-Of-View (effective), deg: %.1f' % round(v_aov_eff, 1))
    print('Diagonal Angle-Of-View (effective), deg: %.1f' % round(d_aov_eff, 1))
    print('Focal lenght 35 mm equivalent cropped, mm: %.1f' % round(focal_35mm_crop, 1))
    print('Horizontal Angle-Of-View (cropped), deg: %.1f' % round(h_aov_cr, 1))
    print('Vertical Angle-Of-View (cropped), deg: %.1f' % round(v_aov_cr, 1))
    print('Diagonal Angle-Of-View (cropped), deg: %.1f' % round(d_aov_cr, 1))
    print('Hyperfocal object distance, mm: %d' % int(hyperfocal + 0.5))
    print('Near Depth-Of-Field at hyperfocal distance, mm: %d' % int(near_dof_hyp + 0.5))
    print('Lens value at FAR position: %d' % config.lens_value_far)
    print('FAR position object distance, mm: %d' % config.object_distance_far_mm)
    print('Lens value at NEAR position: %d' % config.lens_value_near)
    print('NEAR position object distance, mm: %d' % config.object_distance_near_mm)
    print('Image distance at INFINITY, mm: %.3f' % round(i_d_inf, 3))
    print('Image distance at HYPERFOCAL, mm: %.3f' % round(i_d_hyp, 3))
    print('Image distance at 100cm, mm: %.3f' % round(i_d_1m, 3))
    print('Image distance at MACRO, mm: %.3f' % round(i_d_macro, 3))
    print('Lens value at INFINITY: %.d' % linf)
    print('Lens value at HYPERFOCAL: %.d' % lhyp)
    print('Lens value at 200cm: %.d' % l200cm)
    print('Lens value at 150cm: %.d' % l150cm)
    print('Lens value at 120cm: %.d' % l120cm)
    print('Lens value at 100cm: %.d' % l100cm)
    print('Lens value at 70cm: %.d' % l70cm)
    print('Lens value at 50cm: %.d' % l50cm)
    print('Lens value at 40cm: %.d' % l40cm)
    print('Lens value at 20cm: %.d' % l20cm)
    print('Lens value at 10cm: %.d' % l10cm)

    # Create plot object
    figures = Plots(config, calc, 200)

    figures.draw_crops()
    figures.draw_dof_curves(o_d, i_d, idof_n, idof_f, hyperfocal)
    figures.show_figures()
    print('OK')

if __name__ == '__main__':
    main()
