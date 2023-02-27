from enum import Enum

class State(Enum):
   TaskSelection = 0
   DatasetSelection = 1
   ModelConfiguration = 2
   Execution = 3
   Completed = 4