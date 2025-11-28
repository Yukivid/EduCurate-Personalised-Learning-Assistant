import re
from typing import List, Dict, Tuple

def extract_modules_and_topics_structured(text: str) -> Tuple[str, List[Dict[str, List[str]]]]:
    if not text:
        return "", []

    text = text.replace("\r", "\n")

    # Regex to capture "Module:1 Title" or "Module 1 Title"
    module_re = re.compile(r'(?im)Module\s*[:\-]?\s*(\d+)\s+([A-Za-z].*?)(?:\d+\s*hours)?')

    modules = []
    for m in module_re.finditer(text):
        mod_num = m.group(1)
        mod_title = m.group(2).strip()
        start = m.end()
        # Find next module or end of text
        next_m = module_re.search(text, start)
        end = next_m.start() if next_m else len(text)
        content = text[start:end]

        # Split topics: commas, dashes, line breaks
        raw_parts = re.split(r'[,–\-]\s+|\n', content)
        topics = []
        for part in raw_parts:
            t = part.strip(" -•.\n\t")
            if t and not re.match(r'^\d+\s*hours$', t, re.I):
                topics.append(t)

        modules.append({
            "title": f"Module - {mod_num}: {mod_title}",
            "topics": topics
        })

    # Build pretty string
    pretty_lines = []
    for mod in modules:
        pretty_lines.append(mod["title"])
        for i, t in enumerate(mod["topics"], start=1):
            pretty_lines.append(f"  Topic - {i}: {t}")

    return "\n".join(pretty_lines), modules
