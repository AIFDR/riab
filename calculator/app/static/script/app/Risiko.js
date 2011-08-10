/**
 * Copyright (c) 2009-2011 The Open Planning Project
 */

/**
 * Constructor: Risiko
 * Create a new Risiko application.
 *
 * Parameters:
 * config - {Object} Optional application configuration properties.
 *
 * Valid config properties:
 * map - {Object} Map configuration object.
 * ows - {String} OWS URL
 *
 * Valid map config properties:
 * layers - {Array} A list of layer configuration objects.
 * center - {Array} A two item array with center coordinates.
 * zoom - {Number} An initial zoom level.
 *
 * Valid layer config properties:
 * name - {String} Required WMS layer name.
 * title - {String} Optional title to display for layer.
 */
var Risiko = Ext.extend(gxp.Viewer, {
    
    constructor: function(config) {
        config = Ext.applyIf(config || {}, {
            proxy: "/proxy?url=",
            portalConfig: {
                layout: "border",
                region: "center",

                // by configuring items here, we don't need to configure portalItems
                // and save a wrapping container
                items: [{
                    id: "centerpanel",
                    xtype: "panel",
                    layout: "fit",
                    region: "center",
                    border: false,
                    items: ["map"]
                }, {
                    id: "westpanel",
                    xtype: "container",
                    layout: "fit",
                    region: "west",
                    width: 200
                }, {
                    id: "east",
                    region: "east",
                    width: 290,
                    collapsible: true,
                    collapseMode: "mini",
                    header: false,
                    border: false,
                    layout: "vbox",
                    defaults: {
                        align: 'stretch',
                        pack: 'start',
                        padding: 10
                    },
                    items:[{
                        id: "calcform",
                        title: this.calculatorTitleText,
                        xtype: 'form',
                        labelWidth: 60,
                        height: 180,
                        split: true,
                        items: [{
                            xtype: 'combo',
                            id: 'hazardcombo',
                            store: hazardstore,
                            width: '100%',
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
                            width: '100%',
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
                            store: this.combo_functionstore,
                            width: '100%',
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
                        id: "logopanel",
                        flex: 2,
                        frame: false,
                        border: false,
                        width: '100%',
                        html: "<div><p>"+
                                "<img src='theme/app/img/bnpb_logo.jpg' alt='BNPB' title='BNPB' width=120 style='padding-left: 10px; float: left' />"+
                                "<img src='theme/app/img/bppt_logo.jpg' alt='BPPT' title='BPPT' width=120 style='padding-right: 10px; padding-top: 20px;float: right' />" +
                                "<img src='theme/app/img/gfdrr.jpg' alt='GFDRR' title='GFDRR' width=100 style='padding-left: 20px; float: left;' />" +
                                "<img src='theme/app/img/aifdr.png' alt='AIFDR' title='AIFDR' width=100 style='padding-right: 20px; float: right;' />" +
                              "</p></div>",
                        xtype: "panel",
                        defaults: {
                            hideBorders: true
                        }
                    }]
                }]
            },

            // configuration of all tool plugins for this application
            tools: [{
                ptype: "gxp_layertree",
                outputConfig: {
                    id: "tree",
                    border: true,
                    tbar: [] // we will add buttons to "tree.bbar" later
                },
                outputTarget: "westpanel"
            }, {
                ptype: "gxp_addlayers",
                actionTarget: "tree.tbar"
            }, {
                ptype: "gxp_removelayer",
                actionTarget: ["tree.tbar", "tree.contextMenu"]
            }, {
                ptype: "gxp_zoomtoextent",
                actionTarget: "map.tbar"
            }, {
                ptype: "gxp_zoom",
                actionTarget: "map.tbar"
            }, {
                ptype: "gxp_navigationhistory",
                actionTarget: "map.tbar"
            }],

            // map items
            mapItems: [{
                xtype: "gx_zoomslider",
                vertical: true,
                height: 100
            }]
        });
        
        Risiko.superclass.constructor.apply(this, [config]);
    },

    /**
     * api: config[localGeoServerBaseUrl]
     * ``String`` url of the local GeoServer instance
     */
    localGeoServerBaseUrl: "",

    /**
     * api: config[fromLayer]
     * ``Boolean`` true if map view was loaded with layer parameters
     */
    fromLayer: false,

    /**
     * private: property[mapPanel]
     * the :class:`GeoExt.MapPanel` instance for the main viewport
     */
    mapPanel: null,

    /**
     * Property: legendPanel
     * {GeoExt.LegendPanel} the legend for the main viewport's map
     */
    legendPanel: null,

    /**
     * Property: toolbar
     * {Ext.Toolbar} the toolbar for the main viewport
     */
    toolbar: null,

    /**
     * Property: capGrid
     * {<Ext.Window>} A window which includes a CapabilitiesGrid panel.
     */
    capGrid: null,

    /**
     * Property: modified
     * ``Number``
     */
    modified: 0,

    /**
     * Property: popupCache
     * {Object} An object containing references to visible popups so that
     *     we can insert responses from multiple requests.
     */
    popupCache: null,

    /** private: property[propDlgCache]
     *  ``Object``
     */
    propDlgCache: null,

    /** private: property[stylesDlgCache]
     *  ``Object``
     */
    stylesDlgCache: null,

    /** private: property[busyMask]
     *  ``Ext.LoadMask``
     */
    busyMask: null,

    /** private: property[urlPortRegEx]
     *  ``RegExp``
     */
    urlPortRegEx: /^(http[s]?:\/\/[^:]*)(:80|:443)?\//,

    //TODO i18n from gxp, move Indonesian GeoExplorer translations to gxp
    //Risiko
    hazardComboLabelText: "Hazard",
    exposureComboLabelText: "Exposure",
    functionComboLabelText: "Function",
    resetButtonText: "Reset",
    calculateButtonText: "Calculate",
    calculatingText: "Calculating",
    calculatorTitleText: "Impact Calculator",
    hazardSelectText: "Select Hazard ...",
    exposureSelectText: "Select Exposure ...",
    functionSelectText: "Select Function ...",

    displayXHRTrouble: function(response) {
        response.status && Ext.Msg.show({
            title: this.connErrorTitleText,
            msg: this.connErrorText +
                ": " + response.status + " " + response.statusText,
            icon: Ext.MessageBox.ERROR,
            buttons: {ok: this.connErrorDetailsText, cancel: true},
            fn: function(result) {
                if(result == "ok") {
                    var details = new Ext.Window({
                        title: response.status + " " + response.statusText,
                        width: 400,
                        height: 300,
                        items: {
                            xtype: "container",
                            cls: "error-details",
                            html: response.responseText
                        },
                        autoScroll: true,
                        buttons: [{
                            text: "OK",
                            handler: function() { details.close(); }
                        }]
                    });
                    details.show();
                }
            }
        });
    },

    loadConfig: function(config, callback) {
        Ext.Ajax.request({
            url: "/maps/new/data",
            success: function(response) {
                //TODO remove the replace call below when
                // https://github.com/AIFDR/riab/issues/112 is fixed
                var json = response.responseText.replace(/gxp_wmscsource/g, "gxp_wmssource");
                Ext.apply(config, Ext.decode(json, true));
                config.map.id = "map";
                callback.call(this, config);
            },
            scope: this
        });
    }
});


    
//FIXME: Implement drawing the polygon with the bounding box at the end
//       of the calculation
function drawBox(bbox) {

    this.polygonLayer = new OpenLayers.Layer.Vector("Polygon Layer");
    var style_green = {
        strokeColor: "#000000",
        strokeOpacity: 1,
        strokeWidth: 2,
        fillColor: "#00FF00",
        fillOpacity: 0.6
    };

    var p1 = new OpenLayers.Geometry.Point(439000, 114000);
    var p2 = new OpenLayers.Geometry.Point(440000, 115000);
    var p3 = new OpenLayers.Geometry.Point(437000, 116000);
    var p4 = new OpenLayers.Geometry.Point(436000, 115000);
    var p5 = new OpenLayers.Geometry.Point(436500, 113000);

    var points = [];
    points.push(p1);
    points.push(p2);
    points.push(p3);
    points.push(p4);
    points.push(p5);

    // create a polygon feature from a list of points
    var linearRing = new OpenLayers.Geometry.LinearRing(points);
    var polygonFeature = new OpenLayers.Feature.Vector(linearRing, null, style_green);
    drawBox(NaN);
    this.polygonLayer.addFeatures([polygonFeature]);
};

exposurestore = new Ext.data.JsonStore({
    id: 'exposurestore',
    fields: ['name', 'server_url'],
    autoLoad: true,
    url: '/api/v1/layers/?category=exposure',
    root: 'objects'
});

hazardstore = new Ext.data.JsonStore({
    id: 'hazardstore',
    fields: ['name', 'server_url'],
    autoLoad: true,
    url: '/api/v1/layers/?category=hazard',
    root: 'objects'
});

this.combo_functionstore = new Ext.data.JsonStore({
    id: 'combo_functionstore',
    fields: ['name','doc', 'layers'],
    root: 'functions'
});

function addLayer(server_url, label, layer_name, opacity_value) {
    var layer = new OpenLayers.Layer.WMS(
        label, server_url, {layers: layer_name, format: 'image/png', transparent: true},
	    {opacity: opacity_value}, {attribution: 'My attribuion'}
    );
    var map = app.mapPanel.map;
    map.addLayer(layer);
    return layer;
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
    layers = map.getLayersByName(layer_name);
    if (layers.length > 0) {
	//for each(var lay in layers){
		map.removeLayer(layers[0]);
	//  }
    }
}

function addLayerFromCombo(combo){
    var layer_name = combo.value;
    id = combo.store.find('name', combo.value,0,true,false);
    item = combo.store.data.items[id];
    addLayer(item.data.server_url, layer_name, layer_name, 0.5);
}

var lastHazardSelect = "None";
var lastExposureSelect = "None";
var lastImpactSelect = "None";
var lastImpactLayer = "None";

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
    url: '/api/v1/functions/',
    root: 'functions'
});

function reset_view() {
    exposure = Ext.getCmp('exposurecombo');
    hazard = Ext.getCmp('hazardcombo');

    removeLayer(exposure.getValue());
    removeLayer(hazard.getValue());
    removeLayer(lastImpactLayer);
    lastImpactSelect = "None";
    lastExposureSelect = "None";
    lastHazardSelect = "None";
    exposure.setValue("");
    hazard.setValue("");
    exposure.disable();
    Ext.getCmp('functioncombo').disable();
    Ext.getCmp('functioncombo').setValue("");
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
    items = functionstore.data.items;

    // Clear the function combobox
    fCombo.store.removeAll();
    fCombo.store.totalLength = 0;

    for (var ii=0; ii<items.length; ii++) {
    	var item = items[ii];
    	if (item.data == undefined){
            continue;
        }
        name = item.data.name;
        layers = item.data.layers;
        found_exposure = false;
        found_hazard = false;
        // Find if hazard is in layers
        for (var li=0; li<layers.length; li++) {
    	    lay=layers[li];
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
    Ext.MessageBox.alert('Calculation finished successfully', caption);
}

function received(result, request) {
    var progressbar = Ext.getCmp('calculateprogress');
    progressbar.reset();
    progressbar.hide();

    data = Ext.decode( result.responseText );
    if (data.errors !== null){
        Ext.MessageBox.alert('Calculation failed with error:', data.errors);
        if (window.console && console.log){
             console.log(data.stacktrace);
        }
        return;
    }
    reset_view();
    removeLayer(lastImpactLayer);
    var layer_uri = data.layer;
    var run_date = data.run_date;
    var run_duration = data.run_duration;
    var bbox = data.bbox;
    var caption = data.caption;
    var exposure = data.exposure_layer;
    var hazard = data.hazard_layer;
    var base_url = layer_uri.split('/')[2];
    var server_url = data.ows_server_url;
    var result_name = layer_uri.split('/')[4].split(':')[1];
    var result_label = exposure + ' X ' + hazard + '=' +result_name;
    layer = addLayer(server_url, result_label, result_name, 0.9);
    lastImpactLayer = result_label;
    showCaption(caption);
}

function calculate() {
    hazardcombo = Ext.getCmp('hazardcombo');
    exposurecombo = Ext.getCmp('exposurecombo');
    hazardid = hazardcombo.store.find('name', hazardcombo.value,0,true,false);
    exposureid = exposurecombo.store.find('name', exposurecombo.value,0,true,false);
    hazarditem = hazardcombo.store.data.items[hazardid];
    exposureitem = exposurecombo.store.data.items[exposureid];

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
        url: '/api/v1/calculate/',
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

