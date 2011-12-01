import numpy
from numpy import nansum as sum
from impact.plugins.core import FunctionProvider
from impact.plugins.core import get_hazard_layer, get_exposure_layer
from impact.storage.raster import Raster


class FloodPovertyImpactFunction(FunctionProvider):
    """Risk plugin for flood poverty impact

    :author HKV
    :rating 1
    :param requires category=='hazard' and \
                    subcategory.startswith('flood') and \
                    layer_type=='raster' and \
                    unit=='m'

    :param requires category=='exposure' and \
                    subcategory.startswith('population') and \
                    layer_type=='raster' and \
                    datatype=='households'
    """

    plugin_name = 'Dalam bahaya'

    @staticmethod
    def run(layers):
        """Risk plugin for earthquake fatalities

        Input
          layers: List of layers expected to contain
              H: Raster layer of flood depth
              P: Raster layer of poor household density on the same grid as H
        """

        # Depth above which people are regarded affected [m]
        threshold = 1.0

        # Identify hazard and exposure layers
        inundation = get_hazard_layer(layers)  # Flood inundation [m]
        poor_households = get_exposure_layer(layers)  # Poverty density

        # Extract data as numeric arrays
        D = inundation.get_data(nan=0.0)  # Depth

        # This is the new generic way of scaling (issue #168 and #172)
        P = poor_households.get_data(nan=0.0, scaling=True)
        I = numpy.where(D > threshold, P, 0)

        # Generate text with result for this study
        total = str(int(sum(P.flat) / 1000))
        count = str(int(sum(I.flat) / 1000))

        # Create report
        caption = ('<b>Apabila terjadi "%s" perkiraan dampak terhadap "%s" '
                   'kemungkinan yang terjadi&#58;</b><br><br><p>' % (inundation.get_name(),
                                                    poor_households.get_name()))

        caption += ('<table border="0" width="320px">')
                   #'   <tr><td><b>%s&#58;</b></td>'
                   #'<td align="right"><b>%s</b></td></tr>'
                   #% ('Jumlah Rumah Tangga Miskin', total))

        caption += ('   <tr><td><b>%s&#58;</b></td>'
                    '<td align="right"><b>%s</b></td></tr>'
                    % ('Jumlah Rumah Tangga Terdampak (x 1000)', count))

        caption += '</table>'

        caption += '<br>'  # Blank separation row
        caption += '<b>Catatan&#58;</b><br>'
        caption += '- Jumlah Rumah Tangga Miskin %s<br>' % total
        caption += '- Jumlah dalam ribuan<br>'
        caption += ('- Rumah Tangga Miskin dalam bahaya ketika '
                    'banjir lebih dari %.1f m. ' % threshold)


        # Create raster object and return
        R = Raster(I,
                   projection=inundation.get_projection(),
                   geotransform=inundation.get_geotransform(),
                   name='People affected',
                   keywords={'caption': caption})
        return R

    def generate_style(self, data):
        """Generates and SLD file based on the data values
        """

        s = """<?xml version="1.0" encoding="UTF-8"?>
<sld:StyledLayerDescriptor xmlns="http://www.opengis.net/sld" xmlns:sld="http://www.opengis.net/sld" xmlns:ogc="http://www.opengis.net/ogc" xmlns:gml="http://www.opengis.net/gml" version="1.0.0">
  <sld:NamedLayer>
    <sld:Name>raster</sld:Name>
    <sld:UserStyle>
      <sld:Name>raster</sld:Name>
      <sld:Title>A very simple color map</sld:Title>
      <sld:Abstract>A very basic color map</sld:Abstract>
      <sld:FeatureTypeStyle>
        <sld:Name>name</sld:Name>
        <sld:FeatureTypeName>Feature</sld:FeatureTypeName>
        <sld:Rule>
          <sld:RasterSymbolizer>
            <sld:Geometry>
              <ogc:PropertyName>geom</ogc:PropertyName>
            </sld:Geometry>
            <sld:ChannelSelection>
              <sld:GrayChannel>
                <sld:SourceChannelName>1</sld:SourceChannelName>
              </sld:GrayChannel>
            </sld:ChannelSelection>
            <sld:ColorMap>
              <sld:ColorMapEntry color="#ffffff" opacity="0" quantity="-9999.0"/>
              <sld:ColorMapEntry color="#E1E1E1" quantity="0.1" opacity="0"/>
              <sld:ColorMapEntry color="#FFFFBE" quantity="0.25"/>
              <sld:ColorMapEntry color="#FFAA00" quantity="0.5"/>
              <sld:ColorMapEntry color="#FF6600" quantity="1.25"/>
              <sld:ColorMapEntry color="#FF0000" quantity="2.5"/>
              <sld:ColorMapEntry color="#CC0000" quantity="4"/>
              <sld:ColorMapEntry color="#730000" quantity="5"/>
              <sld:ColorMapEntry color="#330010" quantity="8"/>
            </sld:ColorMap>
          </sld:RasterSymbolizer>
        </sld:Rule>
      </sld:FeatureTypeStyle>
    </sld:UserStyle>
  </sld:NamedLayer>
</sld:StyledLayerDescriptor>
        """

        return s
