'''
A Simple UMLS CUI to SNOMEDCT CTS2 MapEntry Service.
'''
__author__ = "Kevin Peterson"
__credits__ = ["Harold Solbrig"]
__license__ = "MIT"
__version__ = "1.0.0"
__maintainer__ = "Kevin Peterson"
__email__ = "kevin.peterson@mayo.edu"

from flask import Flask
from flask import jsonify
from flask import Response
from flask import request
from flask import redirect
from collections import defaultdict
from collections import OrderedDict
import string
import datetime
import argparse

app = Flask(__name__)
serverRoot = None

cuiToCodes = defaultdict(set)

UMLS_VERSION = "2012AA"

mapEntryXml = """<?xml version="1.0" encoding="UTF-8"?>
<MapEntryMsg xmlns="http://schema.omg.org/spec/CTS2/1.0/MapVersion"
    xmlns:core="http://schema.omg.org/spec/CTS2/1.0/Core"
    xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance" 
    xsi:schemaLocation="http://schema.omg.org/spec/CTS2/1.0/MapVersion http://www.omg.org/spec/cts2/201206/mapversion/MapVersion.xsd">
    <core:heading>
        <core:resourceRoot>map/UMLS_TO_SNOMEDCT/version/"""+UMLS_VERSION+"""/entry/{cui}</core:resourceRoot>
        <core:resourceURI>{serverRoot}/map/UMLS_TO_SNOMEDCT/version/"""+UMLS_VERSION+"""/entry/{cui}</core:resourceURI>
        <core:accessDate>{date}</core:accessDate>
    </core:heading>
    <entry entryState="ACTIVE" processingRule="ALL_MATCHES">
        <assertedBy>
            <core:mapVersion uri="http://umls.nlm.nih.gov/sab/MTH/version/MTH"""+UMLS_VERSION+"""/map/UMLS_TO_SNOMEDCT_"""+UMLS_VERSION+"""">UMLS_TO_SNOMEDCT_"""+UMLS_VERSION+"""</core:mapVersion>
            <core:map uri="http://umls.nlm.nih.gov/sab/MTH/map/UMLS_TO_SNOMEDCT">UMLS_TO_SNOMEDCT</core:map>
        </assertedBy>
        <mapFrom uri="http://umls.nlm.nih.gov/sab/MTH/{cui}">
            <core:namespace>cui</core:namespace>
            <core:name>{cui}</core:name>
        </mapFrom>
        <mapSet processingRule="ALL_MATCHES" entryOrder="1">
           {targets}
        </mapSet>
    </entry>
</MapEntryMsg>
"""

mapTargetXml = """
		<mapTarget entryOrder="{entryNum}">
		    <mapTo uri="http://snomed.info/id/{code}" href="http://informatics.mayo.edu/cts2/services/sct/cts2/codesystem/SNOMED_CT_core/version/20120731/entity/{code}">
		        <core:namespace>sctid</core:namespace>
		        <core:name>{code}</core:name>
		    </mapTo>
		</mapTarget>
"""

mapTargetListListXml = """<?xml version="1.0" encoding="UTF-8"?>
<MapTargetListList 
    xmlns="http://schema.omg.org/spec/CTS2/1.0/MapEntryServices"
    xmlns:core="http://schema.omg.org/spec/CTS2/1.0/Core"
    xmlns:mapVersion="http://schema.omg.org/spec/CTS2/1.0/MapVersion"
    xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance"
    xsi:schemaLocation="http://schema.omg.org/spec/CTS2/1.0/MapEntryServices http://www.omg.org/spec/cts2/201206/mapversion/MapEntryServices.xsd">
    {targets}
</MapTargetListList>
"""

mapTargetListListEntryXml = """
    <entry>
        {targets}
    </entry>
"""

mapTargetListListEntryEntryXml = """
    <entry entryOrder="{entryNum}">
        <mapVersion:mapTo uri="http://snomed.info/id/{code}" href="http://informatics.mayo.edu/cts2/services/sct/cts2/codesystem/SNOMED_CT_core/version/20120731/entity/{code}">
            <core:namespace>sctid</core:namespace>
            <core:name>{code}</core:name>
        </mapVersion:mapTo>
    </entry>
"""

mapEntryNotFoundXml = """<?xml version="1.0" encoding="UTF-8"?>
<UnknownResourceReference
    xmlns="http://schema.omg.org/spec/CTS2/1.0/Exceptions"
    xmlns:core="http://schema.omg.org/spec/CTS2/1.0/Core"
    xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance" xsi:schemaLocation="http://www.omg.org/spec/cts2/201206/core/Exceptions.xsd">
    <exceptionType>INVALID_SERVICE_INPUT</exceptionType>
    <message>
        <core:value>Resource with Identifier - {cui} not found.</core:value>
    </message>
    <severity>ERROR</severity>
</UnknownResourceReference>
"""

class EntryNotFoundError(Exception):
    def __init__(self, code):
        self.code = code
    def __str__(self):
        return repr(self.code)

@app.errorhandler(404)
def not_found(error):
    return respond_not_found(error.code)

def respond_not_found(code):
    xml = mapEntryNotFoundXml.format(cui=code)
    return Response(xml, mimetype='text/xml'), 404

def get_targetlistlist_xml(cuis):
    '''Build the CTS2 MapTargetListList XML'''
    entries = ''
    entryNum = 1;
    for cui in cuis:
        if not cui in cuiToCodes:
            raise EntryNotFoundError(cui)
        targets = ""
        for code in cuiToCodes[cui]:
            targets += mapTargetListListEntryEntryXml.format(code=code,entryNum=entryNum)
            entryNum += 1
        entries += mapTargetListListEntryXml.format(targets=targets)

    return mapTargetListListXml.format(cui=cui, targets=entries, date=datetime.datetime.now().isoformat())

def get_map_entry_xml(cui):
    '''Build the CTS2 MapEntry XML'''
    if not cui in cuiToCodes:
        raise EntryNotFoundError(cui)

    targets = ''
    entryNum = 1;
    for code in cuiToCodes[cui]:
    	targets += mapTargetXml.format(code=code,entryNum=entryNum)
    	entryNum += 1

    return mapEntryXml.format(cui=cui, targets=targets, serverRoot=serverRoot, date=datetime.datetime.now().isoformat())

def load_file():
    '''Load the data file'''
    file = open("./data/cuiToSnomedCodes.out")
    for line in file:
        parts = [p.strip() for p in line.split("|")]
        cui = parts[0]
        code = parts[1]
        if not cui in cuiToCodes:
        	cuiToCodes[cui] = set()

        cuiToCodes[cui].add(code)
    file.close()

@app.route("/map/UMLS_TO_SNOMEDCT/version/"+UMLS_VERSION+"/resolution")
def get_map_targetlistlist():
    '''Get a MapTargetListList based on a list of UMLS CUIs'''
    cuis = cuiOrUrisToCuis(remove_duplicates(request.args['mapfrom'].split(',')))
    try:
        return Response(get_targetlistlist_xml(cuis), mimetype='text/xml') 
    except EntryNotFoundError as e:
        return not_found(e)

def cuiOrUriToCui(cuiOrUri):
    parts = cuiOrUri.rsplit('/',1)
    if len(parts) == 1:
        return parts[0]
    else:
        return parts[1]

def cuiOrUrisToCuis(cuiOrUris):
    cuis = []
    for cuiOrUri in cuiOrUris:
        cuis.append(cuiOrUriToCui(cuiOrUri))

    return remove_duplicates(cuis)
        
def remove_duplicates(lst):
    dset = set()
    # relies on the fact that dset.add() always returns None.
    return [ l for l in lst if 
             l not in dset and not dset.add(l) ] 

@app.route("/map/UMLS_TO_SNOMEDCT/version/"+UMLS_VERSION+"/entry/<cui>")
def get_map_entry(cui):
    '''Get a MapEntry based on a UMLS CUI'''
    try:
    	return Response(get_map_entry_xml(cui), mimetype='text/xml')
    except EntryNotFoundError as e:
        return not_found(e)

@app.route("/map/UMLS_TO_SNOMEDCT/version/"+UMLS_VERSION+"/entrybyuri")
def get_map_entry_by_uri():
    '''Get a MapEntry based on a UMLS CUI URI'''
    uri = request.args['uri']
    cui = cuiOrUriToCui(uri)
    if not cui in cuiToCodes:
        return respond_not_found(uri)

    return redirect(serverRoot + "/map/UMLS_TO_SNOMEDCT/version/"+UMLS_VERSION+"/entry/"+cui, code=302)

if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument('-p', '--port', help='Server Port', type=int, default=5000, required=False)
    parser.add_argument('-r', '--root', help='Server Root', default="http://localhost:5000", required=True)
    args = parser.parse_args()
    port = args.port
    serverRoot = args.root

    print "Loading..."
    load_file()
    print "Done loading."

    app.run(debug=False,host='0.0.0.0',port=port)