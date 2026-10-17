def generate_prefixes(text: str, min_size: int = 2, max_size: int = 10) -> list[str]:
    prefixes = set()
    text = text.lower()
    for word in text.split():
        word_len = len(word)

        for n in range(min_size, min(word_len, max_size) + 1):
            prefixes.add(word[:n])
    return list(prefixes)
