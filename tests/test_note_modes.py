"""A student's own notes read with their own prompt (kinds.MODES): lecture notes, assignment notes and a quiz-prep note,
told from their headings and callouts or from `textfold-mode:` in their front matter, kept in meta["mode"] through a
refold, and chosen by the reader (pipeline.generate(mode=...)). In a data folder of its own; no model is called.

Run from the repo root:
    python3 -m unittest tests.test_note_modes
"""
import os
import re
import tempfile
import unittest
from pathlib import Path
from unittest import mock

from textfold import kinds, llm, local, pipeline, store

LECTURE = """# Lecture 5: Transformers

## Topic Inventory

- 1. Tokens

## 1. Tokens

A patch of samples is one token. This may be enough for forecasting.

## Formula Summary Sheet

| Concept | Formula |
|---|---|
| Patches | $N = L / P$ |

## Cheat Sheet & Recall Aids

- A patch is a token.
"""

PA = """# PA2 Notes

## 0 The big picture

The assignment trains a small model.

## Task 1 — DPO

The loss subtracts the reference log-ratio.

> [!warning] Sign of the reference term
> Adding it runs and is wrong.

> [!question]- Self-check
> 1. Which sign? → minus
"""

QUIZ = """# PA2 Quiz Prep

> [!todo] Study plan
> Read the core sections.

## 1 DPO

The loss subtracts the reference log-ratio, because the policy is scored against it.

## Practice questions

1. Which sign does the reference term take?

## Last-minute checklist

- [ ] The sign, and why.
"""

DIARY = "# Heat pump diary\n\n## Monday\n\nThe heat pump ran all night.\n"


class Detect(unittest.TestCase):
    def test_each_kind_of_note_is_told_by_its_shape(self):
        self.assertEqual(kinds.detect(LECTURE), "lecture")
        self.assertEqual(kinds.detect(PA), "pa")
        self.assertEqual(kinds.detect(QUIZ), "quiz")
        self.assertIsNone(kinds.detect(DIARY))   # nothing of a student's notes: a text, as before

    def test_front_matter_decides(self):
        self.assertEqual(kinds.detect("---\ntextfold-mode: Quiz\n---\n" + DIARY), "quiz")
        self.assertIsNone(kinds.detect("---\ntextfold-mode: text\n---\n" + LECTURE))


    def test_a_note_exported_by_the_bridge_is_told_too(self):
        """TextFold Bridge sends a note without its front matter (but its title), callouts as bold-titled quotes and
        no %% comments (its src/flatten.ts): what is left still tells the kind, and a mode in an HTML comment stays."""
        def bridge(text):
            text = re.sub(r"\A---\n.*?\n---\n", "", text, flags=re.S)
            text = re.sub(r"^(\s*(?:>\s*)+)\[![\w-]+\][+-]?\s*(.+)$", r"\1**\2**\n\1", text, flags=re.M)
            return re.sub(r"%%.*?%%", "", text, flags=re.S)
        self.assertEqual(kinds.detect(bridge(LECTURE)), "lecture")
        self.assertEqual(kinds.detect(bridge(PA.replace("## 0 The big picture", "## Overview"))), "pa")   # by its callouts
        self.assertEqual(kinds.detect(bridge(QUIZ)), "quiz")
        self.assertIsNone(kinds.detect(bridge("---\ntextfold-mode: quiz\n---\n" + DIARY)))   # a property: left in Obsidian
        self.assertEqual(kinds.detect(bridge(DIARY + "\n<!-- textfold-mode: quiz -->\n")), "quiz")


def fake_model(asked):
    def once(prompt, schema, spec, timeout, system):
        asked.append((prompt, system))
        if "Its units in reading order" not in prompt:
            return {"links": []}, 0
        n = prompt.count("\n[U")
        return {"section": {"takeaway": "The section in brief", "topic": "The section"},
                "units": [{"id": f"U{k}", "role": "claim", "takeaway": f"Point {k}", "topic": "Point", "reason": "",
                           "evidence": [0]} for k in range(n)]}, 0
    return once


class Modes(unittest.TestCase):
    SPEC = {"id": "fake/model", "kind": "api", "protocol": "openai", "base": "http://127.0.0.1:9", "api_key": "", "model": "fake"}

    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        patch = mock.patch.object(store, "DATA", Path(self.tmp.name))
        patch.start()
        self.addCleanup(patch.stop)
        self.addCleanup(self.tmp.cleanup)

    def meta(self, pid):
        return store.parsed(pid)["meta"]

    def levels(self, pid, mode=None):
        asked = []
        with mock.patch.object(llm, "_once", fake_model(asked)), mock.patch.dict(os.environ):
            os.environ.pop("TEXTFOLD_NO_MODELS", None)
            pipeline.generate(pid, "en", self.SPEC, mode=mode)
        return [a for a in asked if "Its units in reading order" in a[0]]

    def test_a_note_is_read_with_its_own_prompt(self):
        pid = local.import_text(PA, "PA2 Notes.md")
        self.assertEqual(self.meta(pid)["mode"], "pa")
        prompt, system = self.levels(pid)[0]
        self.assertTrue(prompt.startswith("Assignment notes: PA2 Notes"))
        self.assertIn("quiz trap", prompt)
        self.assertIn("programming assignment", system)

    def test_the_mode_comment_is_not_read_as_text(self):
        pid = local.import_text(DIARY + "\n<!-- textfold-mode: pa -->\n", "diary.md")
        doc = store.parsed(pid)
        self.assertEqual(doc["meta"]["mode"], "pa")
        self.assertFalse(any("textfold-mode" in "".join(t.get("t", "") for t in u["toks"]) for u in doc["units"].values()))

    def test_a_text_keeps_the_general_prompt(self):
        pid = local.import_text(DIARY, "diary.md")
        self.assertNotIn("mode", self.meta(pid))
        prompt, system = self.levels(pid)[0]
        self.assertTrue(prompt.startswith("Text: Heat pump diary"))
        self.assertEqual(system, llm.system_for(self.meta(pid)))

    def test_the_readers_choice_is_kept_through_a_refold(self):
        pid = local.import_text(LECTURE, "L5.md")
        self.levels(pid)
        prompt, _ = self.levels(pid, mode="quiz")[0]   # another prompt: the levels are written again
        self.assertTrue(prompt.startswith("Quiz-prep note:"))
        local.replace_text(pid, LECTURE.replace("one token", "a single token"))
        self.assertEqual(self.meta(pid)["mode"], "quiz")
        self.levels(pid, mode="auto")   # back to what it looks like
        self.assertEqual(self.meta(pid)["mode"], "lecture")
        local.replace_text(pid, DIARY)   # no longer looks like notes, and nobody chose: a text
        self.assertNotIn("mode", self.meta(pid))


if __name__ == "__main__":
    unittest.main()
