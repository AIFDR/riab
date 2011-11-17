"""Merge multiple shp files into one with the union of their fields plus the root filename as an extra new field.
"""

import os
import csv
import sys
import glob
from impact.storage.vector import Vector
from impact.storage.projection import DEFAULT_PROJECTION

def merge_shp(filenames, newname):
    """Merge multiple shapfiles into one

    Input
        filenames: Input shape files
        newname: Name of merged shapefile

    Note: This has been tested for point data only
    """

    # Read shapefiles, determine datatype and union of attributes
    datasets = []
    keys = {}
    geometry_type = None
    for filename in filenames:
        msg = 'File %s is not a shp file' % filename
        assert filename.endswith('.shp'), msg

        v = Vector(filename)
        if geometry_type is None:
            geometry_type = v.geometry_type
            projection = v.get_projection()
        else:
            msg = ('Shapefiles must have same geometry type.'
                   'I got %s but expected %s' % (v.geometry_type,
                                                 geometry_type))
            assert geometry_type == v.geometry_type, msg

            msg = ('Shapefiles must have same projection.'
                   'I got %s but expected %s' % (v.get_projection(),
                                                 projection))
            assert projection == v.get_projection(), msg

        datasets.append(v)
        print 'Read filename %s' % filename

        # Get union of all attributes across datasets
        d = v.get_data()
        for key in d[0]:
            keys[key] = None

    print 'Read %i shapefiles' % len(filenames)

    # Merge
    print 'Merging'
    data = []
    geom = []
    for v in datasets:
        name = v.get_name()
        geometry = v.get_geometry()
        features = v.get_data()
        assert len(geometry) == len(features)

        for feature in features:
            # Add filename as new attribute
            feature['Asal'] = name

            # Augment attributes to make all sets have the same
            for key in keys:
                if key not in feature:
                    feature[key] = None

        # Join data
        assert len(geometry) == len(features)
        geom += geometry
        data += features


    V = Vector(data=data,
               projection=projection,
               geometry=geom)

    # Write as shapefile
    V.write_to_file(newname)

    basename, _ = os.path.splitext(newname)

    fid = open(basename + '.keywords', 'w')
    fid.write('category:exposure\n')
    fid.write('subcategory:building\n')
    fid.write('datatype:sigab\n')
    fid.close()

    print 'Created shape file %s' % newname
    print 'To upload to Risiko, run'
    print 'risiko-upload %s' % newname
    print

def usage():
    s = 'merge_shp.py dir'
    return s


if __name__ == '__main__':

    if len(sys.argv) < 2:
        print usage()
        import sys; sys.exit()

    dirname = sys.argv[1]
    if not os.path.isdir(dirname):
        print usage()
        import sys; sys.exit()

    newname = dirname + '.shp'

    merge_shp(glob.glob(dirname + '/*.shp'), newname)




