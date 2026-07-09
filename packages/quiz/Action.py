import numpy as np
class Action():
    def __init__(self, magnitude):
        self._name = "未定義"
        self._magnitude = magnitude
        self._si_magnitude = magnitude

    def __str__(self):
        return f"{self._name} {self._magnitude} {self._unit}"
    
    def __repr__(self):
        return self.__str__()
    

    def __add__(self, other):
        # 他のオブジェクトと型が同一かを確認
        
        if type(other) is type(self):
            #自身と同じ型のオブジェクトを新規作成
            newinstance = type(self)(self._magnitude + other._magnitude)
            newinstance._si_magnitude = float(self._si_magnitude + other._si_magnitude)
            return newinstance
        
        raise TypeError(f"{type(self)}は{type(self)}とのみ加算できます。{type(other)}はサポートされていません。")

    @property
    def name(self):
        return self._name

    @property
    def magnitude(self):
        return self._magnitude
    
    @property
    def absolute_magnitude(self):
        return abs(self._magnitude)
    
    @property
    def si_magnitude(self):
        return self._si_magnitude
    
    @property
    def unit(self):
        return self._unit

class TensileLoad(Action):
    def __init__(self, magnitude):
        super().__init__(magnitude)
        self._name = "引張荷重"
        self._unit = "kN"    
        self._si_magnitude = magnitude * 1e3

class StaticLoad(Action):
    def __init__(self, magnitude):
        super().__init__(magnitude)
        self._name = "静荷重"
        self._unit = "kN"    
        self._si_magnitude = magnitude * 1e3

class RepeatedLoad(Action):
    def __init__(self, magnitude):
        super().__init__(magnitude)
        self._name = "片振荷重"
        self._unit = "kN"    
        self._si_magnitude = magnitude * 1e3

class AlternatingLoad(Action):
    def __init__(self, magnitude):
        super().__init__(magnitude)
        self._name = "両振荷重"
        self._unit = "kN"    
        self._si_magnitude = magnitude * 1e3

class ImpactLoad(Action):
    def __init__(self, magnitude):
        super().__init__(magnitude)
        self._name = "衝撃荷重"
        self._unit = "kN"    
        self._si_magnitude = magnitude * 1e3

class CompressiveLoad(Action):
    def __init__(self, magnitude):
        super().__init__(magnitude)
        self._name = "圧縮荷重"
        self._unit = "kN"
        self._magnitude = -magnitude
        self._si_magnitude = -magnitude * 1e3

    def __str__(self):
        return f"{self._name} {-self._magnitude} {self._unit}"

class ShearLoad(Action):
    def __init__(self, magnitude):
        super().__init__(magnitude)
        self._name = "せん断荷重"
        self._unit = "kN"    
        self._si_magnitude = magnitude * 1e3

class TwistingMoment(Action):
    def __init__(self, magnitude):
        super().__init__(magnitude)
        self._name = "ねじりモーメント"
        self._unit = "N・m"    
        self._si_magnitude = magnitude

class Couple(Action):
    def __init__(self, magnitude):
        super().__init__(magnitude)
        self._name = "偶力"
        self._unit = "N"    
        self._si_magnitude = magnitude


"""ここから梁用作用"""

class ConcentratedLoad(Action):
    def __init__(self, magnitude, position=None, angle=None):
        super().__init__(magnitude)
        self._name = "集中荷重"
        self._unit = "kN"    
        import sympy as sp
        self._position = sp.nsimplify(position, tolerance=1e-10) if isinstance(position, (float, np.float64, np.float32)) else position
        self._angle = angle
        self._si_magnitude = magnitude * 1e3
    
    @property
    def position(self):
        return self._position

    @property
    def angle(self):
        return self._angle

class ConcentratedMoment(Action):
    def __init__(self, magnitude, position=None, direction="CCW"):
        super().__init__(magnitude)
        self._name = "集中モーメント"
        self._unit = "kNm"    
        import sympy as sp
        self._position = sp.nsimplify(position, tolerance=1e-10) if isinstance(position, (float, np.float64, np.float32)) else position
        self._direction = direction
        self._si_magnitude = magnitude * 1e3
    
    @property
    def position(self):
        return self._position

    @property
    def direction(self):
        return self._direction


class DistributedLoad(Action):
    """
    単位長さあたりの荷重
    function: 荷重分布関数 (文字列) 例 "1", "x", "x**2", "x - L"などxとLを使った式
    base_magnitude: 荷重分布関数の基準値 (kN/m)　この基準値にfunctionをかけたものが実際の分布荷重になる 
    total_length: 荷重が作用する長さ (mm)
    """

    def __init__(self, base_magnitude, position_range=(0, 1), total_length=1, function="1"):
        super().__init__(base_magnitude)

        self._name = "分布荷重"
        self._unit = "kN/m"  

        self._base_magnitude = base_magnitude
        self._total_length = total_length
        self._si_total_length = total_length * 1e-3
        self._function = function
        import sympy as sp
        new_range = []
        for p in position_range:
            if isinstance(p, (float, np.float64, np.float32)):
                new_range.append(sp.nsimplify(p, tolerance=1e-10))
            else:
                new_range.append(p)
        self._position_range = tuple(new_range)

        self._magnitude = None  
        self._magnitude_eq = None
        self._position = None
        self._position_eq = None

    
    @property
    def position(self):
        if self._position is None:
            self.equivalent_concentrated_load()
        return float(self._position)

    @property
    def position_eq(self):
        if self._position_eq is None:
            self.equivalent_concentrated_load()
        return self._position_eq

    @property
    def base_magnitude(self):
        return float(self._base_magnitude)

    @property
    def si_base_magnitude(self):
        return float(self._base_magnitude) * 1e3

    @property
    def magnitude(self):
        if self._magnitude is None:
            self.equivalent_concentrated_load()
        return float(self._magnitude)

    @property
    def si_magnitude(self):
        if self._magnitude is None:
            self.equivalent_concentrated_load()
        return float(self._magnitude) * 1e3

    @property
    def magnitude_eq(self):
        if self._magnitude_eq is None:
            self.equivalent_concentrated_load()
        return self._magnitude_eq

    @property
    def angle(self):
        return self._angle
    
    @property
    def function(self):
        return self._function
    
    def equivalent_concentrated_load_of_FBD(self, start_eq_str, end_eq_str, act_x = 0.5):
        """
        FBD上での等価な集中荷重を計算するメソッド
        start_x: FBD上での分布荷重の開始位置 (mm)
        end_x: FBD上での分布荷重の終了位置 (mm)
        """
        import sympy as sp
        w_0, x, L = sp.symbols(f'w_0 x L')
        orig_start = sp.sympify(start_eq_str)
        orig_end = sp.sympify(end_eq_str)
        
        start_symbol = orig_start
        end_symbol = orig_end

        def to_rational(val):
            # 0.1刻み程度ならRationalに変換
            if isinstance(val, (float, np.float64, np.float32)):
                return sp.nsimplify(val, tolerance=1e-10)
            return sp.sympify(val)

        pos0 = to_rational(self._position_range[0])
        pos1 = to_rational(self._position_range[1])
        act_x_sym = to_rational(act_x)

        if start_eq_str == "0":
            if self._position_range[0] > 0:
                start_symbol = pos0 * L

            if act_x > self._position_range[1]:
                end_symbol = pos1 * L
            if act_x < self._position_range[0]:
                start_symbol = end_symbol

        if end_eq_str == "L": 
            if self._position_range[1] < 1:
                end_symbol = pos1 * L

            if act_x < self._position_range[0]:
                start_symbol = pos0 * L
            if act_x > self._position_range[1]:
                start_symbol = end_symbol

        w = w_0 * sp.sympify(self._function)

        magnitude_eq = sp.nsimplify(sp.simplify(w.integrate((x, start_symbol, end_symbol))), tolerance=1e-10)

        # 分布荷重の作用点を計算
        moment_eq = w * x
        moment = moment_eq.integrate((x, start_symbol, end_symbol))
        position_eq = sp.nsimplify(sp.simplify(moment / magnitude_eq - orig_start), tolerance=1e-10)

        #nanの場合は0を返す
        if position_eq.has(sp.nan):
            position_eq = sp.sympify(0)

        return magnitude_eq, position_eq

    # 等価な集中荷重を計算するメソッド
    def equivalent_concentrated_load(self):
        
        # 分布荷重の総荷重を計算
        import sympy as sp
        w_0, x, L = sp.symbols(f'w_0 x L')
        w = w_0 * sp.sympify(self._function)
        subs = {w_0: self.base_magnitude/1e3, L: self._total_length}
        #print(subs)
        start = self._position_range[0]
        end = self._position_range[1]

        self._magnitude_eq = sp.nsimplify(sp.simplify(w.integrate((x, start*L, end*L))), tolerance=1e-10)
        self._magnitude = self._magnitude_eq.evalf(subs=subs)

        # 分布荷重の作用点を計算
        moment_eq = w * x   
        moment = moment_eq.integrate((x, start*L, end*L))
        self._position_eq = moment / self.magnitude_eq

        #self._position_eqを分数表記に変換
        self._position = self._position_eq.evalf(subs=subs) / self._total_length
        self._position_eq = sp.nsimplify(L*self._position, tolerance=1e-10)

        #print(f"分布荷重の作用位置のlengthシンボル: {self._position_eq}, value: {self._position}, moment: {moment}, magnitude_eq: {self.magnitude_eq}")
