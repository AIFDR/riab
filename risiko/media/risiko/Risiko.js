
/**
 * Copyright (c) 2009 The Open Planning Project
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

    //public variables for string literals needed for localization
    addLayersButtonText: GeoExplorer.prototype.addLayersButtonText,
    areaActionText: GeoExplorer.prototype.areaActionText,
    backgroundContainerText: GeoExplorer.prototype.backgroundContainerText,
    capGridAddLayersText: GeoExplorer.prototype.capGridAddLayersText,
    capGridDoneText: GeoExplorer.prototype.capGridDoneText,
    capGridText: GeoExplorer.prototype.capGridText,
    connErrorTitleText: GeoExplorer.prototype.connErrorTitleText,
    connErrorText: GeoExplorer.prototype.connErrorText,
    connErrorDetailsText: GeoExplorer.prototype.connErrorDetailsText,
    heightLabel: GeoExplorer.prototype.heightLabel,
    infoButtonText: GeoExplorer.prototype.infoButtonText,
    largeSizeLabel: GeoExplorer.prototype.largeSizeLabel,
    layerAdditionLabel: GeoExplorer.prototype.layerAdditionLabel,
    layerContainerText: GeoExplorer.prototype.layerContainerText,
    layerPropertiesText: GeoExplorer.prototype.layerPropertiesText,
    layerPropertiesTipText: GeoExplorer.prototype.layerPropertiesTipText,
    layerStylesText: GeoExplorer.prototype.layerStylesText,
    layerStylesTipText: GeoExplorer.prototype.layerStylesTipText,
    layerSelectionLabel: GeoExplorer.prototype.layerSelectionLabel,
    layersContainerText: GeoExplorer.prototype.layersContainerText,
    layersPanelText: GeoExplorer.prototype.layersPanelText,
    legendPanelText: GeoExplorer.prototype.legendPanelText,
    lengthActionText: GeoExplorer.prototype.lengthActionText,
    loadingMapMessage: GeoExplorer.prototype.loadingMapMessage,
    mapSizeLabel: GeoExplorer.prototype.mapSizeLabel,
    measureSplitText: GeoExplorer.prototype.measureSplitText,
    metadataFormCancelText : GeoExplorer.prototype.metadataFormCancelText ,
    metadataFormSaveAsCopyText : GeoExplorer.prototype.metadataFormSaveAsCopyText ,
    metadataFormSaveText : GeoExplorer.prototype.metadataFormSaveText ,
    metaDataHeader: GeoExplorer.prototype.metaDataHeader,
    metaDataMapAbstract: GeoExplorer.prototype.metaDataMapAbstract,
    metaDataMapTitle: GeoExplorer.prototype.metaDataMapTitle,
    miniSizeLabel: GeoExplorer.prototype.miniSizeLabel,
    navActionTipText: GeoExplorer.prototype.navActionTipText,
    navNextAction: GeoExplorer.prototype.navNextAction,
    navPreviousActionText: GeoExplorer.prototype.navPreviousActionText,
    premiumSizeLabel: GeoExplorer.prototype.premiumSizeLabel,
    printTipText: GeoExplorer.prototype.printTipText,
    printWindowTitleText: GeoExplorer.prototype.printWindowTitleText,
    propertiesText: GeoExplorer.prototype.propertiesText,
    publishActionText: GeoExplorer.prototype.publishActionText,
    removeLayerActionText: GeoExplorer.prototype.removeLayerActionText,
    removeLayerActionTipText: GeoExplorer.prototype.removeLayerActionTipText,
    saveFailMessage: GeoExplorer.prototype.saveFailMessage,
    saveFailTitle: GeoExplorer.prototype.saveFailTitle,
    saveMapText: GeoExplorer.prototype.saveMapText,
    saveMapAsText: GeoExplorer.prototype.saveMapAsText,
    saveNotAuthorizedMessage: GeoExplorer.prototype.saveNotAuthorizedMessage,
    smallSizeLabel: GeoExplorer.prototype.smallSizeLabel,
    sourceLoadFailureMessage: GeoExplorer.prototype.sourceLoadFailureMessage,
    switchTo3DActionText: GeoExplorer.prototype.switchTo3DActionText,
    unknownMapMessage: GeoExplorer.prototype.unknownMapMessage,
    unknownMapTitle: GeoExplorer.prototype.unknownMapTitle,
    unsupportedLayersTitleText: GeoExplorer.prototype.unsupportedLayersTitleText,
    unsupportedLayersText: GeoExplorer.prototype.unsupportedLayersText,
    widthLabel: GeoExplorer.prototype.widthLabel,
    zoomInActionText: GeoExplorer.prototype.zoomInActionText,
    zoomOutActionText: GeoExplorer.prototype.zoomOutActionText,
    zoomSelectorText: GeoExplorer.prototype.zoomSelectorText,
    zoomSliderTipText: GeoExplorer.prototype.zoomSliderTipText,
    zoomToLayerExtentText: GeoExplorer.prototype.zoomToLayerExtentText,
    zoomVisibleButtonText: GeoExplorer.prototype.zoomVisibleButtonText,

    constructor: function(config) {
        this.popupCache = {};
        this.propDlgCache = {};
        this.stylesDlgCache = {};
        // add any custom application events
        this.addEvents(
            /**
             * api: event[saved]
             * Fires when the map has been saved.
             *  Listener arguments:
             *  * ``String`` the map id
             */
            "saved",
            /**
             * api: event[beforeunload]
             * Fires before the page unloads. Return false to stop the page
             * from unloading.
             */
            "beforeunload"
        );

        // add old ptypes
        Ext.preg("gx_wmssource", gxp.plugins.WMSSource);
        Ext.preg("gx_olsource", gxp.plugins.OLSource);
        Ext.preg("gx_googlesource", gxp.plugins.GoogleSource);

        // global request proxy and error handling
        Ext.util.Observable.observeClass(Ext.data.Connection);
        Ext.data.Connection.on({
            "beforerequest": function(conn, options) {
                // use django's /geoserver endpoint when talking to the local
                // GeoServer's RESTconfig API
                var url = options.url.replace(this.urlPortRegEx, "$1/");
                var localUrl = this.localGeoServerBaseUrl.replace(
                    this.urlPortRegEx, "$1/");
                if(url.indexOf(localUrl + "rest/") === 0) {
                    options.url = url.replace(new RegExp("^" +
                        localUrl), "/geoserver/");
                    return;
                };
                // use the proxy for all non-local requests
                if(this.proxy && options.url.indexOf(this.proxy) !== 0 &&
                        options.url.indexOf(window.location.protocol) === 0) {
                    var parts = options.url.replace(/&$/, "").split("?");
                    var params = Ext.apply(parts[1] && Ext.urlDecode(
                        parts[1]) || {}, options.params);
                    var url = Ext.urlAppend(parts[0], Ext.urlEncode(params));
                    delete options.params;
                    options.url = this.proxy + encodeURIComponent(url);
                }
            },
            "requestexception": function(conn, response, options) {
                if(options.failure) {
                    // exceptions are handled elsewhere
               } else {
                    this.busyMask && this.busyMask.hide();
                    var url = options.url;
                    if (response.status == 401 && url.indexOf("http" != 0) &&
                                            url.indexOf(this.proxy) === -1) {
                        var submit = function() {
                            form.getForm().submit({
                                waitMsg: "Logging in...",
                                success: function(form, action) {
                                    win.close();
                                    document.cookie = action.response.getResponseHeader("Set-Cookie");
                                    // resend the original request
                                    Ext.Ajax.request(options);
                                },
                                failure: function(form, action) {
                                    var username = form.items.get(0);
                                    var password = form.items.get(1);
                                    username.markInvalid();
                                    password.markInvalid();
                                    username.focus(true);
                                },
                                scope: this
                            });
                        }.bind(this);
                        var win = new Ext.Window({
                            title: "GeoNode Login",
                            modal: true,
                            width: 230,
                            autoHeight: true,
                            layout: "fit",
                            items: [{
                                xtype: "form",
                                autoHeight: true,
                                labelWidth: 55,
                                border: false,
                                bodyStyle: "padding: 10px;",
                                url: "/accounts/ajax_login",
                                waitMsgTarget: true,
                                errorReader: {
                                    // teach ExtJS a bit of RESTfulness
                                    read: function(response) {
                                        return {
                                            success: response.status == 200,
                                            records: []
                                        }
                                    }
                                },
                                defaults: {
                                    anchor: "100%"
                                },
                                items: [{
                                    xtype: "textfield",
                                    name: "username",
                                    fieldLabel: "Username"
                                }, {
                                    xtype: "textfield",
                                    name: "password",
                                    fieldLabel: "Password",
                                    inputType: "password"
                                }, {
                                    xtype: "hidden",
                                    name: "csrfmiddlewaretoken",
                                    value: this.csrfToken
                                }, {
                                    xtype: "button",
                                    text: "Login",
                                    inputType: "submit",
                                    handler: submit
                                }]
                            }],
                            keys: {
                                "key": Ext.EventObject.ENTER,
                                "fn": submit
                            }
                        });
                        win.show();
                        var form = win.items.get(0);
                        form.items.get(0).focus(false, 100);
                    } else {
                        this.displayXHRTrouble(response);
                    }
                }
            },
            scope: this
        });

        // global beforeunload handler
       // window.onbeforeunload = (function() {
       //     if (this.fireEvent("beforeunload") === false) {
       //         return "If you leave this page, unsaved changes will be lost.";
       //     }
       // }).bind(this);

        // register the color manager with every color field
        Ext.util.Observable.observeClass(gxp.form.ColorField);
        gxp.form.ColorField.on({
            render: function(field) {
                var manager = new Styler.ColorManager();
                manager.register(field);
            }
        });

        // limit combo boxes to the window they belong to - fixes issues with
        // list shadow covering list items
        Ext.form.ComboBox.prototype.getListParent = function() {
            return this.el.up(".x-window") || document.body;
        }

        // don't draw window shadows - allows us to use autoHeight: true
        // without using syncShadow on the window
        Ext.Window.prototype.shadow = false;

        // set SLD defaults for symbolizer
        OpenLayers.Renderer.defaultSymbolizer = {
            fillColor: "#808080",
            fillOpacity: 1,
            strokeColor: "#000000",
            strokeOpacity: 1,
            strokeWidth: 1,
            strokeDashstyle: "solid",
            pointRadius: 3,
            graphicName: "square",
            fontColor: "#000000",
            fontSize: 10,
            haloColor: "#FFFFFF",
            haloOpacity: 1,
            haloRadius: 1
        };

        // set maxGetUrlLength to avoid non-compliant GET urls for WMS GetMap
        OpenLayers.Tile.Image.prototype.maxGetUrlLength = 2048;

        if (!config.map) {
            config.map = {};
        }
        config.map.numZoomLevels = config.map.numZoomLevels || 22;

        Risiko.superclass.constructor.apply(this, arguments);

        this.mapID = this.initialConfig.id;
    },

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

    initMapPanel: function() {
        this.mapItems = [{
            xtype: "gx_zoomslider",
            vertical: true,
            height: 100,
            plugins: new GeoExt.ZoomSliderTip({
                template: "<div>"+this.zoomSliderTipText+": {zoom}<div>"
            })
        }];

        Risiko.superclass.initMapPanel.apply(this, arguments);

        var layerCount = 0;

        this.mapPanel.map.events.register("preaddlayer", this, function(e) {
            var layer = e.layer;
            if (layer instanceof OpenLayers.Layer.WMS) {
                !layer.singleTile && layer.maxExtent && layer.mergeNewParams({
                    tiled: true,
                    tilesOrigin: [layer.maxExtent.left, layer.maxExtent.bottom]
                });
                layer.events.on({
                    "loadstart": function() {
                        layerCount++;
                        if (!this.busyMask) {
                            this.busyMask = new Ext.LoadMask(
                                this.mapPanel.map.div, {
                                    msg: this.loadingMapMessage
                                }
                            );
                            this.busyMask.show();
                        }
                        layer.events.unregister("loadstart", this, arguments.callee);
                    },
                    "loadend": function() {
                        layerCount--;
                        if(layerCount === 0) {
                            this.busyMask.hide();
                        }
                        layer.events.unregister("loadend", this, arguments.callee);
                    },
                    scope: this
                })
            }
        });
    },

    /**
     * Method: initPortal
     * Create the various parts that compose the layout.
     */
    initPortal: function() {
        this.on("beforeunload", function() {
            if (this.modified) {
                this.showMetadataForm();
                return false;
            }
        }, this);

        // TODO: make a proper component out of this
        var mapOverlay = this.createMapOverlay();
        this.mapPanel.add(mapOverlay);

        var addLayerButton = new Ext.Button({
            tooltip : this.addLayersButtonText,
            disabled: true,
            iconCls: "icon-addlayers",
            handler : this.showCapabilitiesGrid,
            scope: this
        });
        this.on("ready", function() {
            addLayerButton.enable();
            this.mapPanel.layers.on({
                "update": function() {this.modified |= 1;},
                "add": function() {this.modified |= 1;},
                "remove": function(store, rec) {
                    this.modified |= 1;
                    delete this.stylesDlgCache[rec.getLayer().id];
                },
                scope: this
            });
        });

        var getRecordFromNode = function(node) {
            if(node && node.layer) {
                var layer = node.layer;
                var store = node.layerStore;
                record = store.getAt(store.findBy(function(r) {
                    return r.getLayer() === layer;
                }));
            }
            return record;
        };

        var getSelectedLayerRecord = function() {
            var node = layerTree.getSelectionModel().getSelectedNode();
            return getRecordFromNode(node);
        };

        var removeLayerAction = new Ext.Action({
            text: this.removeLayerActionText,
            iconCls: "icon-removelayers",
            disabled: true,
            tooltip: this.removeLayerActionTipText,
            handler: function() {
                var record = getSelectedLayerRecord();
                if(record) {
                    this.mapPanel.layers.remove(record);
                    removeLayerAction.disable();
                }
            },
            scope: this
        });

        var treeRoot = new Ext.tree.TreeNode({
            text: "Layers",
            expanded: true,
            isTarget: false,
            allowDrop: false
        });
        treeRoot.appendChild(new GeoExt.tree.LayerContainer({
            text: this.layerContainerText,
            iconCls: "gx-folder",
            expanded: true,
            loader: new GeoExt.tree.LayerLoader({
                store: this.mapPanel.layers,
                filter: function(record) {
                    return !record.get("group") &&
                        record.getLayer().displayInLayerSwitcher == true;
                },
                createNode: function(attr) {
                    var layer = attr.layer;
                    var store = attr.layerStore;
                    if (layer && store) {
                        var record = store.getAt(store.findBy(function(r) {
                            return r.getLayer() === layer;
                        }));
                        if (record && !record.get("queryable")) {
                            attr.iconCls = "gx-tree-rasterlayer-icon";
                        }
                    }
                    return GeoExt.tree.LayerLoader.prototype.createNode.apply(this, [attr]);
                }
            }),
            singleClickExpand: true,
            allowDrag: false,
            listeners: {
                append: function(tree, node) {
                    node.expand();
                }
            }
        }));

        treeRoot.appendChild(new GeoExt.tree.LayerContainer({
            text: this.backgroundContainerText,
            iconCls: "gx-folder",
            expanded: true,
            group: "background",
            loader: new GeoExt.tree.LayerLoader({
                baseAttrs: {checkedGroup: "background"},
                store: this.mapPanel.layers,
                filter: function(record) {
                    return record.get("group") === "background" &&
                        record.getLayer().displayInLayerSwitcher == true;
                },
                createNode: function(attr) {
                    var layer = attr.layer;
                    var store = attr.layerStore;
                    if (layer && store) {
                        var record = store.getAt(store.findBy(function(r) {
                            return r.getLayer() === layer;
                        }));
                        if (record) {
                            if (!record.get("queryable")) {
                                attr.iconCls = "gx-tree-rasterlayer-icon";
                            }
                            if (record.get("fixed")) {
                                attr.allowDrag = false;
                            }
                        }
                    }
                    return GeoExt.tree.LayerLoader.prototype.createNode.apply(this, arguments);
                }
            }),
            singleClickExpand: true,
            allowDrag: false,
            listeners: {
                append: function(tree, node) {
                    node.expand();
                }
            }
        }));

        createPropertiesDialog = function() {
            var node = layerTree.getSelectionModel().getSelectedNode();
            if (node && node.layer) {
                var layer = node.layer;
                var store = node.layerStore;
                var record = store.getAt(store.findBy(function(record){
                    return record.getLayer() === layer;
                }));
                var backupParams = Ext.apply({}, record.getLayer().params);
                var prop = this.propDlgCache[layer.id];
                if (!prop) {
                    prop = this.propDlgCache[layer.id] = new Ext.Window({
                        title: "Properties: " + record.getLayer().name,
                        width: 280,
                        autoHeight: true,
                        closeAction: "hide",
                        items: [{
                            xtype: "gxp_wmslayerpanel",
                            autoHeight: true,
                            layerRecord: record,
                            defaults: {
                                autoHeight: true,
                                hideMode: "offsets"
                            },
                            listeners: {
                                "change": function() {this.modified |= 1;},
                                scope: this
                            }
                        }]
                    });
                    // disable the "About" tab's fields to indicate that they
                    // are read-only
                    //TODO WMSLayerPanel should be easier to configure for this
                    prop.items.get(0).items.get(0).cascade(function(i) {
                        i instanceof Ext.form.Field && i.setDisabled(true);
                    });
                    var stylesPanel = this.createStylesPanel({
                        layerRecord: record
                    });
                    stylesPanel.items.get(0).on({
                        "styleselected": function() {this.modified |= 1;},
                        "modified": function() {this.modified |= 2;},
                        scope: this
                    });
                    stylesPanel.setTitle("Styles");
                    // add styles tab
                    prop.items.get(0).add(stylesPanel)
                }
                prop.show();
            }
        };

        var showPropertiesAction = new Ext.Action({
            text: this.layerPropertiesText,
            iconCls: "icon-layerproperties",
            disabled: true,
            tooltip: this.layerPropertiesTipText,
            handler: createPropertiesDialog.createSequence(function() {
                var node = layerTree.getSelectionModel().getSelectedNode();
                this.propDlgCache[node.layer.id].items.get(0).setActiveTab(1);
            }, this),
            scope: this,
            listeners: {
                "enable": function() {showStylesAction.enable()},
                "disable": function() {showStylesAction.disable()}
            }
        });

        var showStylesAction = new Ext.Action({
            text: this.layerStylesText,
            iconCls: "icon-layerstyles",
            disabled: true,
            tooltip: this.layerStylesTipText,
            handler: createPropertiesDialog.createSequence(function() {
                var node = layerTree.getSelectionModel().getSelectedNode();
                this.propDlgCache[node.layer.id].items.get(0).setActiveTab(2);
            }, this),
            scope: this
        });

        var updateLayerActions = function(sel, node) {
            if(node && node.layer) {
                // allow removal if more than one non-vector layer
                var count = this.mapPanel.layers.queryBy(function(r) {
                    return !(r.getLayer() instanceof OpenLayers.Layer.Vector);
                }).getCount();
                if(count > 1) {
                    removeLayerAction.enable();
                } else {
                    removeLayerAction.disable();
                }
                var record = getRecordFromNode(node);
                if (record.get("properties")) {
                    showPropertiesAction.enable();
                } else {
                    showPropertiesAction.disable();
                }
            } else {
                removeLayerAction.disable();
                showPropertiesAction.disable();
            }
        };

        var layerTree = new Ext.tree.TreePanel({
            root: treeRoot,
            rootVisible: false,
            border: false,
            enableDD: true,
            selModel: new Ext.tree.DefaultSelectionModel({
                listeners: {
                    beforeselect: updateLayerActions,
                    scope: this
                }
            }),
            listeners: {
                contextmenu: function(node, e) {
                    if(node && node.layer) {
                        node.select();
                        var c = node.getOwnerTree().contextMenu;
                        c.contextNode = node;
                        c.showAt(e.getXY());
                    }
                },
                beforemovenode: function(tree, node, oldParent, newParent, index) {
                    // change the group when moving to a new container
                    if(oldParent !== newParent) {
                        var store = newParent.loader.store;
                        var index = store.findBy(function(r) {
                            return r.getLayer() === node.layer;
                        });
                        var record = store.getAt(index);
                        record.set("group", newParent.attributes.group);
                    }
                },
                scope: this
            },
            contextMenu: new Ext.menu.Menu({
                items: [
                    {
                        text: this.zoomToLayerExtentText,
                        iconCls: "icon-zoom-to",
                        handler: function() {
                            var node = layerTree.getSelectionModel().getSelectedNode();
                            if(node && node.layer) {
                                var map = this.mapPanel.map;
                                var extent = node.layer.restrictedExtent || map.maxExtent;
                                map.zoomToExtent(extent, true);
                            }
                        },
                        scope: this
                    },
                    removeLayerAction,
                    showPropertiesAction,
                    showStylesAction
                ]
            })
        });

        var layersContainer = new Ext.Panel({
            autoScroll: true,
            border: false,
            title: this.layersContainerText,
            items: [layerTree],
            tbar: [
                addLayerButton,
                Ext.apply(new Ext.Button(removeLayerAction), {text: ""}),
                Ext.apply(new Ext.Button(showPropertiesAction), {text: ""}),
                Ext.apply(new Ext.Button(showStylesAction), {text: ""})
            ]
        });

        this.legendPanel = new GeoExt.LegendPanel({
            title: this.legendPanelText,
            border: false,
            hideMode: "offsets",
            split: true,
            autoScroll: true,
            ascending: false,
            map: this.mapPanel.map,
            defaults: {cls: 'legend-item'}
        });

        this.on("ready", function(){
          //  if (!this.fromLayer && !this.mapID) {
          //      this.showCapabilitiesGrid();
          //  }
        }, this);

        var layersTabPanel = new Ext.TabPanel({
            border: false,
            region: 'center',
            deferredRender: false,
            items: [layersContainer, this.legendPanel],
            activeTab: 0
        });


     this.polygonLayer = new OpenLayers.Layer.Vector("Polygon Layer");

    //FIXME: Implement drawing the polygon with the bounding box at the end
    //       of the calculation
   function drawBox(bbox){
 
     this.polygonLayer = new OpenLayers.Layer.Vector("Polygon Layer");
       var style_green =
         {
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
    this.exposurestore = new Ext.data.JsonStore({
     id: 'exposurestore',
     fields: ['name', 'server_url'],
     autoLoad: true,
     url: '/api/v1/layers/?category=exposure',
     root: 'objects'
     });

    this.hazardstore = new Ext.data.JsonStore({
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



function addLayer(server_url, label, layer_name, opacity_value){
      var layer = new OpenLayers.Layer.WMS(
           label, server_url,{layers: layer_name, format: 'image/png', transparent: true},
                              {opacity: opacity_value}
      );
      var map = app.mapPanel.map;
      map.addLayer(layer);
}

function removeLayer(layer_name){
      var map = app.mapPanel.map;
      map.layers.remove(layer);
}

function addLayerFromCombo(combo){
      var layer_name = combo.value;
      id = combo.store.find('name', combo.value,0,true,false)
      item = combo.store.data.items[id]
      addLayer(item.data.server_url, layer_name, layer_name, 0.5);
}


function hazardSelected(combo){
       addLayerFromCombo(combo);
       Ext.getCmp('exposurecombo').enable()
       Ext.getCmp('functioncombo').disable()
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

    Ext.getCmp('exposurecombo').setValue("");
    Ext.getCmp('exposurecombo').disable();
    Ext.getCmp('functioncombo').disable();
    Ext.getCmp('functioncombo').setValue("");
}

function exposureSelected(combo){
       addLayerFromCombo(combo);
       // Get the complete list of functions and it's compatible layers
       var combo = Ext.getCmp('functioncombo');

       var hazard_name = Ext.getCmp('hazardcombo').value;
       var exposure_name = Ext.getCmp('exposurecombo').value;
       
       Ext.getCmp('functioncombo').enable();
       items = functionstore.data.items;
       
       // Clear the function combobox
       combo.store.removeAll(); 
       combo.store.totalLength = 0;
       
       for each (var item in items){
          if (item.data === undefined){
              continue;
          }
          name = item.data.name;
          layers = item.data.layers;
          found_exposure = false;
          found_hazard = false;
          // Find if hazard is in layers
          for each(var lay in layers){
               if (lay === exposure_name) {              
                    found_exposure = true;
               } 
               if (lay === hazard_name) {              
                    found_hazard = true;
               } 
          }

          if (found_exposure && found_hazard){
	      // add the function name to the combo box
	      combo.store.insert(0, new Ext.data.Record({name:name}));
	      combo.setValue(name)
             }
       }

}

function received(result, request) {
    var progressbar = Ext.getCmp('calculateprogress');
    progressbar.reset();
    progressbar.hide();

    data = Ext.decode( result.responseText );
    if (data.errors !== null){
        alert('Calculation failed with error: '+ data.errors);
        if (window.console && console.log){
             console.log(data.stacktrace);
        }
        return
    }

    var layer_uri = data.layer;
    var run_date = data.run_date;
    var run_duration = data.run_duration;
    var bbox = data.bbox;
    var keywords = data.keywords;
    var exposure = data.exposure_layer;
    var hazard = data.hazard_layer;
    var base_url = layer_uri.split('/')[2]
    var server_url = data.ows_server_url;
    var result_name = layer_uri.split('/')[4].split(':')[1]
    var result_label = exposure.split(':')[1] + ' X ' + hazard.split(':')[1] + '=' +result_name
    addLayer(server_url, result_label, result_name, 0.9);
}

function calculate()
{
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
                            new OpenLayers.Projection('EPSG:900913'), new OpenLayers.Projection('EPSG:4326'));
  var bbox = bounds.toBBOX();
  progressbar.show();
  progressbar.wait({
            interval:100,
            duration:50000,
	      increment:5});

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
       impact_function: impact_function,
       impact_level: 10
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
};

        //needed for Safari
        var westPanel = new Ext.Panel({
            layout: "border",
            collapseMode: "mini",
            header: false,
            split: true,
            items: [layersTabPanel],
            region: "west",
            width: 200,
            collapsible: true,
            collapsed: true
        });

        var eastPanel = new Ext.Panel({
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
                title: "Impact Calculator",
                xtype: 'form',
                labelWidth: 60,
                height: 180,
                split: true,
                items: [{
                             xtype: 'combo',
                             id: 'hazardcombo',
                             store: this.hazardstore,
                             width: '100%',
                             displayField:'name',
                             valueField: 'name',
                             fieldLabel: 'Hazard',
                             typeAhead: true,
                             mode: 'local',
                             triggerAction: 'all',
                             emptyText:'Select Hazard...',
                             selectOnFocus:false,
                             listeners: {
                                "select": hazardSelected
                             }
                           },{
                             xtype: 'combo',
                             id: 'exposurecombo',
                             store: this.exposurestore,
                             width: '100%',
                             displayField:'name',
                             valueField:'name',
                             fieldLabel: 'Exposure',
                             typeAhead: true,
                             mode: 'local',
                             triggerAction: 'all',
                             emptyText:'Select Exposure...',
                             selectOnFocus:false,
                             disabled: true,
                             listeners: {
                                "select": exposureSelected
                             }
                   },{
                             xtype: 'combo',
                             id: 'functioncombo',
                             store: this.combo_functionstore,
                             width: '100%',
                             displayField:'name',
                             valueField:'name',
                             fieldLabel: 'Function',
                             typeAhead: true,
                             mode: 'local',
                             triggerAction: 'all',
                             disabled: true,
                             emptyText:'Select Function...',
                             selectOnFocus:false
		    }, {
                             xtype: 'progress',
                             id: 'calculateprogress',
			     cls: 'right-align',
                             displayField:'name',
			     fieldLabel: 'Calculating',
                             hidden: true
		    }
		    ],

		buttons: [{text:'Reset',
			   handler:reset_view}
		         ,{
                           text: 'Calculate',
                           handler: calculate
			  }]
             },{
                id: "logopanel",
                flex: 2,
                frame: false,
                border: false,
                html:
            "<img src='/media/theme/img/bnpb_logo.jpg' alt='BNPB' title='BNPB' width=60 style='padding-left: 40px;margin-top:20px'/>" +
            "<img src='/media/theme/img/bppt_logo.jpg' alt='BPPT' title='BPPT' width=100 style='padding-left: 40px;margin-top:20px'/>" +
            "<img src='/media/theme/img/gfdrr.jpg' alt='GFDRR' title='GFDRR' width=200 style='padding-left:40px;margin-top:20px'/>" +
            "<img src='/media/theme/img/aifdr.png' alt='AIFDR' title='AIFDR' width=200 style='padding-left:40px;padding-top:20px'/>" +
               "",
                xtype: "panel",
                defaults:{hideBorders: true}
               }]
        });



        this.toolbar = new Ext.Toolbar({
            disabled: true,
            items: this.createTools()
        });

        this.on("ready", function() {
            // enable only those items that were not specifically disabled
            var disabled = this.toolbar.items.filterBy(function(item) {
                return item.initialConfig && item.initialConfig.disabled;
            });
            this.toolbar.enable();
            disabled.each(function(item) {
                item.disable();
            });
        }, this);

        this.googleEarthPanel = new gxp.GoogleEarthPanel({
            mapPanel: this.mapPanel,
            listeners: {
                "beforeadd": function(record) {
                    return record.get("group") !== "background";
                },
                "show": function() {
                    addLayerButton.disable();
                    removeLayerAction.disable();
                    layerTree.getSelectionModel().un(
                        "beforeselect", updateLayerActions, this);
                },
                "hide": function() {
                    addLayerButton.enable();
                    updateLayerActions();
                    layerTree.getSelectionModel().on(
                        "beforeselect", updateLayerActions, this);
                }
            }
        });

        this.mapPanelContainer = new Ext.Panel({
            layout: "card",
            region: "center",
            defaults: {
                // applied to each contained panel
                border:false
            },
            items: [
                this.mapPanel,
                this.googleEarthPanel
            ],
            activeItem: 0
        });

        var header = new Ext.Panel({
            region: "north",
            autoHeight: true,
            contentEl: 'header-wrapper'
        });

        Lang.registerLinks();

        this.portalItems = [
            header, {
                region: "center",
                xtype: "container",
                layout: "fit",
                border: false,
                hideBorders: true,
                items: {
                    layout: "border",
                    deferredRender: false,
                    tbar: this.toolbar,
                    items: [
                        this.mapPanelContainer,
                        westPanel,
                        eastPanel
                    ]
                }
            }
        ];

        Risiko.superclass.initPortal.apply(this, arguments);
    },

    /** api: method[createStylesPanel]
     *  :param options: ``Object`` Options for the :class:`gxp.WMSStylesDialog`.
     *      Supported options are ``layerRecord``, ``styleName``, ``editable``
     *      and ``listeners`` (except "ready", "modified" and "styleselected"
     *      listeners)
     *  :return: ``Ext.Panel`` A panel with a :class:`gxp.WMSStylesDialog` as
     *      only item.
     */
    createStylesPanel: function(options) {
        var layer = options.layerRecord.getLayer();

        var stylesPanel, stylesDialog;
        var createStylesDialog = function() {
            if (stylesPanel) {
                stylesDialog.destroy();
                stylesPanel.getFooterToolbar().items.each(function(i) {
                    i.disable();
                });
            }
            var modified = false;
            stylesDialog = this.stylesDlgCache[layer.id] =
                                            new gxp.WMSStylesDialog(Ext.apply({
                style: "padding: 10px 10px 0 10px;",
                editable: layer.url.replace(
                    this.urlPortRegEx, "$1/").indexOf(
                    this.localGeoServerBaseUrl.replace(
                    this.urlPortRegEx, "$1/")) === 0,
                plugins: [{
                    ptype: "gxp_geoserverstylewriter",
                    baseUrl: layerUrl.split(
                        "?").shift().replace(/\/(wms|ows)\/?$/, "/rest")
                }, {
                    ptype: "gxp_wmsrasterstylesdialog"
                }],
                autoScroll: true,
                listeners: Ext.apply(options.listeners || {}, {
                    "ready": function() {
                        // we don't want the Cancel and Save buttons
                        // if we cannot edit styles
                        stylesDialog.editable === false &&
                            stylesPanel.getFooterToolbar().hide();
                    },
                    "modified": function(cmp, name) {
                        // enable the cancel and save button
                        stylesPanel.buttons[0].enable();
                        stylesPanel.buttons[1].enable();
                        // instant style preview
                        layer.mergeNewParams({
                            "STYLES": name,
                            "SLD_BODY": cmp.createSLD({userStyles: [name]})
                        });
                        modified = true;
                    },
                    "styleselected": function(cmp, name) {
                        // enable the cancel button
                        stylesPanel.buttons[0].enable();
                        layer.mergeNewParams({
                            "STYLES": name,
                            "SLD_BODY": modified ?
                                cmp.createSLD({userStyles: [name]}) : null
                        });
                    },
                    "saved": function() {
                        this.busyMask.hide();
                        this.modified ^= this.modified & 2;
                        var rec = stylesDialog.selectedStyle;
                        var styleName = rec.get("userStyle").isDefault ?
                            "" : rec.get("name");
                        if (options.applySelectedStyle === true ||
                                    styleName === initialStyle ||
                                    rec.get("name") === initialStyle) {
                            layer.mergeNewParams({
                                "STYLES": styleName,
                                "SLD_BODY": null,
                                "_dc": Math.random()
                            });
                        }
                        stylesPanel.ownerCt instanceof Ext.Window ?
                            stylesPanel.ownerCt.close() :
                            createStylesDialog();
                    },
                    scope: this
                })
            }, options));
            if (stylesPanel) {
                stylesPanel.add(stylesDialog);
                stylesPanel.doLayout();
            }
        }.bind(this);

        var layerUrl = layer.url;

        // remember the layer's current style
        var initialStyle = layer.params.STYLES;

        createStylesDialog();
        stylesPanel = new Ext.Panel({
            autoHeight: true,
            border: false,
            items: stylesDialog,
            buttons: [{
                text: "Cancel",
                disabled: true,
                handler: function() {
                    layer.mergeNewParams({
                        "STYLES": initialStyle,
                        "SLD_BODY": null
                    });
                    stylesPanel.ownerCt instanceof Ext.Window ?
                        stylesPanel.ownerCt.close() :
                        createStylesDialog();
                },
                scope: this
            }, {
                text: "Save",
                disabled: true,
                handler: function() {
                    this.busyMask = new Ext.LoadMask(stylesPanel.el,
                        {msg: "Applying style changes..."});
                    this.busyMask.show();
                    stylesDialog.saveStyles();
                },
                scope: this
            }],
            listeners: {
                "added": function(cmp, ownerCt) {
                    ownerCt instanceof Ext.Window &&
                        cmp.buttons[0].enable();
                }
            }
        });
        return stylesPanel;
    },

    /**
     * Method: initCapGrid
     * Constructs a window with a capabilities grid.
     */
    initCapGrid: function(){

        var initialSourceId, source, data = [];
        for (var id in this.layerSources) {
            source = this.layerSources[id];
            if (initialSourceId === undefined &&
                    source instanceof gxp.plugins.WMSSource &&
                    source.url.replace(this.urlPortRegEx, "$1/").indexOf(
                        this.localGeoServerBaseUrl.replace(
                            this.urlPortRegEx, "$1/")) === 0) {
                initialSourceId = id;
            }
            if (source.store) {
                data.push([id, this.layerSources[id].title || id]);
            }
        }
        // fall back to 1st source if the local GeoServer WMS is not used
        if (initialSourceId === undefined) {
            initialSourceId = data[0][0];
        }

        var sources = new Ext.data.ArrayStore({
            fields: ["id", "title"],
            data: data
        });

        var expander = new GeoExplorer.CapabilitiesRowExpander({
            ows: this.localGeoServerBaseUrl + "ows"
        });

        var addLayers = function() {
            var key = sourceComboBox.getValue();
            var layerStore = this.mapPanel.layers;
            var source = this.layerSources[key];
            var records = capGridPanel.getSelectionModel().getSelections();
            var record;
            for (var i=0, ii=records.length; i<ii; ++i) {
                record = source.createLayerRecord({
                    name: records[i].get("name"),
                    source: key,
                    buffer: 0
                });
                if (record) {
                    if (record.get("group") === "background") {
                        var pos = layerStore.queryBy(function(rec) {
                            return rec.get("group") === "background"
                        }).getCount();
                        layerStore.insert(pos, [record]);
                    } else {
                        layerStore.add([record]);
                    }
                }
            }
        };

        var source = this.layerSources[initialSourceId];
        source.store.filterBy(function(r) {
            return !!source.getProjection(r);
        }, this);
        var capGridPanel = new Ext.grid.GridPanel({
            store: source.store,
            layout: 'fit',
            region: 'center',
            autoScroll: true,
            autoExpandColumn: "title",
            plugins: [expander],
            colModel: new Ext.grid.ColumnModel([
                expander,
                {header: "Name", dataIndex: "name", width: 150, sortable: true},
                {id: "title", header: "Title", dataIndex: "title", sortable: true}
            ]),
            listeners: {
                rowdblclick: addLayers,
                scope: this
            }
        });

        var sourceComboBox = new Ext.form.ComboBox({
            store: sources,
            valueField: "id",
            displayField: "title",
            triggerAction: "all",
            editable: false,
            allowBlank: false,
            forceSelection: true,
            mode: "local",
            value: initialSourceId,
            listeners: {
                select: function(combo, record, index) {
                    var source = this.layerSources[record.get("id")];
                    var store = source.store;
                    store.filterBy(function(r) {
                        return !!source.getProjection(r);
                    }, this);
                    expander.ows = store.url;
                    capGridPanel.reconfigure(store, capGridPanel.getColumnModel());
                    // TODO: remove the following when this Ext issue is addressed
                    // http://www.extjs.com/forum/showthread.php?100345-GridPanel-reconfigure-should-refocus-view-to-correct-scroller-height&p=471843
                    capGridPanel.getView().focusRow(0);
                },
                scope: this
            }
        });

        var capGridToolbar = null;

        if (this.proxy || this.layerSources.getCount() > 1) {
            capGridToolbar = [
                new Ext.Toolbar.TextItem({
                    text: this.layerSelectionLabel
                }),
                sourceComboBox
            ];
        }

        if (this.proxy) {
            capGridToolbar.push(new Ext.Button({
                text: this.layerAdditionLabel,
                handler: function() {
                    newSourceWindow.show();
                }
            }));
        }

        var app = this;
        var newSourceWindow = new gxp.NewSourceWindow({
            modal: true,
            listeners: {
                "server-added": function(url) {
                    newSourceWindow.setLoading();
                    this.addLayerSource({
                        config: {url: url}, // assumes default of gxp_wmssource
                        callback: function(id) {
                            // add to combo and select
                            var record = new sources.recordType({
                                id: id,
                                title: this.layerSources[id].title || "Untitled" // TODO: titles
                            });
                            sources.insert(0, [record]);
                            sourceComboBox.onSelect(record, 0);
                            newSourceWindow.hide();
                        },
                        failure: function() {
                            // TODO: wire up success/failure
                            newSourceWindow.setError("Error contacting server.\nPlease check the url and try again.");
                        },
                        scope: this
                    });
                },
                scope: this
            },
            // hack to get the busy mask so we can close it in case of a
            // communication failure
            addSource: function(url, success, failure, scope) {
                app.busyMask = scope.loadMask;
            }
        });

        this.capGrid = new Ext.Window({
            title: this.capGridText,
            closeAction: 'hide',
            layout: 'border',
            height: 300,
            width: 600,
            modal: true,
            items: [
                capGridPanel
            ],
            tbar: capGridToolbar,
            bbar: [
                "->",
                new Ext.Button({
                    text: this.capGridAddLayersText,
                    iconCls: "icon-addlayers",
                    handler: addLayers,
                    scope : this
                }),
                new Ext.Button({
                    text: this.capGridDoneText,
                    handler: function() {
                        this.capGrid.hide();
                    },
                    scope: this
                })
            ],
            listeners: {
                hide: function(win){
                    capGridPanel.getSelectionModel().clearSelections();
                }
            }
        });
    },

    /**
     * Method: showCapabilitiesGrid
     * Shows the window with a capabilities grid.
     */
    showCapabilitiesGrid: function() {
        if(!this.capGrid) {
            this.initCapGrid();
        }
        this.capGrid.show();
    },

    /** private: method[createMapOverlay]
     * Builds the :class:`Ext.Panel` containing components to be overlaid on the
     * map, setting up the special configuration for its layout and
     * map-friendliness.
     */
    createMapOverlay: function() {
        var scaleLinePanel = new Ext.BoxComponent({
            autoEl: {
                tag: "div",
                cls: "olControlScaleLine overlay-element overlay-scaleline"
            }
        });

        scaleLinePanel.on('render', function(){
            var scaleLine = new OpenLayers.Control.ScaleLine({
                div: scaleLinePanel.getEl().dom,
                geodesic: true
            });

            this.mapPanel.map.addControl(scaleLine);
            scaleLine.activate();
        }, this);

        var zoomSelectorWrapper = new Ext.Panel({
            cls: 'overlay-element overlay-scalechooser',
            border: false
        });

        this.on("ready", function() {
            var zoomStore = new GeoExt.data.ScaleStore({
                map: this.mapPanel.map
            });

            var zoomSelector = new Ext.form.ComboBox({
                emptyText: this.zoomSelectorText,
                tpl: '<tpl for="."><div class="x-combo-list-item">1 : {[parseInt(values.scale)]}</div></tpl>',
                editable: false,
                triggerAction: 'all',
                mode: 'local',
                store: zoomStore,
                width: 110
            });

            zoomSelector.on({
                click: function(evt) {
                    evt.stopEvent();
                },
                mousedown: function(evt) {
                    evt.stopEvent();
                },
                select: function(combo, record, index) {
                    this.mapPanel.map.zoomTo(record.data.level);
                },
                scope: this
            });

            function setScale() {
                var scale = zoomStore.queryBy(function(record) {
                    return this.mapPanel.map.getZoom() == record.data.level;
                }, this);

                if (scale.length > 0) {
                    scale = scale.items[0];
                    zoomSelector.setValue("1 : " + parseInt(scale.data.scale, 10));
                } else {
                    if (!zoomSelector.rendered) {
                        return;
                    }
                    zoomSelector.clearValue();
                }
            }
            setScale.call(this);
            this.mapPanel.map.events.register('zoomend', this, setScale);

            zoomSelectorWrapper.add(zoomSelector);
            zoomSelectorWrapper.doLayout();
        }, this);

        var mapOverlay = new Ext.Panel({
            // title: "Overlay",
            cls: 'map-overlay',
            items: [
                scaleLinePanel,
                zoomSelectorWrapper
            ]
        });

        mapOverlay.on("afterlayout", function(){
            scaleLinePanel.getEl().dom.style.position = 'relative';
            scaleLinePanel.getEl().dom.style.display = 'inline';

            mapOverlay.getEl().on("click", function(x){x.stopEvent();});
            mapOverlay.getEl().on("mousedown", function(x){x.stopEvent();});
        }, this);

        return mapOverlay;
    },

    createTools: function() {
        var toolGroup = "toolGroup";

        var printButton = new Ext.Button({
            tooltip: this.printTipText,
            iconCls: "icon-print",
            handler: function() {
                var unsupportedLayers = [];
                var printWindow = new Ext.Window({
                    title: this.printWindowTitleText,
                    modal: true,
                    border: false,
                    autoHeight: true,
                    resizable: false,
                    items: [{
                        xtype: "gxux_printpreview",
                        mapTitle: this.about["title"],
                        comment: this.about["abstract"],
                        minWidth: 336,
                        printMapPanel: {
                            height: Math.min(450, Ext.get(document.body).getHeight()-150),
                            autoWidth: true,
                            limitScales: true,
                            map: {
                                theme: null,
                                controls: [
                                    new OpenLayers.Control.Navigation({
                                        zoomWheelEnabled: false,
                                        zoomBoxEnabled: false
                                    }),
                                    new OpenLayers.Control.PanPanel(),
                                    new OpenLayers.Control.Attribution(),
                                    new OpenLayers.Control.DrawFeature(
                                            this.polygonLayer,
                                            OpenLayers.Handler.RegularPolygon,
                                            {handlerOptions: {
                                                     sides: 4,
                                                     irregular: true
                                            }
                                    })


                                ],
                                eventListeners: {
                                    "preaddlayer": function(evt) {
                                        if(evt.layer instanceof OpenLayers.Layer.Google) {
                                            unsupportedLayers.push(evt.layer.name);
                                            return false;
                                        }
                                    },
                                    scope: this
                                }
                            }
                        },
                        printProvider: {
                            capabilities: window.printCapabilities,
                            listeners: {
                                "beforeprint": function() {
                                    // The print module does not like array params.
                                    //TODO Remove when http://trac.geoext.org/ticket/216 is fixed.
                                    printWindow.items.get(0).printMapPanel.layers.each(function(l){
                                        var params = l.getLayer().params;
                                        for(var p in params) {
                                            if (params[p] instanceof Array) {
                                                params[p] = params[p].join(",");
                                            }
                                        }
                                    })
                                },
                                "print": function() {printWindow.close();},
                                "printException": function(cmp, response) {
                                    this.displayXHRTrouble(response);
                                },
                                scope: this
                            }
                        },
                        includeLegend: true,
                        sourceMap: this.mapPanel,
                        legend: this.legendPanel
                    }]
                }).show();
                printWindow.center();

                unsupportedLayers.length &&
                    Ext.Msg.alert(this.unsupportedLayersTitleText, this.unsupportedLayersText +
                        "<ul><li>" + unsupportedLayers.join("</li><li>") + "</li></ul>");

            },
            scope: this
        });

        // create a navigation control
        var navAction = new GeoExt.Action({
            tooltip: this.navActionTipText,
            iconCls: "icon-pan",
            enableToggle: true,
            pressed: true,
            allowDepress: false,
            control: new OpenLayers.Control.Navigation(),
            map: this.mapPanel.map,
            toggleGroup: toolGroup
        });

        // create a navigation history control
        var historyControl = new OpenLayers.Control.NavigationHistory();
        this.mapPanel.map.addControl(historyControl);

        // create actions for previous and next
        var navPreviousAction = new GeoExt.Action({
		tooltip: this.navPreviousActionText,
            iconCls: "icon-zoom-previous",
            disabled: true,
            control: historyControl.previous
        });

        var navNextAction = new GeoExt.Action({
		tooltip: this.navNextAction,
            iconCls: "icon-zoom-next",
            disabled: true,
            control: historyControl.next
        });


        // create a get feature info control
        var info = {controls: []};
        var infoButton = new Ext.Button({
		tooltip: this.infoButtonText,
            iconCls: "icon-getfeatureinfo",
            toggleGroup: toolGroup,
            enableToggle: true,
            allowDepress: false,
            toggleHandler: function(button, pressed) {
                for (var i = 0, len = info.controls.length; i < len; i++){
                    if(pressed) {
                        info.controls[i].activate();
                    } else {
                        info.controls[i].deactivate();
                    }
                }
            }
        });

        var updateInfo = function() {
            var queryableLayers = this.mapPanel.layers.queryBy(function(x){
                return x.get("queryable");
            });

            var map = this.mapPanel.map;
            var control;
            for (var i = 0, len = info.controls.length; i < len; i++){
                control = info.controls[i];
                control.deactivate();  // TODO: remove when http://trac.openlayers.org/ticket/2130 is closed
                control.destroy();
            }

            info.controls = [];
            queryableLayers.each(function(x){
                var control = new OpenLayers.Control.WMSGetFeatureInfo({
                    url: x.getLayer().url,
                    queryVisible: true,
                    layers: [x.getLayer()],
                    eventListeners: {
                        getfeatureinfo: function(evt) {
                            this.displayPopup(evt, x.get("title") || x.get("name"));
                        },
                        scope: this
                    }
                });
                map.addControl(control);
                info.controls.push(control);
                if(infoButton.pressed) {
                    control.activate();
                }
            }, this);
        };

        this.mapPanel.layers.on("update", updateInfo, this);
        this.mapPanel.layers.on("add", updateInfo, this);
        this.mapPanel.layers.on("remove", updateInfo, this);

        // create split button for measure controls
        var activeIndex = 0;
        var measureSplit = new Ext.SplitButton({
            iconCls: "icon-measure-length",
            tooltip: this.measureSplitText,
            enableToggle: true,
            toggleGroup: toolGroup, // Ext doesn't respect this, registered with ButtonToggleMgr below
            allowDepress: false, // Ext doesn't respect this, handler deals with it
            handler: function(button, event) {
                // allowDepress should deal with this first condition
                if(!button.pressed) {
                    button.toggle();
                } else {
                    button.menu.items.itemAt(activeIndex).setChecked(true);
                }
            },
            listeners: {
                toggle: function(button, pressed) {
                    // toggleGroup should handle this
                    if(!pressed) {
                        button.menu.items.each(function(i) {
                            i.setChecked(false);
                        });
                    }
                },
                render: function(button) {
                    // toggleGroup should handle this
                    Ext.ButtonToggleMgr.register(button);
                }
            },
            menu: new Ext.menu.Menu({
                items: [
                    new Ext.menu.CheckItem(
                        new GeoExt.Action({
				text: this.lengthActionText,
                            iconCls: "icon-measure-length",
                            map: this.mapPanel.map,
                            toggleGroup: toolGroup,
                            group: toolGroup,
                            allowDepress: false,
                            map: this.mapPanel.map,
                            control: this.createMeasureControl(
                                OpenLayers.Handler.Path, "Length")
                        })),
                    new Ext.menu.CheckItem(
                        new GeoExt.Action({
                            text: this.areaActionText,
                            iconCls: "icon-measure-area",
                            map: this.mapPanel.map,
                            toggleGroup: toolGroup,
                            group: toolGroup,
                            allowDepress: false,
                            map: this.mapPanel.map,
                            control: this.createMeasureControl(
                                OpenLayers.Handler.Polygon, "Area")
                            }))
                  ]})});
        measureSplit.menu.items.each(function(item, index) {
            item.on({checkchange: function(item, checked) {
                measureSplit.toggle(checked);
                if(checked) {
                    activeIndex = index;
                    measureSplit.setIconClass(item.iconCls);
                }
            }});
        });

        var enable3DButton = new Ext.Button({
            iconCls:"icon-3D",
            tooltip: this.switchTo3DActionText,
            enableToggle: true,
            toggleHandler: function(button, state) {
                if (state === true) {
                    this.mapPanelContainer.getLayout().setActiveItem(1);
                    this.toolbar.disable();
                    button.enable();
                } else {
                    this.mapPanelContainer.getLayout().setActiveItem(0);
                    this.toolbar.enable();
                }
            },
            scope: this
        });

        var tools = [
            new Ext.Button({
                tooltip: this.saveMapText,
                handler: this.showMetadataForm,
                scope: this,
                iconCls: "icon-save"
            }),
            new Ext.Action({
                tooltip: this.publishActionText,
                handler: this.makeExportDialog,
                scope: this,
                iconCls: 'icon-export',
                disabled: !this.mapID
            }),
            window.printCapabilities ? printButton : "",
            "-",
            new Ext.Button({
                handler: function(){
                    this.mapPanel.map.zoomIn();
                },
                tooltip: this.zoomInActionText,
                iconCls: "icon-zoom-in",
                scope: this
            }),
            new Ext.Button({
		    tooltip: this.zoomOutActionText,
                handler: function(){
                    this.mapPanel.map.zoomOut();
                },
                iconCls: "icon-zoom-out",
                scope: this
            }),
            navPreviousAction,
            navNextAction,
            new Ext.Button({
		    	tooltip: this.zoomVisibleButtonText,
                iconCls: "icon-zoom-visible",
                handler: function() {
                    var extent, layer;
                    for(var i=0, len=this.map.layers.length; i<len; ++i) {
                        layer = this.mapPanel.map.layers[i];
                        if(layer.getVisibility()) {
                            if(extent) {
                                extent.extend(layer.maxExtent);
                            } else {
                                extent = layer.maxExtent.clone();
                            }
                        }
                    }
                    if(extent) {
                        this.mapPanel.map.zoomToExtent(extent);
                    }
                },
                scope: this
            }),
            enable3DButton
        ];
        this.on("saved", function() {
            // enable the "Publish Map" button
            tools[1].enable();
            this.modified ^= this.modified & 1;
        }, this);

        return tools;
    },

    createMeasureControl: function(handlerType, title) {

        var styleMap = new OpenLayers.StyleMap({
            "default": new OpenLayers.Style(null, {
                rules: [new OpenLayers.Rule({
                    symbolizer: {
                        "Point": {
                            pointRadius: 4,
                            graphicName: "square",
                            fillColor: "white",
                            fillOpacity: 1,
                            strokeWidth: 1,
                            strokeOpacity: 1,
                            strokeColor: "#333333"
                        },
                        "Line": {
                            strokeWidth: 3,
                            strokeOpacity: 1,
                            strokeColor: "#666666",
                            strokeDashstyle: "dash"
                        },
                        "Polygon": {
                            strokeWidth: 2,
                            strokeOpacity: 1,
                            strokeColor: "#666666",
                            fillColor: "white",
                            fillOpacity: 0.3
                        }
                    }
                })]
            })
        });

        var cleanup = function() {
            if (measureToolTip) {
                measureToolTip.destroy();
            }
        };

        var makeString = function(metricData) {
            var metric = metricData.measure;
            var metricUnit = metricData.units;

            measureControl.displaySystem = "english";

            var englishData = metricData.geometry.CLASS_NAME.indexOf("LineString") > -1 ?
            measureControl.getBestLength(metricData.geometry) :
            measureControl.getBestArea(metricData.geometry);

            var english = englishData[0];
            var englishUnit = englishData[1];

            measureControl.displaySystem = "metric";
            var dim = metricData.order == 2 ?
                '<sup>2</sup>' :
                '';

            return metric.toFixed(2) + " " + metricUnit + dim + "<br>" +
                english.toFixed(2) + " " + englishUnit + dim;
        };

        var measureToolTip;
        var measureControl = new OpenLayers.Control.Measure(handlerType, {
            persist: true,
            handlerOptions: {layerOptions: {styleMap: styleMap}},
            eventListeners: {
                measurepartial: function(event) {
                    cleanup();
                    measureToolTip = new Ext.ToolTip({
                        target: Ext.getBody(),
                        html: makeString(event),
                        title: title,
                        autoHide: false,
                        closable: true,
                        draggable: false,
                        mouseOffset: [0, 0],
                        showDelay: 1,
                        listeners: {hide: cleanup}
                    });
                    if(event.measure > 0) {
                        var px = measureControl.handler.lastUp;
                        var p0 = this.mapPanel.getPosition();
                        measureToolTip.targetXY = [p0[0] + px.x, p0[1] + px.y];
                        measureToolTip.show();
                    }
                },
                measure: function(event) {
                    cleanup();
                    measureToolTip = new Ext.ToolTip({
                        target: Ext.getBody(),
                        html: makeString(event),
                        title: title,
                        autoHide: false,
                        closable: true,
                        draggable: false,
                        mouseOffset: [0, 0],
                        showDelay: 1,
                        listeners: {
                            hide: function() {
                                measureControl.cancel();
                                cleanup();
                            }
                        }
                    });
                },
                deactivate: cleanup,
                scope: this
            }
        });

        return measureControl;
    },

    /** private: method[makeExportDialog]
     *
     * Create a dialog providing the HTML snippet to use for embedding the
     * (persisted) map, etc.
     */
    makeExportDialog: function() {
        new Ext.Window({
            title: this.publishActionText,
            layout: "fit",
            width: 380,
            autoHeight: true,
            items: [{
                xtype: "gxp_embedmapdialog",
                url: this.rest + this.mapID + "/embed"
            }]
        }).show();
    },

    /** private: method[initMetadataForm]
     *
     * Initialize metadata entry form.
     */
    initMetadataForm: function(){

        var titleField = new Ext.form.TextField({
            width: '95%',
            fieldLabel: this.metaDataMapTitle,
            value: this.about.title,
            allowBlank: false,
            enableKeyEvents: true,
            listeners: {
                "valid": function() {
                    saveAsButton.enable();
                    saveButton.enable();
                },
                "invalid": function() {
                    saveAsButton.disable();
                    saveButton.disable();
                }
            }
        });

        var abstractField = new Ext.form.TextArea({
            width: '95%',
            height: 200,
            fieldLabel: this.metaDataMapAbstract,
            value: this.about["abstract"]
        });

        var metaDataPanel = new Ext.FormPanel({
            bodyStyle: {padding: "5px"},
            labelAlign: "top",
            items: [
                titleField,
                abstractField
            ]
        });

        metaDataPanel.enable();

        var saveAsButton = new Ext.Button({
            text: this.metadataFormSaveAsCopyText,
            disabled: !this.about.title,
            handler: function(e){
                this.about.title = titleField.getValue();
                this.about["abstract"] = abstractField.getValue();
                this.metadataForm.hide();
                this.save(true);
            },
            scope: this
        });
        var saveButton = new Ext.Button({
            text: this.metadataFormSaveText,
            disabled: !this.about.title,
            handler: function(e){
                this.about.title = titleField.getValue();
                this.about["abstract"] = abstractField.getValue();
                this.metadataForm.hide();
                this.save();
            },
            scope: this
        });

        this.metadataForm = new Ext.Window({
            title: this.metaDataHeader,
            closeAction: 'hide',
            items: metaDataPanel,
            modal: true,
            width: 400,
            autoHeight: true,
            bbar: [
                "->",
                saveAsButton,
                saveButton,
                new Ext.Button({
                    text: this.metadataFormCancelText,
                    handler: function() {
                        titleField.setValue(this.about.title);
                        abstractField.setValue(this.about["abstract"]);
                        this.metadataForm.hide();
                    },
                    scope: this
                })
            ]
        });
    },

    /** private: method[showMetadataForm]
     *  Shows the window with a metadata form
     */
    showMetadataForm: function() {
        if(!this.metadataForm) {
            this.initMetadataForm();
        }

        this.metadataForm.show();
    },

    updateURL: function() {
        /* PUT to this url to update an existing map */
        return this.rest + this.mapID + '/data';
    },

    /** api: method[save]
     *  :arg as: ''Boolean'' True if map should be "Saved as..."
     *
     *  Subclasses that load config asynchronously can override this to load
     *  any configuration before applyConfig is called.
     */
    save: function(as){
        // save unsaved styles first
        for (var id in this.stylesDlgCache) {
            this.stylesDlgCache[id].saveStyles();
        }

        var config = this.getState();

        if (!this.mapID || as) {
            /* create a new map */
            Ext.Ajax.request({
                url: this.rest,
                method: 'POST',
                jsonData: config,
                success: function(response, options) {
                    var id = response.getResponseHeader("Location");
                    // trim whitespace to avoid Safari issue where the trailing newline is included
                    id = id.replace(/^\s*/,'');
                    id = id.replace(/\s*$/,'');
                    id = id.match(/[\d]*$/)[0];
                    this.mapID = id; //id is url, not mapID
                    this.fireEvent("saved", id);
                },
                scope: this
            });
        }
        else {
            /* save an existing map */
            Ext.Ajax.request({
                url: this.updateURL(),
                method: 'PUT',
                jsonData: config,
                success: function(response, options) {
                    /* nothing for now */
                    this.fireEvent("saved", this.mapID);
                },
                scope: this
            });
        }
    }
});
