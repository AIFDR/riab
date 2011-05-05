import numpy

from impact.plugins.core import FunctionProvider
from impact.storage.raster import Raster

# FIXME (Ole): This one works, but needs styling
class FloodImpactFunction(FunctionProvider):
    """Risk plugin for flood impact

    :author HKV
    :rating 1
    :param requires category=="hazard" and \
                    subcategory.startswith("flood") and \
                    layerType=="raster"
    :param requires category=="exposure" and \
                    subcategory.startswith("population") and \
                    layerType=="raster"
    """

    @staticmethod
    def run(layers):
        """Risk plugin for earthquake fatalities

        Input
          layers: List of layers expected to contain
              H: Raster layer of flood depth
              P: Raster layer of population data on the same grid as H
        """

        # Identify hazard and exposure layers
        inundation = layers[0]  # Flood inundation [m]
        population = layers[1]  # Population density [people/100000 m^2]

        # Extract data as numeric arrays
        D = inundation.get_data(nan=0.0)  # Depth
        P = population.get_data(nan=0.0)  # Population density

        # Calculate impact as population exposed to depths > 0.1 m
        pixel_area = 2500
        I = numpy.where(D > 0.1, P, 0) / 100000 * pixel_area

        # FIXME (Ole): Need helper to generate new layer using
        #              correct spatial reference
        #              (i.e. sensibly wrap the following lines)
        projection = layers[0].get_projection()
        geotransform = layers[0].get_geotransform()

        # Create raster object and return
        R = Raster(I, projection, geotransform,
                   name='People affected')
        return R
