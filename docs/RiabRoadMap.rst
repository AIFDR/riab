**Risk in a Box - Project Plan**

*Project Plan*

.. sectnum::

.. role:: raw-math(raw)
    :format: latex html

:Name:
  Riab (Risk in a Box)

:Version: 0.2
:Date: 14/3/2011

================== ==================================== =========== ==========
Name               Changes                              Doc Vers    Date
================== ==================================== =========== ==========
Ole Nielsen        Initial Document                     0.1a        16/12/2010
Ariel Nunez        Architecture modifications           0.1b        19/12/2010
Ole Nielsen        Moved to RST format                  0.2         14/03/2011
================== ==================================== =========== ==========


.. contents::

TEST

.. image:: https://docs.google.com/drawings/pub?id=1DG2RT3wREAd0fC0mGUqgbFR3YwNDY9QWHZ4Kb7p_uRU&w=960&h=720

.. figure:: https://docs.google.com/drawings/pub?id=1DG2RT3wREAd0fC0mGUqgbFR3YwNDY9QWHZ4Kb7p_uRU&w=960&h=720

.. image:: https://docs.google.com/drawings/pub?id=1DG2RT3wREAd0fC0mGUqgbFR3YwNDY9QWHZ4Kb7p_uRU&w=960&h=720

GITHUB

.. image:: https://github.com/AIFDR/riab/blob/master/docs/images/ground_shaking.jpg

LOCAL

.. image:: images/ground_shaking.jpg

GOOGLE

.. image:: https://docs.google.com/drawings/pub?id=14meGu1c8xRfUNlWq1eAk-vkiUHM1RoqRZ926jv1khlk&w=480&h=360




GITHUB

.. figure:: https://github.com/AIFDR/riab/blob/master/docs/images/ground_shaking.jpg

LOCAL

.. figure:: images/ground_shaking.jpg

GOOGLE

.. figure:: https://docs.google.com/drawings/pub?id=14meGu1c8xRfUNlWq1eAk-vkiUHM1RoqRZ926jv1khlk&w=480&h=360


Background
==========

The impacts from natural hazards are increasing worldwide and it is widely
acknowledged that understanding and communicating the risks of hazards
becoming disasters are fundamental to saving lives, livelihoods and
infrastructure. Modelling of hazards, their consequences and likelihoods to
establish the necessary information is a key to understanding disaster risk
faced by communities. Governments worldwide are therefore increasingly
requiring rigorous, standardised and accessible risk modelling to underpin
disaster management decisions. In Indonesia this requirement is expressed
through the Disaster Management law (24/2007) which among other things
require emergency managers in each province to conduct multi hazard risk
assessments based on national risk assessment guidelines.

Good risk analyses rely on modelling using spatial information ranging from
geophysical data to population information and administrative jurisdictions.
The purpose of this project is to develop a tool that will support the
implementation of risk assessment guidelines by

1.  Making them easy to use
2.  Allowing results to be reproduced
3.  Ensuring consistency across different provinces

The purpose of this project is to develop a web based tool that will model
impacts of different hazard events on population or infrastructure according
to given guidelines to support the overall process of sub national risk
assessments in Indonesia. However, the software developed is likely to be
useful more broadly as a general impact modelling tool.


Summary
=======

Impact modelling is typically done by combining spatial data sets
representing hazard levels such as ground shaking intensity, water
depth/velocity, volcanic ash deposit thickness, wind speed etc with
information about population, buildings and infrastructure. Risk-in-a-Box
will let the user select the data sets from a server, conduct the impact
model, create an impact map and upload it to a server. The tool is
independent of hazard and exposure types and configured entirely by the
(hazard and exposure) data sets and impact functions used.

In general, impact assessments involve applying hazard levels from a hazard
map to exposed infrastructure or population according to specific impact
functions (e.g. fragility curves for building loss estimation or fatality
models for estimation of loss of life) and then aggregating the results
according to some administrative boundary.

Mathematically, this can be expressed as

:raw-math:`\[ I_{h,i,k} = \sum_{j \in \Omega_k} F_{h, i}(\lambda_h(x_j), \kappa_i(x_j) \]`


where

*  I_{h, i, k} is the impact level for hazard h, exposure data i and region k
* \Omega_k is the set of indices of points inside region k
* x_j are the coordinates of the j'th point. Points will typically coincide with locations of exposure data.
* \lambda_h(x) is the hazard level for hazard h at point x
* \kappa_i(x) is the exposure value (e.g. population, structure value) for exposure data i at point x
* F_{h, i}(a, b) is the impact function for hazard h and exposure data i with hazard level a and exposure value b

If there is the need for the impact function to also explicitly take location
into account, it can be defined to take x as a third argument.

Hazard levels can also be vector values e.g. one for each mode of ground
acceleration.

Exposure values can also be vector e.g. number of buildings of each type
(masonry, reinforced concrete, wood, etc)


Scope
=====

The scope for this document is the development of Risk-in-a-Box version 1.0
(RIAB v1.0) with the following features.

*  Ability to calculate impact from hazard and exposure levels provided
   as raster, polygons, lines or point data at arbitrary resolutions.

*  Ability to optionally aggregate calculated impacts within arbitrary
   polygons

*  Ability to register impact functions according to type of hazard and
   exposure data
*  Ability to import simple exposure data as points or polygons

*  This may be through a stand-alone tool for upload and simple QC of
   data. It should for instance allow users to upload a CSV file of data
   with an option to select which column represent what data (e.g. latitue,
   longitude, exposure level) - inspired a bit by EXCEL or ARC?s csv import
   facility. The range of input formats and functionality should be
   determined from use cases emerging from trials of Risk-in-a-box.

*  Ability to import hazard levels from other sources (lower priority)

The following functionality is considered out-of-scope for RIAB v1.0

*  RIAB v1.0 will not include fully probabilistic risk assessments as
   these are usually dependent on the the individual hazard. Future versions
   may well start to include this on a hazard by hazard basis.

*  Although most impact models are simply a functional combination of a
   hazard scenario with exposure data, there are examples where more complex
   specific combinations are needed. For example adding ground acceleration,
   site amplification, distance to known faults, distance to nearest
   earthquake. While this is probably easy to do by programming to the API
   it is not in scope for the RIAB v1.0 web front end.
*  RIAB v1.0 does not include any hazard modelling

Identified versions of RIAB are

*  RIAB v0.1: Current Ruby demonstrator:`
    `_`http://203.77.224.75:3000/`_

*  RIAB v0.2: Rebuild of demonstrator using chosen platform (e.g. Django
    and Geonode)

*  RIAB v1.0: The version aimed at in this project plan

Note (Don?t know where this fits):

RIAB v1.0 aims at determining admissible impact function based on the
?type? of hazard and exposure levels. This type could be registered with
keywords fields in GeoServer and extracted via REST. However, earlier
versions could skip this and just provide the user with a full list of
possible impact functions to select from.


Architecture
============

Risk-in-a-Box is conceived to consist of the following components

1.  Web interface that will allow

1.  Display of layers involved
2.  Selection of hazard, exposure, boundaries and optionally impact
    function
3.  Selection of aggregation boundaries
4.  Manual uploading of new data sets

1.  Library that will provide the ability to

1.  up and download spatial layers into internal data structures
2.  calculate impact functions of the form given in the Summary
3.  Aggregate results to specified boundaries if requested
4.  Map from hazard and exposure types to impact function

1.  One or more servers that

1.  host the spatial data
2.  capture the meta data for new layers
3.  can run either locally or on public web servers

See
https://github.com/AIFDR/riab/blob/master/docs/RiabSoftwareDesign.rst
for design details.


Platforms and languages

Based on scoping work so far and relationships established, it looks like
Risk-in-a-Box should be based on the following:

1.  Geoserver for storage of spatial data

1.  Python (and C) for numerical calculations and data transfer to and
    from Geoservers
2.  Django for web front end
3.  OpenLayers for presentation of spatial layers
4.  Geonode (which includes Geoserver, Django and more) as a desirable
    key component


Use Cases
=========


National earthquake fatality estimate
--------------------------------------

A national estimate of earthquake fatalities is required. It is based on the
following data sets

1.  A national earthquake hazard map providing estimates of peak ground
    shaking intensity at a grid resolution of 0.008333 degrees with return
    periods 100 years and spectral mode 1Hz is selected as a Hazard level to
    plan for.
2.  A population data set is produced at the same grid resolution
    providing an estimate of the number of people present in each grid cell.
3.  A simple model is adopted calculating estimated number of fatalities
    at each grid cell as follows:

.. image:: images/ground_shaking.jpg

.. image:: https://github.com/AIFDR/riab/blob/master/docs/images/ground_shaking.jpg

1.  .. image::
    https://www.google.com/chart?cht=tx&chf=bg,s,FFFFFF00&chco=000000&chl=H
is the ground shaking intensity from the hazard map
2.  E is the population count
3.  .. image::
    https://www.google.com/chart?cht=tx&chf=bg,s,FFFFFF00&chco=000000&chl=a
and .. image::
https://www.google.com/chart?cht=tx&chf=bg,s,FFFFFF00&chco=000000&chl=b
are fitted parameters (.. image:: https://www.google.com/chart?cht=tx&chf=bg,
s,FFFFFF00&chco=000000&chl=a%3D0.97429%2C%5C+b%5C+%3D11.037%29%2C
Allen et al 2009

.. image:: pubimage?id=1CPM1Vvm7uWCzBqhUfWNXdSrHRmEvn8oaLPbOQEZaF3s&image
    _id=16ndHxq0_7DhbS7GLgSQg0X8ez3HEjw


Hazard levels: ?H

.. image::
    pubimage?id=1CPM1Vvm7uWCzBqhUfWNXdSrHRmEvn8oaLPbOQEZaF3s&image_id
    =1Jic2zx8BEgpIo0EBFDO2ul5MAz-GAA


Population counts: E

.. image:: pubimage?id=1CPM1Vvm7uWCzBqhUfWNXdSrHRmEvn8oaLPbOQEZaF3s&image
    _id=15x6ZLM5R44A_ztF6VH2avOa0WbfjCA


Estimated fatalities: F

.. image:: pubimage?id=1CPM1Vvm7uWCzBqhUfWNXdSrHRmEvn8oaLPbOQEZaF3s&image
    _id=1yW8yHSnbqqXlAjb3KloIrjaiqSdOMQ


Zoom of estimated fatalities. The fatality model highlights highly impacted
communities that would not have shown up by looking at only the population
data or the hazard map individually.


Local earthquake scenario loss estimate
---------------------------------------

Based on an earthquake scenario from the Lembang fault north of Bandung,
AusAID wants an estimate of damage that would likely be sustained at each of
the AIBEP schools. The datasets used are

1.  An map of predicted ground shaking intensity at a grid resolution of
    0.008333 degrees for the Lembang fault.
2.  A point data set representing the AIBEP schools

1.  Number of people (linked to fatality model)
2.  Value of structure (linked to engineering fragility curve)

1.  An impact function relating ground shaking intensity to damage level
    (or direct losses?) for buildings of the type used for the schools

.. image:: pubimage?id=1CPM1Vvm7uWCzBqhUfWNXdSrHRmEvn8oaLPbOQEZaF3s&image
    _id=1UJ8GEisGWIOaqTXj93jXdOdkVAPhow


Ground shaking intensity for Lembang fault scenario at a given magnitude.

.. image::
    pubimage?id=1CPM1Vvm7uWCzBqhUfWNXdSrHRmEvn8oaLPbOQEZaF3s&image_id
    =1f3O8Tgk_UAxrcuLahXsL-mgQbmtXdg


????????Schools colour coded according to predicted damage (or loss?)

????????There is no legend here, but that would be a requirement.


Collections of hazard scenarios
-------------------------------

1.  Impact is needed for a large collection of hazard scenarios e.g. as
    obtained from a probabilistic hazard model.Spatial hazard data from all
    scenarios must therefore be combined with exposure data and aggregated to
    form e.g. a risk map.


Example where impacts are aggregated
------------------------------------

????????To appear

.. image:: pubimage?id=1CPM1Vvm7uWCzBqhUfWNXdSrHRmEvn8oaLPbOQEZaF3s&image
    _id=1EUDlisrDoI7g8TdYHrCWz0i8Q61lGg


????????????????????????Example of aggregation boundaries

Other similar use cases would be based on tsunami inundation depth or
volcanic ash load.


Tsunami Scenario Impact Assessment
----------------------------------

This use case is based on an emergency manger wanting to measure the impact
from a tsunami scenario. The tsunami scenario for an area of interest will
first be modelled by a technical personnel within the local government using
TsuDAT2.0 (`Refer to Google Doc`_) which will then be analysed in RIAB to
calculate the impact.

The data sets used will be:

1.  An inundation water depth raster from `TsuDat2.0`_. This will be an
    ESRI ascii file with a spatial resolution on the order of 20m that
    describes the maximum tsunami water depth over the tsunami scenario
    within each cell. This will be in UTM coordinates.

PUT INUNDATION IMAGE HERE

1.  An exposure dataset. This will be an ESRI polygon shape file that
    describes the number of persons living within this area and the number of
    buildings and their value.

PUT EXPOSURE IMAGE HERE

1.  A vulnerability function. This will be a mathematical relationship
    between the water depth and the distance to the coastline, and the
    resulting percentage of fatalities (people) or percentage damage to
    buildings.

To calculate the impact the following steps will need to be conducted for
each exposure polygon that is in the inundation area:

1.  Calculate the nearest distance between the exposure polygon and the
    coastline.
2.  Calculate the percentage of the exposure polygon that is inundated.
3.  Calculate the average water depth within the exposure polygon.
4.  Using steps 1,2,3 calculate the number of fatalities and the building
    loss within the exposure polygon using the vulnerability function
    described above.
5.  Assign the levels of fatalities and building loss for each exposure
    polygon.
6.
Admissible Data Formats
=======================

Based on the use cases, the data formats required for each data type can be
summarised as follows:

+---------+--------+----------+-------------+--------+
|         | Hazard | Exposure | Aggregation | Impact |
|         | Level  | Value    | Region      | Result |
+=========+========+==========+=============+========+
| Grid    | Y      | Y        |             | Y      |
+---------+--------+----------+-------------+--------+
| Point   |        | Y        |             | Y      |
+---------+--------+----------+-------------+--------+
| Line    |        |          |             |        |
+---------+--------+----------+-------------+--------+
| Polygon |        | Y        | Y           | Y      |
+---------+--------+----------+-------------+--------+


Requirements
============

Based on the use cases, requirements for Risk-in-a-Box can be summarised as
follows:

1.  Ability to run identified use cases (earthquake fatalities,
    earthquake damage to schools and building losses due to tsunami
    inundation, ?.)
2.  Ability to restrict calculation by a bounding box applied to hazard
    and exposure data
3.  Ability to upload local raster and vector data for processing
4.  Ability to ingest e.g. shakemap from external source for processing.
5.  Results presented in a sensible way with context and legends
6.  The tool is robust (i.e. the service doesn?t break for no reason)
7.  Risk-in-a-Box can run from a Thumb drive without internet access
    (using a local GeoNode)
8.  Internationalised (especially in Indonesian)
9.  Appropriate LOGOs on the tool (AIFDR, BNPB, BPPT, ?.)

Secondary requirements under the hood include

1.  Ability to download raster and vector data and convert into suitable
    Python structures (e.g. numpy arrays)
2.  Establish hazard levels at arbitrary points (ability to interpolate)
3.  Sensible handling of missing data (-9999 and NaN)


Timeline
========

Draft road map for developing RIAB v1.0 due around 30 April 2011 (week17)

1.  Week 2-3: Develop specific use cases and associated specification.
    Setup development frameworks (Git or SVN, tracking, workstations, IRC,
    etherpads etc)

1.  Week 3-5: Gather test data and develop test cases based on use
    cases/specs

1.  Week 3-5: Gather familiarity with Geoserver, Geonode, Django and RIAB
    v0.1 prototype

1.  Week 5-9: Develop RIAB v0.2 based on Geonode and Django.

1.  Week 7-8: Develop roadmap for RIAB1.0 development

1.  Week 9: Get cracking on API and Frontend


Principles for development of Risk-in-a-Box
===========================================

1.  Coding should follow a style guide, e.g.
    `http://www.python.org/dev/peps/pep-0008/`_ in case of Python, unless
    there are good reasons to deviate (e.g. consistency with other tools,
    mathematical notation, readability, etc).
2.  Adherence to regression/unit testing wherever possible
3.  Use of revision control and issue tracking (git, subversion, TRAC, as
    the team decides)
4.  Simple deployment procedure i.e. automatic system configuration and
    installation of dependencies (at least for Ubuntu)
5.  Use elements from XP/Agile, i.e. frequent releases, continuous
    integration, iterative development etc
6.  All principles should apply continually throughout the development
    cycle


Style guides
============

1.  Python style guide: `http://www.python.org/dev/peps/pep-0008`_
2.  Python documentation guide:
    `http://www.python.org/dev/peps/pep-0257`_
3.  Git commands:
    `http://www.kernel.org/pub/software/scm/git/docs/everyday.html`_
4.  Git guide: `http://spheredev.org/wiki/Git_for_the_lazy`_


Related resources
=================

Previous work related to this project are available at

1.  `http://www.aifdr.org/projects/riat`_ (TRAC page for development of
    RIAB v0.1 demo)
2.  `http://203.77.224.75:3000`_ (RIAB v0.1 live demo)
3.  `www.aifdr.org:8080/geoserver`_ (Geoserver with test dataset)
4.  `www.aifdr.org/riab/layers.html`_ (OpenLayers view of test dataset)
5.  `http://www.cmcrossroads.com/bradapp/docs/sdd.html#TOC_SEC16`_ (A
    Software Design Template)


Related projects
================

1.  Tsunami Data Access Tool: `TsuDat2.0`_
2.  OpenQuake (GEM?s open earthquake risk tool)
3.  CAPRA

