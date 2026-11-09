import re
import unicodedata


def slugify(text: str) -> str:
    # Normalize unicode characters (e.g., 'é' -> 'e')
    text = (
        unicodedata.normalize("NFKD", text)
        .encode("ascii", "ignore")
        .decode("utf-8")
    )
    # Convert to lowercase and replace non-word characters with hyphens
    text = re.sub(r"[^\w\s-]", "", text.lower())
    # Replace whitespace or multiple hyphens with a single hyphen
    return re.sub(r"[-\s]+", "-", text).strip("-")
