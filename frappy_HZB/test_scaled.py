import random

from frappy.core import Parameter, Readable, ScaledInteger


class ScaleInt(Readable):
    value = Parameter(datatype=ScaledInteger(scale= 0.01,minval = 0,maxval =100,))
    
    def read_value(self):
        return random.randint(1,9)*0.1 