from enum import Enum


class SplitEnum(Enum):
    TRAIN = "train"
    VALIDATION = "validation"
    TEST = "test"
    FULL = "full"


class LevelEnum(Enum):
    LAST = "last"
    TRIAL = "trial"
    STEP = "step"
    EPOCH = "epoch"
    FOLD = "fold"
    OUTER_FOLD = "outer_fold"
    LAST_OUTER = "last_outer"
