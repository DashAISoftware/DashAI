from dataclasses import dataclass, field

from datasets import Value, ClassLabel

@dataclass
class Integer(Value):
    size: int = 64
    unsigned: bool = False
    dtype: str = field(default="", init=False)

    def __post_init__(self):
        if self.size not in {8, 16, 32, 64}:
            self.size = 64
        
        self.dtype= f"uint{self.size}" if self.unsigned else f"int{self.size}"
        super().__post_init__()

    @staticmethod
    def from_value(value: Value):
        if not value.dtype.startswith(("int", "uint")):
            raise ValueError(f"dtype {value.dtype} is not an integer")
        
        unsigned: bool = value.dtype.startswith("uint")
        size: int = int(value.dtype[4:]) if unsigned else int(value.dtype[3:])
        
        return Integer(size=size, unsigned=unsigned)

            



