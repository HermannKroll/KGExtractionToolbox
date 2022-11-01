SELECT *
FROM document
WHERE collection = 'scientists_ml'


-- Delete short entity mentions
DELETE FROM Tag
WHERE document_collection = 'scientists_ml' and length(ent_str) < 5;


-- Only Stanza (upper case entity types)
SELECT ent_str, ent_id, ent_type, COUNT(*)
From Tag
where document_collection = 'scientists_ml' and ent_type = UPPER(ent_type)
GROUP BY ent_str, ent_id, ent_type
ORDER BY COUNT(*) DESC
LIMIT 500

-- Vocab Entity Linking
SELECT ent_str, ent_id, ent_type, COUNT(*)
From Tag
where document_collection = 'scientists_ml' and ent_type <> UPPER(ent_type)
GROUP BY ent_str, ent_id, ent_type
ORDER BY COUNT(*) DESC
LIMIT 500


-- Wikipedia
-- Award Received
SELECT subject_str, subject_id, subject_type, predicate_org, predicate, relation, object_str, object_id, object_type, Sentence.text
FROM Predication JOIN Sentence ON (Predication.sentence_id = Sentence.id)
WHERE Predication.document_collection = 'scientists_ml' and subject_type = 'Person' and object_type = 'Award' and extraction_type = 'PathIE'
and relation = 'award received'
ORDER BY random()
LIMIT 100;


SELECT subject_str, subject_id, subject_type, predicate_org, predicate, relation, object_str, object_id, object_type, Sentence.text
FROM Predication JOIN Sentence ON (Predication.sentence_id = Sentence.id)
WHERE Predication.document_collection = 'scientists_ml' and extraction_type = 'PathIE'
ORDER BY random()
LIMIT 100;



SELECT subject_str, subject_id, subject_type, predicate_org, predicate, object_str, object_id, object_type, Sentence.text
FROM Predication JOIN Sentence ON (Predication.sentence_id = Sentence.id)
WHERE Predication.document_collection = 'scientists_ml' and subject_type = 'PERSON' and object_type = 'Award' and extraction_type = 'PathIE'
ORDER BY random()
LIMIT 100;

-- PathIE Statistics
SELECT predicate, relation, count(*)
FROM Predication WHERE Predication.document_collection = 'scientists_ml' and extraction_type = 'PathIE'
GROUP BY predicate, relation
ORDER BY COUNT(*) DESC
LIMIT 500

SELECT predicate, relation, count(*)
FROM Predication WHERE Predication.document_collection = 'scientists_ml' and extraction_type = 'PathIE'
and relation is not null
GROUP BY predicate, relation
ORDER BY COUNT(*) DESC
LIMIT 500


-- Analyse OpenIE results
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
SELECT Predication.document_id, subject_str, predicate_org, predicate, object_str, Sentence.text
FROM Predication JOIN Sentence ON (Predication.sentence_id = Sentence.id)
WHERE Predication.document_collection = 'scientists_ml' and extraction_type = 'OPENIE6_NF'
ORDER BY Predication.document_id;

-- Exact Filter
SELECT Predication.document_id, subject_str, subject_id, subject_type, predicate_org, predicate, object_str, object_id, object_type, Sentence.text
FROM Predication JOIN Sentence ON (Predication.sentence_id = Sentence.id)
WHERE Predication.document_collection = 'scientists_ml' and extraction_type = 'OPENIE6_EF'
ORDER BY Predication.document_id;

-- Partial Filter
SELECT Predication.document_id, subject_str, subject_id, subject_type, predicate_org, predicate, object_str, object_id, object_type, Sentence.text
FROM Predication JOIN Sentence ON (Predication.sentence_id = Sentence.id)
WHERE Predication.document_collection = 'scientists_ml' and extraction_type = 'OPENIE6_PF'
ORDER BY Predication.document_id;

-- Subject Filter
SELECT Predication.document_id, subject_str, subject_id, subject_type, predicate_org, predicate, object_str, object_id, object_type, Sentence.text
FROM Predication JOIN Sentence ON (Predication.sentence_id = Sentence.id)
WHERE Predication.document_collection = 'scientists_ml'  and extraction_type = 'OPENIE6_SF'
ORDER BY Predication.document_id;


