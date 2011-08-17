/**
 * Copyright (c) 2009-2011 The Open Planning Project
 */

// define gettext in case we run standalone
if (!window.gettext) { gettext = function(s) { return s; }; }

/** api: constructor
 *  .. class:: Risiko(config)
 *
 *    Risiko application.
 */
var Risiko = Ext.extend(gxp.Viewer, {
    
    /** private: method[constructor]
     *  :arg config: ``Object``
     */
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

    /** private: method[loadConfig]
     *  :arg config: ``Object``
     *  :arc callback: ``Function``
     */
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