-- Entity statistics
-- Stanza NER Tags
SELECT document_collection, COUNT(*)
From TAG
WHERE ent_type = UPPER(ent_type)
GROUP BY document_collection

-- EL Tags
SELECT document_collection, COUNT(*)
From TAG
WHERE ent_type <> UPPER(ent_type)
GROUP BY document_collection


-- Only Stanza (upper case entity types)
SELECT ent_str, ent_id, ent_type, COUNT(*)
From Tag
where document_collection = 'pollux' and ent_type = UPPER(ent_type)
GROUP BY ent_str, ent_id, ent_type
ORDER BY COUNT(*) DESC
LIMIT 500

-- Vocab Entity Linking
SELECT ent_str, ent_id, ent_type, COUNT(*)
From Tag
where document_collection = 'pollux' and ent_type <> UPPER(ent_type)
GROUP BY ent_str, ent_id, ent_type
ORDER BY COUNT(*) DESC
LIMIT 500


-- No Filter
SELECT subject_str, subject_id, subject_type, predicate_org, predicate, object_str, object_id, object_type, Sentence.text
FROM Predication JOIN Sentence ON (Predication.sentence_id = Sentence.id)
WHERE extraction_type = 'OPENIE6_NF' and document_collecton = 'pollux'
ORDER BY random()
LIMIT 100;

-- Subject Filter
SELECT subject_str, subject_id, subject_type, predicate_org, predicate, object_str, object_id, object_type, Sentence.text
FROM Predication JOIN Sentence ON (Predication.sentence_id = Sentence.id)
WHERE extraction_type = 'OPENIE6_SF' and document_collecton = 'pollux'
ORDER BY random()
LIMIT 100;

-- Exact Filter
SELECT subject_str, subject_id, subject_type, predicate_org, predicate, object_str, object_id, object_type, Sentence.text
FROM Predication JOIN Sentence ON (Predication.sentence_id = Sentence.id)
WHERE extraction_type = 'OPENIE6_EF' and document_collecton = 'pollux'
ORDER BY random()
LIMIT 100;

-- Partial Filter
SELECT subject_str, subject_id, subject_type, predicate_org, predicate, object_str, object_id, object_type, Sentence.text
FROM Predication JOIN Sentence ON (Predication.sentence_id = Sentence.id)
WHERE extraction_type = 'OPENIE6_PF' and document_collecton = 'pollux'
LIMIT 100;


-- See extraction statistics:
SELECT document_collection, extraction_type, count(*)
From Predication
GROUP by document_collection, extraction_type
ORDER BY  document_collection, extraction_type ASC;
