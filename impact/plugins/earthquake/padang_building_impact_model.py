from django.template.loader import render_to_string
from impact.plugins.core import FunctionProvider
from impact.storage.vector import Vector
from django.utils.translation import ugettext as _
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
        N = len(shaking)

        # List attributes to carry forward to result layer
        attributes = E.get_attribute_names()

        # Calculate building damage
        count50 = 0
        count25 = 0
        count10 = 0
        building_damage = []
        for i in range(N):
            mmi = float(shaking[i].values()[0])

            building_class = E.get_data('TestBLDGCl', i)
            building_type = str(int(building_class))
            damage_params = damage_curves[building_type]
            percent_damage = scipy.stats.lognorm.cdf(
                                        mmi,
                                        damage_params['beta'],
                                        scale=damage_params['median']) * 100

            # Collect shake level and calculated damage
            result_dict = {'DAMAGE': percent_damage,
                           'MMI': mmi}

            # Carry all orginal attributes forward
            for key in attributes:
                result_dict[key] = E.get_data(key, i)

            # Record result for this feature
            building_damage.append(result_dict)

            # Calculate statistics
            if 10 <= percent_damage < 25:
                count10 += 1

            if 25 <= percent_damage < 50:
                count25 += 1

            if 50 <= percent_damage:
                count50 += 1

        # Create report
        caption = ('<table border="0" width="350px">'
                   '   <tr><th><b>%s</b></th><th><b>%s</b></th></th>'
                    '   <tr></tr>'
                    '   <tr><td>%s&#58;</td><td>%i</td></tr>'
                    '   <tr><td>%s (10-25%%)&#58;</td><td>%i</td></tr>'
                    '   <tr><td>%s (25-50%%)&#58;</td><td>%i</td></tr>'
                    '   <tr><td>%s (50-100%%)&#58;</td><td>%i</td></tr>'
                    '</table>' % (_('Buildings'),  _('Total'),
                                  _('All'), N,
                                  _('Low damage'), count10,
                                  _('Medium damage'), count25,
                                  _('High damage'), count50))


        # Create vector layer and return
        V = Vector(data=building_damage,
                   projection=E.get_projection(),
                   geometry=coordinates,
                   name='Estimated pct damage',
                   keywords={'caption': caption})
        return V
