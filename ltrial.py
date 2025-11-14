from lyricsgenius import Genius

# secret : V3AKEc_EBx5HlEfpe551Be7bvIPI8oSBovoBVPhzGcTHkR5twT_oFu98B3Xzb9hqrazkVJxa-Frjfl_IHY1tEg
# id : -w80Krlziz9Dp0u17u1nXSlgC67jXjOAPoISmpsMSy1R5-bfJqpsxXkg3wq26Cxs

genius = Genius("wKsz3ReEb5PkczRIUXr9stXPRb3PyvkqZX6XHoE4Ffcze404s_n4mCeM0-dU9tdR")
artist = genius.search_artist('Drake')
artist.save_lyrics()