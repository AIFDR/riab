<?xml version='1.0' encoding='UTF-8'?>
<sld:StyledLayerDescriptor xmlns:xlink='http://www.w3.org/1999/xlink' xmlns:gml='http://www.opengis.net/gml' xmlns:ogc='http://www.opengis.net/ogc' xmlns:xsi='http://www.w3.org/2001/XMLSchema-instance' version='1.0.0' xsi:schemaLocation='http://www.opengis.net/sld StyledLayerDescriptor.xsd' xmlns:sld='http://www.opengis.net/sld' >
    <sld:NamedLayer>
        <sld:Name><![CDATA[{{ name }}]]></sld:Name>
            <sld:UserStyle>
                <sld:FeatureTypeStyle>
{% for scale_size in scale_sizes %}
    {% for output_class in output_classes %}
        {% for symbol_map in symbol_mapping %}
                    <sld:Rule>
                        <sld:Name><![CDATA[{{ output_class.name }}% Damage]]></sld:Name>
                        <sld:Title><![CDATA[{{ output_class.name }}% Damage]]]></sld:Title>
                        <ogc:Filter>
                            <ogc:And>
                                <ogc:PropertyIsEqualTo>
                                    <ogc:PropertyName>{{ symbol_field }}</ogc:PropertyName>
                                    <ogc:Literal><![CDATA[{{ symbol_map.value }}]]></ogc:Literal>
                                </ogc:PropertyIsEqualTo>
                                <ogc:PropertyIsGreaterThanOrEqualTo>
                                    <ogc:PropertyName>{{ damage_field }}</ogc:PropertyName>
                                    <ogc:Literal>{{ output_class.clmin }}</ogc:Literal>
                                </ogc:PropertyIsGreaterThanOrEqualTo>
                                <ogc:PropertyIsLessThan>
                                    <ogc:PropertyName>{{ damage_field }}</ogc:PropertyName>
                                    <ogc:Literal>{{ output_class.clmax }}</ogc:Literal>
                                </ogc:PropertyIsLessThan>
                            </ogc:And>
                        </ogc:Filter>
                        <sld:MaxScaleDenominator>{{ scale_size.level }}</sld:MaxScaleDenominator>
                        <sld:PointSymbolizer>
                            <sld:Graphic>
                                <sld:Mark>
                                    <sld:WellKnownName>{{ symbol_map.icon }}</sld:WellKnownName>
                                    <sld:Fill>
                                        <sld:CssParameter name='fill' >{{ output_class.fill_color }}</sld:CssParameter>
                                        <sld:CssParameter name='fill-opacity' >1</sld:CssParameter>
                                    </sld:Fill>
                                    <sld:Stroke>
                                        <sld:CssParameter name='stroke' >#000000</sld:CssParameter>
                                        <sld:CssParameter name='stroke-opacity' >1</sld:CssParameter>
                                    </sld:Stroke>
                                </sld:Mark>
                                <sld:Size>{{ scale_size.size }}</sld:Size>
                            </sld:Graphic>
                        </sld:PointSymbolizer>
                    </sld:Rule>
        {% endfor %} 
    {% endfor %} 
{% endfor %} 
                </sld:FeatureTypeStyle>
            </sld:UserStyle>
    </sld:NamedLayer>
</sld:StyledLayerDescriptor>
