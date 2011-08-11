from impact.plugins.core import FunctionProvider
from impact.storage.vector import Vector

# FIXME: Need style for this and allow the name to
# be different from Percen_da


class TephraImpactFunction(FunctionProvider):
    """Risk plugin for tephra damage (FIXME: Origin?)

    :param requires category=="hazard" and \
                    subcategory.startswith("tephra") and \
                    layer_type=="raster"
    :param requires category=="exposure" and \
                    subcategory.startswith("building") and \
                    layer_type=="feature"
    """

    @staticmethod
    def run(layers):
        """Risk plugin for tephra impact
        """

        # Extract data
        # FIXME (Ole): This will be replaced by a helper function
        #              to separate hazard from exposure using keywords
        H = layers[0]  # Ash load
        E = layers[1]  # Building locations

        # Interpolate hazard level to building locations
        H = H.interpolate(E, 'load')

        # Calculate building damage
        result = []
        for i in range(len(E)):

            #-------------------
            # Extract parameters
            #-------------------
            load = H.get_data('load', i)

            #------------------------
            # Compute damage level
            #------------------------
            if 0.01 <= load < 90.0:
                impact = 25
            elif 90.0 <= load < 150.0:
                impact = 50
            elif 150.0 <= load < 300.0:
                impact = 75
            elif load >= 300.0:
                impact = 100
            else:
                impact = 0

            result.append({'DAMAGE': impact, 'ASHLOAD': load})

        # FIXME (Ole): Need helper to generate new layer using
        #              correct spatial reference
        #              (i.e. sensibly wrap the following lines)
        projection = E.get_projection()

        V = Vector(data=result,
                   projection=E.get_projection(),
                   geometry=E.get_geometry(),
                   name='Estimated ashload damage')
        return V
