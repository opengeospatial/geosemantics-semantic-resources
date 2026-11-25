# GeoSPARQL 1.1

This directory contains the RDF resources for [GeosPARQL 1.1](http://www.opengis.net/doc/IS/geosparql/1.1) as loaded into the OGC's [Definitions Service](https://defs.opengis.net/).

## Use

The resources are organized and (can be) synchronized using [KGM](https://github.com/Kurrawong/kgm) which is a tool 
that reads repository content and loads it into an RDF DB.

KGM reads the `manifest.ttl` file, discovers the resources linked to from there, validates them and then synchronizes 
them with a target RDF DB via _Graph Store Protocol_ commands like this:

```bash
kgm sync manifest.ttl
```

## Contact

This register's _Register Manager_ is currently the:

**GeoSPARQL Standards Working Group**  
Please contact the GeoSPARQL SWG using
[details on its main repo](https://github.com/opengeospatial/ogc-geosparql/#contact).

The _Register Owner_ is the [Open Geospatial Consortium](https://www.ogc.org).
