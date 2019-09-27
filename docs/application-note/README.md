# GEMtractor: Extracting Views into Genome-scale Metabolic Models

### Authors
* Martin Scharm
* Olaf Wolkenhauer
* Ali Salehzadeh-Yazdi

### Rules

* approx 1000 words
* Software or data must be freely available to non-commercial users. 
* Availability and Implementation must be clearly stated in the article.
* Additional Supplementary data can be published online-only by the journal. This supplementary material should be referred to in the abstract of the Application Note.
* The name of the application should be included in the title.
* $190 per excess page - so we should try to stay within 2 pages

## Cover letter
* explaining the suitability of the paper for Bioinformatics


## Abstract
* **Summary:** Computational models in systems biology typically encode for multipartite graphs of species, reactions, and enzymes.
Analysing and comparing these complex networks and their topology is challenging.
The GEMtractor is an online tool to extract subnetworks, for example focussing on enzyme-centric views into the model.
* **Availability and Implementation:** The GEMtractor is licensed under the terms of [GPLv3]() and developed at [github.com/binfalse/GEMtractor/](https://github.com/binfalse/GEMtractor/) -- a public version is available at [sbi.uni-rostock.de/gemtractor](https://www.sbi.uni-rostock.de/gemtractor).
* **Contact:** ..@..


## Introduction

Genome-scale metabolic models (GEMs) describe the molecular mechanisms of a particular organism.
Such models are typically encoded in multipartite graphs, whose vertices can be categorised into metabolites, reactions, and enzymes.
Due to the intrinsic complexity it is challenging to analyse and compare the molecular topology of metabolic networks.
Extracting the reaction-centric (links of reactions) or enzyme-centric (links of enzymes) view onto the metabolism simplifies the graph structure and shifts its perspective -- from kinetic connections to phenotypical interactions.
Thus, it opens opportunities for novel topological analysis of the metabolism.
In fact, enzyme-centric networks provide us a critical precursor of physiological representation from genomics data, by determining metabolic distances between enzymes.

The idea of extracting and analysing the enzyme-centric network of a GEM is not new and there are already two tools claiming to do so.
However, [Horne et al 2004](https://academic.oup.com/bioinformatics/article/20/13/2050/241978) is not available any more and the authors are not reachable, and [Asgari et al 2018](https://www.ingentaconnect.com/contentone/ben/cbio/2018/00000013/00000001/art00015) apparently mistook the reaction-centric network for an enzyme-centric network.

Here we introduce the GEMtractor, an online tool to extract reaction-centric and enzyme-centric views from metabolite-reaction networks.
In addition, the GEMtractor allows for trimming of models to, for example, remove currency metabolites or to focus on the results of flux balance analyses.
The GEMtractor is free software and easy to deploy to third party infrastructures, including an increased privacy and speed.

## Technical Notes
The GEMtractor is a Django web application, that we developed with privacy, simplicity and speed in mind.
The interactive front-end is developed using jQuery and designed using W3CSS.
Thus, it works in all modern browsers as well as on mobile devices and there is no need for registration.


explain workflow
* read SBML using libsbml
* filter for entities
* optionally extract a specific view into the remaining network
* directed reaction and enzyme interactions
* export in one of several formats

specialities
* gemtractor module can basically be extracted and used individually
* api


* limitations? model size etc
  * some models do not work, because of incorrect gene associations, biomodels is informed of those we spotted
  * not all GEMs have gene associations... (especially not in biomodels)


* deployment
* easy to install

The GEMtractor has a souvereign test coverage

* docker + nginx
* preserves annotations if possible
* mention caches
* cite BiGG Biomodels cytoscape.js
* Compatibility

As documentation is key to dissemination, the GEMtractor comes with an extensive FAQ, proper Python documentation and example client implementations in different programming languages.


![workflow](fig.svg)


## Conclusion

The GEMtractor is good!
It's the best GEMtractor people have ever seen.

even though the gemtractor was build for genome scale metabolic networks, it is basically applicable to any sbml model. You won't get useful enzyme networks, as kinetic models typically lack the gene association annotations, but you can still trim models to focus on submodels or extract the reaction centric network to analyze these...

## Acknowledgements

We would like to thank Markus Wolfien and Tom Gebhardt for creative brainstormings ;-)

## Funding


