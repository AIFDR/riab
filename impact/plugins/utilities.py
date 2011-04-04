"""Module to create damage curves from point data
"""

import numpy
from scipy.interpolate import interp1d


class Damage_curve:

    def __init__(self, data):

        try:
            data = numpy.array(data)
        except:
            msg = 'Could not convert data %s to damage curve' % str(data)
            raise Exception(msg)

        msg = 'Damage curve data must be a 2d array or a list of lists'
        assert len(data.shape) == 2, msg

        msg = 'Damage curve data must have two columns'
        assert data.shape[1] == 2, msg

        x = data[:, 0]
        y = data[:, 1]

        self.curve = interp1d(x, y)

    def __call__(self, x):
        return self.curve(x)
