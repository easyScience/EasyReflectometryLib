from __future__ import annotations

from copy import deepcopy

from easyCore import np
from easyCore.Fitting.Constraints import FunctionalConstraint
from easyCore.Objects.ObjectClasses import Parameter

from EasyReflectometry.special.calculations import apm_to_sld
from EasyReflectometry.special.calculations import neutron_scattering_length

from ..materials.material import Material
from ..materials.material_solvated import MaterialSolvated
from .layer import Layer

LAYERAPM_DETAILS = {
    'thickness': {
        'description': 'The thickness of the layer in angstroms',
        'value': 10.0,
        'units': 'angstrom',
        'min': 0,
        'max': np.inf,
        'fixed': True,
    },
    'molecular_formula': 'C10H18NO8P',
    'roughness': {
        'description': 'Conformal roughness',
        'value': 3.0,
        'units': 'angstrom',
        'min': 0,
        'max': np.inf,
        'fixed': True,
    },
    'area_per_molecule': {
        'description': 'Surface coverage',
        'value': 48.2,
        'units': 'angstrom ** 2',
        'min': 0,
        'max': np.inf,
        'fixed': True,
    },
    'solvation': {
        'description': 'Fraction of solvent present',
        'value': 0.2,
        'units': 'dimensionless',
        'min': 0,
        'max': 1,
        'fixed': True,
    },
    'sl': {
        'description': 'The real scattering length for a chemical formula in angstrom.',
        'url': 'https://www.ncnr.nist.gov/resources/activation/',
        'value': 4.186,
        'units': 'angstrom',
        'min': -np.Inf,
        'max': np.Inf,
        'fixed': True,
    },
    'isl': {
        'description': 'The real scattering length for a chemical formula in angstrom.',
        'url': 'https://www.ncnr.nist.gov/resources/activation/',
        'value': 0.0,
        'units': 'angstrom',
        'min': -np.Inf,
        'max': np.Inf,
        'fixed': True,
    },
}


class LayerApm(Layer):
    """
    The :py:class:`LayerApm` class allows a layer to be defined in terms of some
    molecular formula (chemical structure) an area per molecule, and a solvent.

    """

    # Added in __init__
    _area_per_molecule: Parameter
    _scattering_length_real: Parameter
    _scattering_length_imag: Parameter

    # Other typer than in __init__.super()
    material: MaterialSolvated

    def __init__(
        self,
        molecular_formula: str,
        thickness: Parameter,
        solvent: Material,
        solvation: Parameter,
        area_per_molecule: Parameter,
        roughness: Parameter,
        name: str = 'EasyLayerApm',
        interface=None,
    ):
        """
        :param molecular_formula: Formula for the molecules in the layer
        :param thickness: Layer thickness
        :param solvent: Solvent containing the molecules
        :param solvation: Fraction of solvent present
        :param area_per_molecule: Area per molecule in the layer
        :param roughness: Upper roughness on the layer
        :param name: Identifier, defaults to :py:attr:`EasyLayerApm`
        :param interface: Interface object, defaults to :py:attr:`None`
        """
        scattering_length = neutron_scattering_length(molecular_formula)
        default_options = deepcopy(LAYERAPM_DETAILS)
        del default_options['sl']['value']
        del default_options['isl']['value']
        scattering_length_real = Parameter('scattering_length_real', scattering_length.real, **default_options['sl'])
        scattering_length_imag = Parameter('scattering_length_imag', scattering_length.imag, **default_options['isl'])
        sld = apm_to_sld(scattering_length_real.raw_value, thickness.raw_value, area_per_molecule.raw_value)
        isld = apm_to_sld(scattering_length_imag.raw_value, thickness.raw_value, area_per_molecule.raw_value)

        material = Material.from_pars(sld, isld, name=molecular_formula, interface=interface)

        constraint = FunctionalConstraint(
            dependent_obj=material.sld,
            func=apm_to_sld,
            independent_objs=[scattering_length_real, thickness, area_per_molecule],
        )
        thickness.user_constraints['apm'] = constraint
        area_per_molecule.user_constraints['apm'] = constraint
        scattering_length_real.user_constraints['apm'] = constraint

        iconstraint = FunctionalConstraint(
            dependent_obj=material.isld,
            func=apm_to_sld,
            independent_objs=[scattering_length_imag, thickness, area_per_molecule],
        )
        thickness.user_constraints['iapm'] = iconstraint
        area_per_molecule.user_constraints['iapm'] = iconstraint
        scattering_length_imag.user_constraints['iapm'] = iconstraint

        solvated_material = MaterialSolvated(
            material=material,
            solvent=solvent,
            solvation=solvation,
            name=molecular_formula + '/' + solvent.name,
            interface=interface,
        )
        super().__init__(
            material=solvated_material,
            thickness=thickness,
            roughness=roughness,
            name=name,
            interface=interface,
        )
        self._add_component('_scattering_length_real', scattering_length_real)
        self._add_component('_scattering_length_imag', scattering_length_imag)
        self._add_component('_area_per_molecule', area_per_molecule)
        self._molecular_formula = molecular_formula
        self.interface = interface

    @property
    def area_per_molecule(self) -> Parameter:
        """
        :return: Area per molecule
        """
        return self._area_per_molecule

    @property
    def solvent(self) -> Material:
        """
        :return: Solvent material
        """
        return self.material.solvent

    @solvent.setter
    def solvent(self, new_solvent: Material) -> None:
        """
        :param new_solvent: New solvent material.
        """
        self.material.solvent = new_solvent

    @property
    def solvation(self) -> Parameter:
        """
        :return: Solvation fraction.
        """
        return self.material.fraction

    @solvation.setter
    def solvation(self, solvation: float) -> None:
        """
        :param solvation: Fraction of solvent.
        """
        self.material.solvation = solvation

    # Class constructors
    @classmethod
    def default(cls, interface=None) -> LayerApm:
        """
        Default constructor for layer defined from chemical structure
        and area per molecule.

        :param interface: Interface object, defaults to :py:attr:`None`
        :return: Layer with correct structure
        """
        area_per_molecule = Parameter('area_per_molecule', **LAYERAPM_DETAILS['area_per_molecule'])
        thickness = Parameter('thickness', **LAYERAPM_DETAILS['thickness'])
        roughness = Parameter('roughness', **LAYERAPM_DETAILS['roughness'])
        solvent = Material.from_pars(6.36, 0, 'D2O', interface=interface)
        solvation = Parameter('solvation', **LAYERAPM_DETAILS['solvation'])
        return cls(
            LAYERAPM_DETAILS['molecular_formula'],
            thickness,
            solvent,
            solvation,
            area_per_molecule,
            roughness,
            interface=interface,
        )

    @classmethod
    def from_pars(
        cls,
        molecular_formula: str,
        thickness: float,
        solvent: Material,
        solvation: float,
        area_per_molecule: float,
        roughness: float,
        name: str = 'EasyLayerApm',
        interface=None,
    ) -> LayerApm:
        """
        Constructor for a layer described with the area per molecule,
        where the parameters are known.

        :param molecular_formula: Chemical formula for the material in the layer
        :param thickness: Layer thickness
        :param solvent: Solvent present in material
        :param solvation: Fraction of solvent present
        :param area_per_molecule: Area per molecule for the chemical material
        :param roughness: Upper roughness on the layer
        :param name: Identifier, defaults to :py:attr:`EasyLayerApm`
        :param interface: Interface object, defaults to :py:attr:`None`
        :return: Layer with correct structure
        """
        default_options = deepcopy(LAYERAPM_DETAILS)
        del default_options['area_per_molecule']['value']
        del default_options['thickness']['value']
        del default_options['roughness']['value']
        del default_options['solvation']['value']
        del default_options['molecular_formula']

        area_per_molecule = Parameter('area_per_molecule', area_per_molecule, **default_options['area_per_molecule'])
        thickness = Parameter('thickness', thickness, **default_options['thickness'])
        roughness = Parameter('roughness', roughness, **default_options['roughness'])
        solvation = Parameter('solvation', solvation, **default_options['solvation'])

        return cls(
            molecular_formula,
            thickness,
            solvent,
            solvation,
            area_per_molecule,
            roughness,
            name=name,
            interface=interface,
        )

    @property
    def molecular_formula(self) -> str:
        """
        :return: Molecular formula
        """
        return self._molecular_formula

    @molecular_formula.setter
    def molecular_formula(self, formula_string: str) -> None:
        """
        :param formula_string: String that defines the molecular formula.
        """
        self._molecular_formula = formula_string
        scattering_length = neutron_scattering_length(formula_string)
        self._scattering_length_real.value = scattering_length.real
        self._scattering_length_imag.value = scattering_length.imag
        self.material.name = formula_string + '/' + self.material._material_b.name

    @property
    def _dict_repr(self) -> dict[str, str]:
        """
        Dictionary representation of the :py:class:`LayerApm` object.

        :return: Simple dictionary
        """
        layerapm_dict = super()._dict_repr
        layerapm_dict['molecular_formula'] = self._molecular_formula
        layerapm_dict['area_per_molecule'] = f'{self._area_per_molecule.raw_value:.1f} ' f'{self._area_per_molecule.unit}'
        return layerapm_dict

    def as_dict(self, skip: list = None) -> dict[str, str]:
        """
        Custom as_dict method to skip necessary things.

        :return: Cleaned dictionary.
        """
        if skip is None:
            skip = []
        this_dict = super().as_dict(skip=skip)
        del this_dict['material']
        del this_dict['_scattering_length_real']
        del this_dict['_scattering_length_imag']
        return this_dict