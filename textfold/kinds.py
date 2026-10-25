"""What a document is, for the words used about it. A research paper (arXiv, Europe PMC, bioRxiv, medRxiv) is a
paper; anything else (a web page, a Wikipedia article, a README, a PDF, a Markdown file) is a text, which may be a
letter or a report as well as an article. The prompts were written for papers: a paper's stay word for word what they
were (and so do their cached answers); a text's are the same prompts with the paper's words exchanged for a text's."""
import re

PAPERS = {"europepmc", "biorxiv", "medrxiv"}

# the paper's words in the prompts, and a text's, most specific first
TEXT = [
    ("sections of research papers", "sections of documents of every kind (articles, web pages, READMEs, reports, letters)"),
    ("understand a research paper", "understand a text (an article, a web page, a README, a report, a letter)"),
    ("Paper abstract, for context:", "Its opening, for context:"),
    ("Paper: ", "Text: "),
    ("a research paper", "a text"),
    ("research paper", "text"),
    ("fluent, precise academic", "fluent, precise"),
    ("the paper title itself", "the title itself"),
    ("titles of the paper", "titles of the text"),
    ("the paper's title", "the text's title"),
    ("the paper's own text", "the text's own words"),
    ("\nAbstract: ", "\nOpening: "),
    ("the paper's", "the text's"),
    ("the whole paper", "the whole text"),
    ("this paper", "this text"),
    ("of the paper", "of the text"),
    ("in the paper", "in the text"),
    ("from the paper", "from the text"),
    ("The paper,", "The text,"),
    ("the paper", "the text"),
    ("the authors' text", "the original text"),
    ("the authors' own", "the author's own"),
    ("the authors'", "the author's"),
    ("The paper", "The text"),
]


def is_paper(meta):
    kind = (meta.get("source") or {}).get("kind")
    return kind in PAPERS or (not kind and bool(re.fullmatch(r"\d{4}\.\d{4,5}", meta.get("id") or "")))


def adapt(prompt, meta):
    """A prompt written for a paper, as it is for a paper, and in a text's words for anything else."""
    if is_paper(meta):
        return prompt
    for a, b in TEXT:
        prompt = prompt.replace(a, b)
    return prompt


# A student's own notes, each with its own prompts (ladder.py): lecture notes (the lecture-notes-formatter skill), an
# assignment's implementation notes (pa-notes) and a quiz-prep note on it (pa-quiz). Stored as meta["mode"], set when a
# Markdown file is read (local.py) or chosen by the reader (pipeline.py); anything else is a paper or a text, as above.
MODES = ("lecture", "pa", "quiz")


def mode_of(meta):
    return meta.get("mode") if meta.get("mode") in MODES else None


def detect(text):
    """A Markdown text's mode, from `textfold-mode: <mode>` in its front matter or in an HTML comment (which outlives
    TextFold Bridge's export: it keeps no front matter but the title), else its headings and callouts; None: a text."""
    fm = re.match(r"\A---\n(.*?)\n---", text, re.S)
    m = (fm and re.search(r"^(?:textfold|adr)-mode\s*:\s*['\"]?(\w+)", fm.group(1), re.M | re.I)) \
        or re.search(r"<!--\s*textfold-mode\s*:\s*(\w+)\s*-->", text, re.I)
    if m:
        return m.group(1).lower() if m.group(1).lower() in MODES else None
    heads = re.findall(r"^#{1,6}\s+(.+)$", text, re.M)
    n = lambda pat: sum(bool(re.search(pat, h, re.I)) for h in heads)  # noqa: E731
    has = lambda pat: bool(re.search(pat, text, re.I | re.M))  # noqa: E731
    # a callout's title: as Obsidian writes it (> [!todo] Study plan), or as the Bridge sends it (> **Study plan**)
    callout = lambda title: has(r"^\s*>\s*(?:\[![\w-]+\][+-]?\s*|\*\*)" + title)  # noqa: E731
    score = {
        "quiz": 4 * bool(n(r"\bquiz\b|\bviva\b")) + 3 * n(r"practice questions") + 3 * n(r"last-minute checklist")
                + 2 * callout("study plan") + 2 * callout("answer"),
        "pa": 3 * n(r"^\W*batch \d+") + 2 * n(r"^\W*task \d+") + 2 * n(r"the big picture") + 2 * n(r"`[\w/.]+\.py`|viva|^\W*part \w+")
              + 2 * callout("self-check") + 2 * callout("test output") + 2 * callout("required evidence"),
        "lecture": 3 * n(r"^topic inventory") + 3 * n(r"cheat sheet|formula summary") + n(r"^numerical problems")
                   + has(r"nav:start"),
    }
    best = max(score, key=score.get)   # on a tie, the first: quiz, pa, lecture
    return best if score[best] >= 3 else None
