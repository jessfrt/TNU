import pandas as pd

def find_concept_gaps(csv_path):
    df = pd.read_csv(csv_path)

    # garantir texto limpo
    df["concept"] = df["concept"].astype(str).str.strip()

    # converter center para número
    df["center"] = pd.to_numeric(df["center"], errors="coerce")

    # manter só linhas válidas do bloco de conceitos
    df = df.dropna(subset=["center"])
    df = df[~df["concept"].str.contains("↔", na=False)]
    df = df[~df["concept"].isin(["all", "Separation", "summary"])]

    # ordenar pelo centro
    df = df.sort_values(by="center")

    centers = df["center"].tolist()
    concepts = df["concept"].tolist()

    gaps = []

    for i in range(len(centers) - 1):
        left = centers[i]
        right = centers[i + 1]

        gap_size = right - left
        midpoint = (left + right) / 2

        gaps.append({
            "between": f"{concepts[i]} ↔ {concepts[i+1]}",
            "gap": round(gap_size, 6),
            "suggested_point": round(midpoint, 6)
        })

    gaps = sorted(gaps, key=lambda x: x["gap"], reverse=True)

    return df, gaps


if __name__ == "__main__":
    df_valid, gaps = find_concept_gaps("out/gauge_metrics_weighted_lang.csv")

    print("\n✅ CONCEITOS VÁLIDOS USADOS:\n")
    print(df_valid[["concept", "center"]].to_string(index=False))

    print("\n🔍 MAIORES LACUNAS ENTRE CONCEITOS:\n")
    for g in gaps:
        print(g)