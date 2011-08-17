/**
 * Copyright (c) 2009-2011 The Open Planning Project
 */

// define gettext in case we run standalone
if (!window.gettext) { gettext = function(s) { return s; }; }

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
                    width: 350,
                    collapsible: true,
                    collapseMode: "mini",
                    header: false,
                    border: true,
                    layout: "vbox",
                    defaults: {
                        align: 'stretch',
                        pack: 'start',
                        padding: 10
                    }
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
            }, {
                actions: ["-"]
            }, {
                ptype: "gxp_wmsgetfeatureinfo",
                format: "grid",
                actionTarget: "map.tbar"
            }, {
                ptype: "gxp_layerproperties",
                layerPanelConfig: {
                    "gxp_wmslayerpanel": {
                        styling: false
                    }
                },
                actionTarget: ["tree.tbar", "tree.contextMenu"]
            }, {
                ptype: "app_calculator",
                outputTarget: "east"
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