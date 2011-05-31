from impact.plugins.core import FunctionProvider
from impact.storage.raster import Raster

import scipy
import scipy.stats
import numpy


class USGSFatalityFunction(FunctionProvider):
    """Risk plugin for earthquake damage based on empirical results

    :author Hadi Ghasemi
    :rating 2

    :param requires category == 'hazard' and \
                    subcategory == 'earthquake' and \
                    unit == 'mmi' and \
                    layer_type == 'raster'

    :param requires category == 'exposure' and \
                    subcategory == 'population' and \
                    layer_type == 'raster'
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

        print
        print '------------------'
        print 'Got input layers'
        print intensity
        print population

        print 'Population Resolution', population.get_geotransform()

        # Extract data
        H = intensity.get_data(nan=0)   # Ground Shaking
        P = population.get_data(nan=0)  # Population Density

        # Calculate population affected by each MMI level
        for mmi in range(2, 10):
            mask = numpy.logical_and(mmi - 0.5 < H,
                                     H <= mmi + 0.5)
            I = numpy.where(mask, P, 0)

            # Generate text with result for this study
            number_of_people_affected = sum(I.flat)

            print ('Number of people affected by mmi '
                   'level %i: %.0f' % (mmi,
                                       number_of_people_affected / 1000))

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
