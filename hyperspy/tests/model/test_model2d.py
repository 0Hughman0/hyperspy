# -*- coding: utf-8 -*-
# Copyright 2007-2020 The HyperSpy developers
#
# This file is part of  HyperSpy.
#
#  HyperSpy is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
#  HyperSpy is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with  HyperSpy.  If not, see <http://www.gnu.org/licenses/>.


import numpy as np
import pytest

import hyperspy.api as hs
from hyperspy.decorators import lazifyTestClass


@lazifyTestClass
class TestModel2D:
    def setup_method(self, method):
        g = hs.model.components2D.Gaussian2D(
            centre_x=-5.0, centre_y=-5.0, sigma_x=1.0, sigma_y=2.0
        )
        scale = 0.05
        x = np.arange(-10, 10, scale)
        y = np.arange(-10, 10, scale)
        X, Y = np.meshgrid(x, y)
        im = hs.signals.Signal2D(g.function(X, Y))
        im.axes_manager[0].scale = scale
        im.axes_manager[0].offset = -10
        im.axes_manager[1].scale = scale
        im.axes_manager[1].offset = -10
        self.im = im

    def test_fitting(self):
        im = self.im
        m = im.create_model()
        gt = hs.model.components2D.Gaussian2D(
            centre_x=-4.5, centre_y=-4.5, sigma_x=0.5, sigma_y=1.5
        )
        m.append(gt)
        m.fit()
        np.testing.assert_allclose(gt.centre_x.value, -5.0)
        np.testing.assert_allclose(gt.centre_y.value, -5.0)
        np.testing.assert_allclose(gt.sigma_x.value, 1.0)
        np.testing.assert_allclose(gt.sigma_y.value, 2.0)


def test_Model2D_NotImplementedError_range():
    im = hs.signals.Signal2D(np.ones((128, 128)))
    m = im.create_model()
    gt = hs.model.components2D.Gaussian2D(
        centre_x=-4.5, centre_y=-4.5, sigma_x=0.5, sigma_y=1.5
    )
    m.append(gt)

    for member_f in [
        "_set_signal_range_in_pixels",
        "_remove_signal_range_in_pixels",
        "_add_signal_range_in_pixels",
        "reset_the_signal_range",
        "reset_signal_range",
    ]:
        with pytest.raises(NotImplementedError):
            _ = getattr(m, member_f)()


def test_Model2D_NotImplementedError_fitting():
    im = hs.signals.Signal2D(np.ones((128, 128)))
    m = im.create_model()
    gt = hs.model.components2D.Gaussian2D(
        centre_x=-4.5, centre_y=-4.5, sigma_x=0.5, sigma_y=1.5
    )
    m.append(gt)

    for member_f in [
        "_jacobian",
        "_poisson_likelihood_function",
        "_gradient_ml",
        "_gradient_ls",
        "_huber_loss_function",
        "_gradient_huber",
    ]:
        with pytest.raises(NotImplementedError):
            _ = getattr(m, member_f)(None, None)


def test_Model2D_NotImplementedError_plot():
    im = hs.signals.Signal2D(np.ones((128, 128)))
    m = im.create_model()
    gt = hs.model.components2D.Gaussian2D(
        centre_x=-4.5, centre_y=-4.5, sigma_x=0.5, sigma_y=1.5
    )
    m.append(gt)

    for member_f in ["plot", "enable_adjust_position", "disable_adjust_position"]:
        with pytest.raises(NotImplementedError):
            _ = getattr(m, member_f)()

    for member_f in ["_plot_component", "_connect_component_line"]:
        with pytest.raises(NotImplementedError):
            _ = getattr(m, member_f)(None)
