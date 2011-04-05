from django.template.loader import render_to_string
from impact.plugins.core import FunctionProvider


class EarthquakeSchoolDamageFunction(FunctionProvider):
    """Risk plugin for earthquake damage to schools

    :param requires category=="hazard" and subcategory.startswith("earthquake") and layerType=="raster"
    :param requires category=="exposure" and subcategory.startswith("buildings") and layerType=="feature"
    """

    @staticmethod
    def run(hazard_data, exposure_data):
        """Risk plugin for earthquake school damage
        """

        # FIXME (Ole): Currently vector data comes as a 2-tuple with
        # coordinates and associated attributes.
        coordinates, shaking = hazard_data
        coordinates, schools = exposure_data

        school_damage = []
        for i in range(len(schools)):
            x = float(shaking[i].values()[0])
            if x < 6.0:
                value = 0.0
            else:
                value = (0.692 * (x ** 4) -
                         15.82 * (x ** 3) +
                         135.0 * (x ** 2) -
                         509.0 * x +
                         714.4)

            school_damage.append({'Percent_damage': value, 'MMI': x})

        return school_damage

    @staticmethod
    def generate_style(data):
        style_by = 'Percent_damage'
        impact_range = (0, 50)
        levels = 5
        return render_to_string('impact/styles/ladder.sld',
                                 {'field_name': style_by,
                                  'data_range': impact_range,
                                  'levels': levels})

