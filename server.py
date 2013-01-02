'''
Simple UMLS CUI to SNOMEDCT CTS2 Mapping Service.
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
from collections import defaultdict
import string
import datetime
import argparse

app = Flask(__name__)
SERVER_ROOT = "http://informatics.mayo.edu/cts2/services/ecis/"

cuiToCodes = defaultdict(set)

mapEntryXml = """<?xml version="1.0" encoding="UTF-8"?>
<MapEntryMsg xmlns="http://schema.omg.org/spec/CTS2/1.0/MapVersion"
    xmlns:core="http://schema.omg.org/spec/CTS2/1.0/Core"
    xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance" 
    xsi:schemaLocation="http://schema.omg.org/spec/CTS2/1.0/MapVersion http://www.omg.org/spec/cts2/201206/mapversion/MapVersion.xsd">
    <core:heading>
        <core:resourceRoot>map/UMLS_TO_SNOMEDCT/version/1.0/entry/{cui}</core:resourceRoot>
        <core:resourceURI>"""+SERVER_ROOT+"""/map/UMLS_TO_SNOMEDCT/version/1.0/entry/{cui}</core:resourceURI>
        <core:accessDate>{date}</core:accessDate>
    </core:heading>
    <entry entryState="ACTIVE" processingRule="ALL_MATCHES">
        <assertedBy>
            <core:mapVersion uri="http://umls.nlm.nih.gov/sab/MTH/version/MTH2012AA/map/UMLS_TO_SNOMEDCT_1.0">UMLS_TO_SNOMEDCT_1.0</core:mapVersion>
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

def get_map_entry_xml(cui, codes):
    '''Build the CTS2 MapEntry XML'''
    targets = ''
    entryNum = 1;
    for code in codes:
    	targets = targets + mapTargetXml.format(code=code,entryNum=entryNum)
    	entryNum += 1

	return mapEntryXml.format(cui=cui, targets=targets, date=datetime.datetime.now().isoformat())

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

@app.route("/map/UMLS_TO_SNOMEDCT/version/1.0/entry/<cui>")
def get_map_entry(cui):
    '''Get a MapEntry based on a UMLS CUI'''
    if cui in cuiToCodes:
    	return Response(get_map_entry_xml(cui,cuiToCodes[cui]), mimetype='text/xml')
    else:
    	xml = mapEntryNotFoundXml.format(cui=cui)
    	return Response(xml, mimetype='text/xml'), 404

if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument('-p', '--port', help='Server Port', type=int, default=5000, required=False)
    args = parser.parse_args()
    port = args.port

    print "Loading..."
    load_file()
    print "Done loading."

    app.run(debug=False,host='0.0.0.0',port=port)