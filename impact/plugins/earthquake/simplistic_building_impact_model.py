from django.template.loader import render_to_string
from impact.plugins.core import FunctionProvider
from impact.storage.vector import Vector
import scipy.stats


class SimplisticEarthquakeBuildingDamageFunction(FunctionProvider):
    """Risk plugin for simplistic earthquake damage to buildings

    :param requires category=="hazard" and \
                    subcategory.startswith("earthquake") and \
                    layer_type=="raster"
    :param requires category=="exposure" and \
                    subcategory.startswith("building")
    """

    @staticmethod
    def run(layers):
        """Risk plugin for earthquake school damage
        """

        # Extract data
        # FIXME (Ole): This will be replaced by a helper function
        #              to separate hazard from exposure using keywords
        H = layers[0]  # Ground shaking
        E = layers[1]  # Building locations

        # Interpolate hazard level to building locations
        H = H.interpolate(E)

        # Extract relevant numerical data
        coordinates = E.get_geometry()
        shaking = H.get_data()

        # Calculate building damage
        building_damage = []
        for i in range(len(shaking)):
            mmi = float(shaking[i].values()[0])
            if mmi >= 7.0:
                percent_damage = 100
            elif mmi >= 6.0:
                percent_damage = 50
            else:
                percent_damage = 0

            building_damage.append({'DAMAGE': percent_damage,
                                    'MMI': mmi})

        # Create vector layer and return
        V = Vector(data=building_damage,
                   projection=E.get_projection(),
                   geometry=coordinates,
                   name='Estimated pct damage')
        return V
