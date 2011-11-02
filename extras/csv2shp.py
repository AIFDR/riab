"""Convert csv file with spatial data to shp file
"""

import os
import csv
import sys
import glob
from impact.storage.vector import Vector
from impact.storage.projection import DEFAULT_PROJECTION

def csv2shp(path, lonname='Bujur', latname='Lintang'):

    # Read csv data
    reader = csv.DictReader(open(path, 'r'))
    data = []
    for x in reader:
        data.append(x)

    # Determine latitude and longitude fields
    fieldnames = reader.fieldnames
    msg = ('Could not find requested longitude "%s" in %s. Available '
           'field names are: %s' % (lonname, path, str(fieldnames)))
    assert lonname in fieldnames, msg

    msg = ('Could not find requested latitude "%s" in %s. Available '
           'field names are: %s' % (latname, path, str(fieldnames)))
    assert latname in fieldnames, msg

    # Extract point geometry
    lon = [float(x[lonname]) for x in data]
    lat = [float(x[latname]) for x in data]
    geometry = zip(lon, lat)
    #print geometry

    # Create vector object
    V = Vector(data=data, projection=DEFAULT_PROJECTION, geometry=geometry)

    #print path
    #print V.get_data()



    # Write as shapefile
    basename, _ = os.path.splitext(path)
    V.write_to_file(basename + '.shp')

    fid = open(basename + '.keywords', 'w')
    fid.write('category:exposure\n')
    fid.write('subcategory:building\n')
    fid.write('datatype:sigab\n')
    fid.close()

def usage():
    s = 'csv2shp.py [csvfile | dir]'
    return s


if __name__ == '__main__':

    if len(sys.argv) < 2:
        print usage()

    name = sys.argv[1]

    if os.path.isdir(name):
        for filename in glob.glob(name + '/*.csv'):
            print filename
            csv2shp(filename)
    else:
        csv2shp(name)


