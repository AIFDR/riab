from django.template.loader import render_to_string
from impact.plugins.core import FunctionProvider
from impact.storage.vector import Vector



#------------------------------------------------------------
# Define damage curves for structural building damage
#
# MMI: % Damage
#------------------------------------------------------------
struct_damage_curve = {'Weak': Damage_curve([[-MAXFLOAT, 0.0],
                                             [4.0, 0],
                                             [5.0, 15],
                                             [6.0, 30],
                                             [6.5, 50],
                                             [6.8, 70],
                                             [7.0, 85],
                                             [8.0, 100],
                                             [9.0, 100],
                                             [MAXFLOAT, 100]]),
                       'Strong': Damage_curve([[-MAXFLOAT, 0.0],
                                               [4.0, 0],
                                               [5.0, 10],
                                               [6.0, 20],
                                               [6.5, 30],
                                               [6.8, 45],
                                               [7.0, 55],
                                               [8.0, 90],
                                               [9.0, 100],
                                               [MAXFLOAT, 100]]),
                       }


class HOTEarthquakeBuildingDamageFunction(FunctionProvider):
    """Risk plugin for earthquake damage to buildings

    :param requires category=="hazard" and \
                    subcategory.startswith("earthquake") and \
                    layer_type=="raster"
    :param requires category=="exposure" and \
                    subcategory.startswith("building")
    """

    @staticmethod
    def run(layers):
        """Risk plugin for HOT building data
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
            x = float(shaking[i].values()[0])

            structure_type = E.get_data('STRUCTURE_TYPE', i)


            if x < 6.0:
                value = 0.0
            else:
                value = (0.692 * (x ** 4) -
                         15.82 * (x ** 3) +
                         135.0 * (x ** 2) -
                         509.0 * x +
                         714.4)

            building_damage.append({'Percent_damage': value, 'MMI': x})

        # FIXME (Ole): Need helper to generate new layer using
        #              correct spatial reference
        #              (i.e. sensibly wrap the following lines)
        projection = E.get_projection()

        V = Vector(data=building_damage,
                   projection=E.get_projection(),
                   geometry=coordinates,
                   name='Estimated pct damage')
        return V
