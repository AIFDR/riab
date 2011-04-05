
from impact.plugins.core import FunctionProvider

class EarthquakeFatalityFunction(FunctionProvider):
    """Risk plugin for earthquake damage

    :author Allen
    :rating 1
    :param requires category=="hazard" and subcategory.startswith("earthquake") and layerType=="raster"
    :param requires category=="exposure" and subcategory.startswith("population") and layerType=="raster"
    """

    @staticmethod
    def run(H, E,
            a=0.97429, b=11.037):
        """Risk plugin for earthquake fatalities

        Input
          H: Numerical array of hazard data
          E: Numerical array of exposure data
        """

        # Calculate impact
        F = 10 ** (a * H - b) * E

        # Return
        return F

