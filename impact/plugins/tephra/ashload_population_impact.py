import numpy

from impact.plugins.core import FunctionProvider
from impact.storage.raster import Raster


class TephraPopulationImpactFunction(FunctionProvider):
    """Risk plugin for flood impact

    :author HKV
    :rating 1
    :param requires category=='hazard' and \
                    subcategory.startswith('tephra') and \
                    layer_type=='raster'
    :param requires category=='exposure' and \
                    subcategory.startswith('population') and \
                    layer_type=='raster'
    """

    @staticmethod
    def run(layers):
        """Risk plugin for earthquake fatalities

        Input
          layers: List of layers expected to contain
              H: Raster layer of flood depth
              P: Raster layer of population data on the same grid as H
        """

        threshold = 1  # Load above which people are regarded affected [kg/m2]

        # Identify hazard and exposure layers
        inundation = layers[0]  # Tephra load [kg/m2]
        population = layers[1]  # Population density [people/km^2]

        # Extract data as numeric arrays
        D = inundation.get_data(nan=0.0)  # Depth
        P = population.get_data(nan=0.0, scaling=True)  # Population density

        # Calculate impact as population exposed to depths > threshold
        I = numpy.where(D > threshold, P, 0)

        # Generate text with result for this study
        number_of_people_affected = numpy.nansum(I.flat)
        caption = ('%i people affected by ash levels greater '
                   'than %i kg/m^2' % (number_of_people_affected,
                                       threshold))

        # Create raster object and return
        R = Raster(I,
                   projection=inundation.get_projection(),
                   geotransform=inundation.get_geotransform(),
                   name='People affected',
                   keywords={'caption': caption})
        return R
