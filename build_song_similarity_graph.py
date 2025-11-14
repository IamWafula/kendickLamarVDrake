import pandas as pd
import numpy as np
from pathlib import Path


EMOTION_COLS = [
    "anger_score",
    "disgust_score",
    "fear_score",
    "joy_score",
    "neutral_score",
    "sadness_score",
    "surprise_score",
]


def load_lyrics_with_emotions(csv_path: Path) -> pd.DataFrame:
    """Load the per-line lyric emotions CSV."""
    df = pd.read_csv(csv_path)

    missing = [c for c in EMOTION_COLS + ["artist", "title", "label", "score"] if c not in df.columns]
    if missing:
        raise ValueError(f"Missing expected columns in {csv_path}: {missing}")

    return df


def compute_song_level_stats(df: pd.DataFrame) -> pd.DataFrame:
    """Aggregate line-level emotions and sentiment to song-level."""
    # Signed sentiment: positive lines get +score, negative get -score
    signed_sentiment = df["score"].where(df["label"] == "POSITIVE", -df["score"])
    df = df.copy()
    df["signed_sentiment"] = signed_sentiment

    group_cols = ["artist", "title"]

    emotion_means = df.groupby(group_cols)[EMOTION_COLS].mean()
    sentiment_mean = df.groupby(group_cols)["signed_sentiment"].mean().rename("avg_sentiment_score")

    song_stats = pd.concat([emotion_means, sentiment_mean], axis=1).reset_index()
    return song_stats


def build_nodes_df(song_stats: pd.DataFrame) -> pd.DataFrame:
    """Create node table for Gephi."""
    nodes = song_stats.copy()
    nodes["id"] = nodes["artist"] + " - " + nodes["title"]
    nodes["label"] = nodes["title"]

    cols = ["id", "label", "artist", "avg_sentiment_score"] + EMOTION_COLS
    return nodes[cols]


def compute_cosine_similarity_matrix(X: np.ndarray) -> np.ndarray:
    """Compute cosine similarity matrix for rows of X."""
    # Normalize rows to unit length
    norms = np.linalg.norm(X, axis=1, keepdims=True)
    # Avoid division by zero
    norms[norms == 0] = 1.0
    X_norm = X / norms
    # Cosine similarity is dot product of normalized vectors
    return np.dot(X_norm, X_norm.T)


def build_edges_df(song_stats: pd.DataFrame, threshold: float = 0.7) -> pd.DataFrame:
    """
    Create edge list where edge weight is cosine similarity over emotion vectors.

    Only cross-artist edges are created (Drake–Kendrick), not within-artist edges.
    """
    X = song_stats[EMOTION_COLS].to_numpy(dtype=float)
    sim = compute_cosine_similarity_matrix(X)

    ids = (song_stats["artist"] + " - " + song_stats["title"]).tolist()
    artists = song_stats["artist"].tolist()

    sources = []
    targets = []
    weights = []

    n = len(ids)
    for i in range(n):
        for j in range(i + 1, n):
            # Skip same-artist pairs; we only want Drake–Kendrick similarities
            if artists[i] == artists[j]:
                continue
            w = float(sim[i, j])
            if w >= threshold:
                sources.append(ids[i])
                targets.append(ids[j])
                weights.append(w)

    return pd.DataFrame({"source": sources, "target": targets, "weight": weights})


def main():
    root = Path(__file__).resolve().parent
    input_csv = root / "drake_kendrick_lyrics_with_emotions.csv"

    df = load_lyrics_with_emotions(input_csv)
    song_stats = compute_song_level_stats(df)

    nodes_df = build_nodes_df(song_stats)
    edges_df = build_edges_df(song_stats, threshold=0.99)

    nodes_out = root / "song_nodes_emotion_space.csv"
    edges_out = root / "song_edges_emotion_similarity.csv"

    nodes_df.to_csv(nodes_out, index=False)
    edges_df.to_csv(edges_out, index=False)

    print(f"Wrote nodes to: {nodes_out}")
    print(f"Wrote edges to: {edges_out}")


if __name__ == "__main__":
    main()


