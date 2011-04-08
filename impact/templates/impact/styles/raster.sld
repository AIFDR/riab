<?xml version="1.0" encoding="UTF-8"?>
<sld:UserStyle xmlns="http://www.opengis.net/sld" xmlns:sld="http://www.opengis.net/sld" xmlns:ogc="http://www.opengis.net/ogc" xmlns:gml="http://www.opengis.net/gml">
  <sld:Name>{{ name }}</sld:Name>
  <sld:Title>{{ name|title }}</sld:Title>
  <sld:Abstract>{{ name|title}</sld:Abstract>
  <sld:FeatureTypeStyle>
    <sld:Name>name</sld:Name>
    <sld:FeatureTypeName>Feature</sld:FeatureTypeName>
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
          <sld:ColorMapEntry color="#ffffff" opacity="0" quantity="-9999.0"/>
          <sld:ColorMapEntry color="#38A800" opacity="0" quantity="5.0"/>
          <sld:ColorMapEntry color="#38A800" quantity="5.5"/>
          <sld:ColorMapEntry color="#79C900" quantity="6"/>
          <sld:ColorMapEntry color="#CEED00" quantity="6.5"/>
          <sld:ColorMapEntry color="#FFCC00" quantity="7"/>
          <sld:ColorMapEntry color="#FF6600" quantity="7.5"/>
          <sld:ColorMapEntry color="#FF0000" quantity="8"/>
          <sld:ColorMapEntry color="#7A0000" quantity="10"/>
        </sld:ColorMap>
      </sld:RasterSymbolizer>
    </sld:Rule>
  </sld:FeatureTypeStyle>
</sld:UserStyle>
