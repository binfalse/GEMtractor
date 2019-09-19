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

