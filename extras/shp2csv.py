"""Convert csv file with spatial data to shp file
"""

import os
import csv
import sys
import glob
from impact.storage.vector import Vector
from impact.storage.projection import DEFAULT_PROJECTION

def shp2csv(filename):
    """Store shape file attribute table as csv file

    Geometry is ignored
    """

    basename, ext = os.path.splitext(filename)
    assert ext.endswith('shp')

    csvfilename = basename + '.csv'

    v = Vector(filename)
    headers = v.get_attribute_names()
    data = v.get_data()

    # Write headers
    fid = open(csvfilename, 'w')
    fid.write(','.join(headers) + '\n')

    # Write attribute values
    for x in data:
        s = ''
        for key in headers:
            val = str(x[key])
            s += val + ','
        s = s[:-1]
        fid.write(s + '\n')

    fid.close()


def usage():
    s = 'shp2csv.py [shpfile | dir]'
    return s


if __name__ == '__main__':

    if len(sys.argv) < 2:
        print usage()

    name = sys.argv[1]

    if os.path.isdir(name):
        fields = {}
        for filename in glob.glob(name + '/*.csv'):
            shp2csv(filename)
    else:
        shp2csv(name)
