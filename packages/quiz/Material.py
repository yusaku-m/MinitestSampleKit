from . import SafetyFactor 


class Material():
    def __init__(self):
        self._name = ""
        self._density = 0
        self._young_modulus = 0
        self._poisson_ratio = 0
        self._shear_modulus = 0
        self._yield_strength = 0
        self._tensile_strength = 0
        self._compressive_strength = 0
        self._shear_strength = 0
        self._thermal_expansion = 0
        self._safety_factor = None

    def __str__(self):
        return self.name
    
    def __repr__(self):
        return self.__str__()
    
    @property
    def name(self):
        return self._name
    
    @property
    def density(self):
        return self._density
    
    @property
    def young_modulus(self):
        return self._young_modulus

    @property
    def young_modulus_with_unit(self):
        return f"{self._young_modulus/1e9:4g} GPa"
 
    @property
    def poisson_ratio(self):
        return self._poisson_ratio
    
    @property
    def poisson_ratio_with_unit(self):
        return f"{self._poisson_ratio:4g}"
        
    @property
    def shear_modulus(self):
        if self._shear_modulus == 0:
            self._shear_modulus = self._young_modulus / (2 * (1 + self._poisson_ratio))
        return self._shear_modulus
    
    @property
    def yield_strength(self):
        return self._yield_strength
    
    @property
    def tensile_strength(self):
        return self._tensile_strength
    
    @property
    def tensile_strength_with_unit(self):
        return f"{self._tensile_strength/1e6:4g} MPa"
    
    @property
    def compressive_strength(self):
        return self._compressive_strength
    
    @property
    def shear_strength(self):
        return self._shear_strength

    @property
    def shear_strength_with_unit(self):
        return f"{self._shear_strength/1e6:4g} MPa"
    
    @property
    def thermal_expansion(self):
        return self._thermal_expansion
    
    @property
    def safety_factor(self):
        return self._safety_factor
    
    
class Steel(Material):
    def __init__(self):
        super().__init__()
        self._name = "軟鋼"
        self._density = 7860
        self._young_modulus = 206e9
        self._poisson_ratio = 0.3
        self._yield_strength = 250e6
        self._tensile_strength = 392e6
        self._compressive_strength = 250e6
        self._shear_strength = 280e6
        self._thermal_expansion = 1.12e-5
        self._safety_factor = SafetyFactor.Steel()


class CastIron(Material):
    def __init__(self):
        super().__init__()
        self._name = "鋳鉄"
        self._density = 7200
        self._young_modulus = 98e9
        self._poisson_ratio = 0.3
        self._yield_strength = 196e6
        self._tensile_strength = 196e6
        self._compressive_strength = 721e6
        self._shear_strength = 300e6
        self._thermal_expansion = 10e-6
        self._safety_factor = SafetyFactor.CastIron()

class CastSteel(Material):
    def __init__(self):
        super().__init__()
        self._name = "鋳鋼"
        self._density = 7960
        self._young_modulus = 206e9
        self._poisson_ratio = 0.3
        self._yield_strength = 200e6
        self._tensile_strength = 588e6
        self._shear_strength = 300e6
        self._thermal_expansion = 0.99e-5
        self._safety_factor = SafetyFactor.CastSteel()

class Aluminum(Material):
    def __init__(self):
        super().__init__()
        self._name = "アルミ"
        self._density = 2800
        self._young_modulus = 69e9
        self._poisson_ratio = 0.33
        self._yield_strength = 50e6
        self._tensile_strength = 294e6
        self._compressive_strength = 190e6
        self._shear_strength = 150e6
        self._thermal_expansion = 2.29e-5
        self._safety_factor = SafetyFactor.otherMetal()

class Copper(Material):
    def __init__(self):
        super().__init__()
        self._name = "銅"
        self._density = 8650
        self._young_modulus = 126e9
        self._poisson_ratio = 0.33
        self._yield_strength = 70e6
        self._tensile_strength = 314e6
        self._compressive_strength = 204e6
        self._shear_strength = 170e6
        self._thermal_expansion = 1.67e-5
        self._safety_factor = SafetyFactor.otherMetal()

class Concrete(Material):
    def __init__(self):
        super().__init__()
        self._name = "コンクリート"
        self._density = 2400
        self._young_modulus = 20e9
        self._poisson_ratio = 0.2
        self._yield_strength = 0
        self._tensile_strength = 2e6
        self._compressive_strength = 30e6
        self._shear_strength = 4e6
        self._thermal_expansion = 0.92e-5
        self._safety_factor = SafetyFactor.Stone()

class Wood(Material):
    def __init__(self):
        super().__init__()
        self._name = "木"
        self._young_modulus = 10e9
        self._poisson_ratio = 0.4
        self._tensile_strength = 118e6
        self._compressive_strength = 54e6
        self._shear_strength = 7e6
        self._thermal_expansion = 4e-6
        self._density = 700
        self._safety_factor = SafetyFactor.Wood()

class PET(Material):
    def __init__(self):
        super().__init__()
        self._name = "PET"
        self._density = 1350
        self._young_modulus = 3.5e9
        self._poisson_ratio = 0.21
        self._yield_strength = 50e6
        self._tensile_strength = 90e6
        self._compressive_strength = 110e6
        self._shear_strength = 65e6
        self._thermal_expansion = 65e-6
        self._safety_factor = None # No safety factor provided in previous version, keeping it None or adding if needed.
