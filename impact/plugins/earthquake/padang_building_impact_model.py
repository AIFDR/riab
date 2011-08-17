from django.template.loader import render_to_string
from impact.plugins.core import FunctionProvider
from impact.storage.vector import Vector
from django.utils.translation import ugettext as _
from impact.plugins.utilities import PointZoomSize
from impact.plugins.utilities import PointClassColor
from impact.plugins.utilities import PointSymbol
import scipy.stats


class PadangEarthquakeBuildingDamageFunction(FunctionProvider):
    """Risk plugin for Padang earthquake damage to buildings

    :param requires category=="hazard" and \
                    subcategory.startswith("earthquake") and \
                    layer_type=="raster"
    :param requires category=="exposure" and \
                    subcategory.startswith("building")
    """

    target_field = 'DAMAGE'
    symbol_field = 'USE_MAJOR'

    def run(self, layers):
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
            result_dict = {self.target_field: percent_damage,
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
        caption = ('<table border="0" width="320px">'
                   '   <tr><th><b>%s</b></th><th><b>%s</b></th></th>'
                    '   <tr></tr>'
                    '   <tr><td>%s&#58;</td><td>%i</td></tr>'
                    '   <tr><td>%s (10-25%%)&#58;</td><td>%i</td></tr>'
                    '   <tr><td>%s (25-50%%)&#58;</td><td>%i</td></tr>'
                    '   <tr><td>%s (50-100%%)&#58;</td><td>%i</td></tr>'
                    '</table>' % (_('Buildings'), _('Total'),
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

    def generate_style(self, data):
        """Generates and SLD file based on the data values
        """

        # Define default behaviour to be used when
        # - symbol attribute is missing
        # - attribute value is None or ''
        DEFAULT_SYMBOL = 'circle'

        symbol_field = None

        # FIXME: Replace these by dict and extend below
        symbol_keys = [None, '']
        symbol_values = [DEFAULT_SYMBOL, DEFAULT_SYMBOL]

        # Predefined scales and corresponding font sizes
        scale_keys = [10000000000, 10000000, 5000000,
                      1000000, 500000, 250000, 100000]
        scale_values = [3, 5, 8, 12, 14, 16, 18]

        # Predefined colour classes
        class_keys = ['No Damage', '10-25', '25-50', '50-100']
        class_values = [{'min': 0, 'max': 10,
                         'color': '#cccccc', 'opacity': '1'},
                        {'min': 10, 'max': 25,
                         'color': '#fecc5c', 'opacity': '1'},
                        {'min': 25, 'max': 50,
                         'color': '#fd8d3c', 'opacity': '1'},
                        {'min': 50, 'max': 100,
                         'color': '#e31a1c', 'opacity': '1'}]

        # Definition of symbols for each attribute value
        if self.symbol_field in data.get_attribute_names():

            # Get actual symbol field to use
            symbol_field = self.symbol_field

            symbols = {'Church/Mosque': 'ttf://ESRI US MUTCD 3#0x00F6',
                       'Commercial (office)': 'ttf://ESRI Business#0x0040',
                       'Hotel': 'ttf://ESRI Public1#0x00b6',
                       'Medical facility': 'ttf://ESRI Cartography#0x00D1',
                       'Other': 'ttf://ESRI Business#0x002D',
                       'Other industrial': 'ttf://ESRI Business#0x0043',
                       'Residential': 'ttf://ESRI Cartography#0x00d7',
                       'Retail': 'ttf://Comic Sans MS#0x0024',
                       'School': 'ttf://ESRI Cartography#0x00e5',
                       'Unknown': 'ttf://Comic Sans MS#0x003F',
                       'Warehouse': 'ttf://ESRI US MUTCD 3#0x00B5'}
        else:
            symbols = {None: DEFAULT_SYMBOL, '': DEFAULT_SYMBOL}

        # Generate sld style file
        params = dict(name=data.get_name(),
                      damage_field=self.target_field,
                      symbol_field=symbol_field,
                      symbols=symbols,
                      scales=dict(zip(scale_keys, scale_values)),
                      classifications=dict(zip(class_keys, class_values)))

        return render_to_string('impact/styles/point_classes.sld', params)
