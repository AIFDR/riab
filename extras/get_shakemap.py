"""Get Shakemap
"""

import os
import sys


def run(cmd):
    print cmd
    os.system(cmd)


def usage():
    print 'Usage:'
    print '%s <shakefile zipname>' % sys.argv[0]

if __name__ == '__main__':

    if len(sys.argv) != 2:
        usage()
    else:
        # Here is where we'll get the latest zip file
        # from geospasial.bnpb.go.id since is works
        # from within BNPB.

        zipfile = sys.argv[1]

        print '------------------------'
        print zipfile

        localname = os.path.split(zipfile)[-1]
        basename, ext = os.path.splitext(localname)

        msg = 'Input file %s should have extension .zip' % zipfile
        assert ext == '.zip', msg

        # Strip timestamp form names like 20110505155015.out
        timestamp, _ = os.path.splitext(basename)


        # Unzip
        print 'Unzipping file %s' % zipfile
        s = 'unzip -o %s' % zipfile
        run(s)

        print 'Getting MMI data'
        basefilename = 'shakemap_%s' % timestamp
        grd_filename = '%s.grd' % basefilename
        asc_filename = '%s.asc' % basefilename
        tif_filename = '%s.tif' % basefilename
        sld_filename = '%s.sld' % basefilename

        print basefilename
        print grd_filename
        print asc_filename

        s = ('cp usr/local/smap/data/%s/output/mi.grd %s'
             % (timestamp, grd_filename))
        run(s)

        # Convert grd file to asc
        s = 'python convert_gmt_grid.py %s' % grd_filename
        run(s)

        # View in QGIS
        d = os.environ['RIAB_HOME']

        basemap = '%s/riab_data/risiko_demo_data/backgrounds/Basemap_300dpi.tif' % d
        s = 'qgis %s %s &' % (basemap, asc_filename)
        run(s)

        # Upload to Risiko
        s = 'cp %s hazard_%s' % (tif_filename, tif_filename)
        run(s)
        s = 'cp %s hazard_%s' % (sld_filename, sld_filename)
        run(s)

        # Does not work yet
        s = '. %s/riab_env/bin/activate' % d
        run(s)

        print 'To upload this to Risiko, do in a separate terminal'
        print '  risiko-activate'
        print '  risiko-start'
        print 'Then'
        print '  risiko-activate'
        print '  %s/riab/scripts/risiko-upload hazard_%s' % (d, tif_filename)
