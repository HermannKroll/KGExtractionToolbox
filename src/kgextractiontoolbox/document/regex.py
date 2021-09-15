import re

TAG_LINE_NORMAL = re.compile(r"(\d+)\t(\d+)\t(\d+)\t(.*?)\t(.*?)\t(.*?)\n")
DOCUMENT_ID = re.compile(r"(\d+)\|t\|.*\n")
TAG_DOCUMENT_ID = re.compile(r"(\d+)\t.*\n")
CONTENT_ID_TIT_ABS = re.compile(r"(\d+)\|t\|(.*?)\n\d+\|a\|(.*?)\n.*")
CONTENT_RAW = re.compile(r"\d+.*?\n\n", re.DOTALL)
PUBTATOR_TITLE = re.compile(r"\|t\|(.*?)\n")
PUBTATOR_ABSTRACT = re.compile(r"\|a\|(.*?)\n")
ILLEGAL_CHAR = re.compile(r"[^ -{}~]", re.UNICODE)  # Match all non ascii characters, control sequences and |
PUBMED_ID = re.compile(r"(\d+)")
PMC_ID = re.compile(r"PMC(\d+)")
