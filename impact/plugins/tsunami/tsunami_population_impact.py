from django.template.loader import render_to_string
from impact.plugins.core import FunctionProvider
from impact.storage.vector import Vector
from django.utils.translation import ugettext as _
from impact.plugins.utilities import PointZoomSize
from impact.plugins.utilities import PointClassColor
from impact.plugins.utilities import PointSymbol
import scipy.stats


class TsunamiPopulationImpactFunction(FunctionProvider):
    """Risk plugin for tsunami impact on population data

    :param requires category=="hazard" and \
                    subcategory.startswith("tsunami") and \
                    layer_type=="raster"
    :param requires category=="exposure" and \
                    subcategory.startswith("population") and \
                    layer_type=="feature"
    """

    target_field = 'AFFECTED'

    def run(self, layers):
        """Risk plugin for tsunami population
        """

        # Extract data
        # FIXME (Ole): This will be replaced by a helper function
        #              to separate hazard from exposure using keywords
        H = layers[0]  # Depth
        E = layers[1]  # Building locations

        # Interpolate hazard level to building locations
        H = H.interpolate(E)

        # Extract relevant numerical data
        coordinates = E.get_geometry()
        depth = H.get_data()
        N = len(depth)

        # List attributes to carry forward to result layer
        attributes = E.get_attribute_names()

        #print attributes
        #print 'Number of population points', N

        # Calculate population impact
        count = 0
        population_impact = []
        for i in range(N):
            dep = float(depth[i].values()[0])
            pop = E.get_data('GRID_CODE', i)
            pointid = E.get_data('POINTID', i)

            if dep > 1:
                affected = 99.5
            else:
                affected = 0

            #if pointid == 263:
            #    print i, pointid, dep, pop, affected

            # Collect depth and calculated damage
            result_dict = {'AFFECTED': affected,
                           'DEPTH': dep}

            # Carry all original attributes forward
            for key in attributes:
                result_dict[key] = E.get_data(key, i)

            # Record result for this feature
            population_impact.append(result_dict)

            # Calculate statistics
            if affected > 99:
                count += pop

        # Create report
        caption = ('Number of people affected by tsunami inundation greater '
                   'than 1 m = %i' % count)

        #print population_impact
        # Create vector layer and return
        V = Vector(data=population_impact,
                   projection=E.get_projection(),
                   geometry=coordinates,
                   name='Estimated population affected',
                   keywords={'caption': caption})
        return V

    def generate_style(self, data):
        """Generates and SLD file based on the data values
        """
        DEFAULT_SYMBOL = 'ttf://Webdings#0x0067'

        symbol_field = None
        symbol_keys = [None, '']
        symbol_values = [DEFAULT_SYMBOL, DEFAULT_SYMBOL]

        scale_keys = [10000000000, 10000000, 5000000,
                      1000000, 500000, 250000, 100000]
        scale_values = [8, 8, 8, 8, 8, 8, 8]

        class_keys = ['No Damage', '90-100']
        class_values = [{'min': 0, 'max': 90,
                         'color': '#cccccc', 'opacity': '0'},
                        {'min': 90, 'max': 100,
                         'color': '#e31a1c', 'opacity': '1'}]

        if self.symbol_field in data.get_attribute_names():
            symbol_field = self.symbol_field

            symbol_keys.extend(['Church/Mosque', 'Commercial (office)',
                                'Hotel',
                                'Medical facility', 'Other',
                                'Other industrial',
                                'Residential', 'Retail', 'School',
                                'Unknown', 'Warehouse'])

            symbol_values.extend([DEFAULT_SYMBOL, DEFAULT_SYMBOL,
                                  DEFAULT_SYMBOL,
                                  DEFAULT_SYMBOL, DEFAULT_SYMBOL,
                                  DEFAULT_SYMBOL,
                                  DEFAULT_SYMBOL, DEFAULT_SYMBOL,
                                  DEFAULT_SYMBOL,
                                  DEFAULT_SYMBOL, DEFAULT_SYMBOL])

        params = dict(name=data.get_name(),
                      damage_field=self.target_field,
                      symbol_field=symbol_field,
                      symbols=dict(zip(symbol_keys, symbol_values)),
                      scales=dict(zip(scale_keys, scale_values)),
                      classifications=dict(zip(class_keys, class_values)))

        return render_to_string('impact/styles/point_classes.sld', params)
