-- Per Article
SELECT document_collection, extraction_type, count(*)
FROM predication
WHERE extraction_type LIKE 'CORENLP%'
GROUP BY document_collection, extraction_type
ORDER BY document_collection, extraction_type;

SELECT Predication.document_id, subject_str, predicate_org, predicate, object_str, Sentence.text
FROM Predication JOIN Sentence ON (Predication.sentence_id = Sentence.id)
WHERE extraction_type = 'CORENLP_OPENIE_NF' and Predication.document_collection = 'pollux'
ORDER by random()
LIMIT 200;
