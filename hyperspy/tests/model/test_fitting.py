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
from scipy.optimize import OptimizeResult

import hyperspy.api as hs
from hyperspy.decorators import lazifyTestClass
from hyperspy.exceptions import VisibleDeprecationWarning


@lazifyTestClass
class TestModelFitBinnedLeastSquares:
    def setup_method(self, method):
        np.random.seed(1)
        s = hs.signals.Signal1D(np.random.normal(scale=2, size=10000)).get_histogram()
        s.metadata.Signal.binned = True
        g = hs.model.components1D.Gaussian()
        self.m = s.create_model()
        self.m.append(g)
        g.sigma.value = 1
        g.centre.value = 0.5
        g.A.value = 1000

    def _check_model_values(self, model, expected, **kwargs):
        np.testing.assert_allclose(model.A.value, expected[0], **kwargs)
        np.testing.assert_allclose(model.centre.value, expected[1], **kwargs)
        np.testing.assert_allclose(model.sigma.value, expected[2], **kwargs)

    @pytest.mark.parametrize(
        "bounded, expected",
        [
            (False, (9976.145261, -0.110611, 1.983807)),
            (True, (9991.654220, 0.5, 2.083982)),
        ],
    )
    def test_fit_lm(self, bounded, expected):
        if bounded:
            self.m[0].centre.bmin = 0.5

        self.m.fit(optimizer="lm", bounded=bounded)
        self._check_model_values(self.m[0], expected, rtol=1e-5)

        assert isinstance(self.m.fit_output, OptimizeResult)
        assert self.m.p_std is not None
        assert len(self.m.p_std) == 3
        assert np.all(~np.isnan(self.m.p_std))

    @pytest.mark.parametrize(
        "grad, expected",
        [
            (None, (9976.145320, -0.110611, 1.983807)),
            ("analytical", (9976.145320, -0.110611, 1.983807)),
        ],
    )
    def test_fit_odr(self, grad, expected):
        self.m.fit(optimizer="odr", grad=grad)
        self._check_model_values(self.m[0], expected, rtol=1e-5)
        assert isinstance(self.m.fit_output, OptimizeResult)

        assert self.m.p_std is not None
        assert len(self.m.p_std) == 3
        assert np.all(~np.isnan(self.m.p_std))

    @pytest.mark.parametrize(
        "optimizer, expected", [("lm", (9991.654220, 0.5, 2.083982))],
    )
    def test_fit_bounded_bad_starting_values(self, optimizer, expected):
        self.m[0].centre.bmin = 0.5
        self.m[0].centre.value = -1
        self.m.fit(optimizer=optimizer, bounded=True)
        self._check_model_values(self.m[0], expected, rtol=1e-5)

    @pytest.mark.parametrize(
        "optimizer, expected", [("lm", (9950.0, 0.5, 2.078154))],
    )
    def test_fit_ext_bounding(self, optimizer, expected):
        self.m[0].A.bmin = 9950.0
        self.m[0].A.bmax = 10050.0
        self.m[0].centre.bmin = 0.5
        self.m[0].centre.bmax = 5.0
        self.m[0].sigma.bmin = 0.5
        self.m[0].sigma.bmax = 2.5

        with pytest.warns(
            VisibleDeprecationWarning, match="`ext_bounding=True` has been deprecated",
        ):
            self.m.fit(optimizer=optimizer, ext_bounding=True)

        self._check_model_values(self.m[0], expected, rtol=1e-5)


class TestModelFitBinnedScipyMinimize:
    def setup_method(self, method):
        np.random.seed(1)
        s = hs.signals.Signal1D(np.random.normal(scale=2, size=10000)).get_histogram()
        s.metadata.Signal.binned = True
        g = hs.model.components1D.Gaussian()
        self.m = s.create_model()
        self.m.append(g)
        g.sigma.value = 1
        g.centre.value = 0.5
        g.A.value = 1000

    def _check_model_values(self, model, expected, **kwargs):
        np.testing.assert_allclose(model.A.value, expected[0], **kwargs)
        np.testing.assert_allclose(model.centre.value, expected[1], **kwargs)
        np.testing.assert_allclose(model.sigma.value, expected[2], **kwargs)

    @pytest.mark.filterwarnings("ignore:divide by zero:RuntimeWarning")
    @pytest.mark.parametrize(
        "optimizer, loss_function, bounded, expected",
        [
            ("Nelder-Mead", "ls", False, (9976.145193, -0.110611, 1.983807)),
            ("Nelder-Mead", "ml-poisson", False, (10001.396139, -0.104151, 2.000536)),
            ("Nelder-Mead", "huber", False, (10032.953495, -0.110309, 1.987885)),
            ("L-BFGS-B", "ls", False, (9976.145193, -0.110611, 1.983807)),
            ("L-BFGS-B", "ml-poisson", False, (10001.390498, -0.104152, 2.000534)),
            ("L-BFGS-B", "huber", False, (10032.953495, -0.110309, 1.987885)),
            ("L-BFGS-B", "ls", True, (9991.627563, 0.5, 2.083987)),
        ],
    )
    def test_fit_scipy_minimize(self, optimizer, loss_function, bounded, expected):
        if bounded:
            self.m[0].centre.bmin = 0.5

        self.m.fit(optimizer=optimizer, loss_function=loss_function, bounded=bounded)
        self._check_model_values(self.m[0], expected, rtol=1e-5)
        assert isinstance(self.m.fit_output, OptimizeResult)

    @pytest.mark.filterwarnings("ignore:divide by zero:RuntimeWarning")
    @pytest.mark.parametrize(
        "grad, expected",
        [
            (None, (9976.145193, -0.110611, 1.983807)),
            ("analytical", (9976.145193, -0.110611, 1.983807)),
            ("auto", (9976.145193, -0.110611, 1.983807)),
        ],
    )
    def test_fit_scipy_minimize_gradients(self, grad, expected):
        self.m.fit(optimizer="L-BFGS-B", loss_function="ls", grad=grad)
        self._check_model_values(self.m[0], expected, rtol=1e-5)
        assert isinstance(self.m.fit_output, OptimizeResult)

    @pytest.mark.parametrize(
        "optimizer, expected",
        [
            ("Powell", (9991.464524, 0.500064, 2.083900)),
            ("L-BFGS-B", (9991.654220, 0.5, 2.083982)),
        ],
    )
    def test_fit_bounded_bad_starting_values(self, optimizer, expected):
        self.m[0].centre.bmin = 0.5
        self.m[0].centre.value = -1
        self.m.fit(optimizer=optimizer, bounded=True)
        self._check_model_values(self.m[0], expected, rtol=1e-5)

    @pytest.mark.parametrize(
        "optimizer, expected", [("SLSQP", (988.401164, -177.122887, -10.100562))]
    )
    def test_constraints(self, optimizer, expected):
        # Primarily checks that constraints are passed correctly,
        # even though the end result is a bad fit
        cons = {"type": "ineq", "fun": lambda x: x[0] - x[1]}
        self.m.fit(optimizer=optimizer, constraints=cons)
        self._check_model_values(self.m[0], expected, rtol=1e-5)


class TestModelFitBinnedGlobal:
    def setup_method(self, method):
        np.random.seed(1)
        s = hs.signals.Signal1D(np.random.normal(scale=2, size=10000)).get_histogram()
        s.metadata.Signal.binned = True
        g = hs.model.components1D.Gaussian()
        self.m = s.create_model()
        self.m.append(g)
        g.sigma.value = 1
        g.centre.value = 0.5
        g.A.value = 1000

    def _check_model_values(self, model, expected, **kwargs):
        np.testing.assert_allclose(model.A.value, expected[0], **kwargs)
        np.testing.assert_allclose(model.centre.value, expected[1], **kwargs)
        np.testing.assert_allclose(model.sigma.value, expected[2], **kwargs)

    @pytest.mark.parametrize(
        "loss_function, expected",
        [
            ("ls", (9972.351479, -0.110612, 1.983298)),
            ("ml-poisson", (10046.513541, -0.104155, 2.000547)),
            ("huber", (10032.952811, -0.110309, 1.987885)),
        ],
    )
    def test_fit_differential_evolution(self, loss_function, expected):
        self.m[0].A.bmin = 9950.0
        self.m[0].A.bmax = 10050.0
        self.m[0].centre.bmin = -5.0
        self.m[0].centre.bmax = 5.0
        self.m[0].sigma.bmin = 0.5
        self.m[0].sigma.bmax = 2.5

        self.m.fit(
            optimizer="Differential Evolution",
            loss_function=loss_function,
            bounded=True,
            seed=1,
        )
        self._check_model_values(self.m[0], expected, rtol=1e-5)
        assert isinstance(self.m.fit_output, OptimizeResult)

    @pytest.mark.parametrize(
        "loss_function, expected",
        [
            ("ls", (9976.145304, -0.110611, 1.983807)),
            ("ml-poisson", (10001.395614, -0.104151, 2.000536)),
            ("huber", (10032.952811, -0.110309, 1.987885)),
        ],
    )
    def test_fit_dual_annealing(self, loss_function, expected):
        pytest.importorskip("scipy", minversion="1.2.0")
        self.m[0].A.bmin = 9950.0
        self.m[0].A.bmax = 10050.0
        self.m[0].centre.bmin = -5.0
        self.m[0].centre.bmax = 5.0
        self.m[0].sigma.bmin = 0.5
        self.m[0].sigma.bmax = 2.5

        self.m.fit(
            optimizer="Dual Annealing",
            loss_function=loss_function,
            bounded=True,
            seed=1,
        )
        self._check_model_values(self.m[0], expected, rtol=1e-5)
        assert isinstance(self.m.fit_output, OptimizeResult)

    @pytest.mark.parametrize(
        "loss_function, expected",
        [
            ("ls", (9997.107685, -0.289231, 1.557846)),
            ("ml-poisson", (9999.999922, -0.104151, 2.000536)),
            ("huber", (10032.952811, -0.110309, 1.987885)),
        ],
    )
    def test_fit_shgo(self, loss_function, expected):
        pytest.importorskip("scipy", minversion="1.2.0")
        self.m[0].A.bmin = 9950.0
        self.m[0].A.bmax = 10050.0
        self.m[0].centre.bmin = -5.0
        self.m[0].centre.bmax = 5.0
        self.m[0].sigma.bmin = 0.5
        self.m[0].sigma.bmax = 2.5

        self.m.fit(optimizer="SHGO", loss_function=loss_function, bounded=True)
        self._check_model_values(self.m[0], expected, rtol=1e-5)
        assert isinstance(self.m.fit_output, OptimizeResult)


@lazifyTestClass
class TestModelWeighted:
    def setup_method(self, method):
        np.random.seed(1)
        v = 2.0 * np.exp(-((np.arange(10, 100, 0.1) - 50) ** 2) / (2 * 5.0 ** 2))
        s = hs.signals.Signal1D(v)
        s_var = hs.signals.Signal1D(np.arange(10, 100, 0.01))
        s.set_noise_variance(s_var)
        s.axes_manager[0].scale = 0.1
        s.axes_manager[0].offset = 10
        s.add_poissonian_noise()
        g = hs.model.components1D.Gaussian()
        g.centre.value = 50.0
        self.m = s.create_model()
        self.m.append(g)

    def _check_model_values(self, model, expected, **kwargs):
        np.testing.assert_allclose(model.A.value, expected[0], **kwargs)
        np.testing.assert_allclose(model.centre.value, expected[1], **kwargs)
        np.testing.assert_allclose(model.sigma.value, expected[2], **kwargs)

    @pytest.mark.parametrize("grad", ["auto", "analytical"])
    def test_chisq(self, grad):
        self.m.signal.metadata.Signal.binned = True
        self.m.fit(grad=grad)
        np.testing.assert_allclose(self.m.chisq.data, 18.81652763)

    @pytest.mark.parametrize("grad", ["auto", "analytical"])
    def test_red_chisq(self, grad):
        self.m.fit(grad=grad)
        np.testing.assert_allclose(self.m.red_chisq.data, 0.02100059)

    @pytest.mark.parametrize(
        "optimizer, binned, expected",
        [
            ("lm", True, [256.77519733, 49.97707093, 5.30083786]),
            ("odr", True, [102.84625027, 51.91686817, 64.89788172]),
            ("lm", False, [25.67755222, 49.97705725, 5.30085179]),
            ("odr", False, [25.67758724, 49.97705032, 5.30086644]),
        ],
    )
    def test_fit(self, optimizer, binned, expected):
        self.m.signal.metadata.Signal.binned = binned
        self.m.fit(optimizer=optimizer)
        self._check_model_values(self.m[0], expected, rtol=1e-5)


class TestModelScalarVariance:
    def setup_method(self, method):
        self.s = hs.signals.Signal1D(np.ones(100))
        self.m = self.s.create_model()
        self.m.append(hs.model.components1D.Offset())

    @pytest.mark.parametrize("std, expected", [(1, 78.35015229), (10, 78.35015229)])
    def test_std1_chisq(self, std, expected):
        np.random.seed(1)
        self.s.add_gaussian_noise(std)
        self.s.set_noise_variance(std ** 2)
        self.m.fit()
        np.testing.assert_allclose(self.m.chisq.data, expected)

    @pytest.mark.parametrize("std, expected", [(1, 0.79949135), (10, 0.79949135)])
    def test_std1_red_chisq(self, std, expected):
        np.random.seed(1)
        self.s.add_gaussian_noise(std)
        self.s.set_noise_variance(std ** 2)
        self.m.fit()
        np.testing.assert_allclose(self.m.red_chisq.data, expected)

    @pytest.mark.parametrize("std, expected", [(1, 0.86206965), (10, 0.86206965)])
    def test_std1_red_chisq_in_range(self, std, expected):
        self.m.set_signal_range(10, 50)
        np.random.seed(1)
        self.s.add_gaussian_noise(std)
        self.s.set_noise_variance(std ** 2)
        self.m.fit()
        np.testing.assert_allclose(self.m.red_chisq.data, expected)


@lazifyTestClass
class TestModelSignalVariance:
    def setup_method(self, method):
        variance = hs.signals.Signal1D(
            np.arange(100, 300, dtype="float64").reshape((2, 100))
        )
        s = variance.deepcopy()
        np.random.seed(1)
        std = 10
        np.random.seed(1)
        s.add_gaussian_noise(std)
        np.random.seed(1)
        s.add_poissonian_noise()
        s.set_noise_variance(variance + std ** 2)
        m = s.create_model()
        m.append(hs.model.components1D.Polynomial(order=1, legacy=False))
        self.s = s
        self.m = m
        self.var = (variance + std ** 2).data

    def test_std1_red_chisq(self):
        # HyperSpy 2.0: remove setting iterpath='serpentine'
        self.m.multifit(iterpath="serpentine")
        np.testing.assert_allclose(self.m.red_chisq.data[0], 0.813109, atol=1e-5)
        np.testing.assert_allclose(self.m.red_chisq.data[1], 0.697727, atol=1e-5)


class TestFitPrintInfo:
    def setup_method(self, method):
        np.random.seed(1)
        s = hs.signals.Signal1D(np.random.normal(scale=2, size=10000)).get_histogram()
        s.metadata.Signal.binned = True
        g = hs.model.components1D.Gaussian()
        self.m = s.create_model()
        self.m.append(g)
        g.sigma.value = 1
        g.centre.value = 0.5
        g.A.value = 1000

    @pytest.mark.parametrize("optimizer", ["odr", "Nelder-Mead", "L-BFGS-B"])
    def test_print_info(self, optimizer, capfd):
        self.m.fit(optimizer=optimizer, print_info=True)
        captured = capfd.readouterr()
        assert "Fit info:" in captured.out

    @pytest.mark.parametrize("bounded", [True, False])
    def test_print_info_lm(self, bounded, capfd):
        if bounded:
            self.m[0].centre.bmin = 0.5

        self.m.fit(optimizer="lm", bounded=bounded, print_info=True)
        captured = capfd.readouterr()
        assert "Fit info:" in captured.out

    def test_no_print_info(self, capfd):
        self.m.fit(optimizer="lm")  # Default is print_info=False
        captured = capfd.readouterr()
        assert "Fit info:" not in captured.out


class TestFitErrorsAndWarnings:
    def setup_method(self, method):
        np.random.seed(1)
        s = hs.signals.Signal1D(np.random.normal(scale=2, size=10000)).get_histogram()
        s.metadata.Signal.binned = True
        g = hs.model.components1D.Gaussian()
        m = s.create_model()
        m.append(g)
        g.sigma.value = 1
        g.centre.value = 0.5
        g.A.value = 1000
        self.m = m

    @pytest.mark.parametrize("optimizer", ["fmin", "mpfit", "leastsq"])
    def test_deprecated_optimizers(self, optimizer):
        with pytest.warns(
            VisibleDeprecationWarning,
            match=r".* has been deprecated and will be removed",
        ):
            self.m.fit(optimizer=optimizer)

    def test_deprecated_fitter(self):
        with pytest.warns(
            VisibleDeprecationWarning,
            match=r"fitter=.* has been deprecated and will be removed",
        ):
            self.m.fit(fitter="lm")

    def test_wrong_loss_function(self):
        with pytest.raises(ValueError, match="loss_function must be one of"):
            self.m.fit(loss_function="dummy")

    def test_not_support_loss_function(self):
        with pytest.raises(
            NotImplementedError, match=r".* only supports least-squares fitting"
        ):
            self.m.fit(loss_function="ml-poisson", optimizer="lm")

    def test_not_support_bounds(self):
        with pytest.raises(ValueError, match="Bounded optimization is only supported"):
            self.m.fit(optimizer="odr", bounded=True)

    def test_wrong_grad(self):
        with pytest.raises(ValueError, match="`grad` must be one of"):
            self.m.fit(grad="random")

    def test_wrong_fd_scheme(self):
        with pytest.raises(ValueError, match="`fd_scheme` must be one of"):
            self.m.fit(optimizer="L-BFGS-B", grad="auto", fd_scheme="random")

    @pytest.mark.parametrize("some_bounds", [True, False])
    def test_global_optimizer_wrong_bounds(self, some_bounds):
        if some_bounds:
            self.m[0].centre.bmin = 0.5
            self.m[0].centre.bmax = np.inf

        with pytest.raises(ValueError, match="Finite upper and lower bounds"):
            self.m.fit(optimizer="Differential Evolution", bounded=True)

    def test_error_for_ml_poisson(self):
        self.m.signal.set_noise_variance(2.0)
        with pytest.raises(ValueError, match="Weighted fitting is not supported"):
            self.m.fit(optimizer="Nelder-Mead", loss_function="ml-poisson")


class TestCustomOptimization:
    def setup_method(self, method):
        # data that should fit with A=49, centre=5.13, sigma=2.0
        s = hs.signals.Signal1D([1.0, 2, 3, 5, 7, 12, 8, 6, 3, 2, 2])
        self.m = s.create_model()
        self.m.append(hs.model.components1D.Gaussian())

        def sets_second_parameter_to_two(model, parameters, data, weights=None):
            return np.abs(parameters[1] - 2)

        self.fmin = sets_second_parameter_to_two

    def test_custom_function(self):
        self.m.fit(loss_function=self.fmin, optimizer="TNC")
        np.testing.assert_allclose(self.m[0].centre.value, 2.0)

    def test_custom_gradient_function(self):
        from unittest import mock

        gradf = mock.Mock(return_value=[10, 1, 10])
        self.m.fit(loss_function=self.fmin, optimizer="BFGS", grad=gradf)
        assert gradf.called
        assert all([args[0] is self.m for args, kwargs in gradf.call_args_list])


@lazifyTestClass
class TestMultifit:
    def setup_method(self, method):
        s = hs.signals.Signal1D(np.zeros((2, 200)))
        s.axes_manager[-1].offset = 1
        s.data[:] = 2 * s.axes_manager[-1].axis ** (-3)
        m = s.create_model()
        m.append(hs.model.components1D.PowerLaw())
        m[0].A.value = 2
        m[0].r.value = 2
        m.store_current_values()
        m.axes_manager.indices = (1,)
        m[0].r.value = 100
        m[0].A.value = 2
        m.store_current_values()
        m[0].A.free = False
        self.m = m
        m.axes_manager.indices = (0,)
        m[0].A.value = 100

    def test_fetch_only_fixed_false(self):
        # HyperSpy 2.0: remove setting iterpath='serpentine'
        self.m.multifit(fetch_only_fixed=False, iterpath="serpentine", optimizer="trf")
        np.testing.assert_array_almost_equal(self.m[0].r.map["values"], [3.0, 100.0])
        np.testing.assert_array_almost_equal(self.m[0].A.map["values"], [2.0, 2.0])

    def test_fetch_only_fixed_true(self):
        # HyperSpy 2.0: remove setting iterpath='serpentine'
        self.m.multifit(fetch_only_fixed=True, iterpath="serpentine", optimizer="trf")
        np.testing.assert_array_almost_equal(self.m[0].r.map["values"], [3.0, 3.0])
        np.testing.assert_array_almost_equal(self.m[0].A.map["values"], [2.0, 2.0])

    def test_parameter_as_signal_values(self):
        # There are more as_signal tests in test_parameters.py
        rs = self.m[0].r.as_signal(field="values")
        np.testing.assert_allclose(rs.data, np.array([2.0, 100.0]))
        assert rs.get_noise_variance() is None
        # HyperSpy 2.0: remove setting iterpath='serpentine'
        self.m.multifit(fetch_only_fixed=True, iterpath="serpentine")
        rs = self.m[0].r.as_signal(field="values")
        assert rs.get_noise_variance() is not None
        assert isinstance(rs.get_noise_variance(), hs.signals.Signal1D)

    @pytest.mark.parametrize("optimizer", ["lm", "L-BFGS-B"])
    def test_bounded_snapping(self, optimizer):
        m = self.m
        m[0].A.free = True
        m.signal.data *= 2.0
        m[0].A.value = 2.0
        m[0].A.bmin = 3.0
        # HyperSpy 2.0: remove setting iterpath='serpentine'
        m.multifit(optimizer=optimizer, bounded=True, iterpath="serpentine")
        np.testing.assert_allclose(self.m[0].r.map["values"], [3.0, 3.0], rtol=1e-5)
        np.testing.assert_allclose(self.m[0].A.map["values"], [4.0, 4.0], rtol=1e-5)

    @pytest.mark.parametrize("iterpath", ["flyback", "serpentine"])
    def test_iterpaths(self, iterpath):
        self.m.multifit(iterpath=iterpath)

    def test_iterpath_none(self):
        with pytest.warns(
            VisibleDeprecationWarning,
            match="'iterpath' default will change from 'flyback' to 'serpentine'",
        ):
            self.m.multifit()  # iterpath = None by default

        with pytest.warns(
            VisibleDeprecationWarning,
            match="'iterpath' default will change from 'flyback' to 'serpentine'",
        ):
            self.m.multifit(iterpath=None)
