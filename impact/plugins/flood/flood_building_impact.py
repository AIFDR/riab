from django.template.loader import render_to_string
from impact.plugins.core import FunctionProvider
from impact.plugins.core import get_hazard_layer, get_exposure_layer
from impact.storage.vector import Vector
from django.utils.translation import ugettext as _
from impact.plugins.utilities import PointZoomSize
from impact.plugins.utilities import PointClassColor
from impact.plugins.utilities import PointSymbol
import scipy.stats


class FloodBuildingImpactFunction(FunctionProvider):
    """Risk plugin for flood impact on building data

    :param requires category=='hazard' and \
                    subcategory.startswith('flood') and \
                    layer_type=='raster' and \
                    unit=='m'

    :param requires category=='exposure' and \
                    subcategory.startswith('building')
    """

    target_field = 'AFFECTED'
    plugin_name = 'Ditutup Sementara'

    def run(self, layers):
        """Risk plugin for tsunami population
        """

        threshold = 1.0  # Flood threshold [m]

        # Extract data
        H_org = get_hazard_layer(layers)    # Depth
        E = get_exposure_layer(layers)  # Building locations

        # FIXME (Ole): interpolate does not carry original name through,
        # so get_name gives "Vector Layer" :-)

        # Interpolate hazard level to building locations
        H = H_org.interpolate(E)

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
        building_impact = []
        for i in range(N):
            dep = float(depth[i].values()[0])

            # Tag and count
            if dep > threshold:
                affected = 99.5
                count += 1
            else:
                affected = 0

            # Collect depth and calculated damage
            result_dict = {'AFFECTED': affected,
                           'DEPTH': dep}

            # Carry all original attributes forward
            for key in attributes:
                result_dict[key] = E.get_data(key, i)

            # Record result for this feature
            building_impact.append(result_dict)

        # Create report
        caption = ('<b>Apabila terjadi "%s" perkiraan dampak terhadap "%s" '
                   'kemungkinan yang terjadi&#58;</b><br><br><p>' % (H_org.get_name(),
                                                    E.get_name()))
        caption += ('<table border="0" width="320px">'
                   '   <tr><th><b>%s</b></th><th><b>%s</b></th></th>'
                    '   <tr></tr>'
                    '   <tr><td>%s&#58;</td><td>%i</td></tr>'
                    '   <tr><td>%s &#58;</td><td>%i</td></tr>'
                    '   <tr><td>%s &#58;</td><td>%i</td></tr>'
                    #'   <tr><td>%s (> %.2f m) &#58;</td><td>%i</td></tr>'
                    #'   <tr><td>%s (< %.2f m) &#58;</td><td>%i</td></tr>'
                    '</table>' % (_('Gedung'), _('Jumlah'),
                                  _('Semua'), N,
                                  #_('Terendam'), threshold, count,
                                  #_('Tidak terendam'), threshold, N - count))
                                  _('Ditutup'), count,
                                  _('Dibuka'), N - count))

        caption += '<br>'  # Blank separation row
        caption += '<b>Anggapan&#58;</b><br>'
        caption += ('Bangunan perlu ditutup ketika banjir '
                   'lebih dari %.1f m' % threshold)

        # Create vector layer and return
        V = Vector(data=building_impact,
                   projection=E.get_projection(),
                   geometry=coordinates,
                   name='Estimated buildings affected',
                   keywords={'caption': caption})
        return V

    def generate_style(self, data):
        """Generates and SLD file based on the data values
        """

        if data.is_point_data:
            return self.generate_point_style(data)
        elif data.is_polygon_data:
            return self.generate_polygon_style(data)
        else:
            msg = 'Unknown style %s' % str(data)
            raise Exception(msg)

    def generate_polygon_style(self, data):
        """Generates a polygon SLD file based on the data values
        """

        # FIXME (Ole): Return static style to start with: ticket #144
        style = """<?xml version="1.0" encoding="UTF-8"?>
<sld:StyledLayerDescriptor xmlns="http://www.opengis.net/sld" xmlns:sld="http://www.opengis.net/sld" xmlns:ogc="http://www.opengis.net/ogc" xmlns:gml="http://www.opengis.net/gml" version="1.0.0">
  <sld:NamedLayer>
    <sld:Name>earthquake_impact</sld:Name>
    <sld:UserStyle>
      <sld:Name>earthquake_impact</sld:Name>
      <sld:Title/>
      <sld:FeatureTypeStyle>
        <sld:Name>name</sld:Name>
        <sld:Rule>
          <sld:Name>1</sld:Name>
          <sld:Title>Low</sld:Title>
          <ogc:Filter>
            <ogc:PropertyIsLessThan>
              <ogc:PropertyName>AFFECTED</ogc:PropertyName>
              <ogc:Literal>25</ogc:Literal>
            </ogc:PropertyIsLessThan>
          </ogc:Filter>
          <sld:PolygonSymbolizer>
            <sld:Fill>
              <sld:CssParameter name="fill">#1EFC7C</sld:CssParameter>
            </sld:Fill>
            <sld:Stroke>
              <sld:CssParameter name="stroke">#0EEC6C</sld:CssParameter>
            </sld:Stroke>
          </sld:PolygonSymbolizer>
        </sld:Rule>
        <sld:Rule>
          <sld:Name>2</sld:Name>
          <sld:Title>Medium</sld:Title>
          <ogc:Filter>
            <ogc:And>
            <ogc:PropertyIsGreaterThanOrEqualTo>
              <ogc:PropertyName>AFFECTED</ogc:PropertyName>
              <ogc:Literal>25</ogc:Literal>
              </ogc:PropertyIsGreaterThanOrEqualTo>
              <ogc:PropertyIsLessThan>
                <ogc:PropertyName>AFFECTED</ogc:PropertyName>
                <ogc:Literal>75</ogc:Literal>
              </ogc:PropertyIsLessThan>
            </ogc:And>
          </ogc:Filter>
          <sld:PolygonSymbolizer>
            <sld:Fill>
              <sld:CssParameter name="fill">#FD8D3C</sld:CssParameter>
            </sld:Fill>
            <sld:Stroke>
              <sld:CssParameter name="stroke">#ED7D2C</sld:CssParameter>
            </sld:Stroke>
          </sld:PolygonSymbolizer>
        </sld:Rule>
        <sld:Rule>
          <sld:Name>3</sld:Name>
          <sld:Title>High</sld:Title>
          <ogc:Filter>
            <ogc:PropertyIsGreaterThanOrEqualTo>
              <ogc:PropertyName>AFFECTED</ogc:PropertyName>
              <ogc:Literal>75</ogc:Literal>
              </ogc:PropertyIsGreaterThanOrEqualTo>
          </ogc:Filter>
          <sld:PolygonSymbolizer>
            <sld:Fill>
              <sld:CssParameter name="fill">#F31A1C</sld:CssParameter>
            </sld:Fill>
            <sld:Stroke>
              <sld:CssParameter name="stroke">#E30A0C</sld:CssParameter>
            </sld:Stroke>
          </sld:PolygonSymbolizer>
        </sld:Rule>
      </sld:FeatureTypeStyle>
    </sld:UserStyle>
  </sld:NamedLayer>
</sld:StyledLayerDescriptor>
"""

        return style


    def generate_point_style(self, data):
        """Generates and SLD file based on the data values
        """

        DEFAULT_SYMBOL = 'circle'

        symbol_field = None
        symbol_keys = [None, '']
        symbol_values = [DEFAULT_SYMBOL, DEFAULT_SYMBOL]

        scale_keys = [10000000000, 10000000, 5000000, 1000000,
                      500000, 250000, 100000]
        scale_values = [5, 5, 5, 5, 5, 8, 14]

        class_keys = ['Not affected', 'Greater than 10 cm']
        class_values = [{'min': 0, 'max': 90,
                         'color': '#cccccc', 'opacity': '0.2'},
                        {'min': 90, 'max': 100,
                         'color': '#F31a0c', 'opacity': '1'}]

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
