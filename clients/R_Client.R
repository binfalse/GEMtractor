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

library(httr)

# read the model
model <- readLines ("../src/test/gene-filter-example-2.xml")

# create a job
# lists will result in dictionaries
# c will get an array
job = list (
        export = list (
                network_type = "en",
                network_format="dot"
                ),
        filter = list (
                species = c ("a", "d"),
                reactions = c("r2", "r3"),
                enzymes = c ("gene_abc", "gene_x"),
                enzyme_complexes = c ("b + c", "x + Y", "b_098 + r_abc")
                ),
        file = paste (model, collapse="\n"))

# post to gemtractor
post_result <- POST(url = "https://gemtractor.bio.informatik.uni-rostock.de/api/execute",
                    body = job,
                    encode = "json"
                    # , verbose() # enable if required
                    )

# print result
cat (content(post_result, as="text",encoding="utf8"))

