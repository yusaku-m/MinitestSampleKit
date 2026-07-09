from .Action import StaticLoad, RepeatedLoad, AlternatingLoad, ImpactLoad

class SafetyFactor():
    def __init__(self):
        self._name = ""
        self._static = None
        self._repeat = None
        self._alternate = None
        self._impact = None
    
    @property
    def static(self):
        return self._static
    
    @property
    def repeat(self):
        return self._repeat
    
    @property
    def alternate(self):
        return self._alternate
    
    @property
    def impact(self):
        return self._impact
    
    def magnitude(self, action):
        if isinstance(action, StaticLoad):
            return self._static
        elif isinstance(action, RepeatedLoad):
            return self._repeat
        elif isinstance(action, AlternatingLoad):
            return self._alternate
        elif isinstance(action, ImpactLoad):
            return self._impact
        else:
            raise ValueError("Invalid action type")

class CastIron(SafetyFactor):
    def __init__(self):
        self._name = "鋳鉄"
        self._static = 4
        self._repeat = 6
        self._alternate = 10
        self._impact = 15

class Steel(SafetyFactor):
    def __init__(self):
        self._name = "軟鋼"
        self._static = 3
        self._repeat = 5
        self._alternate = 8
        self._impact = 12

class CastSteel(SafetyFactor):
    def __init__(self):
        self._name = "鋳鋼"
        self._static = 3
        self._repeat = 5
        self._alternate = 8
        self._impact = 15

class otherMetal(SafetyFactor):
    def __init__(self):
        self._name = "その他金属"
        self._static = 4
        self._repeat = 7
        self._alternate = 9
        self._impact = 15

class Wood(SafetyFactor):
    def __init__(self):
        self._name = "木材"
        self._static = 7
        self._repeat = 10
        self._alternate = 15
        self._impact = 20

class Stone(SafetyFactor):
    def __init__(self):
        super().__init__()
        self._name = "石材"
        self._static = 20
        self._repeat = 30