# pylint: disable=too-many-lines disable=invalid-name disable=missing-class-docstring

"""
A collection of miscellaneous camera related calculations.

MIT License

Copyright (c) 2018 Vitali Samurov
https://github.com/vitasam

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

- Example:
python cameracalc.py -r 16M -s 1/2.3 -l 3.8 -a 2.4 -c UHD4K -f 300 -n 750 -m 100 -i 2500
"""
import sys
import math
import argparse
from dataclasses import dataclass, field
import numpy as np
import matplotlib.pyplot as plt
import matplotlib.lines as lns


@dataclass
class CameraCalcData:
    """Data class to store all camera related parameters and information."""

    # pylint: disable=too-many-instance-attributes disable=missing-function-docstring
    program_version: str = '1.0'
    kell_factor: float = 0.8  # Bandwidth sampling limit
    sensor_35mm_diagonal_mm: float = 43.27
    idx_width = 0
    idx_height = 1
    figure_width_px = 200
    big_object_distance_mm = 65536

    resolutions: list = field(
        default_factory=lambda: [
            'HD720',
            'HD1080',
            '3M',
            '4M',
            '5M',
            '6M',
            '8M',
            'UHD4K',
            '12M',
            '16M',
            '20M',
            '48M',
        ]
    )

    diagonal_names: list = field(
        default_factory=lambda: [
            '1/3.6',
            '1/3.2',
            '1/3',
            '1/2.9',
            '1/2.7',
            '1/2.5',
            '1/2.4',
            '1/2.3',
            '1/2',
            '1/1.8',
            '2/3',
            '1',
            'M4/3',
            'APS-C',
            'FULL',
        ]
    )

    effective_pixels: list = field(
        # (width, height)
        default_factory=lambda: [
            (1280, 720),
            (1920, 1080),
            (2304, 1296),
            (2592, 1520),
            (2592, 1944),
            (3072, 2160),
            (3264, 2448),
            (3840, 2160),
            (4000, 3000),
            (4608, 3456),
            (5184, 3888),
            (8064, 6048),
        ]
    )

    effective_sizes: list = field(
        # (width, height)
        default_factory=lambda: [
            (4.0, 3.0),
            (4.54, 3.42),
            (4.8, 3.6),
            (5.04, 3.77),
            (5.37, 4.29),
            (5.76, 4.29),
            (5.92, 4.57),
            (6.16, 4.62),
            (6.4, 4.8),
            (7.18, 5.32),
            (8.8, 6.6),
            (12.8, 9.6),
            (17.3, 13.0),
            (22.2, 14.8),
            (36.0, 24.0),
        ]
    )

    def __post_init__(self):
        self.image_formats = dict(
            map(lambda i, j: (i, j), self.resolutions, self.effective_pixels)
        )

        self.sensor_sizes = dict(
            map(lambda i, j: (i, j), self.diagonal_names, self.effective_sizes)
        )

        self._image_resolution = None
        self._sensor_diagonal = None
        self._focal_length_mm = None
        self._lens_aperture = None
        self._crop_resolution = None
        self._lens_position_at_far = None
        self._lens_position_at_near = None
        self._object_distance_at_far_mm = None
        self._object_distance_at_near_mm = None
        self._minimum_focusing_distance_mm = None
        self._maximum_object_distance_limit_mm = None

    @property
    def image_resolution(self) -> str:
        """Image (sensor) resolution name."""
        return self._image_resolution

    @image_resolution.setter
    def image_resolution(self, value: str):
        self._image_resolution = value

    def get_image_resolution_in_pixels(self):
        return self.image_formats.get(self._image_resolution)

    @property
    def sensor_diagonal(self) -> str:
        """Image (sensor) diagonal size."""
        return self._sensor_diagonal

    @sensor_diagonal.setter
    def sensor_diagonal(self, value: str):
        self._sensor_diagonal = value

    def get_sensor_sizes_in_mm(self):
        return self.sensor_sizes.get(self._sensor_diagonal)

    @property
    def focal_length_mm(self):
        """Focal length, mm."""
        return self._focal_length_mm

    @focal_length_mm.setter
    def focal_length_mm(self, value):
        self._focal_length_mm = value

    @property
    def aperture(self):
        """Lens aperture (F-number)."""
        return self._lens_aperture

    @aperture.setter
    def aperture(self, value):
        self._lens_aperture = value

    @property
    def crop_resolution(self) -> str:
        """Crop resolution name."""
        return self._crop_resolution

    @crop_resolution.setter
    def crop_resolution(self, value: str):
        self._crop_resolution = value

    def get_crop_resolution_in_pixels(self):
        return self.image_formats.get(self._crop_resolution)

    @property
    def lens_position_at_far(self):
        """Lens position value at FAR."""
        return self._lens_position_at_far

    @lens_position_at_far.setter
    def lens_position_at_far(self, value):
        self._lens_position_at_far = value

    @property
    def lens_position_at_near(self):
        """Lens position value at NEAR."""
        return self._lens_position_at_near

    @lens_position_at_near.setter
    def lens_position_at_near(self, value):
        self._lens_position_at_near = value

    @property
    def object_distance_at_far_mm(self):
        """Object distance, corresponding to FAR."""
        return self._object_distance_at_far_mm

    @object_distance_at_far_mm.setter
    def object_distance_at_far_mm(self, value):
        self._object_distance_at_far_mm = value

    @property
    def object_distance_at_near_mm(self):
        """Object distance, corresponding to NEAR."""
        return self._object_distance_at_near_mm

    @object_distance_at_near_mm.setter
    def object_distance_at_near_mm(self, value):
        self._object_distance_at_near_mm = value

    @property
    def minimum_focusing_distance_mm(self):
        """Minimum focusing distance, lens is capable to focus, mm."""
        return self._minimum_focusing_distance_mm

    @minimum_focusing_distance_mm.setter
    def minimum_focusing_distance_mm(self, value):
        self._minimum_focusing_distance_mm = value

    @property
    def maximum_object_distance_limit_mm(self):
        """Maximum object distance limit for "Lens DOF" plot, mm."""
        return self._maximum_object_distance_limit_mm

    @maximum_object_distance_limit_mm.setter
    def maximum_object_distance_limit_mm(self, value):
        self._maximum_object_distance_limit_mm = value


class Calculation:
    # pylint: disable=missing-function-docstring
    def __init__(self, cam_data: CameraCalcData):
        self._cam_data = cam_data
        self._idx_width = cam_data.idx_width
        self._idx_height = cam_data.idx_height

    def get_35mm_equivalent_mm(self) -> float:
        """Returns camera focal length in 35-mm equivalent, mm."""
        sensor_sizes = self._cam_data.get_sensor_sizes_in_mm()
        sensor_width = sensor_sizes[self._idx_width]
        sensor_height = sensor_sizes[self._idx_height]
        sensor_diag_mm = math.sqrt(sensor_width**2 + sensor_height**2)
        lens_f_length_35mm = (
            self._cam_data.focal_length_mm
            * self._cam_data.sensor_35mm_diagonal_mm
            / sensor_diag_mm
        )
        return lens_f_length_35mm

    def get_sampling_freq_px_per_mm(self) -> float:
        """Returns sampling frequency, pixels per mm."""
        resolutions = self._cam_data.get_image_resolution_in_pixels()
        resolution_horizontal = resolutions[self._idx_width]
        sensor_sizes = self._cam_data.get_sensor_sizes_in_mm()
        sensor_width_mm = sensor_sizes[self._idx_width]
        return resolution_horizontal / sensor_width_mm

    def get_nyquist_limit(self, sampl_freq: float) -> float:
        """Returns Nyquist limit, line pairs per mm."""
        return 0.5 * self._cam_data.kell_factor * sampl_freq

    def get_sensor_crop_sizes(self, crop_factors: dict) -> dict:
        sensor_sizes = self._cam_data.get_sensor_sizes_in_mm()
        sensor_width_mm = sensor_sizes[self._idx_width]
        sensor_height_mm = sensor_sizes[self._idx_height]
        crop_width_mm = sensor_width_mm / crop_factors.get('horz_crop_factor')
        crop_height_mm = sensor_height_mm / crop_factors.get('vert_crop_factor')
        crop_diag_mm = math.sqrt(crop_width_mm**2 + crop_height_mm**2)
        crop_sizes = {
            'crop_width_mm': crop_width_mm,
            'crop_height_mm': crop_height_mm,
            'crop_diag_mm': crop_diag_mm,
        }
        return crop_sizes

    def get_sensor_crop_factors(self) -> dict:
        resolutions = self._cam_data.get_image_resolution_in_pixels()
        resolution_horizontal = resolutions[self._idx_width]
        crop_resolutions = self._cam_data.get_crop_resolution_in_pixels()
        crop_resolution_horizontal = crop_resolutions[self._idx_width]
        hor_crop_factor = resolution_horizontal / crop_resolution_horizontal
        resolution_vertical = resolutions[self._idx_height]
        crop_resolution_vertical = crop_resolutions[self._idx_height]
        ver_crop_factor = resolution_vertical / crop_resolution_vertical
        crop_factors = {
            'horz_crop_factor': hor_crop_factor,
            'vert_crop_factor': ver_crop_factor,
        }
        return crop_factors

    def get_35mm_equivalent_crop(self, sensor_diag_crop: float) -> float:
        lens_f_length_35mm_crop = (
            self._cam_data.focal_length_mm
            * self._cam_data.sensor_35mm_diagonal_mm
            / sensor_diag_crop
        )
        return lens_f_length_35mm_crop

    def get_angles_of_view_effective(self) -> dict:
        sensor_sizes = self._cam_data.get_sensor_sizes_in_mm()
        hor_aov_eff = np.rad2deg(
            (
                2
                * (
                    math.atan(
                        sensor_sizes[self._idx_width]
                        / (2 * self._cam_data.focal_length_mm)
                    )
                )
            )
        )

        ver_aov_eff = np.rad2deg(
            (
                2
                * (
                    math.atan(
                        sensor_sizes[self._idx_height]
                        / (2 * self._cam_data.focal_length_mm)
                    )
                )
            )
        )

        sensor_diag = math.sqrt(
            sensor_sizes[self._idx_width] ** 2 + sensor_sizes[self._idx_height] ** 2
        )

        dia_aov_eff = np.rad2deg(
            (2 * (math.atan(sensor_diag / (2 * self._cam_data.focal_length_mm))))
        )

        angles_of_view = {
            'horz_angle_of_view_eff': hor_aov_eff,
            'vert_angle_of_view_eff': ver_aov_eff,
            'diag_angle_of_view_eff': dia_aov_eff,
        }

        return angles_of_view

    def get_angles_of_view_cropped(self, crop_factors: dict) -> dict:
        h_crop_factor = crop_factors.get('horz_crop_factor')
        v_crop_factor = crop_factors.get('vert_crop_factor')
        sensor_sizes = self._cam_data.get_sensor_sizes_in_mm()
        sensor_width_crop_mm = sensor_sizes[self._idx_width] / h_crop_factor
        sensor_height_crop_mm = sensor_sizes[self._idx_height] / v_crop_factor
        sensor_diag_crop_mm = math.sqrt(
            sensor_width_crop_mm**2 + sensor_height_crop_mm**2
        )
        focal_len = self._cam_data.focal_length_mm
        hor_aov_cr = np.rad2deg(
            (2 * (math.atan(sensor_width_crop_mm / (2 * focal_len))))
        )

        ver_aov_cr = np.rad2deg(
            (2 * (math.atan(sensor_height_crop_mm / (2 * focal_len))))
        )

        diag_aov_cr = np.rad2deg(
            (2 * (math.atan(sensor_diag_crop_mm / (2 * focal_len))))
        )

        angles_of_view_cr = {
            'horz_angle_of_view_crop': hor_aov_cr,
            'vert_angle_of_view_crop': ver_aov_cr,
            'diag_angle_of_view_crop': diag_aov_cr,
        }

        return angles_of_view_cr

    def get_hyperfocal(self, c_of_c_mm=None) -> float:
        if c_of_c_mm is None:
            # Calculate the default CoC
            sampl_freq = self.get_sampling_freq_px_per_mm()
            nyquist_limit = self.get_nyquist_limit(sampl_freq)
            c_o_c = self.get_circle_of_confusion_mm(nyquist_limit)
        else:
            c_o_c = c_of_c_mm
        flen = self._cam_data.focal_length_mm
        fnum = self._cam_data.aperture
        hyp_dist = flen + (flen**2) / (fnum * c_o_c)
        return hyp_dist

    def get_main_image_distances(self, hyperfocal: float) -> dict:
        flen = self._cam_data.focal_length_mm
        od_near_mm = self._cam_data.object_distance_at_near_mm
        id_inf = flen
        id_hyp = 1.0 / (1.0 / flen - 1.0 / hyperfocal)
        id_1_meter = 1.0 / (1.0 / flen - 1.0 / 1000)
        id_macro = 1.0 / (1.0 / flen - 1.0 / od_near_mm)
        main_image_dists = {
            'image_distance_inf': id_inf,
            'image_distance_hyperfocal': id_hyp,
            'image_distance_1_meter': id_1_meter,
            'image_distance_macro': id_macro,
        }

        return main_image_dists

    def get_lens_position(self, object_distance: float) -> float:
        flen = self._cam_data.focal_length_mm
        image_distance = 1.0 / (1.0 / flen - 1.0 / object_distance)
        x1 = 1.0 / (1.0 / flen - 1.0 / self._cam_data.object_distance_at_far_mm)
        y1 = self._cam_data.lens_position_at_far
        x0 = 1.0 / (1.0 / flen - 1.0 / self._cam_data.object_distance_at_near_mm)
        y0 = self._cam_data.lens_position_at_near
        lens_pos = int(0.5 + (y0 + (image_distance - x0) * (y1 - y0) / (x1 - x0)))
        return lens_pos

    def get_optics_values(self, hyperfocal: float) -> dict:
        # pylint: disable=too-many-locals disable=too-many-statements
        flen = self._cam_data.focal_length_mm
        x1 = 1.0 / (1.0 / flen - 1.0 / self._cam_data.object_distance_at_far_mm)
        y1 = self._cam_data.lens_position_at_far
        x0 = 1.0 / (1.0 / flen - 1.0 / self._cam_data.object_distance_at_near_mm)
        y0 = self._cam_data.lens_position_at_near
        i_d_inf = 1.0 / (1.0 / flen - 1.0 / 65535)
        i_d_hyp = 1.0 / (1.0 / flen - 1.0 / hyperfocal)
        i_d_200cm = 1.0 / (1.0 / flen - 1.0 / 2000)
        i_d_150cm = 1.0 / (1.0 / flen - 1.0 / 1500)
        i_d_120cm = 1.0 / (1.0 / flen - 1.0 / 1200)
        i_d_100cm = 1.0 / (1.0 / flen - 1.0 / 1000)
        i_d_70cm = 1.0 / (1.0 / flen - 1.0 / 700)
        i_d_50cm = 1.0 / (1.0 / flen - 1.0 / 500)
        infl = int(0.5 + (y0 + (i_d_inf - x0) * (y1 - y0) / (x1 - x0)))
        hypl = int(0.5 + (y0 + (i_d_hyp - x0) * (y1 - y0) / (x1 - x0)))
        cm200l = int(0.5 + (y0 + (i_d_200cm - x0) * (y1 - y0) / (x1 - x0)))
        cm150l = int(0.5 + (y0 + (i_d_150cm - x0) * (y1 - y0) / (x1 - x0)))
        cm120l = int(0.5 + (y0 + (i_d_120cm - x0) * (y1 - y0) / (x1 - x0)))
        cm100l = int(0.5 + (y0 + (i_d_100cm - x0) * (y1 - y0) / (x1 - x0)))
        cm70l = int(0.5 + (y0 + (i_d_70cm - x0) * (y1 - y0) / (x1 - x0)))
        cm50l = int(0.5 + (y0 + (i_d_50cm - x0) * (y1 - y0) / (x1 - x0)))
        cm40l, cm20l, cm10l = -1, -1, -1
        i_d_10cm, i_d_20cm, i_d_40cm = -1, -1, -1

        if self._cam_data.minimum_focusing_distance_mm <= 100:
            i_d_10cm = 1.0 / (1.0 / flen - 1.0 / 100)
            cm10l = int(0.5 + (y0 + (i_d_10cm - x0) * (y1 - y0) / (x1 - x0)))

        if self._cam_data.minimum_focusing_distance_mm <= 200:
            i_d_20cm = 1.0 / (1.0 / flen - 1.0 / 200)
            cm20l = int(0.5 + (y0 + (i_d_20cm - x0) * (y1 - y0) / (x1 - x0)))

        if self._cam_data.minimum_focusing_distance_mm <= 400:
            i_d_40cm = 1.0 / (1.0 / flen - 1.0 / 400)
            cm40l = int(0.5 + (y0 + (i_d_40cm - x0) * (y1 - y0) / (x1 - x0)))

        # Calculate DOF arrays
        o_d = np.array([0])
        i_d = np.array([0])
        idof_n = np.array([0])  # DOF near
        idof_f = np.array([0])  # DOF far

        for i in range(
            int(self._cam_data.object_distance_at_near_mm),
            int(self._cam_data.maximum_object_distance_limit_mm),
        ):
            o_d = np.append(o_d, i)
            id_cur = 1.0 / (1.0 / flen - 1.0 / i)
            i_d = np.append(i_d, id_cur)
            odof_n_cur = int(((hyperfocal * i) / (hyperfocal + i)) + 0.5)
            idof_n_cur = 1.0 / (1.0 / flen - 1.0 / odof_n_cur)
            idof_n = np.append(idof_n, idof_n_cur)
            odof_f_cur = int(((hyperfocal * i) / (hyperfocal - i)) + 0.5)
            idof_f_cur = 1.0 / (1.0 / flen - 1.0 / odof_f_cur)
            idof_f = np.append(idof_f, idof_f_cur)

        o_d = np.delete(o_d, 0)
        i_d = np.delete(i_d, 0)
        idof_n = np.delete(idof_n, 0)
        idof_f = np.delete(idof_f, 0)
        # return (
        #     infl,
        #     hypl,
        #     cm200l,
        #     cm150l,
        #     cm120l,
        #     cm100l,
        #     cm70l,
        #     cm50l,
        #     cm40l,
        #     cm20l,
        #     cm10l,
        #     od,
        #     id,
        #     idof_n,
        #     idof_f,
        # )
        optics_values = {
            'lens_value_at_inf': infl,
            'lens_value_at_hyp': hypl,
            'lens_value_at_200_cm': cm200l,
            'lens_value_at_150_cm': cm150l,
            'lens_value_at_120_cm': cm120l,
            'lens_value_at_100_cm': cm100l,
            'lens_value_at_70_cm': cm70l,
            'lens_value_at_50_cm': cm50l,
            'lens_value_at_40_cm': cm40l,
            'lens_value_at_20_cm': cm20l,
            'lens_value_at_10_cm': cm10l,
            'od_dof_array': o_d,
            'id_dof_array': i_d,
            'id_dof_near_array': idof_n,
            'id_dof_far_array': idof_f,
            'id_at_10_cm': i_d_10cm,
            'id_at_20_cm': i_d_20cm,
            'id_at_40_cm': i_d_40cm,
            'id_at_50_cm': i_d_50cm,
            'id_at_70_cm': i_d_70cm,
            'id_at_100_cm': i_d_100cm,
            'id_at_120_cm': i_d_120cm,
            'id_at_150_cm': i_d_150cm,
            'id_at_200_cm': i_d_200cm,
            'id_at_hyperfocal': i_d_hyp,
            'id_at_infinity': i_d_inf,
        }
        return optics_values

    @staticmethod
    def get_pixel_pitch_um(sampl_freq: float) -> float:
        return 1000.0 / sampl_freq

    @staticmethod
    def get_circle_of_confusion_mm(nyquist_limit: float) -> float:
        return 1.0 / nyquist_limit

    @staticmethod
    def get_near_dof_at_hyperfocal(hyperfocal: float) -> float:
        odof_n_hyp = (hyperfocal**2) / (hyperfocal * 2)
        return odof_n_hyp


class CameraPlots:
    # pylint: disable=missing-function-docstring disable=too-many-instance-attributes
    def __init__(self, cam_data: CameraCalcData, calc: Calculation):
        self._cam_data = cam_data
        self._calc = calc
        self._fig_full_x = cam_data.figure_width_px
        self._idx_width = cam_data.idx_width
        self._idx_height = cam_data.idx_height
        resolutions = cam_data.get_image_resolution_in_pixels()
        self._fig_full_y = (
            self._fig_full_x
            * resolutions[self._idx_height]
            / resolutions[self._idx_width]
        )

        crop_resolutions = cam_data.get_crop_resolution_in_pixels()
        self._fig_crop_x = (
            self._fig_full_x
            * crop_resolutions[self._idx_width]
            / resolutions[self._idx_width]
        )

        self._fig_crop_y = (
            self._fig_full_y
            * crop_resolutions[self._idx_height]
            / resolutions[self._idx_height]
        )

        self._crop_off_x = (self._fig_full_x - self._fig_crop_x) / 2
        self._crop_off_y = (self._fig_full_y - self._fig_crop_y) / 2
        self._eff_mpix = (
            resolutions[self._idx_width] * resolutions[self._idx_height] / 1000000
        )

    def draw_crops(self):
        plt.figure('Sensor Resolutions')
        full_rect = plt.Rectangle(
            (0, 0),
            self._fig_full_x,
            self._fig_full_y,
            edgecolor='b',
            linewidth=1.5,
            fill=None,
        )

        crop_rect = plt.Rectangle(
            (self._crop_off_x, self._crop_off_y),
            self._fig_crop_x,
            self._fig_crop_y,
            edgecolor='r',
            linewidth=1.5,
            fill=None,
        )

        plt.gca().add_patch(full_rect)
        plt.gca().add_patch(crop_rect)
        resolutions = self._cam_data.get_image_resolution_in_pixels()
        full_x = resolutions[self._idx_width]
        full_y = resolutions[self._idx_height]
        eff_mp = self._eff_mpix

        crop_resolutions = self._cam_data.get_crop_resolution_in_pixels()
        crop_x = crop_resolutions[self._idx_width]
        crop_y = crop_resolutions[self._idx_height]
        crop_mp = crop_x * crop_y / 1000000.0

        plt.text(
            1,
            1,
            f'Sensor: {full_x} x {full_y} ({eff_mp:.1f} MPixels)',
            fontsize='x-small',
            color='b',
        )

        x = self._fig_crop_x / 3
        y = self._crop_off_y + 1

        plt.text(
            x,
            y,
            f'Crop {self._cam_data.crop_resolution}: {crop_x} x {crop_y} ({crop_mp:.1f} MPixels)',
            fontsize='x-small',
            color='r',
        )

        plt.axis('scaled')
        plt.axis('off')

    def draw_dof_curves(self):
        # pylint: disable=too-many-locals disable=too-many-statements
        plt.figure('Depth-Of-Field Curves')
        hyper = self._calc.get_hyperfocal()
        optics_values = self._calc.get_optics_values(hyper)
        i_d = optics_values.get('id_dof_array')
        o_d = optics_values.get('od_dof_array')
        idofn = optics_values.get('id_dof_near_array')
        idoff = optics_values.get('id_dof_far_array')

        plt.plot(i_d, o_d, linewidth=2, label='Focus')
        plt.plot(idofn, o_d, linewidth=2, label='Far DOF')
        plt.plot(idoff, o_d, linewidth=2, label='Near DOF')
        plt.grid(visible=True, which='both', linestyle='-')
        plt.xlabel('Image distance, mm')
        plt.ylabel('Object distance, mm')
        nextPosY = 0
        nextPosYstep = 60
        font_size = 'x-small'
        max_od_dof = self._cam_data.maximum_object_distance_limit_mm
        lp_lines_color = 'r'

        i_d_10cm = optics_values.get('id_at_10_cm')
        if i_d_10cm != -1:
            o_d = 100
            odof_f_10cm = int(((hyper * o_d) / (hyper - o_d)) + 0.5)

            line10cm = lns.Line2D(
                [i_d_10cm, i_d_10cm],
                [0, odof_f_10cm],
                lw=1,
                color=lp_lines_color,
            )
            plt.gca().add_line(line10cm)
            lens_pos = self._calc.get_lens_position(o_d)
            plt.text(
                i_d_10cm,
                odof_f_10cm + 5,
                f'10cm LP: {lens_pos}',
                fontsize=font_size,
                color='r',
            )

        i_d_20cm = optics_values.get('id_at_20_cm')
        if i_d_20cm != -1:
            o_d = 200
            odof_f_20cm = int(((hyper * o_d) / (hyper - o_d)) + 0.5)
            line20cm = lns.Line2D(
                [i_d_20cm, i_d_20cm],
                [0, odof_f_20cm],
                lw=1,
                color=lp_lines_color,
            )
            plt.gca().add_line(line20cm)
            lens_pos = self._calc.get_lens_position(o_d)
            plt.text(
                i_d_20cm,
                odof_f_20cm + 5,
                f'20cm LP: {lens_pos}',
                fontsize=font_size,
                color=lp_lines_color,
            )

        i_d_40cm = optics_values.get('id_at_40_cm')
        if i_d_40cm != -1:
            o_d = 400
            odof_f_40cm = int(((hyper * o_d) / (hyper - o_d)) + 0.5)
            line40cm = lns.Line2D(
                [i_d_40cm, i_d_40cm],
                [0, odof_f_40cm],
                lw=1,
                color=lp_lines_color,
            )
            plt.gca().add_line(line40cm)
            lens_pos = self._calc.get_lens_position(o_d)
            plt.text(
                i_d_40cm,
                odof_f_40cm + 5,
                f'40cm LP: {lens_pos}',
                fontsize=font_size,
                color=lp_lines_color,
            )

        o_d = 500
        i_d_50cm = optics_values.get('id_at_50_cm')
        odof_f_50cm = int(((hyper * o_d) / (hyper - o_d)) + 0.5)
        line50cm = lns.Line2D(
            [i_d_50cm, i_d_50cm],
            [0, odof_f_50cm],
            lw=1,
            color=lp_lines_color,
        )
        plt.gca().add_line(line50cm)
        lens_pos = self._calc.get_lens_position(o_d)
        plt.text(
            i_d_50cm,
            odof_f_50cm + 5,
            f'50cm LP: {lens_pos}',
            fontsize=font_size,
            color=lp_lines_color,
        )

        o_d = 700
        i_d_70cm = optics_values.get('id_at_70_cm')
        odof_f_70cm = int(((hyper * o_d) / (hyper - o_d)) + 0.5)
        if odof_f_70cm > max_od_dof:
            odof_f_70cm = max_od_dof - 5
            nextPosY += nextPosYstep

        line70cm = lns.Line2D(
            [i_d_70cm, i_d_70cm],
            [0, odof_f_70cm - nextPosY],
            lw=1,
            color=lp_lines_color,
        )
        plt.gca().add_line(line70cm)
        lens_pos = self._calc.get_lens_position(o_d)
        plt.text(
            i_d_70cm,
            odof_f_70cm + 5 - nextPosY,
            f'70cm LP: {lens_pos}',
            fontsize=font_size,
            color=lp_lines_color,
        )

        o_d = 1000
        i_d_100cm = optics_values.get('id_at_100_cm')
        odof_f_100cm = int(((hyper * o_d) / (hyper - o_d)) + 0.5)
        if odof_f_100cm > max_od_dof:
            odof_f_100cm = max_od_dof - 5
            nextPosY += nextPosYstep

        line100cm = lns.Line2D(
            [i_d_100cm, i_d_100cm],
            [0, odof_f_100cm - nextPosY],
            lw=1,
            color=lp_lines_color,
        )
        plt.gca().add_line(line100cm)
        lens_pos = self._calc.get_lens_position(o_d)
        plt.text(
            i_d_100cm,
            odof_f_100cm + 5 - nextPosY,
            f'100cm LP: {lens_pos}',
            fontsize=font_size,
            color=lp_lines_color,
        )

        o_d = 1200
        i_d_120cm = optics_values.get('id_at_120_cm')
        odof_f_120cm = int(((hyper * o_d) / (hyper - o_d)) + 0.5)
        if odof_f_120cm > max_od_dof:
            odof_f_120cm = max_od_dof - 5
            nextPosY += nextPosYstep

        line120cm = lns.Line2D(
            [i_d_120cm, i_d_120cm],
            [0, odof_f_120cm - nextPosY],
            lw=1,
            color=lp_lines_color,
        )
        plt.gca().add_line(line120cm)
        lens_pos = self._calc.get_lens_position(o_d)
        plt.text(
            i_d_120cm,
            odof_f_120cm + 5 - nextPosY,
            f'120cm LP: {lens_pos}',
            fontsize=font_size,
            color=lp_lines_color,
        )

        o_d = 1500
        i_d_150cm = optics_values.get('id_at_150_cm')
        if o_d < hyper:
            odof_f_150cm = int(((hyper * o_d) / (hyper - o_d)) + 0.5)
        else:
            odof_f_150cm = self._cam_data.big_object_distance_mm

        if odof_f_150cm > max_od_dof:
            odof_f_150cm = max_od_dof - 5
            nextPosY += nextPosYstep

        line150cm = lns.Line2D(
            [i_d_150cm, i_d_150cm],
            [0, odof_f_150cm - nextPosY],
            lw=1,
            color=lp_lines_color,
        )
        plt.gca().add_line(line150cm)
        lens_pos = self._calc.get_lens_position(o_d)
        plt.text(
            i_d_150cm,
            odof_f_150cm + 5 - nextPosY,
            f'150cm LP: {lens_pos}',
            fontsize=font_size,
            color=lp_lines_color,
        )

        o_d = 2000
        i_d_200cm = optics_values.get('id_at_200_cm')
        if o_d < hyper:
            odof_f_200cm = int(((hyper * o_d) / (hyper - o_d)) + 0.5)
        else:
            odof_f_200cm = self._cam_data.big_object_distance_mm

        if odof_f_200cm > max_od_dof:
            odof_f_200cm = max_od_dof - 5
            nextPosY += nextPosYstep

        line200cm = lns.Line2D(
            [i_d_200cm, i_d_200cm],
            [0, odof_f_200cm - nextPosY],
            lw=1,
            color=lp_lines_color,
        )
        plt.gca().add_line(line200cm)
        lens_pos = self._calc.get_lens_position(o_d)
        plt.text(
            i_d_200cm,
            odof_f_200cm + 5 - nextPosY,
            f'200cm LP: {lens_pos}',
            fontsize=font_size,
            color=lp_lines_color,
        )

        o_d = hyper
        i_d_hyp = optics_values.get('id_at_hyperfocal')
        odof_f_hyp = max_od_dof - 5
        nextPosY += nextPosYstep
        lineHyper = lns.Line2D(
            [i_d_hyp, i_d_hyp],
            [0, odof_f_hyp - nextPosY],
            lw=1,
            color=lp_lines_color,
        )
        plt.gca().add_line(lineHyper)
        lens_pos = self._calc.get_lens_position(o_d)
        plt.text(
            i_d_hyp,
            odof_f_hyp + 5 - nextPosY,
            f'HYPER LP: {lens_pos}',
            fontsize=font_size,
            color=lp_lines_color,
        )

        o_d = self._cam_data.big_object_distance_mm
        i_d_inf = optics_values.get('id_at_infinity')
        odof_f_inf = max_od_dof - 5
        nextPosY += nextPosYstep
        lineInf = lns.Line2D(
            [i_d_inf, i_d_inf],
            [0, odof_f_inf - nextPosY],
            lw=1,
            color=lp_lines_color,
        )
        plt.gca().add_line(lineInf)
        lens_pos = self._calc.get_lens_position(o_d)
        plt.text(
            i_d_inf,
            odof_f_inf + 5 - nextPosY,
            f'INF LP: {lens_pos}',
            fontsize=font_size,
            color=lp_lines_color,
        )

        plt.text(
            i_d_inf,
            70,
            f'Ver: {self._cam_data.program_version}',
            fontsize='x-small',
            color='black',
        )
        plt.legend()

    def show_figures(self):
        plt.show()


def main():
    """Main() function of Camera Calculator."""

    # pylint: disable=too-many-statements disable=too-many-locals
    camera_data = CameraCalcData()
    print(f'Camera Calculator, ver {camera_data.program_version}\n')

    parser = argparse.ArgumentParser()
    parser.add_argument(
        '-r',
        '--resolution',
        type=str,
        choices=camera_data.resolutions,
        help='resolution name of imaging sensor format',
    )

    parser.add_argument(
        '-s',
        '--size',
        type=str,
        choices=camera_data.diagonal_names,
        help='diagonal size of the imaging sensor',
    )

    parser.add_argument(
        '-l',
        '--focal_length',
        type=float,
        help='camera focal length, mm',
    )

    parser.add_argument(
        '-a',
        '--aperture',
        type=float,
        help='lens aperture, F-number',
    )

    parser.add_argument(
        '-o',
        '--object_distance',
        type=int,
        help='maximum object distance for "Lens DOF figure", mm',
    )

    parser.add_argument(
        '-c',
        '--crop',
        type=str,
        choices=camera_data.resolutions,
        help='target crop from native sensor resolution',
    )

    parser.add_argument(
        '-f',
        '--far_lens',
        type=int,
        help='lens position value at FAR',
    )

    parser.add_argument(
        '-n',
        '--near_lens',
        type=int,
        help='lens position value at NEAR',
    )

    parser.add_argument(
        '-m',
        '--macro_distance',
        type=int,
        help='object distance, corresponding to NEAR',
    )

    parser.add_argument(
        '-i',
        '--inf_distance',
        type=int,
        help='object distance, corresponding to FAR',
    )

    parser.add_argument(
        '--min_f_dist',
        type=int,
        default=100,
        help='minimum focusing distance, lens can focus (default=100), mm',
    )

    parser.add_argument(
        '--max_od_dof',
        type=int,
        default=1500,
        help='maximum object distance limit for "Lens DOF" plot (default=1500), mm',
    )

    args = parser.parse_args()
    if len(sys.argv) == 1:
        parser.print_help()
        sys.exit()

    print('===== Parameters =====')
    if args.min_f_dist:
        camera_data.minimum_focusing_distance_mm = args.min_f_dist
        print(
            f'Minimum focusing distance: {camera_data.minimum_focusing_distance_mm} mm'
        )

        if int(args.min_f_dist) > 500:
            print('Calculator is limited to minimum focusing distance <= 500 mm!')
            sys.exit()

    if args.max_od_dof:
        camera_data.maximum_object_distance_limit_mm = args.max_od_dof
        print(
            f'Maximum object distance limit for DOF plot: '
            f'{camera_data.maximum_object_distance_limit_mm} mm'
        )

    if args.resolution:
        camera_data.image_resolution = args.resolution
        resolution_in_pixels = camera_data.get_image_resolution_in_pixels()
        print(f'Image resolution: {args.resolution}, ' f'{resolution_in_pixels} pixels')

    if args.size:
        camera_data.sensor_diagonal = args.size
        sensor_sizes = camera_data.get_sensor_sizes_in_mm()
        print(f'Sensor diagonal size: {args.size}, {sensor_sizes} mm')

    if args.focal_length:
        camera_data.focal_length_mm = args.focal_length
        print(f'Focal length: {camera_data.focal_length_mm} mm')

    if args.aperture:
        camera_data.aperture = args.aperture
        print(f'Lens aperture (F-number): {camera_data.aperture}')

    if args.crop:
        camera_data.crop_resolution = (
            args.crop
        )  # camera_data.image_formats.get(args.crop)
        crop_resolution_in_pixels = camera_data.get_crop_resolution_in_pixels()
        print(f'Target crop: {args.crop}, {crop_resolution_in_pixels} pixels')

    if args.far_lens:
        camera_data.lens_position_at_far = args.far_lens
        print(f'Lens position value at FAR: {camera_data.lens_position_at_far}')

    if args.near_lens:
        camera_data.lens_position_at_near = args.near_lens
        print(f'Lens position value at NEAR: {camera_data.lens_position_at_near}')

    if args.inf_distance:
        camera_data.object_distance_at_far_mm = args.inf_distance
        print(f'Object distance at FAR: {camera_data.object_distance_at_far_mm} mm')

    if args.macro_distance:
        camera_data.object_distance_at_near_mm = args.macro_distance
        print(f'Object distance at NEAR: {camera_data.object_distance_at_near_mm} mm')

    # =================== Start calculations =====================
    calc = Calculation(cam_data=camera_data)

    print('\n===== Calculations =====')
    sampl_freq_px_per_mm = calc.get_sampling_freq_px_per_mm()
    print(f'Sampling frequency: {sampl_freq_px_per_mm:.1f} pixels/mm')

    pixel_pitch_um = calc.get_pixel_pitch_um(sampl_freq_px_per_mm)
    print(f'Pixel pitch: {pixel_pitch_um:.2f} um')

    nyquist_limit_lp_per_mm = calc.get_nyquist_limit(sampl_freq_px_per_mm)
    print(
        f'Nyquist limit: {nyquist_limit_lp_per_mm:.2f} '
        f'lp/mm (kell factor: {camera_data.kell_factor})'
    )

    focal_35mm = calc.get_35mm_equivalent_mm()
    print(f'Focal length in 35-mm equivalent: {focal_35mm:.1f} mm')

    c_o_c_mm = calc.get_circle_of_confusion_mm(nyquist_limit_lp_per_mm)
    print(f'Circle of confusion: {c_o_c_mm:.4f} mm')

    crop_factors = calc.get_sensor_crop_factors()
    crop_name = camera_data.crop_resolution
    print(
        f'{crop_name} horizontal crop factor: '
        f'{crop_factors.get("horz_crop_factor"):.2f}'
    )

    print(
        f'{crop_name} vertical crop factor: '
        f'{crop_factors.get("vert_crop_factor"):.2f}'
    )

    crop_sizes = calc.get_sensor_crop_sizes(crop_factors)
    print(f'{crop_name} cropped sensor width: {crop_sizes.get("crop_width_mm"):.2f} mm')
    print(
        f'{crop_name} cropped sensor height: {crop_sizes.get("crop_height_mm"):.2f} mm'
    )
    print(
        f'{crop_name} cropped sensor diagonal: {crop_sizes.get("crop_diag_mm"):.2f} mm'
    )

    focal_35mm_crop = calc.get_35mm_equivalent_crop(crop_sizes.get("crop_diag_mm"))
    print(f'{crop_name} focal length in 35-mm equivalent: {focal_35mm_crop:.1f} mm')

    view_angles_effective = calc.get_angles_of_view_effective()
    hor_aov_eff = view_angles_effective.get('horz_angle_of_view_eff')
    ver_aov_eff = view_angles_effective.get('vert_angle_of_view_eff')
    dia_aov_eff = view_angles_effective.get('diag_angle_of_view_eff')
    print(f'Horizontal Angle-Of-View (effective): {hor_aov_eff:.1f} deg')
    print(f'Vertical Angle-Of-View (effective): {ver_aov_eff:.1f} deg')
    print(f'Diagonal Angle-Of-View (effective): {dia_aov_eff:.1f} deg')

    view_angles_crop = calc.get_angles_of_view_cropped(crop_factors)
    hor_aov_cr = view_angles_crop.get('horz_angle_of_view_crop')
    ver_aov_cr = view_angles_crop.get('vert_angle_of_view_crop')
    dia_aov_cr = view_angles_crop.get('diag_angle_of_view_crop')
    print(f'Horizontal Angle-Of-View {crop_name}: {hor_aov_cr:.1f} deg')
    print(f'Vertical Angle-Of-View {crop_name}: {ver_aov_cr:.1f} deg')
    print(f'Diagonal Angle-Of-View {crop_name}: {dia_aov_cr:.1f} deg')

    hyperfocal = calc.get_hyperfocal(c_o_c_mm)
    print(f'Hyperfocal distance: {int(hyperfocal)} mm')

    near_dof_hyp = calc.get_near_dof_at_hyperfocal(hyperfocal)
    print(f'Near Depth-Of-Field at hyperfocal distance: {int(near_dof_hyp)} mm')

    main_image_dists = calc.get_main_image_distances(hyperfocal)
    print(
        f'Image distance at INFINITY: '
        f'{main_image_dists.get("image_distance_inf"):.3f} mm'
    )

    print(
        f'Image distance at HYPERFOCAL: '
        f'{main_image_dists.get("image_distance_hyperfocal"):.3f} mm'
    )

    print(
        f'Image distance at 1 meter: '
        f'{main_image_dists.get("image_distance_1_meter"):.3f} mm'
    )

    print(
        f'Image distance at MACRO (focus at {camera_data.object_distance_at_near_mm} mm): '
        f'{main_image_dists.get("image_distance_1_meter"):.3f} mm'
    )

    # (
    #     linf,
    #     lhyp,
    #     l200cm,
    #     l150cm,
    #     l120cm,
    #     l100cm,
    #     l70cm,
    #     l50cm,
    #     l40cm,
    #     l20cm,
    #     l10cm,
    #     o_d,
    #     i_d,
    #     idof_n,
    #     idof_f,
    # ) = calc.get_optics_values(hyperfocal)
    optics_values = calc.get_optics_values(hyperfocal)
    print(f'Lens value at FAR: {camera_data.lens_position_at_far}')
    print(f'Lens value at INFINITY: {optics_values.get("lens_value_at_inf")}')
    print(f'Lens value at HYPERFOCAL: {optics_values.get("lens_value_at_hyp")}')
    print(f'Lens value at 200 cm: {optics_values.get("lens_value_at_200_cm")}')
    print(f'Lens value at 150 cm: {optics_values.get("lens_value_at_150_cm")}')
    print(f'Lens value at 120 cm: {optics_values.get("lens_value_at_120_cm")}')
    print(f'Lens value at 100 cm: {optics_values.get("lens_value_at_100_cm")}')
    print(f'Lens value at 70 cm: {optics_values.get("lens_value_at_70_cm")}')
    print(f'Lens value at 50 cm: {optics_values.get("lens_value_at_50_cm")}')
    print(f'Lens value at 40 cm: {optics_values.get("lens_value_at_40_cm")}')
    print(f'Lens value at 20 cm: {optics_values.get("lens_value_at_20_cm")}')
    print(f'Lens value at 10 cm: {optics_values.get("lens_value_at_10_cm")}')

    # =================== Start plots drawing =====================
    print('\nTo close plots press "q"')
    cam_plot = CameraPlots(camera_data, calc)
    cam_plot.draw_crops()
    cam_plot.draw_dof_curves()
    cam_plot.show_figures()
    print('OK')


if __name__ == '__main__':
    main()
