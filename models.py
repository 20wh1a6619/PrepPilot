import re
import nltk
from nltk.corpus import stopwords
from nltk.util import ngrams
from collections import Counter

nltk.download('stopwords')

EN_STOPWORDS = set(stopwords.words('english'))

CUSTOM_STOPWORDS = set([
    "build","develop","create","help","using","experience",
    "environment","products","services","innovative","collaborate",
    "knowledge","working","ability","good","strong","software",
    "engineering","industry","science","computing","computer",
    "agile","deliver","design","lead","manage","run","scale","speed",
    "team","role","work","fast","growing","company","job"
])

STOPWORDS = EN_STOPWORDS.union(CUSTOM_STOPWORDS)

SKILL_MAP = {
    "data structures": ["data structure", "data structures"],
    "algorithms": ["algorithm", "algorithms", "problem solving"],
    "object oriented": ["object oriented", "oop"],
    "system design": ["system design"],
    "distributed systems": ["distributed systems"],
    "database": ["database", "nosql"],
    "api": ["api", "rest api"],
    "cloud": ["aws", "gcp", "azure"],
    "backend": ["backend"],
    "frontend": ["frontend", "react", "html", "css"]
}

KNOWN_TECH = set([
    "python","java","c++","sql","mongodb","postgresql","mysql",
    "react","node","django","flask","pandas","numpy",
    "aws","docker","kubernetes","git","linux","spark",
    "hadoop","airflow","dbt","snowflake","tableau","powerbi",
    "excel"
])

WORD_REGEX = re.compile(r'\b[A-Za-z0-9#+.-]{2,}\b')


def normalize_skill(skill):
    skill = skill.lower().strip()

    if "object" in skill:
        return "object oriented"
    if "algorithm" in skill:
        return "algorithms"
    if "data structure" in skill:
        return "data structures"

    return skill

def is_valid_skill(word, freq_map):
    word_lower = word.lower()

    if word_lower in KNOWN_TECH:
        return True

    if word[0].isupper() and word_lower not in STOPWORDS:
        return True

    # repeated words
    if freq_map[word_lower] > 1 and word_lower not in STOPWORDS:
        return True

    return False

def extract_skills_from_jd(jd_text):
    jd_text_lower = jd_text.lower()
    all_skills = set()

    # SKILL MAP MATCH
    for skill, keywords in SKILL_MAP.items():
        for k in keywords:
            if re.search(rf'\b{re.escape(k)}\b', jd_text_lower):
                all_skills.add(skill)
                break

    # TOKENIZE
    words = WORD_REGEX.findall(jd_text)
    words_lower = [w.lower() for w in words]
    freq_map = Counter(words_lower)

    # SINGLE WORD
    for w in words:
        if w.lower() not in STOPWORDS and is_valid_skill(w, freq_map):
            all_skills.add(w.lower())

    # BIGRAMS
    bigrams = [" ".join(bg) for bg in ngrams(words_lower, 2)]
    for bg in bigrams:
        for skill, keywords in SKILL_MAP.items():
            if bg in keywords:
                all_skills.add(skill)

    # NORMALIZE + CAMELCASE
    final = set()
    for s in all_skills:
        norm = normalize_skill(s)
        final.add(norm.title())

    return sorted(final)