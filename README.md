##CTS2 UMLS CUI to SNOMEDCT Map Service

A simple CTS2 MapEntry Service implementation to expose UMLS CUI to SNOMEDCT Mappings.

###Installation
Run the _parseMrconso.sh_ script to process MRCONSO.RRF data from a UMLS installation into a form used by the service.

Example:
    parseMrconso.sh ../my/umls/install/MRCONSO.RRF

###Run
Start the service by running 
    python server.py

###Accessing
After starting, you should see content here:
[http://localhost:5000/map/UMLS\_TO\_SNOMEDCT/version/1.0/entry/C0011627](http://localhost:5000/map/UMLS_TO_SNOMEDCT/version/1.0/entry/C0011627)

The REST API Call is:
    map/UMLS_TO_SNOMEDCT/version/1.0/entry/{umls_cui}
