// map url patterns to exported JSGI app functions
var urls = [
    [(/^\/proxy/), require("./proxy").app]
];

// debug mode loads unminified scripts
// assumes markup pulls in scripts under the path /servlet_name/script/
if (java.lang.System.getProperty("app.debug")) {
    var fs = require("fs");
    var config = fs.normal(fs.join(module.directory, "..", "buildjs.cfg"));
    urls.push(
        [(/^\/script(\/.*)/), require("./autoloader").App(config)]
    );

    // proxy a remote geoserver on /geoserver and the original path by setting
    // proxy.geoserver to remote URL - only recommended for debug mode
    var geoserver = java.lang.System.getProperty("app.proxy.geoserver");
    if (geoserver) {
        if (geoserver.charAt(geoserver.length-1) !== "/") {
            geoserver = geoserver + "/";
        }
        var path = geoserver.split("/");
        var geoserverEndpoint = path[path.length-2];
        if (geoserverEndpoint != "geoserver") {
            urls.push(
                [new RegExp("^\\/" + geoserverEndpoint + "\\/(.*)"), require("./proxy").pass({url: geoserver, preserveHost: true})]
            );
        }
        urls.push(
            [(/^\/geoserver\/(.*)/), require("./proxy").pass({url: geoserver, preserveHost: true})]
        );
    }

    // proxy a remote geonode on / - only recommended for debug mode
    var geonode = java.lang.System.getProperty("app.proxy.geonode");
    if (geonode) {
        if (geonode.charAt(geonode.length-1) !== "/") {
            geonode = geonode + "/";
        }
        var endpoints = ["maps", "data", "accounts", "impact", "proxy", "lang.js", "jsi18n"];
        var isJS, endpoint;
        for (var i=endpoints.length-1; i>=0; --i) {
            endpoint = endpoints[i];
            isJS = endpoint.indexOf(".js") == endpoint.length-3;
            urls.push(
                [new RegExp("^\\/" + endpoints[i] + "(\\/(.*))?"), require("./proxy").pass({url: geonode + endpoints[i] + (isJS ? "#" : "/")})]
            );
        }
    }
}

exports.urls = urls;

// redirect requests without a trailing slash
// Jetty does this automatically for /servlet_name, Tomcat does not
function slash(config) {
    return function(app) {
        return function(request) {
            var response;
            var servletRequest = request.env.servletRequest;
            var pathInfo = servletRequest.getPathInfo();
            if (pathInfo === "/") {
                var uri = servletRequest.getRequestURI();
                if (uri.charAt(uri.length-1) !== "/") {
                    var location = servletRequest.getScheme() + "://" + 
                        servletRequest.getServerName() + ":" + servletRequest.getServerPort() + 
                        uri + "/";
                    return {
                        status: 301,
                        headers: {"Location": location},
                        body: []
                    };
                }
            }
            return app(request);
        };
    };
}

exports.middleware = [
    slash(),
    require("ringo/middleware/gzip").middleware,
    require("ringo/middleware/static").middleware({base: module.resolve("static"), index: "index.html"}),
    require("ringo/middleware/error").middleware,
    require("ringo/middleware/notfound").middleware
];

exports.app = require("ringo/webapp").handleRequest;

exports.charset = "UTF-8";
exports.contentType = "text/html";
