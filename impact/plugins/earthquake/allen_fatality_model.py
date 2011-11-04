from impact.plugins.core import FunctionProvider
from impact.storage.raster import Raster
import numpy


class EarthquakeFatalityFunction(FunctionProvider):
    """Risk plugin for earthquake damage

    :author Allen
    :rating 1
    :param requires category=='hazard' and \
                subcategory.startswith('earthquake') and \
                layer_type=='raster'
    :param requires category=='exposure' and \
                subcategory.startswith('population') and \
                layer_type=='raster'
    """

    @staticmethod
    def run(layers,
            a=0.97429, b=11.037):
        """Risk plugin for earthquake fatalities

        Input
          layers: List of layers expected to contain
              H: Raster layer of MMI ground shaking
              P: Raster layer of population data on the same grid as H
        """

        # Identify input layers
        intensity = layers[0]
        population = layers[1]

        # Extract data
        H = intensity.get_data(nan=0)
        P = population.get_data(nan=0)

        # Calculate impact
        F = 10 ** (a * H - b) * P

        # Generate text with result for this study
        count = numpy.nansum(F.flat)
        total = numpy.nansum(P.flat)

        # Create report
        caption = ('<table border="0" width="320px">'
                   '   <tr><td>%s&#58;</td><td>%i</td></tr>'
                   '   <tr><td>%s&#58;</td><td>%i</td></tr>'
                   '</table>' % ('Jumlah Penduduk', int(total),
                                 'Perkiraan Orang Meninggal', int(count)))

        # Create new layer and return
        R = Raster(F,
                   projection=population.get_projection(),
                   geotransform=population.get_geotransform(),
                   name='Estimated fatalities',
                   keywords={'caption': caption})
        return R
