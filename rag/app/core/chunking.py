from __future__ import annotations

import re
from dataclasses import dataclass, field

# ---------------------------------------------------------------------------
# Structural patterns for Russian НПА
# ---------------------------------------------------------------------------

ARTICLE_RE = re.compile(
    r"^Статья\s+(\d+[\d\.\-]*)\.?\s*(.*?)\s*$",
    re.MULTILINE,
)
CHAPTER_RE = re.compile(r"^Глава\s+(\d+[\d\.\-]*)[\.\s]", re.MULTILINE | re.IGNORECASE)
SECTION_RE = re.compile(r"^Раздел\s+([IVXLCDM\d]+)[\.\s]", re.MULTILINE | re.IGNORECASE)

# Numbered paragraphs inside an article: "1.", "1.1.", "2)", "а)", "б)", "ж1)"
PUNKT_RE = re.compile(r"(?m)^(?:\d+(?:\.\d+)*\.|\d+\)|[а-я]\d*\))\s")


# ---------------------------------------------------------------------------
# Data model
# ---------------------------------------------------------------------------

@dataclass
class Chunk:
    content: str
    index: int
    meta: dict = field(default_factory=dict)


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _normalise(text: str) -> str:
    """Remove garbage whitespace produced by PDF/RTF/MHTML extractors."""
    # Must replace \xa0 FIRST so subsequent space-based regexes work correctly.
    text = text.replace("\u00ad", "").replace("\u00a0", " ")
    # MHTML/RTF extractors use runs of spaces as paragraph separators.
    # Insert newlines before structural headings so ^ anchors can find them.
    text = re.sub(r"[ \t]{2,}(?=Статья\s+\d)", "\n", text)
    text = re.sub(r"[ \t]{2,}(?=Глава\s+\d)", "\n", text, flags=re.IGNORECASE)
    text = re.sub(r"[ \t]{2,}(?=Раздел\s+[IVXLCDM\d])", "\n", text, flags=re.IGNORECASE)
    # Insert newlines before numbered paragraphs so PUNKT_RE can match them.
    # Negative lookbehinds:
    #   - Cyrillic letter: prevents splitting compound IDs like "ж1)"
    #   - digit / dot: prevents splitting inside multi-part numbers like "15.1."
    #   - "Статья ", "Глава ", "Раздел ": prevents breaking structural headers
    text = re.sub(
        r"(?<!\n)(?<![а-яА-Я])(?<!\d)(?<!\.)(?<!Статья )(?<!Глава )(?<!Раздел )"
        r"(?=(?:\d+(?:\.\d+)*\.|\d+\)|[а-я]\d*\))\s)",
        "\n", text,
    )
    # Collapse 3+ blank lines into 2
    text = re.sub(r"\n{3,}", "\n\n", text)
    # Remove trailing spaces on each line
    text = re.sub(r"[ \t]+\n", "\n", text)
    return text.strip()


# ---------------------------------------------------------------------------
# Simple character-level chunker (fallback)
# ---------------------------------------------------------------------------

class SimpleChunker:
    """Split plain text into overlapping chunks of at most `max_len` characters."""

    def __init__(self, max_len: int = 1500, overlap: int = 200) -> None:
        self.max_len = max_len
        self.overlap = overlap

    def split(self, text: str, base_meta: dict | None = None) -> list[Chunk]:
        meta = base_meta or {}
        chunks: list[Chunk] = []
        start = 0
        idx = 0
        while start < len(text):
            end = start + self.max_len
            if end < len(text):
                # Try to break at sentence boundary (". "), then at word boundary (" ")
                candidate = text[start:end]
                sent_break = candidate.rfind(". ")
                if sent_break > self.max_len // 2:
                    end = start + sent_break + 1  # include the dot
                else:
                    word_break = candidate.rfind(" ")
                    if word_break > self.max_len // 2:
                        end = start + word_break
            chunk_text = text[start:end].strip()
            if chunk_text:
                chunks.append(Chunk(content=chunk_text, index=idx, meta=dict(meta)))
                idx += 1
            if end >= len(text):
                break
            start = end - self.overlap
            # Align overlap start to word boundary to avoid mid-word starts
            if start > 0 and start < len(text) and text[start] != " ":
                space_pos = text.find(" ", start)
                if space_pos != -1 and space_pos < start + 50:
                    start = space_pos + 1
        return chunks


# ---------------------------------------------------------------------------
# Article-aware chunker for Russian НПА
# ---------------------------------------------------------------------------

class LegalDocumentChunker:
    """Article-aware chunker for Russian НПА.

    Strategy:
    1. Preamble (everything before the first «Статья») → one or more chunks
       tagged article="preamble".
    2. Each «Статья N.» → chunk(s) with article/chapter/section in meta.
    3. Long articles are split preferring пункт (numbered paragraph) boundaries
       before falling back to character-level splitting.
    """

    def __init__(
        self,
        law_name: str = "",
        max_len: int = 1500,
        overlap: int = 200,
    ) -> None:
        self.law_name = law_name
        self._simple = SimpleChunker(max_len=max_len, overlap=overlap)

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    def split(self, text: str) -> list[Chunk]:
        text = _normalise(text)
        matches = list(ARTICLE_RE.finditer(text))

        if not matches:
            return self._simple.split(text, base_meta={"law": self.law_name})

        chunks: list[Chunk] = []
        idx = 0

        # 1. Preamble
        preamble = text[: matches[0].start()].strip()
        if preamble:
            meta = {"law": self.law_name, "article": "preamble", "chapter": "", "section": ""}
            for sub in self._simple.split(preamble, base_meta=meta):
                sub.index = idx
                chunks.append(sub)
                idx += 1

        # 2. Articles
        for i, match in enumerate(matches):
            article_num = match.group(1)
            article_start = match.start()
            article_end = matches[i + 1].start() if i + 1 < len(matches) else len(text)
            article_text = text[article_start:article_end].strip()
            # Strip trailing chapter/section headings that belong to the next structure
            article_text = re.sub(
                r"\n+(?:ГЛАВА|Глава|РАЗДЕЛ|Раздел)\s+.+$",
                "", article_text, flags=re.DOTALL,
            ).strip()

            base_meta = {
                "law": self.law_name,
                "article": article_num,
                "chapter": self._find_context(text, article_start, CHAPTER_RE),
                "section": self._find_context(text, article_start, SECTION_RE),
            }

            # Skip stub articles ("Исключена поправкой...")
            if re.search(r"(?i)исключена\s+поправкой", article_text):
                continue

            for sub in self._chunk_article(article_text, base_meta):
                # Skip orphaned fragments (e.g. amendment metadata lines)
                if len(sub.content.strip()) < 80:
                    continue
                sub.index = idx
                chunks.append(sub)
                idx += 1

        return chunks

    # ------------------------------------------------------------------
    # Internal helpers
    # ------------------------------------------------------------------

    def _chunk_article(self, text: str, base_meta: dict) -> list[Chunk]:
        """Return chunks for a single article, respecting пункт boundaries."""
        if len(text) <= self._simple.max_len:
            return [Chunk(content=text, index=0, meta=base_meta)]

        # Extract article header line ("Статья N ...") for continuation chunks
        first_newline = text.find("\n")
        article_header = text[:first_newline].strip() if first_newline != -1 else ""

        # Try to split at numbered paragraph boundaries
        punkt_splits = self._split_by_punkty(text, base_meta)
        if punkt_splits:
            # Prepend header to continuation chunks so each one is self-contained
            if article_header:
                for chunk in punkt_splits[1:]:
                    if not chunk.content.startswith("Статья"):
                        chunk.content = article_header + "\n\n" + chunk.content
            return punkt_splits

        # Fall back to character-level with header prepended to continuations
        char_splits = self._simple.split(text, base_meta=base_meta)
        if article_header:
            for chunk in char_splits[1:]:
                if not chunk.content.startswith("Статья"):
                    chunk.content = article_header + "\n\n" + chunk.content
        return char_splits

    def _split_by_punkty(self, text: str, base_meta: dict) -> list[Chunk]:
        """Group consecutive пункты into chunks that fit within max_len."""
        boundaries = [m.start() for m in PUNKT_RE.finditer(text)]
        if not boundaries:
            return []

        # Segments: header (before first пункт) + each пункт body
        segments: list[str] = []
        header = text[: boundaries[0]].strip()
        if header:
            segments.append(header)
        for j, start in enumerate(boundaries):
            end = boundaries[j + 1] if j + 1 < len(boundaries) else len(text)
            segments.append(text[start:end].strip())

        # Greedily merge segments into chunks
        chunks: list[Chunk] = []
        current = ""
        for seg in segments:
            candidate = (current + "\n" + seg).strip() if current else seg
            if len(candidate) <= self._simple.max_len:
                current = candidate
            else:
                if current:
                    chunks.extend(self._simple.split(current, base_meta=base_meta))
                current = seg
        if current:
            chunks.extend(self._simple.split(current, base_meta=base_meta))

        return chunks

    @staticmethod
    def _find_context(text: str, pos: int, pattern: re.Pattern) -> str:
        best = ""
        for m in pattern.finditer(text[:pos]):
            best = m.group(1)
        return best
