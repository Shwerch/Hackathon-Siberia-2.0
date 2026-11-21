import re
from pathlib import Path
from pydantic import BaseModel


class KBChunk(BaseModel):
    file: str
    section: str
    text: str


def load_kb_chunks(kb_dir: Path) -> list[KBChunk]:
    chunks: list[KBChunk] = []
    target_files = [
        "01_scope_functions_synonyx_1.9.md",
        "02_methodology.md",
        "03_glossary.md",
    ]
    for fname in target_files:
        fpath = kb_dir / fname
        if not fpath.exists():
            continue
        content = fpath.read_text(encoding="utf-8")
        current_section = "Введение"
        buffer: list[str] = []

        for line in content.splitlines():
            heading = re.match(r"^(#{2,3})\s+(.+)$", line.strip())
            if heading:
                if buffer:
                    text = "\n".join(buffer).strip()
                    if text:
                        chunks.append(KBChunk(file=fname, section=current_section, text=text))
                    buffer = []
                current_section = heading.group(2).strip()
            else:
                buffer.append(line)

        if buffer:
            text = "\n".join(buffer).strip()
            if text:
                chunks.append(KBChunk(file=fname, section=current_section, text=text))
    return chunks
