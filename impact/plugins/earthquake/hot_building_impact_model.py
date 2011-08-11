from django.template.loader import render_to_string
from impact.plugins.core import FunctionProvider
from impact.engine.utilities import MAXFLOAT
from impact.plugins.utilities import Damage_curve

from impact.storage.vector import Vector

#------------------------------------------------------------
# Define damage curves for structural building damage
#
# MMI: % Damage
#------------------------------------------------------------
struct_damage_curve = {'weak': Damage_curve([[-MAXFLOAT, 0.0],
                                             [4.0, 0],
                                             [5.0, 15],
                                             [6.0, 30],
                                             [6.5, 50],
                                             [6.8, 70],
                                             [7.0, 85],
                                             [8.0, 100],
                                             [9.0, 100],
                                             [MAXFLOAT, 100]]),
                       'strong': Damage_curve([[-MAXFLOAT, 0.0],
                                               [4.0, 0],
                                               [5.0, 10],
                                               [6.0, 20],
                                               [6.5, 30],
                                               [7.0, 45],
                                               [7.2, 55],
                                               [8.0, 90],
                                               [9.0, 100],
                                               [MAXFLOAT, 100]])}


# Relate specific attributes in HOT dataset to classification
# (structure, roof) -> class
vulnerability_map = {('unreinforced_masonry', 'tin'): 'weak',
                      ('unreinforced_masonry', 'tile'): 'weak',
                      ('unreinforced_masonry', 'concrete'): 'weak',
                      ('reinforced masonry', 'concrete'): 'strong',
                      ('reinforced_masonry', 'concrete'): 'strong',
                      ('plastered', 'concrete'): 'weak'}


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

        #print E.get_attribute_names()

        # Calculate building damage
        building_damage = []
        for i in range(len(shaking)):
            x = float(shaking[i].values()[0])

            # Get attributes
            structure = E.get_data('structure', i)
            roof = E.get_data('roof', i)
            walls = E.get_data('walls', i)
            levels = E.get_data('levels', i)
            use = E.get_data('levels', i)

            # Get building classification and vulnerability curve
            if (structure, roof) in vulnerability_map:
                classification = vulnerability_map[(structure, roof)]
            else:
                classification = 'weak'

            curve = struct_damage_curve[classification]

            # Calculate percent damage
            value = curve(x)
            building_damage.append({'DAMAGE': value, 'MMI': x})

            #print i, classification, x, value

        # Create resulting layer object and return
        V = Vector(data=building_damage,
                   projection=E.get_projection(),
                   geometry=coordinates,
                   name='Estimated pct damage')
        return V


# Example building data from HOT data (Kampung Bali)
#
# i, structure, roof, walls, levels, use
# 0 unreinforced_masonry tin brick 2 2
# 1 unreinforced_masonry tile brick 1 1
# 2 unreinforced_masonry tin brick 1 1
# 3 unreinforced_masonry tin brick 1 1
# 4 unreinforced_masonry tin brick 1 1
# 5 plastered concrete brick 2 2
# 6 unreinforced_masonry tin brick 1 1
# 7 reinforced masonry concrete brick 8 8
# 8 unreinforced_masonry tin brick 1 1
# 9 unreinforced_masonry tile brick 2 2
# 10 unreinforced_masonry tin brick 2 2
# 11 unreinforced_masonry tile brick 2 2
# 12 reinforced masonry concrete brick 8 8
# 13 reinforced masonry concrete brick 8 8
# 14 unreinforced_masonry tile brick 1 1
# 15 unreinforced_masonry tile brick 2 2
# 16 unreinforced_masonry tin brick 2 2
# 17 unreinforced_masonry tile brick 2 2
# 18 unreinforced_masonry tile brick 1 1
# 19 unreinforced_masonry concrete brick 2 2
# 20 unreinforced_masonry tin brick 2 2
# 21 unreinforced_masonry tile brick 2 2
# 22 unreinforced_masonry tin brick 2 2
# 23 unreinforced_masonry tin brick 1 1
# 24 unreinforced_masonry tile brick 2 2
# 25 unreinforced_masonry tile brick 2 2
# 26 unreinforced_masonry tile brick 1 1
# 27 reinforced masonry concrete brick 8 8
# 28 unreinforced_masonry tile brick 2 2
# 29 unreinforced_masonry tin brick 1 1
# 30 unreinforced_masonry tile brick 2 2
# 31 unreinforced_masonry tin brick 2 2
# 32 unreinforced_masonry tile brick 1 1
# 33 unreinforced_masonry tin brick 1 1
# 34 reinforced_masonry concrete brick 2 2
# 35 reinforced masonry concrete brick 8 8
# 36 unreinforced_masonry tile brick 1 1
# 37 unreinforced_masonry tile brick 1 1
# 38 unreinforced_masonry tile brick 2 2
# 39 reinforced masonry concrete brick 8 8
# 40 unreinforced_masonry tin brick 1 1
# 41 unreinforced_masonry tile brick 1 1
# 42 plastered concrete brick 3 3
