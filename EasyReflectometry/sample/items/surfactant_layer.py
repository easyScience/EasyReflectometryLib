from copy import deepcopy
from typing import Union, List
import yaml

from easyCore.Fitting.Constraints import ObjConstraint
from easyCore.Objects.ObjectClasses import Parameter
from EasyReflectometry.sample.material import Material
from EasyReflectometry.sample.layer import Layer, LayerApm, LAYERAPM_DETAILS
from EasyReflectometry.sample.layers import Layers
from .multilayer import MultiLayer


class SurfactantLayer(MultiLayer):
    """
    A :py:class:`SurfactantLayer` constructs a series of layers representing the head and tail 
    groups of a surfactant. This item allows the definition of a surfactant or lipid using the 
    chemistry of the head and tail regions, additionally this approach will make the application of 
    constraints such as conformal roughness or area per molecule more straight forward.

    More information about the usage of this item is available in the `item library documentation`_

    .. _`item library documentation`: ./item_library.html#surfactantlayer 
    """

    def __init__(self,
                 layer1: LayerApm,
                 layer2: LayerApm,
                 name: str = 'EasySurfactantLayer',
                 interface=None):
        """
        :param head: Head layer object
        :param tail: Tail layer object
        :param name: Name for surfactant layer 
        """
        surfactant = Layers(layer1, layer2, name=name)
        super().__init__(surfactant, name, interface)
        self.layer1 = layer1
        self.layer2 = layer2

        self.interface = interface
        self.type = "Surfactant Layer"

    # Class constructors
    @classmethod
    def default(cls, interface=None) -> "SurfactantLayer":
        """
        Default constructor for a surfactant layer object. The default lipid type is DPPC.

        :return: Surfactant layer object.
        """
        d2o = Material.from_pars(6.36, 0, 'D2O')
        air = Material.from_pars(0, 0, 'Air')
        head = LayerApm.from_pars('C10H18NO8P', 10., d2o, 0.2, 48.2, 3.0, 'DPPC Head')
        tail = LayerApm.from_pars('C32D64', 16, air, 0., 48.2, 3, 'DPPC Tail')
        return cls(tail, head, name='DPPC', interface=interface)

    @classmethod
    def from_pars(cls,
                  layer1_chemical_structure: str,
                  layer1_thickness: float,
                  layer1_solvent: Material,
                  layer1_solvation: float,
                  layer1_area_per_molecule: float,
                  layer1_roughness: float,
                  layer2_chemical_structure: str,
                  layer2_thickness: float,
                  layer2_solvent: Material,
                  layer2_solvation: float,
                  layer2_area_per_molecule: float,
                  layer2_roughness: float,
                  name: str = 'EasySurfactantLayer',
                  interface=None) -> "SurfactantLayer":
        """
        Constructor for the surfactant layer where the parameters are known, layer1 is that 
        which the neutrons interact with first. 
    
        :param layer1_chemical_structure: Chemical formula for first layer
        :param layer1_thickness: Thicknkess of first layer
        :param layer1_solvent: Solvent in first layer
        :param layer1_solvation: Fractional solvation of first layer by :py:attr:`layer1_solvent`
        :param layer1_area_per_molecule: Area per molecule of first layer
        :param layer1_roughness: Roughness of first layer
        :param layer2_chemical_structure: Chemical formula for second layer
        :param layer2_thickness: Thicknkess of second layer
        :param layer2_solvent: Solvent in second layer
        :param layer2_solvation: Fractional solvation of second layer by :py:attr:`layer2_solvent`
        :param layer2_area_per_molecule: Area per molecule of second layer
        :param layer2_roughness: Roughness of second layer
        :param name: Name for surfactant layer 
        """
        layer1 = LayerApm.from_pars(layer1_chemical_structure,
                                    layer1_thickness,
                                    layer1_solvent,
                                    layer1_solvation,
                                    layer1_area_per_molecule,
                                    layer1_roughness,
                                    name=name + ' Layer 1')
        layer2 = LayerApm.from_pars(layer2_chemical_structure,
                                    layer2_thickness,
                                    layer2_solvent,
                                    layer2_solvation,
                                    layer2_area_per_molecule,
                                    layer2_roughness,
                                    name=name + ' Layer 2')
        return cls(layer1, layer2, name, interface)

    @property
    def constrain_apm(self) -> bool:
        """
        :return: if the area per molecule is constrained
        """
        if hasattr(self, 'area_per_molecule'):
            return (self.area_per_molecule.user_constraints['apm1'].enabled and self.area_per_molecule.user_constraints['apm2'].enabled)
        else:
            return False

    @constrain_apm.setter
    def constrain_apm(self, x: bool):
        """
        Set the constraint such that the head and tail layers have the same area per molecule. 

        :param x: Boolean description the presence of the constraint.
        """
        if not hasattr(self, 'area_per_molecule'):
            default_options = deepcopy(LAYERAPM_DETAILS)
            del default_options['area_per_molecule']['value']
            area_per_molecule = Parameter('area_per_molecule', self.layer1.area_per_molecule.raw_value, **default_options['area_per_molecule'])
            self._add_component('area_per_molecule', area_per_molecule)
            self.layer2.area_per_molecule.value = self.layer1.area_per_molecule.raw_value
            apm1 = ObjConstraint(self.layer1.area_per_molecule, '', self.area_per_molecule)
            apm2 = ObjConstraint(self.layer2.area_per_molecule, '', self.area_per_molecule)
            self.area_per_molecule.user_constraints['apm1'] = apm1
            self.area_per_molecule.user_constraints['apm2'] = apm2
        self.area_per_molecule.user_constraints['apm1'].enabled = x
        self.area_per_molecule.user_constraints['apm2'].enabled = x
        self.area_per_molecule.enabled = x

    @property
    def conformal_roughness(self) -> bool:
        """
        :return: is the roughness is the same for both layers.
        """
        if hasattr(self, 'roughness'):
            return (self.roughness.user_constraints['roughness1'].enabled and self.roughness.user_constraints['roughness2'].enabled)
        return False

    @conformal_roughness.setter
    def conformal_roughness(self, x: bool):
        """
        Set the roughness to be the same for both layers.
        """
        if not hasattr(self, 'roughness'):
            default_options = deepcopy(LAYERAPM_DETAILS)
            del default_options['roughness']['value']
            roughness = Parameter('roughness', self.layer1.roughness.raw_value, **default_options['roughness'])
            self._add_component('roughness', roughness)
            self.layer2.roughness.value = self.layer1.roughness.raw_value
            roughness1 = ObjConstraint(self.layer1.roughness, '', self.roughness)
            roughness2 = ObjConstraint(self.layer2.roughness, '', self.roughness)
            self.roughness.user_constraints['roughness1'] = roughness1
            self.roughness.user_constraints['roughness2'] = roughness2
        self.roughness.user_constraints['roughness1'].enabled = x
        self.roughness.user_constraints['roughness2'].enabled = x

    def constrain_solvent_roughness(self, solvent_roughness: Parameter):
        """
        Add the constraint to the solvent roughness. 

        :param solvent_roughness: The solvent roughness parameter.
        """
        if not self.conformal_roughness:
            raise ValueError("Roughness must be conformal to use this function.")
        solvent_roughness.value = self.roughness.value
        rough = ObjConstraint(solvent_roughness, '', self.roughness)
        self.roughness.user_constraints['solvent_roughness'] = rough

    def constain_multiple_contrast(self,
                                   another_contrast: 'SurfactantLayer',
                                   layer1_thickness: bool = True,
                                   layer2_thickness: bool = True,
                                   layer1_area_per_molecule: bool = True,
                                   layer2_area_per_molecule: bool = True,
                                   layer1_fraction: bool = True,
                                   layer2_fraction: bool = True):
        """
        Constrain structural parameters between surfactant layer objects.

        :param another_contrast: The surfactant layer to constrain
        """
        if layer1_thickness:
            layer1_thickness_constraint = ObjConstraint(self.layer1.thickness, '',
                                                      another_contrast.layer1.thickness)
            another_contrast.layer1.thickness.user_constraints[
                f'{another_contrast.name}'] = layer1_thickness_constraint
        if layer2_thickness:
            layer2_thickness_constraint = ObjConstraint(self.layer2.thickness, '',
                                                      another_contrast.layer2.thickness)
            another_contrast.layer2.thickness.user_constraints[
                f'{another_contrast.name}'] = layer2_thickness_constraint
        if layer1_area_per_molecule:
            layer1_area_per_molecule_constraint = ObjConstraint(
                self.layer1.area_per_molecule, '',
                another_contrast.layer1.area_per_molecule)
            another_contrast.layer1.area_per_molecule.user_constraints[
                f'{another_contrast.name}'] = layer1_area_per_molecule_constraint
        if layer2_area_per_molecule:
            layer2_area_per_molecule_constraint = ObjConstraint(
                self.layer2.area_per_molecule, '',
                another_contrast.layer2.area_per_molecule)
            another_contrast.layer2.area_per_molecule.user_constraints[
                f'{another_contrast.name}'] = layer2_area_per_molecule_constraint
        if layer1_fraction:
            layer1_fraction_constraint = ObjConstraint(
                self.layer1.material.fraction, '',
                another_contrast.layer1.material.fraction)
            another_contrast.layer1.material.fraction.user_constraints[
                f'{another_contrast.name}'] = layer1_fraction_constraint
        if layer2_fraction:
            layer2_fraction_constraint = ObjConstraint(
                self.layer2.material.fraction, '',
                another_contrast.layer2.material.fraction)
            another_contrast.layer2.material.fraction.user_constraints[
                f'{another_contrast.name}'] = layer2_fraction_constraint

    @property
    def _dict_repr(self) -> dict:
        """
        A simplified dict representation. 
        
        :return: Simple dictionary
        """
        return {
            'layer1': self.layers[0]._dict_repr,
            'layer2': self.layers[1]._dict_repr,
            'area per molecule constrained': self.constrain_apm,
            'conformal roughness': self.conformal_roughness
        }
