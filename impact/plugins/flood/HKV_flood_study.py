import numpy

from impact.plugins.core import FunctionProvider
from impact.storage.raster import Raster


class FloodImpactFunction(FunctionProvider):
    """Risk plugin for flood impact

    :author HKV
    :rating 1
    :param requires category=='hazard' and \
                    subcategory.startswith('flood') and \
                    layer_type=='raster' and \
                    unit=='m'
    :param requires category=='exposure' and \
                    subcategory.startswith('population') and \
                    layer_type=='raster'
    """

    @staticmethod
    def run(layers):
        """Risk plugin for earthquake fatalities

        Input
          layers: List of layers expected to contain
              H: Raster layer of flood depth
              P: Raster layer of population data on the same grid as H
        """

        # Depth above which people are regarded affected [m]
        threshold = 0.1
        thresholds = [0.1, 0.2, 0.3, 0.5, 0.8, 1.0]

        # Identify hazard and exposure layers
        inundation = layers[0]  # Flood inundation [m]
        population = layers[1]  # Population density [people/100000 m^2]

        # Extract data as numeric arrays
        D = inundation.get_data(nan=0.0)  # Depth

        # Calculate impact as population exposed to depths > threshold
        if population.get_resolution(native=True, isotropic=True) < 0.0005:
            # Keep this for backwards compatibility just a little while
            # This uses the original custom population set and
            # serves as a reference

            P = population.get_data(nan=0.0)  # Population density
            pixel_area = 2500
            I = numpy.where(D > threshold, P, 0) / 100000.0 * pixel_area
        else:
            # This is the new generic way of scaling (issue #168 and #172)
            P = population.get_data(nan=0.0, scaling=True)
            I = numpy.where(D > threshold, P, 0)

        # Generate text with result for this study
        number_of_people_affected = numpy.nansum(I.flat)
        caption = ('%i people affected by flood levels greater '
                   'than %i cm' % (number_of_people_affected,
                                   threshold * 100))

        # Create report
        caption = ('<table border="0" width="320px">'
                   '   <tr><th><b>%s</b></th><th><b>%s</b></th></th>'
                   '   <tr></tr>' % ('Min flood levels', 'People affected'))

        counts = []
        for i, threshold in enumerate(thresholds):
            I_tmp = numpy.where(D > threshold, P, 0)
            counts.append(numpy.nansum(I_tmp.flat))

            caption += '   <tr><td>%s m</td><td>%i</td></tr>' % (threshold,
                                                                 counts[i])

        caption += '</table>'

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
    <sld:Name>People affected by more than 1m of inundation</sld:Name>
    <sld:UserStyle>
      <sld:Name>People affected by more than 1m of inundation</sld:Name>
      <sld:Title>People Affected By More Than 1m Of Inundation</sld:Title>
      <sld:Abstract>People Affected By More Than 1m Of Inundation</sld:Abstract>
      <sld:FeatureTypeStyle>
        <sld:Name>People affected by more than 1m of inundation</sld:Name>
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
              <sld:ColorMapEntry color="#38A800" opacity="0" quantity="2"/>
              <sld:ColorMapEntry color="#38A800" quantity="5"/>
              <sld:ColorMapEntry color="#79C900" quantity="10"/>
              <sld:ColorMapEntry color="#CEED00" quantity="20"/>
              <sld:ColorMapEntry color="#FFCC00" quantity="50"/>
              <sld:ColorMapEntry color="#FF6600" quantity="100"/>
              <sld:ColorMapEntry color="#FF0000" quantity="200"/>
              <sld:ColorMapEntry color="#7A0000" quantity="300"/>
            </sld:ColorMap>
          </sld:RasterSymbolizer>
        </sld:Rule>
      </sld:FeatureTypeStyle>
    </sld:UserStyle>
  </sld:NamedLayer>
</sld:StyledLayerDescriptor>

        """

        return s
