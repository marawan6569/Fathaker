Mutashabihat helps identify and explore similar phrases across Ayahs in the Quran. These similar phrases often reflect similarities in meaning, context, or wording, providing deeper insights into thematic connections and Quranic expression.

For those memorizing the Quran, this data is especially valuable. Many Ayahs in the Quran share nearly identical openings, endings, or similar phrases, which can be confusing during memorization and revision. Showing similar phrases across Ayahs can help learners compare them more effectively and avoid confusion during memorization. Mutashabihat not only reduces mistakes but also strengthens long-term retention by reinforcing subtle differences and patterns.

⚠️ You need Word by Word Quran script to render and highlight phrases. Download it here

Mutashabihat data format
The ZIP file contains two JSON files:

phrases.json: A list of all shared phrases
phrase_verses.json: A mapping of each Ayah to the phrase IDs
phrases.json format and sample data
"50": {
  "surahs": 32,
  "ayahs": 70,
  "count": 71,
  "source": {
    "key": "2:23",
    "from": 15,
    "to": 17
  },
  "ayah": {
    "19:48": [
      [4, 6]
    ],
    "2:23": [
      [15, 17]
    ]
  }
}
key key is the phrase ID (50 is this case)
surahs: Number of Surahs where this phrase appears
ayahs: Number of Ayahs containing this phrase
count: Total number of times the phrase occurs
source: The original Ayah and word range where this phrase is defined
ayah: List of Ayahs containing this phrase, key in this object is the ayah key in surah:ayah format and value is word range in ayah, these words should be highlighted while showing this phrase.
phrase_verses.json format and sample data

  "2:23": [50, 16379]

Key: Ayah key in the surah:ayah format
Value: List of phrase IDs that appear in this Ayah
️How to Highlight Shared Phrases
To highlight phrases in a given Ayah:

Use phrase_verses.json to get phrase IDs for the Ayah
Look up each phrase ID in phrases.json
Get the word ranges for the current Ayah (e.g., [4,6] means words 4 to 6)
Apply styling (e.g., background color) to those word indices in the Ayah
️Example Rendering Logic (pseudo code)
// Required: Load phrases.json, phrase_verses.json, and Quran words data

const phraseVerses = /* loaded from phrase_verses.json */;
const phrases = /* loaded from phrases.json */;
const quranWords = /* word-level Quran script, e.g., { "2:23": ["word1", "word2", ...] } */;

function getPhraseColor(phraseId) {
  // generate phrase color
}

function renderAyahWithPhrases(ayahKey) {
  const words = quranWords[ayahKey];
  const phraseIds = phraseVerses[ayahKey] || [];
  const highlights = [];

  phraseIds.forEach((phraseId) => {
    const phrase = phrases[phraseId];
    const ranges = phrase.ayah[ayahKey] || [];

    ranges.forEach(([start, end]) => {
      for (let i = start - 1; i <= end - 1; i++) {
        highlights[i] = getPhraseColor(phraseId);
      }
    });
  });

  // Render each word with optional highlight
  return words
    .map((word, i) => {
      const color = highlights[i];
      return color
        ? `<span style="background-color: ${color}; padding: 0 4px;">${word}</span>`
        : word;
    })
    .join(" ");
}

const html = renderAyahWithPhrases("2:23");
document.getElementById("ayah").innerHTML = html;
