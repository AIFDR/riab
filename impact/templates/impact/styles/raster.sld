<?xml version="1.0" encoding="UTF-8"?>
<sld:UserStyle xmlns="http://www.opengis.net/sld" xmlns:sld="http://www.opengis.net/sld" xmlns:ogc="http://www.opengis.net/ogc" xmlns:gml="http://www.opengis.net/gml">
  <sld:Name>{{ name }}</sld:Name>
  <sld:Title>{{ name|title }}</sld:Title>
  <sld:Abstract>{{ name|title }}</sld:Abstract>
  <sld:FeatureTypeStyle>
    <sld:Name>{{ name }}</sld:Name>
    <sld:Rule>
      <sld:RasterSymbolizer>
        <sld:Geometry>
          <ogc:PropertyName>geom</ogc:PropertyName>
        </sld:Geometry>
        <sld:ChannelSelection>
          <sld:GrayChannel>
            <sld:SourceChannelName>1</sld:SourceChannelName>
          </sld:GrayChannel>
        </sld:ChannelSelection>
        <sld:ColorMap>
          {% for cm in colormapentries %}
          <sld:ColorMapEntry color="{{ cm.color }}"
                             quantity="{{ cm.quantity }}"
          {% if cm.opacity %}opacity="{{ cm.opacity }}" {% endif %}
          />   
          {% endfor %}          
        </sld:ColorMap>
      </sld:RasterSymbolizer>
    </sld:Rule>
  </sld:FeatureTypeStyle>
</sld:UserStyle>
