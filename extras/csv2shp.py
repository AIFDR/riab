"""Convert csv file with spatial data to shp file
"""

import os
import csv
import sys
import glob
from impact.storage.vector import Vector
from impact.storage.projection import DEFAULT_PROJECTION

def csv2shp(path, lonname='Bujur', latname='Lintang'):
    """Convert spatial csv data to shapefile.

    Input
        path: absolute pathname of csv file
        lonname: Optional name for longitude
        latname: Optional name for latitude

    Output
        Dictionary of field names and their unique attribute values

    """

    # Dictionary of unique fieldnames and possible attribute values
    fields = {}

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

    # Record fieldnames
    for fieldname in fieldnames:
        fields[fieldname] = {}

    # Extract point geometry
    lon = [float(x[lonname]) for x in data]
    lat = [float(x[latname]) for x in data]
    geometry = zip(lon, lat)

    # Replace spaces in attribute names with underscores (issue #177)
    for i, D in enumerate(data):
        D_clean = {}
        for key in D:
            val = D[key]
            D_clean[key.replace(' ', '_')] = val

            # Record unique values
            if not val in fields[key]:
                fields[key][val] = 0

            fields[key][val] += 1

        # Store cleaned data point
        data[i] = D_clean

    # Create vector object
    V = Vector(data=data,
               projection=DEFAULT_PROJECTION,
               geometry=geometry)

    # Write as shapefile
    basename, _ = os.path.splitext(path)
    shpfile = basename + '.shp'
    V.write_to_file(shpfile)

    fid = open(basename + '.keywords', 'w')
    fid.write('category:exposure\n')
    fid.write('subcategory:building\n')
    fid.write('datatype:sigab\n')
    fid.close()

    print 'Created shape file %s' % shpfile
    print 'To upload to Risiko, run'
    print 'risiko-upload %s' % shpfile
    print

    return fields

def usage():
    s = 'csv2shp.py [csvfile | dir]'
    return s


if __name__ == '__main__':

    if len(sys.argv) < 2:
        print usage()

    name = sys.argv[1]

    if os.path.isdir(name):
        fields = {}
        for filename in glob.glob(name + '/*.csv'):
            D = csv2shp(filename)

            # Record all attributes and their unique values
            for key in D:
                if key not in fields:
                    fields[key] = {}

                for val in D[key]:
                    if val not in fields[key]:
                        fields[key][val] = 0

                    # Update count
                    fields[key][val] += D[key][val]


        print 'To upload entire directory to Risiko, run'
        print 'risiko-upload %s' % name
    else:
        fields = csv2shp(name)


    # Stats
    print
    for key in fields:
        if key.lower() in ['no', 'lintang', 'bujur', 'nama_obyek']:
            continue

        print
        print '%s:' % key
        for val in fields[key]:
            print '  %s [%i]' % (val, fields[key][val])

