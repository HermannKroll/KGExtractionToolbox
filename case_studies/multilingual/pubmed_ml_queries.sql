
-- No Filter
SELECT Predication.document_id, subject_type, predicate_org, predicate, object_type, Sentence.text
FROM Predication JOIN Sentence ON (Predication.sentence_id = Sentence.id)
WHERE extraction_type = 'OPENIE6_NF' and Predication.document_collection = 'PubMed_ml'
ORDER BY Predication.document_id;

-- Subject Filter
SELECT Predication.document_id, subject_str, subject_id, subject_type, predicate_org, predicate, object_str, object_id, object_type, Sentence.text
FROM Predication JOIN Sentence ON (Predication.sentence_id = Sentence.id)
WHERE extraction_type = 'OPENIE6_SF' and Predication.document_collection = 'PubMed_ml'
ORDER BY Predication.document_id;

-- Exact Filter
SELECT Predication.document_id, subject_str, subject_id, subject_type, predicate_org, predicate, object_str, object_id, object_type, Sentence.text
FROM Predication JOIN Sentence ON (Predication.sentence_id = Sentence.id)
WHERE extraction_type = 'OPENIE6_EF' and Predication.document_collection = 'PubMed_ml'
ORDER BY Predication.document_id;

-- Partial Filter
SELECT Predication.document_id, subject_str, subject_id, subject_type, predicate_org, predicate, object_str, object_id, object_type, Sentence.text
FROM Predication JOIN Sentence ON (Predication.sentence_id = Sentence.id)
WHERE extraction_type = 'OPENIE6_PF' and Predication.document_collection = 'PubMed_ml'
ORDER BY Predication.document_id;
