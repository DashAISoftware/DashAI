from dataclasses import dataclass

from datasets import Value

from DashAI.back.types.dashai_value import DashAIValue


@dataclass
class Integer(DashAIValue):
    size: int = 64
    unsigned: bool = False

    def __post_init__(self):
        if self.size not in {8, 16, 32, 64}:
            raise ValueError(
                f"Integer size must be 8, 16, 32 or 64, but {self.size} \
                    was given."
            )

        self.dtype = f"uint{self.size}" if self.unsigned else f"int{self.size}"
        super().__post_init__()

    @staticmethod
    def from_value(value: Value):
        if not value.dtype.startswith(("int", "uint")):
            raise ValueError(f"dtype {value.dtype} is not an integer")

        unsigned: bool = value.dtype.startswith("uint")
        size: int = int(value.dtype[4:]) if unsigned else int(value.dtype[3:])

        return Integer(size=size, unsigned=unsigned)


@dataclass
class Float(DashAIValue):
    size: int = 64

    def __post_init__(self):
        if self.size not in {16, 32, 64}:
            raise ValueError(
                f"Float size must be 16, 32 or 64, but {self.size} was given"
            )

        self.dtype = f"float{self.size}"
        super().__post_init__()

    @staticmethod
    def from_value(value: Value):
        if not value.dtype.startswith("float"):
            raise ValueError(f"dtype {value.dtype} is not a float")

        size: int = int(value.dtype[5:])
        return Float(size=size)


@dataclass
class Text(DashAIValue):
    string_type: str = "string"

    def __post_init__(self):
        if self.string_type not in ("large_string", "string"):
            raise ValueError(
                f"String type must be 'string' or 'large_string', but\
                    {self.string_type} was given."
            )

        self.dtype = self.string_type
        super().__post_init__()

    @staticmethod
    def from_value(value: Value):
        if value.dtype not in ("string", "large_string"):
            raise ValueError(f"dtype {value.dtype} is not a string")

        return Text(string_type=value.dtype)


@dataclass
class Null(DashAIValue):
    def __post_init__(self):
        self.dtype = "null"
        super().__post_init__()

    @staticmethod
    def from_value(value: Value):
        if value.dtype != "null":
            raise ValueError(f"dtype {value.dtype} is not null.")
        return Null()


@dataclass
class Time(DashAIValue):
    size: int
    unit: str

    def __post_init__(self):
        if self.size not in [32, 64]:
            raise ValueError(
                f"size must be 32 or 64, but {self.size} was\
                given."
            )

        if self.size == 32 and self.unit not in ["s", "ms"]:
            raise ValueError(
                f"unit for size=32 must be 's' or 'ms', but {self.unit} was\
                    given."
            )

        if self.size == 64 and self.unit not in ["us", "ns"]:
            raise ValueError(
                f"unit for size=64 must be 'us' or 'ns', but {self.unit} was\
                    given."
            )

        self.dtype = f"time{self.size}[{self.unit}]"
        super().__post_init__()

    @staticmethod
    def from_value(value: Value):
        if not value.dtype.startswith("time"):
            raise ValueError(f"dtype {value.dtype} is not a time value")

        size: int = int(value.dtype[4:6])
        unit: str = value.dtype[7:-1]
        return Time(size=size, unit=unit)


@dataclass
class Boolean(DashAIValue):
    def __post_init__(self):
        self.dtype = "bool"
        super().__post_init__()

    @staticmethod
    def from_value(value: Value):
        if value.dtype == "boolean":
            raise ValueError(f"dtype {value.dtype} is not boolean")
        return Boolean()


@dataclass
class Timestamp(DashAIValue):
    unit: str
    timezone: str = None

    def __post_init__(self):
        if self.unit not in ["s", "ms", "us", "ns"]:
            raise ValueError(
                f"Timestamp unit must be 's', 'ms', 'us' or 'ns', but\
                    {self.unit} was given"
            )
        if self.timezone is None:
            self.dtype = f"timestamp[{self.unit}]"

        else:
            self.dtype = f"timestamp[{self.unit}, tz={self.timezone}]"

        super().__post_init__()

    @staticmethod
    def from_value(value: Value):
        if not value.dtype.startswith("timestamp"):
            raise ValueError(f"dtype {value.dtype} is not timestamp.")

        timestamp_params: list[str] = value.dtype[10:-1].split(",")
        unit: str = timestamp_params[0]

        if len(timestamp_params) == 2:
            timezone = timestamp_params[1][4:]
            return Timestamp(unit=unit, timezone=timezone)

        return Timestamp(unit=unit)


@dataclass
class Duration(DashAIValue):
    unit: str = "ms"

    def __post_init__(self):
        if self.unit not in ["s", "ms", "us", "ns"]:
            raise ValueError(
                f"Duration unit must be 's', 'ms', 'us' or 'ns', but\
                    {self.unit} was given."
            )

        self.dtype = self.unit
        super().__post_init__()

    @staticmethod
    def from_value(value: Value):
        if not value.dtype.startswith("duration"):
            raise Value(f"dtype {value.dtype} is not duration")

        unit = value.dtype[8:-1]
        return Duration(unit=unit)


@dataclass
class Decimal(DashAIValue):
    size: int
    precision: int
    scale: int = 0

    def __post_init__(self):
        if self.size not in [128, 256]:
            raise ValueError(
                f"Decimal size must be 128 or 256, but {self.size} was given."
            )
        self.dtype = f"decimal({self.precision}, {self.scale})"
        super().__post_init__()

    @staticmethod
    def from_value(value: Value):
        if not value.dtype.startswith("decimal"):
            raise ValueError(f"dtype {value.dtype} is not decimal")
        size = int(value.dtype[7:10])
        params = value.dtype[11:-1].split(", ")
        return Decimal(size=size, precision=params[0], scale=params[1])


VALUES_DICT: "dict[str, BaseValue]" = {
    "null": Null,
    "bool": Boolean,
    "int8": Integer,
    "int16": Integer,
    "int32": Integer,
    "int64": Integer,
    "uint8": Integer,
    "uint16": Integer,
    "uint32": Integer,
    "uint64": Integer,
    "float16": Float,
    "float32": Float,
    "float64": Float,
    "time32": Time,
    "time64": Time,
    "timestamp": Timestamp,
    "date32": "Date",
    "date64": "Date",
    "duration": "Duration",
    "decimal128": "Decimal",
    "decimal256": "Decimal",
    "binary": "Binary",
    "large_binary": "Binary",
    "string": Text,
    "large_string": Text,
}


def to_dashai_value(value: Value):
    try:
        parenthesis = value.dtype.index("(")
        val = value.dtype[:parenthesis]
    except ValueError:
        val = value.dtype
    if val not in VALUES_DICT:
        raise ValueError(f"{value.dtype} is not a valid value data type.")

    return VALUES_DICT[val].from_value(value)


if __name__ == "__main__":
    int_val = Integer()
    text_val = Text()
    float_val = Float()
