import re
from difflib import SequenceMatcher

def normalize(text):
    # Whitespace and case only. Never strip punctuation, digits, signs or negation.
    return ' '.join(text.split()).casefold()

def similarity(a, b):
    return SequenceMatcher(None, normalize(a), normalize(b), autojunk=False).ratio()

QUANTITY = re.compile(r'(?<!\w)[+-]?\d+(?:[.,]\d+)?\s*(?:mg|mcg|kg|ml|mm|cm|g|l|%|degrees)?(?!\w)', re.I)
NEGATION = re.compile(r"\b(?:no|not|never|without|cannot|mustn't|don't|doesn't)\b", re.I)
WARNING = re.compile(r'\b(?:warning|caution|danger)\b', re.I)

def categories(a, b):
    # Space segmentation errors must not manufacture a lost negation or number.
    # Retain the difference as wording and require source review.
    if a and b and re.sub(r'\s+', '', normalize(a)) == re.sub(r'\s+', '', normalize(b)):
        return ['wording']
    if not a:
        return ['warning'] if WARNING.search(b) else ['wording']
    if not b:
        return ['warning'] if WARNING.search(a) else ['missing_paragraph']
    cats = []
    if QUANTITY.findall(normalize(a)) != QUANTITY.findall(normalize(b)):
        cats.append('quantity_unit')
    if NEGATION.findall(normalize(a)) != NEGATION.findall(normalize(b)):
        cats.append('negation')
    if WARNING.search(a) or WARNING.search(b):
        cats.append('warning')
    return cats or ['wording']
