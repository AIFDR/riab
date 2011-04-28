from impact.plugins import FunctionProvider


# FIXME (Ole): This will not run.
# Please write similar to allen_fatality_model.py

class EmpiricalFatalityFunction(FunctionProvider):
    """Risk plugin for earthquake damage based on empirical results

    :author Haji
    :rating 2
    :param requires category=="hazard" /
           and subcategory.startswith("earthquake") /
           and layerType=="raster"
    :param requires category=="exposure" /
           and subcategory.startswith("population") /
           and layerType=="raster"
    """

    @staticmethod
    def run(H, E,
            teta=14.05, beta=0.17, zeta=2.15):
        """Risk plugin for earthquake fatalities

        Input
          H: Numerical array of hazard data
          E: Numerical array of exposure data
        """

        # Calculate impact
        logHazard = 1 / beta * scipy.log(H / teta)

        # Convert array to be standard floats expected by cdf
        arrayout = numpy.array([[float(value) for value in row]
                               for row in logHazard])
        F = scipy.stats.norm.cdf(arrayout * E)

        # F = round(arrayout * E)
        return F
