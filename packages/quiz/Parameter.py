import numpy as np

class Parameter():
    def __init__(self, magnitude):
        self._name = "未定義"
        self._negative_name = None
        self._magnitude = magnitude
        self._si_magnitude = magnitude

    def __str__(self):
        if self._magnitude < 0 and self._negative_name is not None:
            return f"{self._negative_name} {abs(self._magnitude)} {self._unit}"
        else:
            return f"{self._name} {self._magnitude} {self._unit}"
    
    def __repr__(self):
        return self.__str__()
    
    @property
    def magnitude(self):
        return self._magnitude
    
    @property
    def magnitude_with_unit(self):
        return f"{self._magnitude} {self._unit}"
    
    @property
    def si_magnitude(self):
        return self._si_magnitude

"""
寸法関連
"""
class Length(Parameter):
    def __init__(self, magnitude):
        super().__init__(magnitude)
        self._name = "長さ"
        self._unit = "m"    

class Elongation(Parameter):
    def __init__(self, magnitude):
        super().__init__(magnitude)
        self._name = "伸び"
        self._negative_name = "縮み"
        self._unit = "mm"
        self._si_magnitude = magnitude * 1e-3

class Thickness(Parameter):
    def __init__(self, magnitude):
        super().__init__(magnitude)
        self._name = "板厚"
        self._unit = "mm"
        self._si_magnitude = magnitude * 1e-3

class Width(Parameter):
    def __init__(self, magnitude):
        super().__init__(magnitude)
        self._name = "板幅"
        self._unit = "mm"
        self._si_magnitude = magnitude * 1e-3

"""
荷重関連
"""

class Load(Parameter):
    def __init__(self, magnitude):
        super().__init__(magnitude)
        self._name = "荷重"
        self._unit = "kN"
        self._si_magnitude = magnitude * 1e3

"""
応力関連
"""
class Stress(Parameter):
    def __init__(self, magnitude):
        super().__init__(magnitude)
        self._name = "応力"
        self._unit = "MPa"
        self._si_magnitude = magnitude * 1e6

class AllowableStress(Parameter):
    def __init__(self, magnitude):
        super().__init__(magnitude)
        self._name = "許容引張応力"
        self._unit = "MPa"
        self._si_magnitude = magnitude * 1e6

class ShearStress(Parameter):
    def __init__(self, magnitude):
        super().__init__(magnitude)
        self._name = "せん断応力"
        self._unit = "MPa"
        self._si_magnitude = magnitude * 1e6

class AngleOfTwist(Parameter):
    def __init__(self, magnitude):
        super().__init__(magnitude)
        self._name = "ねじれ角"
        self._unit = "rad"
        self._si_magnitude = magnitude

class PolarMomentOfInertia(Parameter):
    def __init__(self, magnitude):
        super().__init__(magnitude)
        self._name = "断面二次極モーメント"
        self._unit = "mm⁴"
        self._si_magnitude = magnitude * 1e-12

class AllowableShearStress(Parameter):
    def __init__(self, magnitude):
        super().__init__(magnitude)
        self._name = "許容せん断応力"
        self._unit = "MPa"
        self._si_magnitude = magnitude * 1e6


"""
ひずみ関連
"""

class Strain(Parameter):
    def __init__(self, magnitude):
        super().__init__(magnitude)
        self._name = "ひずみ"
        self._unit = "×10⁻⁶"
        self._si_magnitude = magnitude * 1e-6

class AxialStrain(Parameter):
    def __init__(self, magnitude):
        super().__init__(magnitude)
        self._name = "縦ひずみ"
        self._unit = "×10⁻⁶"
        self._si_magnitude = magnitude * 1e-6

class ShearStrain(Parameter):
    def __init__(self, magnitude):
        super().__init__(magnitude)
        self._name = "せん断ひずみ"
        self._unit = "×10⁻⁶"
        self._si_magnitude = magnitude * 1e-6

class TranverseStrain(Parameter):
    def __init__(self, magnitude):
        super().__init__(magnitude)
        self._name = "横ひずみ"
        self._unit = "×10⁻⁶"
        self._si_magnitude = magnitude * 1e-6
        

class AllowableStrain(Parameter):
    def __init__(self, magnitude):
        super().__init__(magnitude)
        self._name = "許容ひずみ"
        self._unit = "×10⁻²"
        self._si_magnitude = magnitude * 1e-2

"""
温度
"""
class Temperature(Parameter):
    def __init__(self, magnitude):
        super().__init__(magnitude)
        self._name = "温度変化"
        self._unit = "℃"
        self._si_magnitude = magnitude

"""
回転数
"""
class RevolutionsPerMinute(Parameter):
    def __init__(self, magnitude):
        super().__init__(magnitude)
        self._name = "回転数"
        self._unit = "rpm"
        self._si_magnitude = magnitude * (2 * np.pi / 60)

