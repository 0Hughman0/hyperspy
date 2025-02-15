# -*- coding: utf-8 -*-
# Copyright 2007-2024 The HyperSpy developers
#
# This file is part of HyperSpy.
#
# HyperSpy is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# HyperSpy is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with HyperSpy. If not, see <https://www.gnu.org/licenses/#GPL>.

import numpy as np
import pytest
import traits.api as t

from hyperspy.api_nogui import _ureg
from hyperspy.axes import AxesManager, DataAxis, UniformDataAxis, UnitConversion
from hyperspy.misc.test_utils import assert_deep_almost_equal


class TestUnitConversion:
    def setup_method(self, method):
        self.uc = UnitConversion()
        self._set_units_scale_size(units="m", scale=1e-3)

    def _set_units_scale_size(self, units=t.Undefined, scale=1.0, size=100, offset=0.0):
        self.uc.units = units
        self.uc.scale = scale
        self.uc.offset = offset
        self.uc.size = size

    def test_units_setter(self):
        self.uc.units = " m"
        assert self.uc.units == " m"
        self.uc.units = "um"
        assert self.uc.units == "um"
        self.uc.units = "µm"
        assert self.uc.units == "µm"
        self.uc.units = "km"
        assert self.uc.units == "km"

    def test_ignore_conversion(self):
        assert self.uc._ignore_conversion(t.Undefined)
        with pytest.warns(UserWarning, match="not supported for conversion."):
            assert self.uc._ignore_conversion("unit_not_supported")
        assert not self.uc._ignore_conversion("m")

    def test_converted_compact_scale_units(self):
        self.uc.units = "toto"
        with pytest.warns(UserWarning, match="not supported for conversion."):
            self.uc._convert_compact_units()
        assert self.uc.units == "toto"
        np.testing.assert_almost_equal(self.uc.scale, 1.0e-3)

    def test_convert_to_units(self):
        self._set_units_scale_size(t.Undefined, 1.0)
        out = self.uc._convert_units("nm")
        assert out is None
        assert self.uc.units == t.Undefined
        np.testing.assert_almost_equal(self.uc.scale, 1.0)

        self._set_units_scale_size("m", 1.0e-3)
        out = self.uc._convert_units("µm")
        assert out is None
        assert self.uc.units == "µm"
        np.testing.assert_almost_equal(self.uc.scale, 1e3)

        self._set_units_scale_size("µm", 0.5)
        out = self.uc._convert_units("nm")
        assert out is None
        assert self.uc.units == "nm"
        np.testing.assert_almost_equal(self.uc.scale, 500)

        self._set_units_scale_size("µm", 5)
        out = self.uc._convert_units("cm")
        assert out is None
        assert self.uc.units == "cm"
        np.testing.assert_almost_equal(self.uc.scale, 0.0005)

        self._set_units_scale_size("1/µm", 5)
        out = self.uc._convert_units("1/nm")
        assert out is None
        assert self.uc.units == "1 / nm"
        np.testing.assert_almost_equal(self.uc.scale, 0.005)

        self._set_units_scale_size("eV", 5)
        out = self.uc._convert_units("keV")
        assert out is None
        assert self.uc.units == "keV"
        np.testing.assert_almost_equal(self.uc.scale, 0.005)

    def test_convert_to_units_not_in_place(self):
        self._set_units_scale_size(t.Undefined, 1.0)
        out = self.uc.convert_to_units("nm", inplace=False)
        assert out is None  # unit conversion is ignored
        assert self.uc.units == t.Undefined
        np.testing.assert_almost_equal(self.uc.scale, 1.0)

        self._set_units_scale_size("m", 1.0e-3)
        out = self.uc.convert_to_units("µm", inplace=False)
        assert out == (1e3, 0.0, "µm")
        assert self.uc.units == "m"
        np.testing.assert_almost_equal(self.uc.scale, 1.0e-3)
        np.testing.assert_almost_equal(self.uc.offset, 0.0)

        self._set_units_scale_size("µm", 0.5)
        out = self.uc.convert_to_units("nm", inplace=False)
        assert out[1:] == (0.0, "nm")
        np.testing.assert_almost_equal(out[0], 500.0)
        assert self.uc.units == "µm"
        np.testing.assert_almost_equal(self.uc.scale, 0.5)

    def test_get_compact_unit(self):
        ##### Imaging #####
        # typical setting for high resolution image
        self._set_units_scale_size("m", 12e-12, 2048, 2e-9)
        self.uc._convert_compact_units()
        assert self.uc.units == "nm"
        np.testing.assert_almost_equal(self.uc.scale, 0.012)
        np.testing.assert_almost_equal(self.uc.offset, 2.0)

        # typical setting for nm resolution image
        self._set_units_scale_size("m", 0.5e-9, 1024)
        self.uc._convert_compact_units()
        assert self.uc.units == "nm"
        np.testing.assert_almost_equal(self.uc.scale, 0.5)
        np.testing.assert_almost_equal(self.uc.offset, 0.0)

        ##### Diffraction #####
        # typical TEM diffraction
        self._set_units_scale_size("1/m", 0.1e9, 1024)
        self.uc._convert_compact_units()
        assert self.uc.units == "1 / nm"
        np.testing.assert_almost_equal(self.uc.scale, 0.1)

        # typical TEM diffraction
        self._set_units_scale_size("1/m", 0.01e9, 256)
        self.uc._convert_compact_units()
        assert self.uc.units == "1 / µm"
        np.testing.assert_almost_equal(self.uc.scale, 10.0)

        # high camera length diffraction
        self._set_units_scale_size("1/m", 0.1e9, 4096)
        self.uc._convert_compact_units()
        assert self.uc.units == "1 / nm"
        np.testing.assert_almost_equal(self.uc.scale, 0.1)

        # typical EDS resolution
        self._set_units_scale_size("eV", 50, 4096, 0.0)
        self.uc._convert_compact_units()
        assert self.uc.units == "keV"
        np.testing.assert_almost_equal(self.uc.scale, 0.05)
        np.testing.assert_almost_equal(self.uc.offset, 0.0)

        ##### Spectroscopy #####
        # typical EELS resolution
        self._set_units_scale_size("eV", 0.2, 2048, 200.0)
        self.uc._convert_compact_units()
        assert self.uc.units == "eV"
        np.testing.assert_almost_equal(self.uc.scale, 0.2)
        np.testing.assert_almost_equal(self.uc.offset, 200.0)

        # typical EELS resolution
        self._set_units_scale_size("eV", 1.0, 2048, 500.0)
        self.uc._convert_compact_units()
        assert self.uc.units == "eV"
        np.testing.assert_almost_equal(self.uc.scale, 1.0)
        np.testing.assert_almost_equal(self.uc.offset, 500)

        # typical high resolution EELS resolution
        self._set_units_scale_size("eV", 0.05, 100)
        self.uc._convert_compact_units()
        assert self.uc.units == "eV"
        assert self.uc.scale == 0.05

    def test_get_set_quantity(self):
        with pytest.raises(ValueError):
            self.uc._get_quantity("size")
        with pytest.raises(ValueError):
            self.uc._set_quantity("size", 10)


class TestUniformDataAxis:
    def setup_method(self, method):
        self.axis = UniformDataAxis(size=2048, scale=12e-12, units="m", offset=5e-9)

    def test_scale_offset_as_quantity_property(self):
        assert self.axis.scale_as_quantity == 12e-12 * _ureg("m")
        assert self.axis.offset_as_quantity == 5e-9 * _ureg("m")

    def test_scale_as_quantity_setter_string(self):
        self.axis.scale_as_quantity = "2.5 nm"
        assert self.axis.scale == 2.5
        np.testing.assert_almost_equal(self.axis.offset, 5.0)
        assert self.axis.units == "nm"
        # Test that the axis array has been recomputed
        np.testing.assert_almost_equal(self.axis.axis[1], 7.5)

    def test_scale_as_quantity_setter_string_no_previous_units(self):
        axis = UniformDataAxis(size=2048, scale=12e-12, offset=5.0)
        axis.scale_as_quantity = "2.5 nm"
        assert axis.scale == 2.5
        # the units haven't been set previously, so the offset is not converted
        np.testing.assert_almost_equal(axis.offset, 5.0)
        assert axis.units == "nm"

    def test_offset_as_quantity_setter_string(self):
        self.axis.offset_as_quantity = "5e-3 mm"
        assert self.axis.scale == 12e-9
        assert self.axis.offset == 5e-3
        assert self.axis.units == "mm"

    def test_offset_as_quantity_setter_string_no_units(self):
        self.axis.offset_as_quantity = "5e-3"
        assert self.axis.offset == 5e-3
        assert self.axis.scale == 12e-12
        assert self.axis.units == "m"

    def test_scale_offset_as_quantity_setter_float(self):
        self.axis.scale_as_quantity = 2.5e-9
        assert self.axis.scale == 2.5e-9
        assert self.axis.units == "m"

    def test_scale_offset_as_quantity_setter_pint_quantity(self):
        self.axis.scale_as_quantity = _ureg.parse_expression("2.5 nm")
        assert self.axis.scale == 2.5
        assert self.axis.units == "nm"

        self.axis.offset_as_quantity = _ureg.parse_expression("5e-3 mm")
        assert self.axis.offset == 5e-3
        assert self.axis.units == "mm"

    def test_convert_to_compact_units(self):
        self.axis.convert_to_units(units=None)
        np.testing.assert_almost_equal(self.axis.scale, 0.012)
        assert self.axis.units == "nm"
        np.testing.assert_almost_equal(self.axis.offset, 5.0)

    def test_convert_to_units(self):
        self.axis.convert_to_units(units="µm")
        np.testing.assert_almost_equal(self.axis.scale, 12e-6)
        assert self.axis.units == "µm"
        np.testing.assert_almost_equal(self.axis.offset, 0.005)

    def test_units_not_supported_by_pint_warning_raised(self):
        # raising a warning, not converting scale
        self.axis.units = "toto"
        with pytest.warns(UserWarning, match="not supported for conversion."):
            self.axis.convert_to_units("m")
        np.testing.assert_almost_equal(self.axis.scale, 12e-12)
        assert self.axis.units == "toto"

    def test_units_not_supported_by_pint_warning_raised2(self):
        # raising a warning, not converting scale
        self.axis.units = "µm"
        with pytest.warns(UserWarning, match="not supported for conversion."):
            self.axis.convert_to_units("toto")
        np.testing.assert_almost_equal(self.axis.scale, 12e-12)
        assert self.axis.units == "µm"


class TestAxesManager:
    def setup_method(self, method):
        self.axes_list = [
            {
                "_type": "UniformDataAxis",
                "name": "x",
                "navigate": True,
                "is_binned": False,
                "offset": 0.0,
                "scale": 1.5e-9,
                "size": 1024,
                "units": "m",
            },
            {
                "_type": "UniformDataAxis",
                "name": "y",
                "navigate": True,
                "is_binned": False,
                "offset": 0.0,
                "scale": 0.5e-9,
                "size": 1024,
                "units": "m",
            },
            {
                "_type": "UniformDataAxis",
                "name": "energy",
                "navigate": False,
                "is_binned": False,
                "offset": 0.0,
                "scale": 5.0,
                "size": 4096,
                "units": "eV",
            },
        ]

        self.am = AxesManager(self.axes_list)

        self.axes_list2 = [
            {
                "name": "x",
                "navigate": True,
                "is_binned": False,
                "offset": 0.0,
                "scale": 1.5e-9,
                "size": 1024,
                "units": "m",
            },
            {
                "name": "energy",
                "navigate": False,
                "is_binned": False,
                "offset": 0.0,
                "scale": 2.5,
                "size": 4096,
                "units": "eV",
            },
            {
                "name": "energy2",
                "navigate": False,
                "is_binned": False,
                "offset": 0.0,
                "scale": 5.0,
                "size": 4096,
                "units": "eV",
            },
        ]
        self.am2 = AxesManager(self.axes_list2)

    def test_compact_unit(self):
        self.am.convert_units()
        assert self.am["x"].units == "nm"
        np.testing.assert_almost_equal(self.am["x"].scale, 1.5)
        assert self.am["y"].units == "nm"
        np.testing.assert_almost_equal(self.am["y"].scale, 0.5)
        assert self.am["energy"].units == "keV"
        np.testing.assert_almost_equal(self.am["energy"].scale, 0.005)

    def test_convert_to_navigation_units(self):
        self.am.convert_units(axes="navigation", units="mm")
        np.testing.assert_almost_equal(self.am["x"].scale, 1.5e-6)
        assert self.am["x"].units == "mm"
        np.testing.assert_almost_equal(self.am["y"].scale, 0.5e-6)
        assert self.am["y"].units == "mm"
        np.testing.assert_almost_equal(
            self.am["energy"].scale, self.axes_list[-1]["scale"]
        )

    def test_convert_units_axes_integer(self):
        # convert only the first axis
        self.am.convert_units(axes=0, units="nm", same_units=False)
        np.testing.assert_almost_equal(self.am[0].scale, 0.5)
        assert self.am[0].units == "nm"
        np.testing.assert_almost_equal(self.am["x"].scale, 1.5e-9)
        assert self.am["x"].units == "m"
        np.testing.assert_almost_equal(
            self.am["energy"].scale, self.axes_list[-1]["scale"]
        )

        self.am.convert_units(axes=0, units="nm", same_units=True)
        np.testing.assert_almost_equal(self.am[0].scale, 0.5)
        assert self.am[0].units == "nm"
        np.testing.assert_almost_equal(self.am["x"].scale, 1.5)
        assert self.am["x"].units == "nm"

    def test_convert_to_navigation_units_list(self):
        self.am.convert_units(axes="navigation", units=["mm", "nm"], same_units=False)
        np.testing.assert_almost_equal(self.am["x"].scale, 1.5)
        assert self.am["x"].units == "nm"
        np.testing.assert_almost_equal(self.am["y"].scale, 0.5e-6)
        assert self.am["y"].units == "mm"
        np.testing.assert_almost_equal(
            self.am["energy"].scale, self.axes_list[-1]["scale"]
        )

    def test_convert_to_navigation_units_list_same_units(self):
        self.am.convert_units(axes="navigation", units=["mm", "nm"], same_units=True)
        assert self.am["x"].units == "mm"
        np.testing.assert_almost_equal(self.am["x"].scale, 1.5e-6)
        assert self.am["y"].units == "mm"
        np.testing.assert_almost_equal(self.am["y"].scale, 0.5e-6)
        assert self.am["energy"].units == "eV"
        np.testing.assert_almost_equal(self.am["energy"].scale, 5)

    def test_convert_to_navigation_units_different(self):
        # Don't convert the units since the units of the navigation axes are
        # different
        self.axes_list.insert(
            0,
            {
                "name": "time",
                "navigate": True,
                "is_binned": False,
                "offset": 0.0,
                "scale": 1.5,
                "size": 20,
                "units": "s",
            },
        )
        am = AxesManager(self.axes_list)
        am.convert_units(axes="navigation", same_units=True)
        assert am["time"].units == "s"
        np.testing.assert_almost_equal(am["time"].scale, 1.5)
        assert am["x"].units == "nm"
        np.testing.assert_almost_equal(am["x"].scale, 1.5)
        assert am["y"].units == "nm"
        np.testing.assert_almost_equal(am["y"].scale, 0.5)
        assert am["energy"].units == "eV"
        np.testing.assert_almost_equal(am["energy"].scale, 5)

    def test_convert_to_navigation_units_Undefined(self):
        self.axes_list[0]["units"] = t.Undefined
        am = AxesManager(self.axes_list)
        am.convert_units(axes="navigation", same_units=True)
        assert am["x"].units == t.Undefined
        np.testing.assert_almost_equal(am["x"].scale, 1.5e-9)
        assert am["y"].units == "m"
        np.testing.assert_almost_equal(am["y"].scale, 0.5e-9)
        assert am["energy"].units == "eV"
        np.testing.assert_almost_equal(am["energy"].scale, 5)

    def test_convert_to_signal_units(self):
        self.am.convert_units(axes="signal", units="keV")
        np.testing.assert_almost_equal(self.am["x"].scale, self.axes_list[0]["scale"])
        assert self.am["x"].units == self.axes_list[0]["units"]
        np.testing.assert_almost_equal(self.am["y"].scale, self.axes_list[1]["scale"])
        assert self.am["y"].units == self.axes_list[1]["units"]
        np.testing.assert_almost_equal(self.am["energy"].scale, 0.005)
        assert self.am["energy"].units == "keV"

    def test_convert_to_units_list(self):
        self.am.convert_units(units=["µm", "nm", "meV"], same_units=False)
        np.testing.assert_almost_equal(self.am["x"].scale, 1.5)
        assert self.am["x"].units == "nm"
        np.testing.assert_almost_equal(self.am["y"].scale, 0.5e-3)
        assert self.am["y"].units == "µm"
        np.testing.assert_almost_equal(self.am["energy"].scale, 5e3)
        assert self.am["energy"].units == "meV"

    def test_convert_to_units_list_same_units(self):
        self.am2.convert_units(units=["µm", "eV", "meV"], same_units=True)
        np.testing.assert_almost_equal(self.am2["x"].scale, 0.0015)
        assert self.am2["x"].units == "µm"
        np.testing.assert_almost_equal(
            self.am2["energy"].scale, self.axes_list2[1]["scale"]
        )
        assert self.am2["energy"].units == self.axes_list2[1]["units"]
        np.testing.assert_almost_equal(
            self.am2["energy2"].scale, self.axes_list2[2]["scale"]
        )
        assert self.am2["energy2"].units == self.axes_list2[2]["units"]

    def test_convert_to_units_list_signal2D(self):
        self.am2.convert_units(units=["µm", "eV", "meV"], same_units=False)
        np.testing.assert_almost_equal(self.am2["x"].scale, 0.0015)
        assert self.am2["x"].units == "µm"
        np.testing.assert_almost_equal(self.am2["energy"].scale, 2500)
        assert self.am2["energy"].units == "meV"
        np.testing.assert_almost_equal(self.am2["energy2"].scale, 5.0)
        assert self.am2["energy2"].units == "eV"

    @pytest.mark.parametrize("same_units", (True, False))
    def test_convert_to_units_unsupported_units(self, same_units):
        with pytest.warns(UserWarning, match="not supported for conversion."):
            self.am.convert_units("navigation", units="toto", same_units=same_units)
        assert_deep_almost_equal(self.am._get_axes_dicts(), self.axes_list)

    def test_conversion_non_uniform_axis(self):
        self.am._axes[0] = DataAxis(axis=np.arange(16) ** 2)
        with pytest.raises(NotImplementedError):
            self.am.convert_units()

    def test_initialize_UnitConversion_bug(self):
        uc = UnitConversion(units="m", scale=1.0, offset=0)
        assert uc.offset == 0
