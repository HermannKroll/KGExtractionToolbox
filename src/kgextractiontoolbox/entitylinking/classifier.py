import re
from pathlib import Path
from typing import Union

from kgextractiontoolbox.document.document import TaggedDocument


class Classifier:
    def __init__(self, classification, rule_path: Union[str, Path] = None, rules=None):
        self.rules = []
        self.classification = classification
        if rule_path:
            self.rules = Classifier.read_ruleset(rule_path)
        elif rules:
            self.rules = rules
        else:
            raise ValueError("Either rules or rule_path must be given")

    def classify_document(self, doc: TaggedDocument, consider_sections=False):
        """
        Classify whether a document text content matches on of the classifier rules
        :param doc: the document to classify
        :param consider_sections: should sections be considered?
        :return:
        """
        matches = []
        for content, offset in doc.iterate_over_text_elements(sections=consider_sections):
            for rule in self.rules:
                rule_match = []
                for term in rule:
                    term_match = term.search(content)
                    if not term_match:
                        break
                    else:
                        pos = term_match.regs[0]
                        pos = (pos[0] + offset, pos[1] + offset)
                        rule_match.append(f"{term.pattern}:{term_match.group(0)}{pos}")
                # else will be executed if loop does not encounter a break
                else:
                    matches.append(' AND '.join([rm for rm in rule_match]))
        # Execute all rules - if a rule matches then add classification
        if matches:
            doc.classification[self.classification] = ';'.join([m for m in matches])
        return doc

    @staticmethod
    def compile_entry_to_regex(term):
        term = term.strip()
        # replace the * operator
        term = term.replace("*", "\\w*")
        # add that the word must start with the term
        term = term + "\\b"
        # check if there is the w/1 operator for one arbitrary word
        if 'w/' in term:
            term_rule = term
            for subterm in term.split(' '):
                # replace w/1 by only one word
                if subterm[0] == 'w' and subterm[1] == '/':
                    word_count = int(subterm.split('/')[1])
                    word_sequence = []
                    for i in range(0, word_count):
                        word_sequence.append(r'\w*')
                    word_sequence = ' '.join([w for w in word_sequence])
                    term_rule = term_rule.replace(subterm, word_sequence)
            # set term now to the new rule
            term = term_rule
        return re.compile(term, re.IGNORECASE)

    @staticmethod
    def compile_line_to_regex(line: str):
        return list([Classifier.compile_entry_to_regex(term) for term in line.split("AND")])

    @staticmethod
    def read_ruleset(filepath: Union[str, Path]):
        ruleset = []
        with open(filepath, "r") as f:
            for line in f:
                terms = Classifier.compile_line_to_regex(line.strip())
                ruleset.append(terms)
        return ruleset
