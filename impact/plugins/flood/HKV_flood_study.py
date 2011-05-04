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

        # Extract data
        # FIXME (Ole): This will be replaced by a helper function
        #              to separate hazard from exposure using keywords
        H = layers[0].get_data(nan=0)
        P = layers[1].get_data(nan=0)

        # Calculate impact
        # FIXME: Just a placeholder for the moment
        F = P * H

        # Return

        # FIXME (Ole): Need helper to generate new layer using
        #              correct spatial reference
        #              (i.e. sensibly wrap the following lines)
        projection = layers[0].get_projection()
        geotransform = layers[0].get_geotransform()

        R = Raster(F, projection, geotransform,
                   name='Estimated fatalities')
        return R
