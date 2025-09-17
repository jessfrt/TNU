from nltk.corpus import sentiwordnet as swn
def valence(word: str) -> float:
    synsets = list(swn.senti_synsets(word))
    if not synsets:
        return 0.5
    pos = sum(s.pos_score() for s in synsets) / len(synsets)
    neg = sum(s.neg_score() for s in synsets) / len(synsets)
    return round(0.5 + pos - neg, 3)

