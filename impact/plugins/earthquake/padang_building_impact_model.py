from django.template.loader import render_to_string
from impact.plugins.core import FunctionProvider
from impact.storage.vector import Vector
from django.utils.translation import ugettext as _
from impact.plugins.utilities import PointZoomSize, PointClassColor, PointSymbol  
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

    def generate_style(self, data):
        """
        """

        params = {'name': data.get_name()}
        params['damage_field'] = self.target_field
        params['symbol_field'] = self.symbol_field
        params['scale_sizes'] = []
        params['output_classes'] = []
        params['symbol_mapping'] = []

        scales = [10000000,5000000,1000000,500000,250000,100000,50000,25000,10000,0]
        scale_zooms = [5,8,12,14,16,18,24,36,42,52]
        scale_sizes = dict(zip(scales, scale_zooms))
        for i in range(len(scales)):
            params['scale_sizes'].append(
                PointZoomSize(level = scales[i], 
                              size = scale_sizes[scales[i]]))
            
        classes = []
        classes.append({'name': '0-10', 'params': {'min':0, 'max':10, 'color': '#ffffff'}})
        classes.append({'name': '10-20', 'params': {'min':10, 'max':20, 'color': '#00ff00'}})
        classes.append({'name': '20-30', 'params': {'min':20, 'max':30, 'color': '#ff67ed'}})
        classes.append({'name': '30-50', 'params': {'min':30, 'max':40, 'color': '#ff0000'}})
        classes.append({'name': '50-100', 'params': {'min':50, 'max':100, 'color': '#0000ff'}})
        for classx in classes:
           params['output_classes'].append(
                PointClassColor(name = classx['name'],
                                clmin = classx['params']['min'],
                                clmax = classx['params']['max'],
                                fill_color = classx['params']['color']))
 
        symbols = []
        symbols.append({'name': 'Church/Mosque', 'symbol': 'ttf://Webdings#0x0064'})
        symbols.append({'name': 'Commercial (office)', 'symbol': 'ttf://Webdings#0x0065'})
        symbols.append({'name': 'Hotel', 'symbol': 'ttf://Webdings#0x0060'})
        symbols.append({'name': 'Medical facility', 'symbol': 'ttf://Webdings#0x0063'})
        symbols.append({'name': 'Other', 'symbol': 'ttf://Webdings#0x0061'})
        symbols.append({'name': 'Other industrial', 'symbol': 'ttf://Webdings#0x0068'})
        symbols.append({'name': 'Residential', 'symbol': 'ttf://Webdings#0x0067'})
        symbols.append({'name': 'Retail', 'symbol': 'ttf://Webdings#0x0069'})
        symbols.append({'name': 'School', 'symbol': 'ttf://Webdings#0x0059'})
        symbols.append({'name': 'Unknown', 'symbol': 'ttf://Webdings#0x0058'})
        symbols.append({'name': 'Warehouse', 'symbol': 'ttf://Webdings#0x0057'})
        
        for symbol in symbols:
            params['symbol_mapping'].append(
               PointSymbol(value = symbol['name'],
                           icon = symbol['symbol']))

        return render_to_string('impact/styles/point_classes.sld', params) 
