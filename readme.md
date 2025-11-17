## How to Navigate This Code Base

This repo contains data, analysis notebooks, and scripts for a digital humanities comparison of Kendrick Lamar and Drake.

### Top-level files
- **`analysis.ipynb`**: Main exploratory analysis of lyrics, word counts, and comparisons.
- **`emotion_analysis.ipynb`**: Emotion and sentiment-focused analysis and visualizations.
- **`build_song_similarity_graph.py`**: Script to build the song similarity graph (uses emotion/sentiment features).
- **`graph_analysis.ipynb`**: Follow-up analysis of the similarity graph structure.
- **`ltrial.py`** / **`fix_poorly_extracted.py`** / **`retry_not_found.py`** / **`scrapper*.py`**: Utility and scraping/cleanup scripts used to assemble and repair the dataset.

### Data files
- **`drake_kendrick_lyrics.csv`**: Core dataset of lyrics used across notebooks.
- **`drake_kendrick_lyrics_with_emotions.csv`**: Lyrics plus per-line/per-song emotion annotations.
- **`drake_word_counts.csv`** / **`kendrick_word_counts.csv`**: Pre-computed word frequency tables by artist.
- **`sentiment_results.csv`**: Sentiment model outputs.
- **`song_nodes_emotion_space.csv`** / **`song_edges_emotion_similarity.csv`**: Node and edge tables for the emotion/similarity graph.
- **`all_emotions.json`**: Large JSON with detailed emotion model outputs (used by graph/analysis scripts).

### Artist-specific raw text
- **`drake/all_songs.txt`**: Raw combined Drake lyrics.
- **`goat/all_songs.txt`**: Raw combined Kendrick (GOAT) lyrics.
- **`drake_meta_text.txt`** / **`kendrick_meta_text.txt`**: Drake or Kendrick lyrics split into individual words

### Metadata from external API
- **`output_metadata/`**: JSON metadata for Drake songs.
  - **`drake-only/`**: Drake solo tracks.
  - **`drake-features/`**: Drake as a feature.
  - **`drake-not-found/`**: Requests where metadata could not be matched.
- **`output_metadata_goat/`**: JSON metadata for Kendrick (GOAT) songs, with a similar structure.

These folders are mainly inputs to analysis, not edited by hand.

### Visualizations
- **`viz/`**: Exported figures used in the write-up (e.g., word clouds, emotion radar charts, graph visualizations).

### Typical entry points
- **For understanding the project**: Start with `analysis.ipynb`, then open `emotion_analysis.ipynb`.
- **For graph-related work**: Read `build_song_similarity_graph.py`, then `graph_analysis.ipynb`.
- **For data provenance or scraping logic**: Inspect `scrapper.py`, `scrapperLamar.py`, and the `output_metadata*` directories.


