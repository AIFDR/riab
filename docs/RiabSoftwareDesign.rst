Risk in a Box - Software Design Specification
=============================================

![][1]

   [1]: http://docs.google.com/document/pubimage?id=1zMydsejDBC27Cvxp2Ci5rIWu59fuC_6j7Mmbqi4Bck8&image_id=1NZFgoNuKhRfUA8M12jHLDr08i4SAfw

Software Design Specification

* * *

* * *

Riab (Risk in a Box) Version 0.2

14/1/2011

Name

Changes

Doc Version

Date

Ted Dunstone

Initial Document

0.1a

14/1/2011

Ole Nielsen

Update and questions

0.1b

         18/1/2011

Ariel Núñez

HTTP Rest API and riab-core python library.

0.1c

23/02/2011

# Contents

[Contents][2]

   [2]: http://docs.google.com/document/pub?id=1zMydsejDBC27Cvxp2Ci5rIWu59fuC_6j7Mmbqi4Bck8#h.3akno4-ihzx49

[Introduction][3]

   [3]: http://docs.google.com/document/pub?id=1zMydsejDBC27Cvxp2Ci5rIWu59fuC_6j7Mmbqi4Bck8#h.442beb-wji2vt

[System Overview][4]

   [4]: http://docs.google.com/document/pub?id=1zMydsejDBC27Cvxp2Ci5rIWu59fuC_6j7Mmbqi4Bck8#h.agkqzg-iunou5

[Design Considerations][5]

   [5]: http://docs.google.com/document/pub?id=1zMydsejDBC27Cvxp2Ci5rIWu59fuC_6j7Mmbqi4Bck8#h.ibshwc-xnoz0m

[Assumptions and Dependencies][6]

   [6]: http://docs.google.com/document/pub?id=1zMydsejDBC27Cvxp2Ci5rIWu59fuC_6j7Mmbqi4Bck8#h.ybpv2h-c81clf

[General Constraints][7]

   [7]: http://docs.google.com/document/pub?id=1zMydsejDBC27Cvxp2Ci5rIWu59fuC_6j7Mmbqi4Bck8#h.r43baz-6ceb7q

[Goals and Guidelines][8]

   [8]: http://docs.google.com/document/pub?id=1zMydsejDBC27Cvxp2Ci5rIWu59fuC_6j7Mmbqi4Bck8#h.178iui-lotqub

[Architectural Strategies][9]

   [9]: http://docs.google.com/document/pub?id=1zMydsejDBC27Cvxp2Ci5rIWu59fuC_6j7Mmbqi4Bck8#h.s8ntl9-323i9o

[System Architecture][10]

   [10]: http://docs.google.com/document/pub?id=1zMydsejDBC27Cvxp2Ci5rIWu59fuC_6j7Mmbqi4Bck8#h.tg4h06-gdwvf2

[Component Communications][11]

   [11]: http://docs.google.com/document/pub?id=1zMydsejDBC27Cvxp2Ci5rIWu59fuC_6j7Mmbqi4Bck8#h.rdnw6e-5cpbi5

[Detailed System Design][12]

   [12]: http://docs.google.com/document/pub?id=1zMydsejDBC27Cvxp2Ci5rIWu59fuC_6j7Mmbqi4Bck8#h.pqj6n8-hro8nj

[Detailed Subsystem – Riab-Server][13]

   [13]: http://docs.google.com/document/pub?id=1zMydsejDBC27Cvxp2Ci5rIWu59fuC_6j7Mmbqi4Bck8#h.u3o6fa-fu0h58

[Detailed Subsystem – Riab-Django][14]

   [14]: http://docs.google.com/document/pub?id=1zMydsejDBC27Cvxp2Ci5rIWu59fuC_6j7Mmbqi4Bck8#h.aa9wk4-w6ec5r

[Detailed Subsystem – PyPlugin][15]

   [15]: http://docs.google.com/document/pub?id=1zMydsejDBC27Cvxp2Ci5rIWu59fuC_6j7Mmbqi4Bck8#h.dpnfv5-jl016v

[Glossary][16]

   [16]: http://docs.google.com/document/pub?id=1zMydsejDBC27Cvxp2Ci5rIWu59fuC_6j7Mmbqi4Bck8#h.fx16zn-70naxf

[BibliographyBibliography][17]

   [17]: http://docs.google.com/document/pub?id=1zMydsejDBC27Cvxp2Ci5rIWu59fuC_6j7Mmbqi4Bck8#h.xpqokl-s1sliw

##

Introduction
############

This document is a software design specification of the “Risk in a Box”
solution or Riab[[1]][18] for short. It is intended as a reference document
for the software architecture to inform and guide developers about the
architecture, standards, coding conventions, use cases and design constrains.

   [18]: http://docs.google.com/document/pub?id=1zMydsejDBC27Cvxp2Ci5rIWu59fuC_6j7Mmbqi4Bck8#ftnt1

Good risk analyses rely on modelling using spatial information ranging from
geophysical data to population information and administrative jurisdictions.
The purpose tool is to support the implementation of risk assessment
guidelines by:

  1. Making them easy to use
  2. Allowing results to be reproduced
  3. Ensuring consistency across different reporting authorities

In support of these aims risk in the box will:

  1. Be able to be run across a variety of common platforms
  2. Run both locally without Internet access and remotely
  3. Use commonly available standards and technologies
  4. Support interfaces to a variety of external systems (e.g. GeoNode)
  5. Support flexible development of impact models using plugins
  6. Be internationalized

Basic system requirements to use Risk in a Box are GeoNode, Apache, Python,
Django, Open Layers. This includes having a Java Runtime Environment
installed.

A document describing the aims of the risk in a box project in more detail is
provided at: [Risk in a Box - Project Plan][19]w

   [19]: https://docs.google.com/document/d/1CPM1Vvm7uWCzBqhUfWNXdSrHRmEvn8oaLPbOQEZaF3s/edit?authkey=CJydxacH&hl=en&pli=1%23

System Overview
---------------

Riab in essence provides a way that scientific data in the form of spatial
hazard estimates from tsunami, earthquake, volcanic ash, storms etc. can be
combined with exposure data such as population or infrastructure to provide
end users such as disaster managers with a geographic risk/impact estimation.
This will ultimately allow the construction of an actionable risk management
plan.

To this end the system must be able to take a variety of geographic data
layers (in either vector or raster) from a GeoNode and intelligently work out
what impact function will be  appropriate for a given hazard and exposure.
These impact functions will be written as plugins and will allow experts to
construct new techniques for an impact calculation of the form

Impact = Risk_Plugin(Hazard, Exposure)

The hazard and exposure types will be determined from the meta data stored
with the GeoNode layer and this is used to choose the correct plugin.

For flexibility and maintainability the software is split into two major
subsystems which will communicate using XML-RPC.

  1. Riab-Engine: The central server that will calculate the impact function using plugins and data fetched from the GeoServers. It is expected to run standalone and have a dependency in Celery. With code based on the djcelery package (http://pypi.python.org/pypi/django-celery)
  2. Riab-Client: The web based front-end allowing both a simplified end-user front end and a more advanced administration mode.

![][20]

   [20]: http://docs.google.com/drawings/image?id=sSmpRKiYtVSU2JF-7D3COGQ&rev=57&h=342&w=400&ac=1

Figure 1: High Level Riab components

Design Considerations
---------------------

This section describes the design issues and considerations that are being
addressed during the full design process.

Assumptions and Dependencies
----------------------------

Primary dependencies exist with the GeoServer REST interface and the Django
Version.

Django was chosen as the web framework as it is synergic with other relevant
project and has an active development community.

Python 2.7x is being used to develop this project (both for Django and Server)
as it provides good flexibility for this type of system design. Version 3.x of
python has been released, and will eventually supersede the 2.x series however
support for 3.x in third party libraries is currently still low so the risk of
software issues in using python versions >2 judged to be higher as of Jan
2011.

The Riab solution will be implemented in phases. See Riab Projec Plan for
details.

The verson 1.0 assumptions are included below:

  1. Riab will need to be able to run on a local disconnected PC via a USB interface.
  2. Centralized server installation must also be supported
  3. Windows and Linux (developed using Ubuntu ![][21] 10.4) will need to be supported
  4. End-user characteristics : Risk Managers

   [21]: https://www.google.com/chart?cht=tx&chf=bg,s,FFFFFF00&chco=000000&chl=%5Cgeq%7B%7D

  1. Risk Managers will not be expert in hazard modelling
  2. Will use the system through a web browser
  3. Interface must be simple and support full language internationalization.
  4. Input should allow local users to upload geo-data from spreadsheets about local conditions.
  5. Output should be clear and understandable.
  6. An expert advanced user mode should be supported for more experienced users.

  1. End-user characteristics: Advanced Modellers

  1. Must be able to upload maps layers and set layer metadata
  2. Should be able to use the plugin API to define new risk/impact functions

  1. End-user characteristics: Administrators

  1. Should be able to setup users permissions
  2. Review an audit of activities
  3. Update local documentation

  1. Possible and/or probable changes in functionality 

  1. Support for more complex impact models
  2. Output should lead to a full risk management plan
  3. Increase support for probabilistic modeling (on a hazard by hazard basis)
  4. Interface with other Risk based web frameworks and with science based hazard estimation tools.

## General Constraints

Describe any global limitations or constraints that have a significant impact
on the design of the system's software (and describe the associated impact).
Such constraints may be imposed by any of the following:

  1. Hardware or software environment 

  1. Limitation of no network cases or low spec’ed machines

  1. End-user environment:
  2. Standards compliance 

  1. Should conform with international standards including WMS [http://www.opengeospatial.org/standards/wms)][22]

   [22]: http://www.google.com/url?q=http%3A%2F%2Fwww.opengeospatial.org%2Fstandards%2Fwms)&sa=D&sntz=1&usg=AFQjCNGial1c8xt6RycdRG8xQhelrYRTlA

  1. Interoperability requirements 

  1. OGC compliant protocols (as above)

  1. Interface/protocol requirements 

  1. Must be able to be completely distributed (i.e. remote geoservers) or completely local (everything running on one PC)

  1. Data repository and distribution requirements 
  2. Security requirements (or other such regulations) 

  1. The system should not hold user sensitive data
  2. Consideration should be given to OpenID as a standard for authentication.

  1. Memory and other capacity limitations 

  1. ?

  1. Performance requirements 

  1. Peak transaction volume even when centralizated will be relatively low (less than 1 request per second)

  1. Verification and validation requirements (testing) 

  1. All builds should have a full test suite used

## Goals and Guidelines

Principles which embody the design of software include:

  1. Modularity and functional separation. Ensuring that API level separation (via web services) is maintained between the functional components (Server, Web frontend and GeoServer) 
  2. Emphasis on maintainability and robustness versus speed. Since this will be an open source project it is desired to make the code simple and well documented.
  3. Ability to play well with other relevant frameworks. The Riab system will need to integrate with other Risk based web frameworks and with science based hazard estimation tools e.g. OpenQuake, BNPB DIPI, Bakosurtanal SIGN project etc.

#

# Architectural Strategies

The Riab server is designed to be stateless. This provides both greater
flexibility and robustness as it allows for easier scaling and for more
comprehensive testing. The impact of this is a slight performance hit since
reconnections (and re: authentication) to GeoServers need to be done for each
transaction.

All user settings and user interface will be managed through the Django
framework application. The GeoServer rendering will be done using OpenLayers 
(http://openlayers.org/) and other associated javascript GeoExt, GXP. Where
practical  functions will be exposed as Ajax calls.

The web interface is yet to be documented.

# System Architecture

This section provides a high-level overview of how the functionality and
responsibilities are partitioned and then assigned to subsystems and
components. The various architectural components of Riab and the protocols
used are described below (see .)[NOTE: GeoServer and pyplugin have been left
out for the moment until we are sure about the overall structure.]

![][23]

   [23]: http://docs.google.com/drawings/image?id=s0eWz-67LaPX24cFuGpBGHg&rev=55&h=362&w=562&ac=1

Figure 2: High Level Architecture Components

Riab Core (riab_core): This module is responsible for calculating the impact
function. It uses file like objects (e.g. geotiff and gml) and associated
metadata to determine which risk plug-in to call. It then calls this plugin
and writes the resulting layer to file and returns the fully qualified
pathname. Riab Core makes the following assumptions:

  1. Input layer files are either geotiff (for raster data) or gml (for vector data)
  2. All layers are in WGS84 geographic coordinates
  3. Layers are named (either as dictionaries or using the internal naming structure of geotiff and gml) 

Risk Plugins: These are plugins written in python that allow customized impact
functions to be run depending on the type of hazard and the exposure. There
may be none, one or many plugins that will satisfy a particular combination of
hazard and exposure. Each plugin makes the following assumptions

  1. Input data are dictionaries of numerical (numpy) arrays where keys are the original layer names.
  2. Data points have been aligned so vector operations are allowed.
  3. It is up to the plugin to know the semantics of names and attributes, i.e. if there is a layer named ‘WALL_TYPE’ with attributes like ‘Fibro’, ‘Timber’, ‘Brick veneer’ etc, the plugin must be aware of the meaning of these names and used them correctly.

PyPlugin: A flexible python library to manage the plugins, find the
appropriate plugin for a given criteria and execute this.

Riab Server (riab_server): This is the central stateless server that exposes
the API for riab_core via XML-RPC.

Riab Web Server (riab_django): The web based front-end allowing both a
simplified, advanced and administration user types. Riab-django is responsible
for retrieving and storing layers on one or more GeoNode and for passing the
associated files on to riab_server for computation. The web client can query
the Riab-Server to find out what plugins are available and request an impact
calculation based on one or more layers hazard and one or more exposure
layers. The administration of users and other local settings are managed by
Django. In particular it will

  1. Allow the user to select layers for hazard levels and exposure data
  2. Get layers from GeoNodes by bounding box and in WGS84 geographical coordinates irrespective of the native projection or datum and provide them to riab_server as geotiff (for rasters) or gml (for vector data).
  3. Put resulting layers back to a GeoNode and provide a view of them
  4. Provide legends for all layers
  5. …..

Riab Web Interface: Rendered using Django Templates and OpenLayers . The
interface talks to both the Riap-Django and the relavent GeoServers.

# Component Communications

The flow of information between subsystems is shown below ().  Note that this
diagram includes a full test case including the initial upload of data into
Geoserver. This will not be required for risk managers. The bold items show
steps that are either input or output for the user.

![][24]

   [24]: http://docs.google.com/document/pubimage?id=1zMydsejDBC27Cvxp2Ci5rIWu59fuC_6j7Mmbqi4Bck8&image_id=1gxQ1nVMSfDjbz7MuPTrJ_eD5lcpu9Q

[][25]

   [25]: http://docs.google.com/document/pub?id=1zMydsejDBC27Cvxp2Ci5rIWu59fuC_6j7Mmbqi4Bck8

Figure 3: Riab Component Communications Flow

#

# Detailed System Design

This section contain a detailed designs of the Riab system components.

## RIAB HTTP API

#### All API calls start with

 http://myriab.com/api/v1

#### Version

#### All API calls begin with API version. For this documentation, we will
assume every request begins with the above path.

#### Path

#### For this documentation, we will assume every request begins with the
above path.

#### Units

#### All coordinates are in WGS-84 (EPSG:4326) unless otherwise specified and
all units of measurement are in the International System of Units (SI).

#### Format

#### All calls are returned in JSON.

#### Status Codes

  1. 200 Successful GET and PUT.
  2. 201 Successful POST.
  3. 202 Successful calculation queued.
  4. 204 Successful DELETE
  5. 401 Unauthenticated.
  6. 409 Unsuccessful POST, PUT, or DELETE (Will return an errors object).

#### Endpoints

  1. POST[/calculation][26]
  2. GET[/calculation/:id][27]
  3. GET[/calculation/:id/status][28]
  4. GET[/functions][29]
  5. GET[/functions/:id][30]

   [26]: http://www.google.com/url?q=http%3A%2F%2Fingenieroariel.com%2Fstatic%2Friab%2F%23POST-%2Fcalculation&sa=D&sntz=1&usg=AFQjCNEiOzkZ6EgGxJuVmsQjy9rIoxhZuQ
   [27]: http://www.google.com/url?q=http%3A%2F%2Fingenieroariel.com%2Fstatic%2Friab%2F%23GET-%2Fcalculation%2F%3Aid&sa=D&sntz=1&usg=AFQjCNG4avodyCqOlYPQH4ibu__kva1pmw
   [28]: http://www.google.com/url?q=http%3A%2F%2Fingenieroariel.com%2Fstatic%2Friab%2F%23GET-%2Fcalculation%2F%3Aid%2Fstatus&sa=D&sntz=1&usg=AFQjCNHo5wE6fFwIeddxH3AtowqW-2sKGw
   [29]: http://www.google.com/url?q=http%3A%2F%2Fingenieroariel.com%2Fstatic%2Friab%2F%23GET-%2Ffunctions&sa=D&sntz=1&usg=AFQjCNHfdOq3r-tM7jcrtWJ3qar27OPErA
   [30]: http://www.google.com/url?q=http%3A%2F%2Fingenieroariel.com%2Fstatic%2Friab%2F%23GET-%2Ffunctions%2F%3Aid&sa=D&sntz=1&usg=AFQjCNFXyP2Q9JSztbA5bzeoKTL3hdsJUg

##### POST /calculation

Calculate the Impact as a function of Hazards and Exposures. Required fields
are:

  1. impact_function: URI of the impact function to be run
  2. hazards: A dictionary of named hazard levels .. {‘h1’: H1, ‘h2’: H2, … ‘hn’: HN] each H is either a GeoNode layer uri or a geoserver layer path where each layer follows the format username:userpass@geoserver_url:layer_name
  3. exposure: An array of exposure levels ..[E1,E2...EN] each E is either a download url a geoserver layer path
  4. impact_level: The output impact level

Possible responses include 202 or 409

example request:

curl -u alice:cooper http://myriab.com/api/v1/calculation \

   -F "impact_function=/functions/1" \

   -F "hazards=/data/geonode:hazard1" \

   -F "exposure=user:pass@geoserver_url:exposure_1" \

   -F "impact_level=100" \

   -F "keywords=some,keywords,added,to,the,created,map"

  
response:

202 Accepted

 {

   "uri": "/riab/calculation/9",

   "transition_uri": "/riab/calculation/9/status",

   "warnings": [ "Projection unknown, layer geoserver_url:exposure_1 does not
have projection information" ]

 }

another possible response:

409 Conflict

  [

   "Invalid Impact function: Impact function does not support the hazard
and/or exposure type",

  ]

##### GET /calculation/:id

Returns the details of a given calculation. Api will respond with status 200
if calculation has been completed and 404 if it is still in progress.

example request

  
 $ curl -u alice:cooper http://myriab.com/api/v1/calculation/9

response:

  
   {

     "uri": "/riab/calculation/9",

     "result_uri": "/data/layer/54",

     "calculation_map_uri": "/data/maps/23",

     "info": ["Retrieving data for layer x", "Calculating impact", "Warning:
Had to cast doubles to single precision", "Calculation finished successfully",
"Uploading impact data", "Creating map in geonode with hazard, exposure and
impact layers"]

   }

##### GET /calculation/:id/status

Gets the status of the calculation. It will usually respond with 200.

example request

  
 $ curl -u alice:cooper http://myriab.com/api/calculation/9/status

response:

  
   {

     "success": "true",

     "message": "The calculation has been performed successfully"

   }

another possible response:

  {

     "success": "false",

     "message": "An error has occurred during processing: (if you have admin
rights a full stack trace can be found below)"

   }

##### GET /functions

Returns a collection of impact functions, if no hazard or exposure levels are
provided it returns all the available ones.. Response will be 200

example request

 $ curl -u alice:cooper http://myriab.com/api/v1/functions \

   -F "hazards=/data/geonode:HazardZ" \

   -F "exposure=/data/geonode:ExposureX"

response:

  
[

   {

     "uri": "/functions/1",

     "name": "Super duper impact function",

     "author": "Alice cooper",

     "description": "It does what you expect it to ...."

   },

   {

     "uri": "/functions/2",

     "name": "Another nice impact function",

     "author": "Alice Cooper",

     "description": "You can't imagine ..."

   },

   ...

 ]

##### GET /function/:id

Returns the details of the given impact function. Possible responses include
200 or 404

example request

  
 $ curl -u alice:cooper http://myriab.com/api/v1/function/1

response:

 {

     "uri": "/functions/1",

     "name": "Another nice impact function",

     "author": "Alice Cooper",

     "description": "You can't imagine ..."

   }

## Detailed Subsystem – Riab-Server

See [http://www.aifdr.org/projects/riat/wiki/ApiDraft][31]

   [31]: http://www.google.com/url?q=http%3A%2F%2Fwww.aifdr.org%2Fprojects%2Friat%2Fwiki%2FApiDraft&sa=D&sntz=1&usg=AFQjCNG8e9ccRB-w1OoNJj4C48ZLVqQWGg

## [Detailed Subsystem – Riab-Django][32]

   [32]: http://www.google.com/url?q=http%3A%2F%2Fwww.cmcrossroads.com%2Fbradapp%2Fdocs%2Fsdd.html%23TOC_SEC16&sa=D&sntz=1&usg=AFQjCNE1wcow3rRA5bsZiAye6mZ2Ht6GXQ

To be completed.

## Detailed Subsystem – PyPlugin

To be completed.

# Glossary

Magnitude: The energy released at the source of the earthquake.

Hazard Level: Ground acceleration, Maximum water depth, Ash Thickness,
Acceleration at selected frequencies or modes are examples of Hazard levels.

Exposure Level: Population density or Infrastructures (house of building type
or dollars per sqm)

Impact: Number of fatalities / Dollar Losses / Buildings Collapsed for example

Risk: Impact with an associated probability - how bad and how often

Return Period: Inverse of probability. e.g. 100 year flood - flood event of
probability of 1% per year

# BibliographyBibliography

References to other RIAB documentation

To be completed.

* * *

[[1]][33]

   [33]: http://docs.google.com/document/pub?id=1zMydsejDBC27Cvxp2Ci5rIWu59fuC_6j7Mmbqi4Bck8#ftnt_ref1

[Edit this page][34] (if you have permission)-Published by [Google
Docs][35]-[Report Abuse][36]-Updated automatically every 5 minutes

   [34]: https://docs.google.com/document/d/1zMydsejDBC27Cvxp2Ci5rIWu59fuC_6j7Mmbqi4Bck8/edit (Risk in a Box - Software Design Specification)
   [35]: http://docs.google.com/ (Learn more about Google Docs)
   [36]: http://docs.google.com/abuse?id=1zMydsejDBC27Cvxp2Ci5rIWu59fuC_6j7Mmbqi4Bck8
