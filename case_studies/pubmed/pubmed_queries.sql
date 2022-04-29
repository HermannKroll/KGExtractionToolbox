-- Entity statistics
-- EL Tags
SELECT document_collection, COUNT(*)
From TAG
WHERE ent_type <> UPPER(ent_type)
GROUP BY document_collection


-- Vocab Entity Linking
SELECT ent_str, ent_id, ent_type, COUNT(*)
From Tag
where document_collection = 'PubMed' and ent_type <> UPPER(ent_type)
GROUP BY ent_str, ent_id, ent_type
ORDER BY COUNT(*) DESC
LIMIT 500;


-- No Filter
SELECT subject_str, subject_id, subject_type, predicate_org, predicate, object_str, object_id, object_type, Sentence.text
FROM Predication JOIN Sentence ON (Predication.sentence_id = Sentence.id)
WHERE extraction_type = 'OPENIE6_NF' and document_collecton = 'PubMed'
ORDER BY random()
LIMIT 100;

-- Subject Filter
SELECT subject_str, subject_id, subject_type, predicate_org, predicate, object_str, object_id, object_type, Sentence.text
FROM Predication JOIN Sentence ON (Predication.sentence_id = Sentence.id)
WHERE extraction_type = 'OPENIE6_SF' and document_collecton = 'PubMed'
ORDER BY random()
LIMIT 100;

-- Exact Filter
SELECT subject_str, subject_id, subject_type, predicate_org, predicate, object_str, object_id, object_type, Sentence.text
FROM Predication JOIN Sentence ON (Predication.sentence_id = Sentence.id)
WHERE extraction_type = 'OPENIE6_EF' and document_collecton = 'PubMed'
ORDER BY random()
LIMIT 100;

-- Partial Filter
SELECT subject_str, subject_id, subject_type, predicate_org, predicate, object_str, object_id, object_type, Sentence.text
FROM Predication JOIN Sentence ON (Predication.sentence_id = Sentence.id)
WHERE extraction_type = 'OPENIE6_PF' and document_collecton = 'PubMed'
LIMIT 100;


-- PathIE:
SELECT subject_str, subject_id, subject_type, predicate_org, predicate, relation, object_str, object_id, object_type, Sentence.text
FROM Predication JOIN Sentence ON (Predication.sentence_id = Sentence.id)
WHERE Predication.document_collection = 'PubMed' and subject_type = 'Drug' and object_type = 'Disease' and extraction_type = 'PathIE'
and relation = 'treats'
ORDER BY random()
LIMIT 100;


SELECT subject_str, subject_id, subject_type, predicate_org, predicate, relation, object_str, object_id, object_type, Sentence.text
FROM Predication JOIN Sentence ON (Predication.sentence_id = Sentence.id)
WHERE Predication.document_collection = 'PubMed' and extraction_type = 'PathIE'
ORDER BY random()
LIMIT 100;

-- PathIE Statistics
SELECT predicate, relation, count(*)
FROM Predication WHERE Predication.document_collection = 'PubMed' and extraction_type = 'PathIE'
GROUP BY predicate, relation
ORDER BY COUNT(*) DESC
LIMIT 500;

SELECT predicate, relation, count(*)
FROM Predication WHERE Predication.document_collection = 'PubMed' and extraction_type = 'PathIE'
and relation is not null
GROUP BY predicate, relation
ORDER BY COUNT(*) DESC
LIMIT 500;


-- See extraction statistics:
SELECT document_collection, extraction_type, count(*)
From Predication
GROUP by document_collection, extraction_type
ORDER BY  document_collection, extraction_type ASC;
