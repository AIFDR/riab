from impact.plugins.core import FunctionProvider
from impact.storage.raster import Raster


class EarthquakeFatalityFunction(FunctionProvider):
    """Risk plugin for earthquake damage

    :author Allen
    :rating 1
    :param requires category=="hazard" and \
                    subcategory.startswith("earthquake") and \
                    layerType=="raster"
    :param requires category=="exposure" and \
                    subcategory.startswith("population") and \
                    layerType=="raster"
    """

    @staticmethod
    def run(layers,
            a=0.97429, b=11.037):
        """Risk plugin for earthquake fatalities

        Input
          layers: List of layers expected to contain
              H: Raster layer of MMI ground shaking
              P: Raster layer of population data on the same grid as H
        """

        # Extract data
        # FIXME (Ole): This will be replaced by a helper function
        #              to separate hazard from exposure using keywords
        H = layers[0].get_data(nan=0)
        P = layers[1].get_data(nan=0)

        # Calculate impact
        F = 10 ** (a * H - b) * P

        # Return

        # FIXME (Ole): Need helper to generate new layer using
        #              correct spatial reference
        #              (i.e. sensibly wrap the following lines)
        projection = layers[0].get_projection()
        geotransform = layers[0].get_geotransform()

        R = Raster(F, projection, geotransform,
                   name='Estimated fatalities')
        return R
