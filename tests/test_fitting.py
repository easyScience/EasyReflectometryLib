__author__ = 'github.com/arm61'

import os
import unittest

import EasyReflectometry
from EasyReflectometry.calculators import CalculatorFactory
from EasyReflectometry.data import load
from EasyReflectometry.experiment.model import Model
from EasyReflectometry.fitting import Fitter
from EasyReflectometry.sample import Layer
from EasyReflectometry.sample import Material
from EasyReflectometry.sample import Sample


class TestFitting(unittest.TestCase):
    def test_fitting(self):
        fpath = os.path.join(
            os.path.dirname(os.path.dirname(EasyReflectometry.__file__)),
            'tests/_static/example.ort',
        )
        data = load(fpath)
        si = Material.from_pars(2.07, 0, 'Si')
        sio2 = Material.from_pars(3.47, 0, 'SiO2')
        film = Material.from_pars(2.0, 0, 'Film')
        d2o = Material.from_pars(6.36, 0, 'D2O')
        si_layer = Layer.from_pars(si, 0, 0, 'Si layer')
        sio2_layer = Layer.from_pars(sio2, 30, 3, 'SiO2 layer')
        film_layer = Layer.from_pars(film, 250, 3, 'Film Layer')
        superphase = Layer.from_pars(d2o, 0, 3, 'D2O Subphase')
        sample = Sample.from_pars(
            si_layer,
            sio2_layer,
            film_layer,
            superphase,
            name='Film Structure',
        )
        model = Model.from_pars(sample, 1, 1e-6, 0.02, 'Film Model')
        # Thicknesses
        sio2_layer.thickness.bounds = (15, 50)
        film_layer.thickness.bounds = (200, 300)
        # Roughnesses
        sio2_layer.roughness.bounds = (1, 15)
        film_layer.roughness.bounds = (1, 15)
        superphase.roughness.bounds = (1, 15)
        # Scattering length density
        film.sld.bounds = (0.1, 3)
        # Background
        model.background.bounds = (1e-7, 1e-5)
        # Scale
        model.scale.bounds = (0.5, 1.5)
        interface = CalculatorFactory()
        model.interface = interface
        fitter = Fitter(model)
        analysed = fitter.fit(data)
        assert 'R_0_model' in analysed.keys()
        assert 'SLD_0' in analysed.keys()
