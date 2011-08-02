from django.template.loader import render_to_string
from impact.plugins.core import FunctionProvider
from impact.storage.vector import Vector
import scipy.stats


class PadangEarthquakeBuildingDamageFunction(FunctionProvider):
    """Risk plugin for Padang earthquake damage to buildings

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

        damage_curves = {
                   '1': dict(median=7.5, beta=0.11),
                   '2': dict(median=8.3, beta=0.1),
                   '3': dict(median=8.8, beta=0.11),
                   '4': dict(median=8.4, beta=0.05),
                   '5': dict(median=9.2, beta=0.11),
                   '6': dict(median=9.7, beta=0.15),
                   '7': dict(median=9, beta=0.08),
                   '8': dict(median=8.9, beta=0.07),
                   '9': dict(median=10.5, beta=0.15),
                  }

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

            building_class = E.get_data('TestBLDGCl', i)
            #building_id = E.get_data('UNIQUE_FIE', i)

            building_type = str(int(building_class))
            damage_params = damage_curves[building_type]
            percent_damage = scipy.stats.lognorm.cdf(
                                        mmi,
                                        damage_params['beta'],
                                        scale=damage_params['median']) * 100
            building_damage.append({'Percent_damage': percent_damage,
                                    'MMI': mmi,
                                    'Building_Class': building_class})

        # Create vector layer and return
        V = Vector(data=building_damage,
                   projection=E.get_projection(),
                   geometry=coordinates,
                   name='Estimated pct damage')
        return V
