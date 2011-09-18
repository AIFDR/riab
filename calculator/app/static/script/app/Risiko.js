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
    
    /* @i18n begin */
    layersText: gettext("Layers"),
    legendText: gettext("Legend"),
    /* @i18n end */
    
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
                    xtype: "tabpanel",
                    region: "west",
                    split: true,
                    collapsible: true,
                    hideCollapseTool: true,
                    collapseMode: "mini",
                    width: 200,
                    defaults: { autoScroll: true },
                    listeners: {
                        "add": {
                            fn: function(cmp) { cmp.setActiveTab(0); },
                            single: true
                        }
                    }
                }, {
                    id: "east",
                    region: "east",
                    width: 350,
                    split: true,
                    collapsible: true,
                    collapseMode: "mini",
                    header: false,
                    border: true,
                    layout: "vbox",
                    layoutConfig: {
                        align: 'stretch',
                        pack: 'start',
                        defaultMargins: "2 2 0 2"
                    },
                    defaults: {
                        padding: 10
                    }
                }]
            },

            // configuration of all tool plugins for this application
            tools: [{
                ptype: "gxp_layertree",
                outputConfig: {
                    id: "tree",
                    title: this.layersText,
                    border: true,
                    tbar: [] // we will add buttons to "tree.tbar" later
                },
                outputTarget: "westpanel"
            }, {
                ptype: "gxp_legend",
                outputTarget: "westpanel",
                outputConfig: {
                    title: this.legendText
                }
            }, {
                ptype: "gxp_addlayers",
                actionTarget: "tree.tbar"
            }, {
                ptype: "gxp_zoomtolayerextent",
                actionTarget: "tree.contextMenu"
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
                controlOptions: {maxFeatures: 3},
                outputConfig: {
                    maximizable: true
                },
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
                ptype: "gxp_styler",
                requireDescribeLayer: false,
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
            }],
            
            map: {
                id: "map"
            }
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
                var loadedConfig = Ext.decode(json, true);
                Ext.applyIf(loadedConfig.map, config.map);
                Ext.apply(config, loadedConfig);
                callback.call(this, config);
            },
            scope: this
        });
        
        // assume that we're not authorized to do anything (especially style
        // editing), until we get note from /data/acls that we're not anonymous
        this.isAuthorized = OpenLayers.Function.False;
        Ext.Ajax.request({
            url: "/data/acls",
            success: function(response) {
                var acls = Ext.decode(response.responseText, true);
                if (acls.is_anonymous === false) {
                    this.isAuthorized = OpenLayers.Function.True;
                }
            },
            scope: this
        });
    }
});

(function() {
    // making symbol names available in UPPERCASE, because Risiko slds use
    // uppercase symbol names.
    //TODO: check if uppercase symbol names are valid according by the spec.
    // If so, make this change in OpenLayers. If not, change it in Risiko.
    var symbol = OpenLayers.Renderer.symbol;
    for (var s in symbol) {
        symbol[s.toUpperCase()] = symbol[s];
    }
})();