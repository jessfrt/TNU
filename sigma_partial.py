from tnu import alfa

def sigma_partial(word: str, lang: str, part: str = 'A') -> str:
    """A=início, B=meio, C=fim do vetor-Alfa"""
    vec = alfa(word, lang).split('-')  # ['0.123','0.456',...]
    n = len(vec)
    if part == 'A':      # 1ª metade
        return '-'.join(vec[:n//2])
    elif part == 'B':    # meio
        return '-'.join(vec[n//4:3*n//4])
    elif part == 'C':    # última metade
        return '-'.join(vec[n//2:])
    return '-'.join(vec)  # fallback