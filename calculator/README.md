# Risiko Calculator

## Preparation

Initialize the build environment.

    ant init

You only need to run `ant init` once (or any time dependencies change).

## Debug Mode

Loads all scripts uncompressed.

    ant debug

This will give you an application available at http://localhost:8080/ by
default.

To use a GeoServer instance other than
http://localhost:8001/geoserver-geonode-dev, add the following option to the
`ant debug` command:

    -Dapp.proxy.geoserver=<geoserver_url>

where `<geoserver_url>` is e.g.
http://my.risiko.box/geoserver-geonode-dev/

## Prepare App for Deployment

To create a servlet run the following:

    ant

The servlet will be assembled in the build directory.
