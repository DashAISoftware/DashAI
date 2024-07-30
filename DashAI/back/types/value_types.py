from dataclasses import dataclass

from datasets import Value

from DashAI.back.types.dashai_data_type import DashAIDataType
from DashAI.back.types.dashai_value import DashAIValue


@dataclass
class Integer(DashAIValue, DashAIDataType):
    """Wrapper class to represent integer and unsigned integer Hugging Face
    values.

    Attributes
    ----------
    size : int
        Number of bits used to represent the integer numbers.
        The accepted sizes are 8, 16, 32 and 64.
    unsigned : bool
        True if the represented integer is unsigned (non negative)

    Raises
    ------
    ValueError
        Raised when an invalid size is given.
    """

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
class Float(DashAIValue, DashAIDataType):
    """Wrapper class to represent float Hugging Face values.

    Attributes
    ----------
    size : int
        Number of bits used to represent the integer numbers.
        The accepted sizes are 16, 32 and 64.

    Raises
    ------
    ValueError
        Raised when an invalid size is given.
    """

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
class Text(DashAIValue, DashAIDataType):
    """Wrapper class to represent string and large string Hugging Face values.

    Attributes
    ----------
    string_type : str
        Type of string represented. It should be 'string' or 'large_string'

    Raises
    ------
    ValueError
        Raised when an invalid string type is given.
    """

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
class Time(DashAIValue, DashAIDataType):
    """Wrapper class to represent time Hugging Face values.

    Attributes
    ----------
    size : int
        Number of bits used to represent the integer numbers.
        The accepted sizes are 32 and 64.
    unit : str
        Unit of time used. It should be 's' or 'ms'.

    Raises
    ------
    ValueError
        Raised when an invalid size or invalid unit is given.
    """

    size: int = 64
    unit: str = "s"

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
class Boolean(DashAIValue, DashAIDataType):
    """Wrapper class to represent boolean Hugging Face values."""

    def __post_init__(self):
        self.dtype = "bool"
        super().__post_init__()

    @staticmethod
    def from_value(value: Value):
        if value.dtype != "boolean":
            raise ValueError(f"dtype {value.dtype} is not boolean")
        return Boolean()


@dataclass
class Timestamp(DashAIValue, DashAIDataType):
    """Wrapper class to represent timestamp Hugging Face values.

    Attributes
    ----------
    unit : str
        Unit of used for the timestamp. It should be 's', 'ms', 'us', or 'ns'.
    timezone : str | None
        Timezone used for the timestamp.
    Raises
    ------
    ValueError
        Raised when an invalid string type is given.
    """

    unit: str = "s"
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
class Duration(DashAIValue, DashAIDataType):
    """Wrapper class to represent duration Hugging Face values.

    Attributes
    ----------
    unit : str
        Unit of time used. It should be 's', 'ms', 'us' or 'ns'.

    Raises
    ------
    ValueError
        Raised when an invalid unit is given.
    """

    unit: str = "ms"

    def __post_init__(self):
        if self.unit not in ["s", "ms", "us", "ns"]:
            raise ValueError(
                f"Duration unit must be 's', 'ms', 'us' or 'ns', but\
                    {self.unit} was given."
            )

        self.dtype = f"duration[{self.unit}]"
        super().__post_init__()

    @staticmethod
    def from_value(value: Value):
        if not value.dtype.startswith("duration"):
            raise Value(f"dtype {value.dtype} is not duration")

        unit = value.dtype[9:-1]
        return Duration(unit=unit)


@dataclass
class Decimal(DashAIValue, DashAIDataType):
    """Wrapper class to represent decimal Hugging Face values.

    Attributes
    ----------
    size : int
        Number of bits used to represent the decimal value.
        It should be 128 or 256.
    precision : int
        Number of digits used in the value.
    scale : int
        Number of decimal digits

    Raises
    ------
    ValueError
        Raised when an invalid size is given.
    """

    size: int = 128
    precision: int = 8
    scale: int = 0

    def __post_init__(self):
        if self.size not in [128, 256]:
            raise ValueError(
                f"Decimal size must be 128 or 256, but {self.size} was given."
            )
        self.dtype = f"decimal{self.size}({self.precision}, {self.scale})"
        super().__post_init__()

    @staticmethod
    def from_value(value: Value):
        if not value.dtype.startswith("decimal"):
            raise ValueError(f"dtype {value.dtype} is not decimal")
        size = int(value.dtype[7:10])
        params = value.dtype[11:-1].split(", ")
        return Decimal(size=size, precision=params[0], scale=params[1])


@dataclass
class Date(DashAIValue, DashAIDataType):
    """Wrapper class to represent date Hugging Face values.

    Attributes
    ----------
    size : int
        Number of bits used to represent the date value.
        It should be 32 or 64.

    Raises
    ------
    ValueError
        Raised when an invalid size is given.
    """

    size: int = 64

    def __post_init__(self):
        if self.size not in [32, 64]:
            raise ValueError(
                f"Date size must be 32 or 64, but {self.size} was\
                given."
            )
        self.dtype = f"date{self.size}"
        super().__post_init__()

    @staticmethod
    def from_value(value: Value):
        if not value.dtype.startswith("date"):
            raise ValueError(f"dtype {value.dtype} is not date.")
        size = int(value.dtype[4:])
        return Date(size=size)


@dataclass
class Binary(DashAIValue, DashAIDataType):
    """Wrapper class to represent binary Hugging Face values.

    Attributes
    ----------
    binary_type : str
        Type of binary. It should be 'binary' or 'large_binary'.

    Raises
    ------
    ValueError
        Raised when an invalid binary type is given.
    """

    binary_type: str = "binary"

    def __post_init__(self):
        if self.binary_type not in ["binary", "large_binary"]:
            raise ValueError(
                f"binary_type must be 'binary' or 'large_binary', but\
                    {self.binary_type} was given."
            )

        self.dtype = self.binary_type
        super().__post_init__()

    @staticmethod
    def from_value(value: Value):
        if value.dtype not in ["binary", "large_binary"]:
            raise ValueError(f"dtype {value.dtype} is not binary")

        return Binary(binary_type=value.dtype)


VALUES_DICT: "dict[str, DashAIValue]" = {
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
    "duration": Duration,
    "decimal128": Decimal,
    "decimal256": Decimal,
    "binary": Binary,
    "large_binary": Binary,
    "string": Text,
    "large_string": Text,
}


def to_dashai_value(value: Value) -> "DashAIValue":
    """Cast a Hugging Face Value into a DashAI Value according its
    dtype attribute.

    Parameters
    ----------
    value : Value
        Hugging Face Value to be casted.

    Returns
    -------
    DashAIValue
        DashAI Value corresponding to the Hugging Face Value.

    Raises
    ------
    ValueError
        Raised when an invalid value data type is given.
    """
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
