SELECT *
FROM document
WHERE collection = 'scientists'


-- Delete short entity mentions
DELETE FROM Tag
WHERE document_collection = 'scientists' and length(ent_str) < 5;


-- Only Stanza (upper case entity types)
SELECT ent_str, ent_id, ent_type, COUNT(*)
From Tag
where document_collection = 'scientists' and ent_type = UPPER(ent_type)
GROUP BY ent_str, ent_id, ent_type
ORDER BY COUNT(*) DESC
LIMIT 500

-- Vocab Entity Linking
SELECT ent_str, ent_id, ent_type, COUNT(*)
From Tag
where document_collection = 'scientists' and ent_type <> UPPER(ent_type)
GROUP BY ent_str, ent_id, ent_type
ORDER BY COUNT(*) DESC
LIMIT 500


-- Wikipedia
-- Award Received
SELECT subject_str, subject_id, subject_type, predicate_org, predicate, relation, object_str, object_id, object_type, Sentence.text
FROM Predication JOIN Sentence ON (Predication.sentence_id = Sentence.id)
WHERE Predication.document_collection = 'scientists' and subject_type = 'Person' and object_type = 'Award' and extraction_type = 'PathIE'
and relation = 'award received'
ORDER BY random()
LIMIT 100;


SELECT subject_str, subject_id, subject_type, predicate_org, predicate, relation, object_str, object_id, object_type, Sentence.text
FROM Predication JOIN Sentence ON (Predication.sentence_id = Sentence.id)
WHERE Predication.document_collection = 'scientists' and extraction_type = 'PathIE'
ORDER BY random()
LIMIT 100;



SELECT subject_str, subject_id, subject_type, predicate_org, predicate, object_str, object_id, object_type, Sentence.text
FROM Predication JOIN Sentence ON (Predication.sentence_id = Sentence.id)
WHERE Predication.document_collection = 'scientists' and subject_type = 'Person' and object_type = 'Award' and extraction_type = 'PathIE'
and subject_id = 'http://www.wikidata.org/entity/Q937'
ORDER BY random()
LIMIT 100;

-- PathIE Statistics
SELECT predicate, relation, count(*)
FROM Predication WHERE Predication.document_collection = 'scientists' and extraction_type = 'PathIE'
GROUP BY predicate, relation
ORDER BY COUNT(*) DESC
LIMIT 500

SELECT predicate, relation, count(*)
FROM Predication WHERE Predication.document_collection = 'scientists' and extraction_type = 'PathIE'
and relation is not null
GROUP BY predicate, relation
ORDER BY COUNT(*) DESC
LIMIT 500


-- The document id for Albert Einstein is 736
-- Albert Einstein Entity id: http://www.wikidata.org/entity/Q937
SELECT subject_str, subject_id, subject_type, predicate_org, predicate, object_str, object_id, object_type, Sentence.text
FROM Predication JOIN Sentence ON (Predication.sentence_id = Sentence.id)
WHERE Predication.document_collection = 'scientists' and Predication.document_id = '736' and extraction_type = 'OPENIE6_NF'
ORDER BY random()
LIMIT 100;

SELECT subject_str, subject_id, subject_type, predicate_org, predicate, object_str, object_id, object_type, Sentence.text
FROM Predication JOIN Sentence ON (Predication.sentence_id = Sentence.id)
WHERE Predication.document_collection = 'scientists' and Predication.document_id = '736' and extraction_type = 'OPENIE6_EF'
ORDER BY random()
LIMIT 100;

SELECT subject_str, subject_id, subject_type, predicate_org, predicate, object_str, object_id, object_type, Sentence.text
FROM Predication JOIN Sentence ON (Predication.sentence_id = Sentence.id)
WHERE Predication.document_collection = 'scientists' and Predication.document_id = '736' and extraction_type = 'OPENIE6_PF'
ORDER BY random()
LIMIT 100;

SELECT subject_str, subject_id, subject_type, predicate_org, predicate, object_str, object_id, object_type, Sentence.text
FROM Predication JOIN Sentence ON (Predication.sentence_id = Sentence.id)
WHERE Predication.document_collection = 'scientists' and Predication.document_id = '736' and extraction_type = 'OPENIE6_SF'
ORDER BY random()
LIMIT 100;


SELECT subject_str, subject_id, subject_type, predicate_org, predicate, object_str, object_id, object_type, Sentence.text
FROM Predication JOIN Sentence ON (Predication.sentence_id = Sentence.id)
WHERE Predication.document_collection = 'scientists' and Predication.document_id = '736' and extraction_type = 'OPENIE6_SF'
and subject_id = 'http://www.wikidata.org/entity/Q937'
ORDER BY random()
LIMIT 100;

