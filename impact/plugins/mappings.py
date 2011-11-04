"""Collection of mappings for standard vulnerability classes
"""
import numpy
from impact.storage.vector import Vector


def osm2padang(E):
    """Map OSM attributes to Padang vulnerability classes

    This maps attributes collected in the OpenStreetMap exposure data
    (data.kompetisiosm.org) to 9 vulnerability classes identified by
    Geoscience Australia and ITB in the post 2009 Padang earthquake
    survey (http://trove.nla.gov.au/work/38470066).
    The mapping was developed by Abigail Baca, GFDRR.

    Input
        E: Vector object representing the OSM data

    Output:
        Vector object like E, but with one new attribute ('VCLASS')
        representing the vulnerability class used in the Padang dataset


    Algorithm

    1. Class the "levels" field into height bands where 1-3 = low,
       4-10 = mid, >10 = high
    2. Where height band = mid then building type = 4
       "RC medium rise Frame with Masonry in-fill walls"
    3. Where height band = high then building type = 6
       "Concrete Shear wall high rise* Hazus C2H"
    4. Where height band = low and structure = (plastered or
       reinforced_masonry) then building type = 7
       "RC low rise Frame with Masonry in-fill walls"
    5. Where height band = low and structure = confined_masonry then
       building type = 8 "Confined Masonry"
    6. Where height band = low and structure = unreinforced_masonry then
       building type = 2 "URM with Metal Roof"
    """

    # Input check
    required = ['levels', 'structure']
    actual = E.get_attribute_names()
    msg = ('Input data to osm2padang must have attributes %s. '
           'It has %s' % (str(required), str(actual)))
    for attribute in required:
        assert attribute in actual, msg

    # Start mapping
    N = len(E)
    attributes = E.get_data()
    count = 0
    for i in range(N):
        levels = E.get_data('levels', i)
        structure = E.get_data('structure', i)
        if levels is None or structure is None:
            vulnerability_class = 2
            count += 1
        else:
            if levels >= 10:
                # High
                vulnerability_class = 6  # Concrete shear
            elif 4 <= levels < 10:
                # Mid
                vulnerability_class = 4  # RC mid
            elif 1 <= levels < 4:
                # Low
                if structure in ['plastered',
                                 'reinforced masonry',
                                 'reinforced_masonry']:
                    vulnerability_class = 7  # RC low
                elif structure == 'confined_masonry':
                    vulnerability_class = 8  # Confined
                elif 'kayu' in structure or 'wood' in structure:
                    vulnerability_class = 9  # Wood
                else:
                    vulnerability_class = 2  # URM
            elif numpy.allclose(levels, 0):
                # A few buildings exist with 0 levels.

                # In general, we should be assigning here the most
                # frequent building in the area which could be defined
                # by admin boundaries.
                vulnerability_class = 2
            else:
                msg = 'Unknown number of levels: %s' % levels
                raise Exception(msg)

        # Store new attribute value
        attributes[i]['VCLASS'] = vulnerability_class

        # Selfcheck for use with osm_080811.shp
        if E.get_name() == 'osm_080811':
            if levels > 0:
                msg = ('Got %s expected %s. levels = %f, structure = %s'
                       % (vulnerability_class,
                          attributes[i]['TestBLDGCl'],
                          levels,
                          structure))
                assert numpy.allclose(attributes[i]['TestBLDGCl'],
                                      vulnerability_class), msg

    #print 'Got %i without levels or structure (out of %i total)' % (count, N)

    # Create new vector instance and return
    V = Vector(data=attributes,
               projection=E.get_projection(),
               geometry=E.get_geometry(),
               name=E.get_name() + ' mapped to Padang vulnerability classes',
               keywords=E.get_keywords())
    return V


def osm2bnpb(E, target_attribute='VCLASS'):
    """Map OSM attributes to BNPB vulnerability classes

    This maps attributes collected in the OpenStreetMap exposure data
    (data.kompetisiosm.org) to 2 vulnerability classes identified by
    BNPB in Kajian Risiko Gempabumi VERS 1.0, 2011. They are
    URM: Unreinforced Masonry and RM: Reinforced Masonry

    Input
        E: Vector object representing the OSM data
        target_attribute: Optional name of the attribute containing
                          the mapped vulnerability class. Default
                          value is 'VCLASS'

    Output:
        Vector object like E, but with one new attribute (e.g. 'VCLASS')
        representing the vulnerability class used in the guidelines
    """

    # Input check
    required = ['levels', 'structure']
    actual = E.get_attribute_names()
    msg = ('Input data to osm2bnpb must have attributes %s. '
           'It has %s' % (str(required), str(actual)))
    for attribute in required:
        assert attribute in actual, msg

    # Start mapping
    N = len(E)
    attributes = E.get_data()
    count = 0
    for i in range(N):
        levels = E.get_data('levels', i)
        structure = E.get_data('structure', i)
        if levels is None or structure is None:
            vulnerability_class = 'URM'
            count += 1
        else:
            if levels >= 4:
                # High
                vulnerability_class = 'RM'
            elif 1 <= levels < 4:
                # Low
                if structure in ['reinforced masonry',
                                 'reinforced_masonry']:
                    vulnerability_class = 'RM'
                elif structure == 'confined_masonry':
                    vulnerability_class = 'RM'
                elif 'kayu' in structure or 'wood' in structure:
                    vulnerability_class = 'RM'
                else:
                    vulnerability_class = 'URM'
            elif numpy.allclose(levels, 0):
                # A few buildings exist with 0 levels.

                # In general, we should be assigning here the most
                # frequent building in the area which could be defined
                # by admin boundaries.
                vulnerability_class = 'URM'
            else:
                msg = 'Unknown number of levels: %s' % levels
                raise Exception(msg)

        # Store new attribute value
        attributes[i][target_attribute] = vulnerability_class

    #print 'Got %i without levels or structure (out of %i total)' % (count, N)

    # Create new vector instance and return
    V = Vector(data=attributes,
               projection=E.get_projection(),
               geometry=E.get_geometry(),
               name=E.get_name() + ' mapped to BNPB vulnerability classes',
               keywords=E.get_keywords())
    return V


def unspecific2bnpb(E, target_attribute='VCLASS'):
    """Map Unspecific point data to BNPB vulnerability classes

    This makes no assumptions about attributes and maps everything to
    URM: Unreinforced Masonry

    Input
        E: Vector object representing the OSM data
        target_attribute: Optional name of the attribute containing
                          the mapped vulnerability class. Default
                          value is 'VCLASS'

    Output:
        Vector object like E, but with one new attribute (e.g. 'VCLASS')
        representing the vulnerability class used in the guidelines
    """

    # Start mapping
    N = len(E)
    attributes = E.get_data()
    count = 0
    for i in range(N):
        # Store new attribute value
        attributes[i][target_attribute] = 'URM'

    # Create new vector instance and return
    V = Vector(data=attributes,
               projection=E.get_projection(),
               geometry=E.get_geometry(),
               name=E.get_name() + ' mapped to BNPB vulnerability class URM',
               keywords=E.get_keywords())
    return V
