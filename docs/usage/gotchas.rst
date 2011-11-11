Known limitations, bugs and gotchas
===================================

* Attribute names with blanks in them do not show up when querying layers.
This is annoying because shapefiles sometimes have this and will work fine in e.g. ESRI, QGIS and even GeoServer's owen previewing pane. This was flagged in https://github.com/AIFDR/riab/issues/177 but something that will have to be addressed by the GeoNode developers.

* Linked layers show up in the selection combo, but should never be selected
explicitly as they will be pulled in by other layers as per the keyword linked.


