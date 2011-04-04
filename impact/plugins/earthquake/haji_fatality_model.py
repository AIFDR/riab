class EmpiricalFatalityFunction(FunctionProvider):
    """Risk plugin for earthquake damage based on empirical results

    :author Haji
    :rating 2
    :param requires category=="hazard" and subcategory.startswith("earthquake") and layerType=="raster"
    :param requires category=="exposure" and subcategory.startswith("population") and layerType=="raster"
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

        ## for some reason cdf function requires all the values to be stanard floats
        ## the next line just converts them to floats
        arryout = numpy.array([[float(value) for value in row] for row in logHazard])
        F = scipy.stats.norm.cdf(arryout * E)

        # F = round(arryout * E)
        return F


