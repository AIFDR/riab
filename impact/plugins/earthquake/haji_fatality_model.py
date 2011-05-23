from impact.plugins.core import FunctionProvider
from impact.storage.raster import Raster

import scipy
import scipy.stats
import numpy


class EmpiricalFatalityFunction(FunctionProvider):
    """Risk plugin for earthquake damage based on empirical results

    :author Hadi Ghasemi
    :rating 2

    FIXME (Ole): Temporarily disabled this function until it has been tested.
    To bring back, go to __init__.py and import again.
    However, it should be possible to
    1: Disable impact functions by manipulating the keyword requiremens
    2: Not have to import the functions explicitly in __init__.py



    """

    @staticmethod
    def run(layers,
            teta=14.05, beta=0.17, zeta=2.15):
        """Risk plugin for earthquake fatalities

        Input
          H: Numerical array of hazard data
          E: Numerical array of exposure data
        """

        # Identify input layers
        intensity = layers[0]
        population = layers[1]

        # Extract data
        H = intensity.get_data(nan=0)
        P = population.get_data(nan=0)

        # Calculate impact
        logHazard = 1 / beta * scipy.log(H / teta)

        # Convert array to be standard floats expected by cdf
        arrayout = numpy.array([[float(value) for value in row]
                               for row in logHazard])
        F = scipy.stats.norm.cdf(arrayout * P)

        # Create new layer and return
        R = Raster(F,
                   projection=population.get_projection(),
                   geotransform=population.get_geotransform(),
                   name='Estimated fatalities')
        return R
