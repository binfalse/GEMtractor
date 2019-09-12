#!/usr/bin/env python3

import json
import urllib.request

# read the model into a variable
with open ("../src/test/gene-filter-example-2.xml", "r") as f:
  model=f.read()

# encode the job
job = {
    "export": {
        "network_type":"en",
        "network_format":"sbml"
    },
    "filter": {
        "species": ["h2o", "atp"],
        "reactions": [],
        "genes": ["gene_abc"],
    },
    "file": model
}

# setup request
req = urllib.request.Request("https://enalyzer.bio.informatik.uni-rostock.de/api/execute")
req.add_header('Content-Type', 'application/json; charset=utf-8')
job_bytes = json.dumps(job).encode('utf-8')
req.add_header('Content-Length', len(job_bytes))

# fire the job
try:
    response = urllib.request.urlopen(req, job_bytes)
    # do whatever you want with the returned file:
    print (response.read())
except urllib.error.HTTPError  as e:
    # there was a problem...!?
    print ("bad request: " + str (getattr(e, 'code', repr(e))) +  getattr(e, 'message', repr(e)))
    print (e.readlines())



