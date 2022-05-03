-- Scientist that have an Wikipedia article
SELECT ?article ?item ?type ?itemLabel (GROUP_CONCAT(?altLabel;separator=";") AS ?labels) WHERE {
  ?item wdt:P106+ wd:Q901 .
  ?item rdfs:label ?country filter (lang(?country) = "en") . 
  ?item skos:altLabel ?altLabel . FILTER (lang(?altLabel) = "en")       
  ?article schema:about ?item .
  ?article schema:inLanguage "en" .
  VALUES ?type { "Person" }.
  FILTER (SUBSTR(str(?article), 1, 25) = "https://en.wikipedia.org/")
  SERVICE wikibase:label { bd:serviceParam wikibase:language "en". }     
}
GROUP BY ?item ?type ?itemLabel ?article
ORDER BY ASC(?itemLabel)

-- Countries
SELECT?item ?type ?itemLabel (GROUP_CONCAT(?altLabel;separator=";") AS ?labels) WHERE {
  ?item wdt:P31 wd:Q3624078 .
  ?item rdfs:label ?itemLabel filter (lang(?itemLabel) = "en") . 
  ?item skos:altLabel ?altLabel . FILTER (lang(?altLabel) = "en")       
  VALUES ?type { "Country" }.
  SERVICE wikibase:label { bd:serviceParam wikibase:language "en". }     
}
GROUP BY ?item ?type ?itemLabel
ORDER BY ASC(?itemLabel)


-- Awards
SELECT?item ?type ?itemLabel (GROUP_CONCAT(?altLabel;separator=";") AS ?labels) WHERE {
  VALUES ?award {wd:Q107467117 wd:Q618779}
  ?item wdt:P31+|wdt:P279+ ?award .
  ?item rdfs:label ?itemLabel filter (lang(?itemLabel) = "en") . 
  ?item skos:altLabel ?altLabel . FILTER (lang(?altLabel) = "en")       
  VALUES ?type { "Award" }.
  SERVICE wikibase:label { bd:serviceParam wikibase:language "en". }     
}
GROUP BY ?item ?type ?itemLabel
ORDER BY ASC(?itemLabel)



-- Profession
SELECT?item ?type ?itemLabel (GROUP_CONCAT(?altLabel;separator=";") AS ?labels) WHERE {
  VALUES ?profession {wd:Q28640}
  ?item wdt:P31|wdt:P279 ?profession .
  ?item rdfs:label ?itemLabel filter (lang(?itemLabel) = "en") . 
  OPTIONAL {?item skos:altLabel ?altLabel . FILTER (lang(?altLabel) = "en")  }     
  VALUES ?type { "Profession" }.
  SERVICE wikibase:label { bd:serviceParam wikibase:language "en". }     
}
GROUP BY ?item ?type ?itemLabel
ORDER BY ASC(?itemLabel)


-- Academia of Sciences
SELECT?item ?type ?itemLabel (GROUP_CONCAT(?altLabel;separator=";") AS ?labels) WHERE {
  VALUES ?academia {wd:Q414147}
  ?item wdt:P31+|wdt:P279+ ?academia .
  ?item rdfs:label ?itemLabel filter (lang(?itemLabel) = "en") . 
  ?item skos:altLabel ?altLabel . FILTER (lang(?altLabel) = "en")       
  VALUES ?type { "Academia of Science" }.
  SERVICE wikibase:label { bd:serviceParam wikibase:language "en". }     
}
GROUP BY ?item ?type ?itemLabel
ORDER BY ASC(?itemLabel)

-- Languages
SELECT?item ?type ?itemLabel (GROUP_CONCAT(?altLabel;separator=";") AS ?labels) WHERE {
  VALUES ?language {wd:Q34770}
  ?item wdt:P31|wdt:P279 ?language .
  ?item rdfs:label ?itemLabel filter (lang(?itemLabel) = "en") . 
  ?item skos:altLabel ?altLabel . FILTER (lang(?altLabel) = "en")       
  VALUES ?type { "Language" }.
  SERVICE wikibase:label { bd:serviceParam wikibase:language "en". }     
}
GROUP BY ?item ?type ?itemLabel
ORDER BY ASC(?itemLabel)

-- Universities
SELECT ?item ?type ?itemLabel (GROUP_CONCAT(?altLabel;separator=";") AS ?labels) WHERE {
  VALUES ?university {wd:Q3918}
  ?item wdt:P31|wdt:P279 ?university .
  ?item rdfs:label ?itemLabel filter (lang(?itemLabel) = "en") . 
  ?item skos:altLabel ?altLabel . FILTER (lang(?altLabel) = "en")       
  VALUES ?type { "University" }.
  SERVICE wikibase:label { bd:serviceParam wikibase:language "en". }     
}
GROUP BY ?item ?type ?itemLabel
ORDER BY ASC(?itemLabel)

-- Scientific Societies
SELECT ?item ?type ?itemLabel (GROUP_CONCAT(?altLabel;separator=";") AS ?labels) WHERE {
  VALUES ?scisoc {wd:Q748019}
  ?item wdt:P31|wdt:P279 ?scisoc .
  ?item rdfs:label ?itemLabel filter (lang(?itemLabel) = "en") . 
  ?item skos:altLabel ?altLabel . FILTER (lang(?altLabel) = "en")       
  VALUES ?type { "Scientific Society" }.
  SERVICE wikibase:label { bd:serviceParam wikibase:language "en". }     
}
GROUP BY ?item ?type ?itemLabel
ORDER BY ASC(?itemLabel)

-- Professional Societies
SELECT ?item ?type ?itemLabel (GROUP_CONCAT(?altLabel;separator=";") AS ?labels) WHERE {
  VALUES ?profsoc {wd:Q1391145}
  ?item wdt:P31|wdt:P279 ?profsoc .
  ?item rdfs:label ?itemLabel filter (lang(?itemLabel) = "en") . 
  ?item skos:altLabel ?altLabel . FILTER (lang(?altLabel) = "en")       
  VALUES ?type { "Professional Society" }.
  SERVICE wikibase:label { bd:serviceParam wikibase:language "en". }     
}
GROUP BY ?item ?type ?itemLabel
ORDER BY ASC(?itemLabel)

-- Doctorate Degrees
SELECT ?item ?type ?itemLabel (GROUP_CONCAT(?altLabel;separator=";") AS ?labels) WHERE {
  VALUES ?doctorate {wd:Q849697}
  ?item wdt:P31+|wdt:P279+ ?doctorate .
  ?item rdfs:label ?itemLabel filter (lang(?itemLabel) = "en") . 
  ?item skos:altLabel ?altLabel . FILTER (lang(?altLabel) = "en")       
  VALUES ?type { "Doctoral Degree" }.
  SERVICE wikibase:label { bd:serviceParam wikibase:language "en". }     
}
GROUP BY ?item ?type ?itemLabel
ORDER BY ASC(?itemLabel)

-- Beliefs
SELECT ?item ?type ?itemLabel (GROUP_CONCAT(?altLabel;separator=";") AS ?labels) WHERE {
  VALUES ?belief {wd:Q9174 wd:Q58721}
  ?item wdt:P31|wdt:P279 ?belief .
  ?item rdfs:label ?itemLabel FILTER (lang(?itemLabel) = "en") . 
  ?item skos:altLabel ?altLabel . FILTER (lang(?altLabel) = "en")       
  VALUES ?type { "Belief" }.
  SERVICE wikibase:label { bd:serviceParam wikibase:language "en". }     
}
GROUP BY ?item ?type ?itemLabel
ORDER BY ASC(?itemLabel)

