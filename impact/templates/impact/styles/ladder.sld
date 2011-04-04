<?xml version="1.0" encoding="UTF-8"?>
<sld:UserStyle xmlns="http://www.opengis.net/sld" xmlns:sld="http://www.opengis.net/sld" xmlns:ogc="http://www.opengis.net/ogc" xmlns:gml="http://www.opengis.net/gml">
  <sld:Name>ladder</sld:Name>
  <sld:Title/>
  <sld:IsDefault>1</sld:IsDefault>
  <sld:FeatureTypeStyle>
    <sld:Name>name</sld:Name>
    <sld:Rule>

      <sld:Title>40-50</sld:Title>
      <ogc:Filter>
        <ogc:And>
          <ogc:PropertyIsLessThanOrEqualTo>
            <ogc:PropertyName>Percent_da</ogc:PropertyName>
            <ogc:Literal>50</ogc:Literal>
          </ogc:PropertyIsLessThanOrEqualTo>

          <ogc:PropertyIsGreaterThan>
            <ogc:PropertyName>Percent_da</ogc:PropertyName>
            <ogc:Literal>40</ogc:Literal>
          </ogc:PropertyIsGreaterThan>
        </ogc:And>
      </ogc:Filter>
      <sld:PointSymbolizer>
        <sld:Graphic>

          <sld:Mark>
            <sld:Fill>
              <sld:CssParameter name="fill">#F40606</sld:CssParameter>
              <sld:CssParameter name="fill-opacity">1</sld:CssParameter>
            </sld:Fill>
          </sld:Mark>
          <sld:Size>
            <ogc:Literal>5</ogc:Literal>

          </sld:Size>
        </sld:Graphic>
      </sld:PointSymbolizer>
      <sld:TextSymbolizer>
        <sld:Label>
          <ogc:PropertyName>Percent_da</ogc:PropertyName>
        </sld:Label>
        <sld:Font>

          <sld:CssParameter name="font-family">Serif</sld:CssParameter>
          <sld:CssParameter name="font-size">8</sld:CssParameter>
          <sld:CssParameter name="font-style">normal</sld:CssParameter>
          <sld:CssParameter name="font-weight">normal</sld:CssParameter>
        </sld:Font>
        <sld:LabelPlacement>
          <sld:PointPlacement>

            <sld:AnchorPoint>
              <sld:AnchorPointX>
                <ogc:Literal>0.0</ogc:Literal>
              </sld:AnchorPointX>
              <sld:AnchorPointY>
                <ogc:Literal>0.5</ogc:Literal>
              </sld:AnchorPointY>
            </sld:AnchorPoint>

            <sld:Rotation>
              <ogc:Literal>0</ogc:Literal>
            </sld:Rotation>
          </sld:PointPlacement>
        </sld:LabelPlacement>
        <sld:Fill>
          <sld:CssParameter name="fill">#FC0C0C</sld:CssParameter>
          <sld:CssParameter name="fill-opacity">1</sld:CssParameter>

        </sld:Fill>
      </sld:TextSymbolizer>
    </sld:Rule>
    <sld:Rule>
      <sld:Title>30-40</sld:Title>
      <ogc:Filter>
        <ogc:And>
          <ogc:PropertyIsLessThanOrEqualTo>

            <ogc:PropertyName>Percent_da</ogc:PropertyName>
            <ogc:Literal>40</ogc:Literal>
          </ogc:PropertyIsLessThanOrEqualTo>
          <ogc:PropertyIsGreaterThan>
            <ogc:PropertyName>Percent_da</ogc:PropertyName>
            <ogc:Literal>60</ogc:Literal>
          </ogc:PropertyIsGreaterThan>

        </ogc:And>
      </ogc:Filter>
      <sld:PointSymbolizer>
        <sld:Graphic>
          <sld:Mark>
            <sld:Fill>
              <sld:CssParameter name="fill">#F97E04</sld:CssParameter>
              <sld:CssParameter name="fill-opacity">1</sld:CssParameter>

            </sld:Fill>
          </sld:Mark>
          <sld:Size>
            <ogc:Literal>5</ogc:Literal>
          </sld:Size>
        </sld:Graphic>
      </sld:PointSymbolizer>
      <sld:TextSymbolizer>

        <sld:Label>
          <ogc:PropertyName>Percent_da</ogc:PropertyName>
        </sld:Label>
        <sld:Font>
          <sld:CssParameter name="font-family">Serif</sld:CssParameter>
          <sld:CssParameter name="font-size">8</sld:CssParameter>
          <sld:CssParameter name="font-style">normal</sld:CssParameter>

          <sld:CssParameter name="font-weight">normal</sld:CssParameter>
        </sld:Font>
        <sld:LabelPlacement>
          <sld:PointPlacement>
            <sld:AnchorPoint>
              <sld:AnchorPointX>
                <ogc:Literal>0.0</ogc:Literal>
              </sld:AnchorPointX>

              <sld:AnchorPointY>
                <ogc:Literal>0.5</ogc:Literal>
              </sld:AnchorPointY>
            </sld:AnchorPoint>
            <sld:Rotation>
              <ogc:Literal>0</ogc:Literal>
            </sld:Rotation>
          </sld:PointPlacement>

        </sld:LabelPlacement>
        <sld:Fill>
          <sld:CssParameter name="fill">#FA7E03</sld:CssParameter>
          <sld:CssParameter name="fill-opacity">1</sld:CssParameter>
        </sld:Fill>
      </sld:TextSymbolizer>
    </sld:Rule>
    <sld:Rule>

      <sld:Title>20-30</sld:Title>
      <ogc:Filter>
        <ogc:And>
          <ogc:PropertyIsLessThanOrEqualTo>
            <ogc:PropertyName>Percent_da</ogc:PropertyName>
            <ogc:Literal>30</ogc:Literal>
          </ogc:PropertyIsLessThanOrEqualTo>

          <ogc:PropertyIsGreaterThan>
            <ogc:PropertyName>Percent_da</ogc:PropertyName>
            <ogc:Literal>20</ogc:Literal>
          </ogc:PropertyIsGreaterThan>
        </ogc:And>
      </ogc:Filter>
      <sld:PointSymbolizer>
        <sld:Graphic>

          <sld:Mark>
            <sld:Fill>
              <sld:CssParameter name="fill">#F9CC01</sld:CssParameter>
              <sld:CssParameter name="fill-opacity">1</sld:CssParameter>
            </sld:Fill>
          </sld:Mark>
          <sld:Size>
            <ogc:Literal>5</ogc:Literal>

          </sld:Size>
        </sld:Graphic>
      </sld:PointSymbolizer>
      <sld:TextSymbolizer>
        <sld:Label>
          <ogc:PropertyName>Percent_da</ogc:PropertyName>
        </sld:Label>
        <sld:Font>

          <sld:CssParameter name="font-family">Serif</sld:CssParameter>
          <sld:CssParameter name="font-size">8</sld:CssParameter>
          <sld:CssParameter name="font-style">normal</sld:CssParameter>
          <sld:CssParameter name="font-weight">normal</sld:CssParameter>
        </sld:Font>
        <sld:LabelPlacement>
          <sld:PointPlacement>

            <sld:AnchorPoint>
              <sld:AnchorPointX>
                <ogc:Literal>0.0</ogc:Literal>
              </sld:AnchorPointX>
              <sld:AnchorPointY>
                <ogc:Literal>0.5</ogc:Literal>
              </sld:AnchorPointY>
            </sld:AnchorPoint>

            <sld:Rotation>
              <ogc:Literal>0</ogc:Literal>
            </sld:Rotation>
          </sld:PointPlacement>
        </sld:LabelPlacement>
        <sld:Fill>
          <sld:CssParameter name="fill-opacity">1</sld:CssParameter>
        </sld:Fill>

      </sld:TextSymbolizer>
    </sld:Rule>
    <sld:Rule>
      <sld:Title>10-20</sld:Title>
      <ogc:Filter>
        <ogc:And>
          <ogc:PropertyIsLessThanOrEqualTo>
            <ogc:PropertyName>Percent_da</ogc:PropertyName>

            <ogc:Literal>20</ogc:Literal>
          </ogc:PropertyIsLessThanOrEqualTo>
          <ogc:PropertyIsGreaterThan>
            <ogc:PropertyName>Percent_da</ogc:PropertyName>
            <ogc:Literal>20</ogc:Literal>
          </ogc:PropertyIsGreaterThan>
        </ogc:And>

      </ogc:Filter>
      <sld:PointSymbolizer>
        <sld:Graphic>
          <sld:Mark>
            <sld:Fill>
              <sld:CssParameter name="fill">#CFD1B3</sld:CssParameter>
              <sld:CssParameter name="fill-opacity">1</sld:CssParameter>
            </sld:Fill>

          </sld:Mark>
          <sld:Size>
            <ogc:Literal>5</ogc:Literal>
          </sld:Size>
        </sld:Graphic>
      </sld:PointSymbolizer>
      <sld:TextSymbolizer>
        <sld:Label>

          <ogc:PropertyName>Percent_da</ogc:PropertyName>
        </sld:Label>
        <sld:Font>
          <sld:CssParameter name="font-family">Serif</sld:CssParameter>
          <sld:CssParameter name="font-size">8</sld:CssParameter>
          <sld:CssParameter name="font-style">normal</sld:CssParameter>
          <sld:CssParameter name="font-weight">normal</sld:CssParameter>

        </sld:Font>
        <sld:LabelPlacement>
          <sld:PointPlacement>
            <sld:AnchorPoint>
              <sld:AnchorPointX>
                <ogc:Literal>0.0</ogc:Literal>
              </sld:AnchorPointX>
              <sld:AnchorPointY>

                <ogc:Literal>0.5</ogc:Literal>
              </sld:AnchorPointY>
            </sld:AnchorPoint>
            <sld:Rotation>
              <ogc:Literal>0</ogc:Literal>
            </sld:Rotation>
          </sld:PointPlacement>
        </sld:LabelPlacement>

        <sld:Fill>
          <sld:CssParameter name="fill">#D4D6B8</sld:CssParameter>
          <sld:CssParameter name="fill-opacity">1</sld:CssParameter>
        </sld:Fill>
      </sld:TextSymbolizer>
    </sld:Rule>
    <sld:Rule>
      <sld:Title>0-10</sld:Title>

      <ogc:Filter>
        <ogc:And>
          <ogc:PropertyIsLessThanOrEqualTo>
            <ogc:PropertyName>Percent_da</ogc:PropertyName>
            <ogc:Literal>10</ogc:Literal>
          </ogc:PropertyIsLessThanOrEqualTo>
          <ogc:PropertyIsGreaterThan>
            <ogc:PropertyName>Percent_da</ogc:PropertyName>

            <ogc:Literal>0</ogc:Literal>
          </ogc:PropertyIsGreaterThan>
        </ogc:And>
      </ogc:Filter>
      <sld:PointSymbolizer>
        <sld:Graphic>
          <sld:Mark>
            <sld:Fill>

              <sld:CssParameter name="fill-opacity">1</sld:CssParameter>
            </sld:Fill>
          </sld:Mark>
          <sld:Size>
            <ogc:Literal>5</ogc:Literal>
          </sld:Size>
        </sld:Graphic>
      </sld:PointSymbolizer>

    </sld:Rule>
  </sld:FeatureTypeStyle>
</sld:UserStyle>
