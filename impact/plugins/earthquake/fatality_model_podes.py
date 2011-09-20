import numpy
from impact.plugins.core import FunctionProvider
from impact.storage.raster import Raster
from impact.storage.vector import Vector, convert_polygons_to_centroids


class EarthquakeFatalityFunction(FunctionProvider):
    """Risk plugin for earthquake damage

    :author Allen
    :rating 1
    :param requires category=='hazard' and \
                subcategory.startswith('earthquake') and \
                layer_type=='raster'
    :param requires category=='exposure' and \
                subcategory.startswith('population') and \
                layer_type=='vector' and \
                datatype=='polygon'
    """

    target_field = 'FATALITIES'

    def run(self, layers,
            a=0.97429, b=11.037):
        """Risk plugin for earthquake fatalities

        Input
          layers: List of layers expected to contain
              H: Raster layer of MMI ground shaking
              E: Polygon population data
          a: Parameter for Allen impact function
          b: Parameter for Allen impact function
        """

        # Identify input layers
        H = layers[0]  # Intensity
        E = layers[1]  # Exposure - population counts

        assert E.is_polygon_data

        P = convert_polygons_to_centroids(E)
        P.write_to_file('Podes_centroids.shp')

        # Interpolate hazard level to building locations
        H = H.interpolate(P)

        # Extract relevant numerical data
        coordinates = E.get_geometry()  # Stay with polygons
        shaking = H.get_data()
        N = len(shaking)

        # List attributes to carry forward to result layer
        attributes = E.get_attribute_names()

        # Calculate fatilities
        count = 0
        total = 0

        result_feature_set = []
        for i in range(N):
            mmi = float(shaking[i].values()[0])
            if mmi < 0.0:
                # FIXME: Hack until interpolation is fixed
                mmi = 0.0

            population_count = E.get_data('Jumlah_Pen', i)

            # Calculate impact
            if numpy.isnan(mmi):
                F = 0.0
            else:
                F = 10 ** (a * mmi - b) * population_count

            # Collect shake level and calculated damage
            result_dict = {self.target_field: F,
                           'MMI': mmi}

            # Carry all orginal attributes forward
            for key in attributes:
                result_dict[key] = E.get_data(key, i)

            # Record result for this feature
            result_feature_set.append(result_dict)

            # Calculate statistics
            count += F
            total += population_count

        print
        print count, total

        # Create report
        caption = ('<table border="0" width="320px">'
                   '   <tr><td>%s&#58;</td><td>%i</td></tr>'
                   '   <tr><td>%s&#58;</td><td>%i</td></tr>'
                   '</table>' % ('Jumlah Penduduk', int(total),
                                 'Perkiraan meninggal', int(count)))


        # Create vector layer and return
        V = Vector(data=result_feature_set,
                   projection=E.get_projection(),
                   geometry=coordinates,
                   name='Estimated fatalities',
                   keywords={'caption': caption})
        return V



