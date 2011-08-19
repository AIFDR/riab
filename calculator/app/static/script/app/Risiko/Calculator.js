/**
 * Copyright (c) 2009-2011 The Open Planning Project
 */

/*
 * @requires Risiko.js
 */

/** api: constructor
 *  .. class:: Risiko.Calculator
 *
 *    Risiko Calculator plugin.
 */
Risiko.Calculator = Ext.extend(gxp.plugins.Tool, {
    
    ptype: "app_calculator",
    
    /* @i18n begin */
    hazardComboLabelText: gettext("Hazard"),
    exposureComboLabelText: gettext("Exposure"),
    functionComboLabelText: gettext("Function"),
    resetButtonText: gettext("Reset"),
    calculateButtonText: gettext("Calculate"),
    calculatingText: gettext("Calculating"),
    calculatorTitleText: gettext("Impact Calculator"),
    hazardSelectText: gettext("Select Hazard ..."),
    exposureSelectText: gettext("Select Exposure ..."),
    functionSelectText: gettext("Select Function ..."),
    /* @i18n end */

    addOutput: function(config) {
        
        var exposurestore, hazardstore, combo_functionstore, popup,
            functionstore, bboxLayer,
            app = this.target,
            lastHazardSelect = "None",
            lastExposureSelect = "None",
            lastImpactSelect = "None",
            lastImpactLayer = "None";

        function drawBox(bbox) {
            var map = app.mapPanel.map;
            
            if (bboxLayer) {
                bboxLayer.destroy();
                bboxLayer = null;
            }
            bboxLayer = new OpenLayers.Layer.Vector("Calculation Extent", {
                styleMap: new OpenLayers.StyleMap({
                    strokeColor: "#000000",
                    strokeOpacity: 0.2,
                    strokeWidth: 3,
                    fillColor: "#00FF00",
                    fillOpacity: 0
                })
            });

            var feature = new OpenLayers.Feature.Vector(bbox.toGeometry());
            bboxLayer.addFeatures([feature]);
            
            map.addLayer(bboxLayer);
        };

        exposurestore = new Ext.data.JsonStore({
            id: 'exposurestore',
            fields: ['name', 'server_url'],
            autoLoad: true,
            url: '/impact/api/layers/?category=exposure',
            root: 'objects'
        });

        hazardstore = new Ext.data.JsonStore({
            id: 'hazardstore',
            fields: ['name', 'server_url'],
            autoLoad: true,
            url: '/impact/api/layers/?category=hazard',
            root: 'objects'
        });

        combo_functionstore = new Ext.data.JsonStore({
            id: 'combo_functionstore',
            fields: ['name','doc', 'layers'],
            root: 'functions'
        });

        function addLayer(server_url, label, layer_name, opacity_value, callback) {
            var record = app.createLayerRecord({
                name: layer_name,
                title: label,
                opacity: opacity_value,
                source: "0"
            }, function(rec) {
                var layer = rec.getLayer();
                rec.getLayer().attribution = "My attribution";
                app.mapPanel.layers.add(rec);
                if (callback) {
                    callback(rec);
                }
            });
        }

        function createPopup(feature) {
        	var content = "<div style='font-size:.9em; width:270px;'><b>" + feature.attributes.name + "</b><hr />" + "</div>";
        	popup = new GeoExt.Popup({
        		title: 'Details',
        		feature: feature,
        		width:270,
        		height:170,
        		html: content,
        		collapsible: true
        	});
        	popup.on({
        		close: function() {
        			if(OpenLayers.Util.indexOf(vecLayer.selectedFeatures, this.feature) > -1) {
        				selectControl.unselect(this.feature);
        			}
        		}
        	});
        	popup.show();
        }


        function removeLayer(layer_name){
            var map = app.mapPanel.map;
            var layers = map.getLayersByName(layer_name);
            if (layers.length > 0) {
        	//for each(var lay in layers){
        		map.removeLayer(layers[0]);
        	//  }
            }
        }

        function addLayerFromCombo(combo){
            var layer_name = combo.value;
            var id = combo.store.find('name', combo.value,0,true,false);
            var item = combo.store.data.items[id];
            addLayer(item.data.server_url, layer_name, layer_name, 0.5);
        }

        function hazardSelected(combo){
            removeLayer(lastHazardSelect);
            addLayerFromCombo(combo);
            Ext.getCmp('exposurecombo').enable();
            Ext.getCmp('functioncombo').disable();
            lastHazardSelect = combo.getValue();
        }

        // Need function store separate from the function combo box
        // since the combo box is rebuilt depending on the selection
        functionstore = new Ext.data.JsonStore({
            id: 'functionstore',
            fields: ['name','doc', 'layers'],
            autoLoad: true,
            url: '/impact/api/functions/',
            root: 'functions'
        });

        function reset_view() {
            var exposure = Ext.getCmp('exposurecombo');
            var hazard = Ext.getCmp('hazardcombo');

            removeLayer(exposure.getValue());
            removeLayer(hazard.getValue());
            removeLayer(lastImpactLayer);
            if (bboxLayer && bboxLayer.map) {
                app.mapPanel.map.removeLayer(bboxLayer);
            }
            lastImpactSelect = "None";
            lastExposureSelect = "None";
            lastHazardSelect = "None";
            exposure.setValue("");
            hazard.setValue("");
            exposure.disable();
            Ext.getCmp('functioncombo').disable();
            Ext.getCmp('functioncombo').setValue("");
            Ext.getCmp('resultpanel').getEl().update('');
        }

        function exposureSelected(combo){
            addLayerFromCombo(combo);
            // Get the complete list of functions and it's compatible layers
            var fCombo = Ext.getCmp('functioncombo');

            var hazard_name = Ext.getCmp('hazardcombo').value;
            var exposure_name = Ext.getCmp('exposurecombo').value;

            removeLayer(lastExposureSelect);
            lastExposureSelect = exposure_name;

            Ext.getCmp('functioncombo').enable();
            var items = functionstore.data.items;

            // Clear the function combobox
            fCombo.store.removeAll();
            fCombo.store.totalLength = 0;

            for (var ii=0; ii<items.length; ii++) {
            	var item = items[ii];
            	if (item.data == undefined){
                    continue;
                }
                var name = item.data.name;
                var layers = item.data.layers;
                var found_exposure = false;
                var found_hazard = false;
                // Find if hazard is in layers
                for (var li=0; li<layers.length; li++) {
            	    var lay=layers[li];
                    if (lay == exposure_name) {
                        found_exposure = true;
                    }
                    if (lay == hazard_name) {
                        found_hazard = true;
                    }
                }

                if (found_exposure && found_hazard) {
            	    // add the function name to the combo box
            	    fCombo.store.insert(0, new Ext.data.Record({name:name}));
            	    fCombo.setValue(name);
                }
            }

        }

        function showCaption(caption){
            var output = '<div>' + caption + '</div>';
            var resultPanel = Ext.getCmp('resultpanel').getEl().update(output);
        }

        function received(result, request) {
            var progressbar = Ext.getCmp('calculateprogress');
            progressbar.reset();
            progressbar.hide();

            var data = Ext.decode( result.responseText );
            if (data.errors !== null){
                Ext.MessageBox.alert('Calculation Failed:', data.errors);
                return;
            }
            reset_view();
            removeLayer(lastImpactLayer);
            var layer_uri = data.layer;
            var run_date = data.run_date;
            var run_duration = data.run_duration;
            var bbox = data.bbox;
            var caption = data.caption;
            var excel = data.excel;
            var exposure = data.exposure_layer;
            var hazard = data.hazard_layer;
            var base_url = layer_uri.split('/')[2];
            var server_url = data.ows_server_url;
            var result_name = layer_uri.split('/')[4].split(':')[1];
            var result_label = exposure + ' X ' + hazard + '=' +result_name;
            app.layerSources["0"].store.reload({
                callback: function() {
                    addLayer(server_url, result_label, "geonode:"+result_name, 0.9, function(rec) {
                        drawBox(rec.getLayer().maxExtent);
                    });
                    lastImpactLayer = result_label;
                    var layer_link = '<a  target="_blank" href="'+ layer_uri + '">Hasil peta</a><br><br>';
                    var excel_link = '';
                    if (excel !== undefined) {
                        excel_link = '<a href="'+ excel + '">Hasil table</a>';
                    };
                    showCaption(caption + '<br><br>' + layer_link + excel_link);
                }
            });
        }

        function calculate() {
            var hazardcombo = Ext.getCmp('hazardcombo');
            var exposurecombo = Ext.getCmp('exposurecombo');
            var hazardid = hazardcombo.store.find('name', hazardcombo.value,0,true,false);
            var exposureid = exposurecombo.store.find('name', exposurecombo.value,0,true,false);
            var hazarditem = hazardcombo.store.data.items[hazardid];
            var exposureitem = exposurecombo.store.data.items[exposureid];

            var hazard_layer = hazarditem.data.name;
            var exposure_layer = exposureitem.data.name;
            var hazard_server = hazarditem.data.server_url;
            var exposure_server = exposureitem.data.server_url;

            var impact_function = Ext.getCmp('functioncombo').getValue();
            var progressbar = Ext.getCmp('calculateprogress');

            var map = app.mapPanel.map;
            var bounds_original = map.getExtent();
            var bounds = bounds_original.transform(
                new OpenLayers.Projection('EPSG:900913'), new OpenLayers.Projection('EPSG:4326')
            );
            var bbox = bounds.toBBOX();
            progressbar.show();
            progressbar.wait({
                interval: 100,
                duration: 50000,
        	    increment: 5
        	});

            Ext.Ajax.request({
                url: '/impact/api/calculate/',
                loadMask: true,
                params: {
                    hazard_server: hazard_server,
                    hazard: hazard_layer,
                    exposure_server: hazard_server,
                    exposure: exposure_layer,
                    bbox: bbox,
                    keywords: 'test,riab_client',
                    impact_function: impact_function
                },
                method: 'POST',
                timeout: 1200000, // 20 minutes
                success: received,
                failure: function ( result, request) {
                    progressbar.hide();
                    progressbar.reset();
                    Ext.MessageBox.alert('Failed', result.responseText);
                }
            });
        }
        
        return Risiko.Calculator.superclass.addOutput.apply(this, [[{
            id: "calcform",
            title: this.calculatorTitleText,
            xtype: 'form',
            labelWidth: 80,
            frame: true,
            height: 200,
            border: false,
            items: [{
                xtype: 'combo',
                id: 'hazardcombo',
                store: hazardstore,
                displayField:'name',
                valueField: 'name',
                fieldLabel: this.hazardComboLabelText,
                typeAhead: true,
                mode: 'local',
                triggerAction: 'all',
                emptyText: this.hazardSelectText,
                selectOnFocus:false,
                listeners: {
                    "select": hazardSelected
                }
            }, {
                xtype: 'combo',
                id: 'exposurecombo',
                store: exposurestore,
                displayField:'name',
                valueField:'name',
                fieldLabel: this.exposureComboLabelText,
                typeAhead: true,
                mode: 'local',
                triggerAction: 'all',
                emptyText: this.exposureSelectText,
                selectOnFocus:false,
                disabled: true,
                listeners: {
                    "select": exposureSelected
                }
            }, {
                xtype: 'combo',
                id: 'functioncombo',
                store: combo_functionstore,
                displayField:'name',
                valueField:'name',
                fieldLabel: this.functionComboLabelText,
                typeAhead: true,
                mode: 'local',
                triggerAction: 'all',
                disabled: true,
                emptyText: this.functionSelectText,
                selectOnFocus:false
            }, {
                xtype: 'progress',
                id: 'calculateprogress',
		        cls: 'right-align',
                displayField:'name',
		        fieldLabel: this.calculatingText,
                hidden: true
	        }],
		    buttons: [{
		        text: this.resetButtonText,
			    handler: reset_view
			}, {
				text: this.calculateButtonText,
                handler: calculate
			}]
        }, {
            id: "resultpanelcontainer",
            title: 'Kalkulasi Hasil',
            flex: 1,
            frame: true,
            border: true,
            autoScroll: true,
            items: [{
                id: "resultpanel",
                html: ""
            }],
            xtype: "panel",
            defaults: {
                hideBorders: true
            }
        }, {
            id: "logopanel",
            height: 180,
            frame: false,
            border: false,
            html: "<div><p>"+
                    "<a href='http://bnpb.go.id' target='_blank'><img src='theme/app/img/bnpb_logo.png' alt='BNPB' title='BNPB' style='padding-left: 100px; float: left' /></a>"+
                  "</p></div>",
            xtype: "panel",
            defaults: {
                hideBorders: false
            }
        }]]);
    }
    
});


Ext.preg(Risiko.Calculator.prototype.ptype, Risiko.Calculator);
