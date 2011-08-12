<?xml version="1.0" encoding="UTF-8"?>
<sld:UserStyle xmlns="http://www.opengis.net/sld" xmlns:sld="http://www.opengis.net/sld" xmlns:ogc="http://www.opengis.net/ogc" xmlns:gml="http://www.opengis.net/gml">
  <sld:Name>{{ name }}</sld:Name>
  <sld:Title>{{ name|title}} Building loss: Attribute-based point</sld:Title>
  <sld:FeatureTypeStyle>
    <sld:Name>name</sld:Name>
    <sld:Rule>
      <sld:Name>2%</sld:Name>
      <sld:Title>0 to 2.0</sld:Title>
      <ogc:Filter>
        <ogc:PropertyIsLessThan>
          <ogc:PropertyName>{{ damage_field }}</ogc:PropertyName>
          <ogc:Literal>2.0</ogc:Literal>
        </ogc:PropertyIsLessThan>
      </ogc:Filter>
      <sld:PointSymbolizer>
        <sld:Graphic>
          <sld:Mark>
            <sld:Fill>
              <sld:CssParameter name="fill">#FFFFBE</sld:CssParameter>
            </sld:Fill>
{% if stroke %}
            <sld:Stroke>
              <sld:CssParameter name="stroke-width">2</sld:CssParameter>
            </sld:Stroke>
{% endif %}
          </sld:Mark>
          <sld:Size>
            <ogc:Literal>10</ogc:Literal>
          </sld:Size>
        </sld:Graphic>
      </sld:PointSymbolizer>
    </sld:Rule>
    <sld:Rule>
      <sld:Name>10%</sld:Name>
      <sld:Title>2.1 to 10</sld:Title>
      <ogc:Filter>
        <ogc:And>
          <ogc:PropertyIsGreaterThanOrEqualTo>
            <ogc:PropertyName>{{ damage_field }}</ogc:PropertyName>
            <ogc:Literal>2.0</ogc:Literal>
          </ogc:PropertyIsGreaterThanOrEqualTo>
          <ogc:PropertyIsLessThan>
            <ogc:PropertyName>{{ damage_field }}</ogc:PropertyName>
            <ogc:Literal>10</ogc:Literal>
          </ogc:PropertyIsLessThan>
        </ogc:And>
      </ogc:Filter>
      <sld:PointSymbolizer>
        <sld:Graphic>
          <sld:Mark>
            <sld:WellKnownName>SQUARE</sld:WellKnownName>
            <sld:Fill>
              <sld:CssParameter name="fill">#F5B800</sld:CssParameter>
            </sld:Fill>
{% if stroke %}
           <sld:Stroke>
              <sld:CssParameter name="stroke-width">2</sld:CssParameter>
            </sld:Stroke>
{% endif %}
          </sld:Mark>
          <sld:Size>
            <ogc:Literal>10</ogc:Literal>
          </sld:Size>
        </sld:Graphic>
      </sld:PointSymbolizer>
    </sld:Rule>
    <sld:Rule>
      <sld:Name>25%</sld:Name>
      <sld:Title>10.1 to 25</sld:Title>
      <ogc:Filter>
        <ogc:And>
          <ogc:PropertyIsGreaterThanOrEqualTo>
            <ogc:PropertyName>{{ damage_field }}</ogc:PropertyName>
            <ogc:Literal>10.0</ogc:Literal>
          </ogc:PropertyIsGreaterThanOrEqualTo>
          <ogc:PropertyIsLessThan>
            <ogc:PropertyName>{{ damage_field }}</ogc:PropertyName>
            <ogc:Literal>25</ogc:Literal>
          </ogc:PropertyIsLessThan>
        </ogc:And>
      </ogc:Filter>
      <sld:PointSymbolizer>
        <sld:Graphic>
          <sld:Mark>
            <sld:WellKnownName>SQUARE</sld:WellKnownName>
            <sld:Fill>
              <sld:CssParameter name="fill">#F57A00</sld:CssParameter>
            </sld:Fill>
{% if stroke %}
            <sld:Stroke>
              <sld:CssParameter name="stroke-width">2</sld:CssParameter>
            </sld:Stroke>
{% endif %}
          </sld:Mark>
          <sld:Size>
            <ogc:Literal>10</ogc:Literal>
          </sld:Size>
        </sld:Graphic>
      </sld:PointSymbolizer>
    </sld:Rule>
    <sld:Rule>
      <sld:Name>50%</sld:Name>
      <sld:Title>25.1 to 50</sld:Title>
      <ogc:Filter>
        <ogc:And>
          <ogc:PropertyIsGreaterThanOrEqualTo>
            <ogc:PropertyName>{{ damage_field }}</ogc:PropertyName>
            <ogc:Literal>25.0</ogc:Literal>
          </ogc:PropertyIsGreaterThanOrEqualTo>
          <ogc:PropertyIsLessThan>
            <ogc:PropertyName>{{ damage_field }}</ogc:PropertyName>
            <ogc:Literal>50</ogc:Literal>
          </ogc:PropertyIsLessThan>
        </ogc:And>
      </ogc:Filter>
      <sld:PointSymbolizer>
        <sld:Graphic>
          <sld:Mark>
            <sld:WellKnownName>SQUARE</sld:WellKnownName>
            <sld:Fill>
              <sld:CssParameter name="fill">#F53D00</sld:CssParameter>
            </sld:Fill>
{% if stroke %}
            <sld:Stroke>
              <sld:CssParameter name="stroke-width">2</sld:CssParameter>
            </sld:Stroke>
{% endif %}
          </sld:Mark>
          <sld:Size>
            <ogc:Literal>10</ogc:Literal>
          </sld:Size>
        </sld:Graphic>
      </sld:PointSymbolizer>
    </sld:Rule>
    <sld:Rule>
      <sld:Name>ABOVE50%</sld:Name>
      <sld:Title>Greater than 50</sld:Title>
      <ogc:Filter>
        <ogc:PropertyIsGreaterThanOrEqualTo>
          <ogc:PropertyName>{{ damage_field }}</ogc:PropertyName>
          <ogc:Literal>50</ogc:Literal>
        </ogc:PropertyIsGreaterThanOrEqualTo>
      </ogc:Filter>
      <sld:PointSymbolizer>
        <sld:Graphic>
          <sld:Mark>
            <sld:WellKnownName>SQUARE</sld:WellKnownName>
            <sld:Fill>
              <sld:CssParameter name="fill">#A80000</sld:CssParameter>
            </sld:Fill>
{% if stroke %}
            <sld:Stroke>
              <sld:CssParameter name="stroke-width">2</sld:CssParameter>
            </sld:Stroke>
{% endif %}
          </sld:Mark>
          <sld:Size>
            <ogc:Literal>10</ogc:Literal>
          </sld:Size>
        </sld:Graphic>
      </sld:PointSymbolizer>
    </sld:Rule>
  </sld:FeatureTypeStyle>
</sld:UserStyle>
