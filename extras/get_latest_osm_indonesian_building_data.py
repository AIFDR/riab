"""Bring building data from kompetisiosm into Risiko

1. File buildings.zip is downloaded from data.kompetitisiosm.org
2. Unzip
3. Rename to OSM_building_footprints_indonesia_<date>.*
4. Create keywords and sld files
5. Upload to local Risiko server
"""

import os
import time
import datetime

zipfile = 'buildings.zip'
url = 'http://data.kompetisiosm.org/%s' % zipfile
timestamp = str(datetime.date.today()).replace('-', '')

# Create new area
tmpdir = '/tmp/OSM_tmp_%s_%s' % (timestamp, time.time())
os.mkdir(tmpdir)
os.chdir(tmpdir)

# Download
s = 'wget %s' % url
print
os.system(s)

# Unzip
s = 'unzip %s' % zipfile
print
os.system(s)

# Rename with todays ISO timestamp
dirname = os.path.splitext(zipfile)[0]
os.chdir(dirname)


basename = 'OSM_building_footprints_%s' % timestamp

s = ('rename -v "s/^building/%s/" building.*' % basename)
print s
os.system(s)

# Create keywords and sld files
fid = open(basename + '.keywords', 'w')
fid.write('''category: exposure
subcategory: building
title: OSM building footprints
datatype: osm
''')
fid.close()

fid = open(basename + '.sld', 'w')
fid.write('''<?xml version="1.0" encoding="UTF-8"?>
<sld:StyledLayerDescriptor xmlns="http://www.opengis.net/sld" xmlns:sld="http://www.opengis.net/sld" xmlns:ogc="http://www.opengis.net/ogc" xmlns:gml="http://www.opengis.net/gml" version="1.0.0">
  <sld:NamedLayer>
    <sld:Name>osm_building_polygons_20110905</sld:Name>
    <sld:UserStyle>
      <sld:Name>osm_building_polygons_20110905</sld:Name>
      <sld:Title/>
      <sld:FeatureTypeStyle>
        <sld:Name>name</sld:Name>
        <sld:Rule>
          <sld:PolygonSymbolizer>
            <sld:Fill>
              <sld:CssParameter name="fill">#888800</sld:CssParameter>
              <sld:CssParameter name="fill-opacity">0.5</sld:CssParameter>
            </sld:Fill>
            <sld:Stroke>
              <sld:CssParameter name="stroke">#000000</sld:CssParameter>
              <sld:CssParameter name="stroke-opacity">0.5</sld:CssParameter>
            </sld:Stroke>
          </sld:PolygonSymbolizer>
        </sld:Rule>
      </sld:FeatureTypeStyle>
    </sld:UserStyle>
  </sld:NamedLayer>
</sld:StyledLayerDescriptor>
''')
fid.close()

# Move and clean
s = 'mv %s.* ..' % basename
os.system(s)

os.chdir('..')
s = '/bin/rm -rf %s buildings' % zipfile
print s
os.system(s)

print 'Latest OSM data available in %s' % tmpdir

# Upload to Risiko
print 'To upload to Risiko, run'
print 'risiko-upload %s' % tmpdir




