-- Entity statistics
-- Stanza NER Tags
SELECT document_collection, COUNT(*)
From TAG
WHERE ent_type = UPPER(ent_type)
GROUP BY document_collection;

-- EL Tags
SELECT document_collection, COUNT(*)
From TAG
WHERE ent_type <> UPPER(ent_type)
GROUP BY document_collection;

SELECT COUNT(*)
From Tag
where document_collection = 'pollux_ml' and (ent_str = '1980s' or ent_str = '1990s');

-- Only Stanza (upper case entity types)
SELECT ent_str, ent_id, ent_type, COUNT(*)
From Tag
where document_collection = 'pollux_ml' and ent_type = UPPER(ent_type)
GROUP BY ent_str, ent_id, ent_type
ORDER BY COUNT(*) DESC
LIMIT 500;

-- Count number of Stanza tags per document
SELECT document_id, COUNT(*)
From Tag
where document_collection = 'pollux_ml'
GROUP BY document_id
ORDER BY document_id
LIMIT 500;

-- Vocab Entity Linking
SELECT ent_str, ent_id, ent_type, COUNT(*)
From Tag
where document_collection = 'pollux_ml' and ent_type <> UPPER(ent_type)
GROUP BY ent_str, ent_id, ent_type
ORDER BY COUNT(*) DESC
LIMIT 500;




-- Delete short entity mentions
DELETE FROM Tag
WHERE document_collection = 'pollux_ml' and length(ent_str) < 5;



-- Analyse OpenIE tuples
SELECT document_collection, extraction_type, count(*)
FROM predication
GROUP BY document_collection, extraction_type
ORDER BY document_collection, extraction_type;

-- Per Article
SELECT document_collection, extraction_type, document_id, count(*)
FROM predication
WHERE extraction_type = 'OPENIE6_NF'
GROUP BY document_collection, extraction_type, document_id
ORDER BY document_collection, extraction_type, document_id;


-- No Filter
SELECT Predication.document_id, subject_type, predicate_org, predicate, object_str, Sentence.text
FROM Predication JOIN Sentence ON (Predication.sentence_id = Sentence.id)
WHERE extraction_type = 'OPENIE6_NF' and Predication.document_collection = 'pollux_ml'
ORDER BY Predication.document_id;

-- Subject Filter
SELECT Predication.document_id, subject_str, subject_id, subject_type, predicate_org, predicate, object_str, object_id, object_type, Sentence.text
FROM Predication JOIN Sentence ON (Predication.sentence_id = Sentence.id)
WHERE extraction_type = 'OPENIE6_SF' and Predication.document_collection = 'pollux_ml'
ORDER BY Predication.document_id;

-- Exact Filter
SELECT Predication.document_id, subject_str, subject_id, subject_type, predicate_org, predicate, object_str, object_id, object_type, Sentence.text
FROM Predication JOIN Sentence ON (Predication.sentence_id = Sentence.id)
WHERE extraction_type = 'OPENIE6_EF' and Predication.document_collection = 'pollux_ml'
ORDER BY Predication.document_id;

-- Partial Filter
SELECT Predication.document_id, subject_str, subject_id, subject_type, predicate_org, predicate, object_str, object_id, object_type, Sentence.text
FROM Predication JOIN Sentence ON (Predication.sentence_id = Sentence.id)
WHERE extraction_type = 'OPENIE6_PF' and Predication.document_collection = 'pollux_ml'
ORDER BY Predication.document_id;


-- See extraction statistics:
SELECT Predication.document_collection, extraction_type, count(*)
From Predication
GROUP by Predication.document_collection, extraction_type
ORDER BY  Predication.document_collection, extraction_type ASC;
