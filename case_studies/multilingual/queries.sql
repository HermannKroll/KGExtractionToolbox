
-- Export OpenIE 6 for Wikipedia
SELECT Predication.document_id, subject_str, predicate_org, predicate, object_str, Sentence.text
FROM Predication JOIN Sentence ON (Predication.sentence_id = Sentence.id)
WHERE extraction_type = 'OPENIE6_NF' and Predication.document_collection = 'scientists_ml'
ORDER BY Predication.document_id;

-- Export PathIE for PubMed
SELECT Predication.document_id, subject_str, subject_id, subject_type, predicate_org, predicate, object_str, object_id, object_type, Sentence.text
FROM Predication JOIN Sentence ON (Predication.sentence_id = Sentence.id)
WHERE extraction_type = 'PathIE' and Predication.document_collection = 'scientists_ml'
ORDER BY Predication.document_id;


-- Export OpenIE 6 for Pollux
SELECT Predication.document_id, subject_str, predicate_org, predicate, object_str, Sentence.text
FROM Predication JOIN Sentence ON (Predication.sentence_id = Sentence.id)
WHERE extraction_type = 'OPENIE6_NF' and Predication.document_collection = 'pollux_ml'
ORDER BY Predication.document_id;

-- Export OpenIE 6 for PubMed
SELECT Predication.document_id, subject_str, predicate_org, predicate, object_str, Sentence.text
FROM Predication JOIN Sentence ON (Predication.sentence_id = Sentence.id)
WHERE extraction_type = 'OPENIE6_NF' and Predication.document_collection = 'PubMed_ml'
ORDER BY Predication.document_id;


-- Export PathIE for PubMed
SELECT Predication.document_id, subject_str, subject_id, subject_type, predicate_org, predicate, object_str, object_id, object_type, Sentence.text
FROM Predication JOIN Sentence ON (Predication.sentence_id = Sentence.id)
WHERE extraction_type = 'PathIE' and Predication.document_collection = 'PubMed_ml'
ORDER BY Predication.document_id;


-- Count Extractions for pure English
SELECT Predication.document_collection, Predication.extraction_type, Count(*)
FROM Predication JOIN Sentence ON (Predication.sentence_id = Sentence.id)
WHERE  Predication.document_collection in ('pollux_ml', 'PubMed_ml', 'scientists_ml')
AND document_id like '%1'
GROUP BY Predication.document_collection, Predication.extraction_type;

-- Count Extractions for DeepL english
SELECT Predication.document_collection, Predication.extraction_type, Count(*)
FROM Predication JOIN Sentence ON (Predication.sentence_id = Sentence.id)
WHERE Predication.document_collection in ('pollux_ml', 'PubMed_ml', 'scientists_ml')
AND document_id like '%2'
GROUP BY Predication.document_collection, Predication.extraction_type;

PubMed_ml	201 -> 180
pollux_ml	161 -> 167
scientists_ml	229 -> 117