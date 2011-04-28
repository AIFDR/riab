
import numpy
import scipy

from django.template.loader import render_to_string
from impact.plugins.core import FunctionProvider

from impact.engine.utilities import MAXFLOAT
from impact.plugins.utilities import Damage_curve


class TephraImpactFunction(FunctionProvider):
    """Risk plugin for tephra damage (FIXME: Origin?)

    :param requires category=="hazard" and \
                    subcategory.startswith("tephra") and \
                    layerType=="raster"
    :param requires category=="exposure" and \
                    subcategory.startswith("building") and \
                    layerType=="feature"
    """

    @staticmethod
    def run(hazard_layers, exposure_layers):
        """Risk plugin for tephra impact
        """

        coordinates, attributes = hazard_layers
        coordinates, _ = exposure_layers

        N = len(attributes)

        result = []
        for i in range(N):

            #-------------------
            # Extract parameters
            #-------------------
            load = float(attributes[i].values()[0])

            #------------------------
            # Compute damage level
            #------------------------
            if 0.01 <= load < 90.0:
                impact = 1
            elif 90.0 <= load < 150.0:
                impact = 2
            elif 150.0 <= load < 300.0:
                impact = 3
            elif load >= 300.0:
                impact = 4
            else:
                impact = 0

            result.append({'Impact': impact})

        return result
