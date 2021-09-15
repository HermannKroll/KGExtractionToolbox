from collections import namedtuple

import networkx as nx
from typing import Dict, List

from kgextractiontoolbox.document.document import TaggedEntity

PathIEToken = namedtuple('PathIEToken', ["text", "text_lower", "text_before", "text_after", "index", "charStart",
                                         "charEnd", "pos", "lemma"])

PathIEDependency = namedtuple('PathIEDependency', ["governor_idx", "dependent_idx", "relation"])

PathIEExtraction = namedtuple('PathIEExtraction', ["document_id", "subject_id", "subject_str", "subject_type",
                                                   "predicate", "predicate_lemmatized", "object_id", "object_str",
                                                   "object_type", "confidence", "sentence"])


def pathie_use_keywords_from_predicate_vocabulary(predicate_vocabulary: Dict[str, List[str]]):
    """
    Extracts important keywords and keyphrases from the used predicate vocabulary
    :param predicate_vocabulary: the predicate vocabulary
    :return: a set of keywords, a set of important phrases (keywords are single terms, phrases consist of multiple terms)
    """
    important_keywords = set()
    important_phrases = set()
    if predicate_vocabulary:
        vocabulary_terms = {k for k in predicate_vocabulary.keys()}
        vocabulary_terms.update({v for predicates in predicate_vocabulary.values() for v in predicates})
        for term in vocabulary_terms:
            term = term.strip().lower()
            if ' ' in term:
                important_phrases.add(term)
            else:
                important_keywords.add(term)
    return important_keywords, important_phrases


def pathie_reconstruct_sentence_sequence_from_tokens(tokens: [PathIEToken]) -> str:
    """
    Reconstructs the whole sentence from the sequence of tokens
    :param tokens: the sentence's PathIE tokens
    :return: the sentence string stripped
    """
    token_sequence = []
    for t in tokens:
        token_sequence.extend([t.text_before, t.text, t.text_after])
    # remove the last element - it does not belong to the string (after token AFTER the last word)
    # replace doubled spaces
    return ''.join(token_sequence).replace('  ', ' ').strip()


def pathie_reconstruct_text_from_token_indexes(tokens: [PathIEToken], token_indexes: [int]):
    """
    PathIE Core Logic
    Reconstruct the text of the given token indexes
    :param tokens: a list of the sentence's PathIE tokens
    :param token_indexes: the selected token indexes
    :return: the computed string stripped
    """
    sequence = []
    for t in tokens:
        if t.index in token_indexes:
            sequence.extend([t.text_before, t.text, t.text_after])
    # remove the last element - it does not belong to the string (after token AFTER the last word)
    return ''.join(sequence[:-1]).replace('  ', ' ').strip()


def pathie_find_tags_in_sentence(tokens: [PathIEToken], doc_tags: [TaggedEntity]):
    """
    PathIE Core Logic
    Finds all entity annotations within a sentence and computes the corresponding token indexes
    :param tokens: a list of PathIE tokens
    :param doc_tags: a list of annotated tags within the document
    :return: a set of tags mapped to sequences of token indexes
    """
    tag_token_index_sequences = []
    for tag in doc_tags:
        toks_for_tag = []
        start_token = None
        for tok in tokens:
            if tok.charStart >= tag.start and tok.charEnd <= tag.end:
                toks_for_tag.append(tok.index)
                if not start_token:
                    start_token = tok.text_lower
        # if we found a sequence and the start token matches
        if toks_for_tag and tag.text.lower().startswith(start_token):
            tag_token_index_sequences.append((tag, toks_for_tag))
    return tag_token_index_sequences


def pathie_find_relations_in_sentence(tokens: [PathIEToken], sentence_text_lower: str, important_keywords: [str] = None,
                                      important_phrases: [str] = None):
    """
    PathIE Core Logic
    Finds suitable relations (verbs) or relevant keywords/keyphrases in a sentence texts
    The corresponding token ids are computed and returnes
    :param tokens: a list of PathIE toknes
    :param sentence_text_lower: the sentence text in lower case
    :param important_keywords: a list of important keywords (optional)
    :param important_phrases: a list of important phrases (optional)
    :return:
    """
    idx2word = dict()
    # root is the empty word
    idx2word[0] = ""
    vidx2text_and_lemma = dict()
    for t in tokens:
        # it's a verb
        if t.pos.startswith('V') and t.lemma not in ["have", "be", "do"]:
            vidx2text_and_lemma[t.index] = (t.text, t.lemma)
        else:
            # check if a keyword is mentioned
            if important_keywords:
                for keyword in important_keywords:
                    if keyword.endswith('*') and t.text_lower.startswith(keyword[0:-1]):
                        vidx2text_and_lemma[t.index] = (t.text, t.lemma)
                    elif keyword.startswith('*') and t.text_lower.endswith(keyword[1:]):
                        vidx2text_and_lemma[t.index] = (t.text, t.lemma)
                    elif keyword.startswith('*') and keyword.endswith('*') and keyword[1:-1] in t.text_lower:
                        vidx2text_and_lemma[t.index] = (t.text, t.lemma)
                    elif keyword == t.text_lower:
                        vidx2text_and_lemma[t.index] = (t.text, t.lemma)

    if important_phrases:
        for phrase in important_phrases:
            phrase_without_star = phrase.replace('*', '')
            if phrase_without_star in sentence_text_lower:
                phrase_parts = phrase.split(' ')
                phrase_matches = []
                # Reconstruct match based on token indexes
                # Iterate over all tokens and search for matching sequences of subsequent tokens
                for j in range(0, len(tokens) - len(phrase_parts)):
                    phrase_matched = True
                    for i in range(0, len(phrase_parts)):
                        kw = phrase_parts[i]
                        if kw.endswith('*'):
                            if not tokens[j + i].text_lower.startswith(kw[0:-1]):
                                phrase_matched = False
                                break
                        elif kw.startswith('*'):
                            if not tokens[j + i].text_lower.endswith(kw[1:]):
                                phrase_matched = False
                                break
                        elif kw.startswith('*') and kw.endswith('*'):
                            if kw[1:-1] not in tokens[j + i]:
                                phrase_matched = False
                                break
                        else:
                            if kw != tokens[j + i].text_lower:  # partial included is enough
                                phrase_matched = False
                                break
                    if phrase_matched:
                        phrase_matches.append([(t.index, t.text, t.lemma) for t in tokens[j:j + len(phrase_parts)]])
                # go through all matches
                for match in phrase_matches:
                    # the whole phrase was matched
                    t_txt = ' '.join([p[1] for p in match])
                    t_lemma = ' '.join([p[2] for p in match])
                    for p in match:
                        # overwrite if a verb was already found for this index
                        vidx2text_and_lemma[p[0]] = (t_txt, t_lemma)
    return vidx2text_and_lemma


def pathie_extract_facts_from_sentence(doc_id: int, doc_tags: [TaggedEntity],
                                       tokens: [PathIEToken],
                                       dependencies: [PathIEDependency],
                                       predicate_vocabulary: {str: [str]} = None,
                                       ignore_not_extractions=True,
                                       ignore_may_extraction=True) -> [PathIEExtraction]:
    """
    Extracts fact from a sentence with PathIE
    :param doc_id: document id
    :param doc_tags: a set of document tags (TaggedEntity)
    :param tokens: a list of the sentence's PathIETokens
    :param dependencies: a list of the sentence's dependencies
    :param predicate_vocabulary: the predicate vocabulary if special words are given
    :param ignore_not_extractions: ignores extractions that are associated with a not
    :param ignore_may_extraction: ignores extractions that are associated with a may or might
    :return: a list of PathIE extractions
    """
    sentence = pathie_reconstruct_sentence_sequence_from_tokens(tokens).strip()
    sentence_lower = sentence.lower()

    important_keywords, important_phrases = pathie_use_keywords_from_predicate_vocabulary(predicate_vocabulary)

    # find all relations in the sentence
    vidx2text_and_lemma = pathie_find_relations_in_sentence(tokens, sentence_lower,
                                                            important_keywords, important_phrases)
    idx2token = {}
    if ignore_not_extractions or ignore_may_extraction:
        idx2token = {t.index: t for t in tokens}

    # no verbs -> no extractions
    if len(vidx2text_and_lemma) == 0:
        return []

    # find entities in sentence
    tag_sequences = pathie_find_tags_in_sentence(tokens, doc_tags)

    # convert the grammatical structure of the sentence into a graph
    dep_graph = nx.Graph()
    node_idxs = set()
    node_ids_to_ignore = set()
    for dep in dependencies:
        governor = int(dep.governor_idx)
        dependent = int(dep.dependent_idx)
        relation = dep.relation

        # delete verbs that are connected with a not
        if ignore_not_extractions:
            if governor in vidx2text_and_lemma and relation == 'advmod' and idx2token[dependent].text_lower in ['not',
                                                                                                                'nt']:
                del vidx2text_and_lemma[governor]
                node_ids_to_ignore.add(governor)

        if ignore_may_extraction:
            if governor in vidx2text_and_lemma and relation == 'aux' and idx2token[dependent].text_lower in ['may',
                                                                                                             'might']:
                node_ids_to_ignore.add(governor)
                del vidx2text_and_lemma[governor]

        if governor not in node_idxs:
            dep_graph.add_node(governor)
            node_idxs.add(governor)
        if dependent not in node_idxs:
            dep_graph.add_node(dependent)
            node_idxs.add(dependent)
        dep_graph.add_edge(governor, dependent)

    # maybe we have deleted all allowed verbs
    if ignore_not_extractions and len(vidx2text_and_lemma) == 0:
        return []

    extracted_tuples = []
    extracted_index = set()
    # perform the extraction
    # PathIE performs a nested loop search upon the entity start tokens and computes shortest path between them
    # if a verb, keyword or keyphrase appears on the path, a fact will be extracted
    sent_len = len(idx2token)
    for e1_idx, (e1_tag, e1_token_ids) in enumerate(tag_sequences):
        for e1_tok_id in e1_token_ids:
            for e2_idx, (e2_tag, e2_token_ids) in enumerate(tag_sequences):
                # do not extract relations between the same entity
                if e1_idx == e2_idx:
                    continue
                for e2_tok_id in e2_token_ids:
                    try:
                        for path in nx.all_shortest_paths(dep_graph, source=e1_tok_id, target=e2_tok_id):
                            path_nodes = []
                            # check if the path includes some nodes that must be ignored (not or may)
                            for n_idx in path:
                                path_nodes.append(n_idx)
                                if n_idx in node_ids_to_ignore:
                                    path_nodes = None
                                    break
                            if not path_nodes:
                                continue
                            # extract all facts from this path
                            for n_idx in path_nodes:
                                # does this path lead over a relation
                                if n_idx in vidx2text_and_lemma:
                                    # this is a valid path
                                    v_txt, v_lemma = vidx2text_and_lemma[n_idx]
                                    # only extract one direction
                                    key_e1_e2 = (
                                        e1_tag.ent_id, e1_tag.ent_type, v_lemma, e2_tag.ent_id, e2_tag.ent_type)
                                    key_e2_e1 = (
                                        e2_tag.ent_id, e2_tag.ent_type, v_lemma, e1_tag.ent_id, e1_tag.ent_type)
                                    if key_e1_e2 in extracted_index or key_e2_e1 in extracted_index:
                                        continue
                                    extracted_index.add(key_e1_e2)
                                    extracted_index.add(key_e2_e1)

                                    path_len = len(path_nodes)
                                    # only entities + verb
                                    if path_len <= 3:
                                        confidence = 1.0
                                    # decrease confidence for every other token on the path
                                    else:
                                        confidence = max(1.0 - 0.1 * float(path_len), 0.0)

                                    extracted_tuples.append(
                                        PathIEExtraction(doc_id,
                                                         e1_tag.ent_id, e1_tag.text, e1_tag.ent_type,
                                                         v_txt, v_lemma,
                                                         e2_tag.ent_id, e2_tag.text, e2_tag.ent_type,
                                                         confidence, sentence))
                    except nx.NetworkXNoPath:
                        pass

    return extracted_tuples
