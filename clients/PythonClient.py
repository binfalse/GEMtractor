#!/usr/bin/env python3
#
# This is free and unencumbered software released into the public domain.
#
# Anyone is free to copy, modify, publish, use, compile, sell, or
# distribute this software, either in source code form or as a compiled
# binary, for any purpose, commercial or non-commercial, and by any
# means.
#
# In jurisdictions that recognize copyright laws, the author or authors
# of this software dedicate any and all copyright interest in the
# software to the public domain. We make this dedication for the benefit
# of the public at large and to the detriment of our heirs and
# successors. We intend this dedication to be an overt act of
# relinquishment in perpetuity of all present and future rights to this
# software under copyright law.
#
# THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND,
# EXPRESS OR IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF
# MERCHANTABILITY, FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT.
# IN NO EVENT SHALL THE AUTHORS BE LIABLE FOR ANY CLAIM, DAMAGES OR
# OTHER LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE,
# ARISING FROM, OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR
# OTHER DEALINGS IN THE SOFTWARE.
#
# For more information, please refer to <http://unlicense.org>

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
        "enzymes": ["gene_abc"],
        "enzyme_complexes": ["a + b + c", "x + Y", "b_098 + r_abc"],
    },
    "file": model
}

# setup request
req = urllib.request.Request("https://gemtractor.bio.informatik.uni-rostock.de/api/execute")
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



