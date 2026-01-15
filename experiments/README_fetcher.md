# Comprehensive Ethics Corpus Fetcher

A production-ready Python tool for building cross-cultural ethics corpora from the world's best open-access text repositories.

## 📚 Supported Sources (10 total)

### REST APIs (Live Fetch)
| Source | Content | Est. Passages | API |
|--------|---------|---------------|-----|
| **Sefaria** | Hebrew/Jewish texts (Mishnah, Talmud, Pirkei Avot) | ~50,000 | sefaria.org |
| **CourtListener** | US Case Law (SCOTUS, Circuit Courts) | ~10,000 | courtlistener.com |
| **AlQuran Cloud** | Quran (114 surahs, multiple translations) | ~6,000 | api.alquran.cloud |
| **Hadith API** | Prophetic traditions (Bukhari, Muslim, Abu Dawud) | ~10,000 | cdn.jsdelivr.net |
| **Bhagavad Gita API** | Hindu scripture (700 verses, Sanskrit + translations) | ~700 | vedicscriptures.github.io |
| **Bible API** | Christian scriptures (multiple translations) | ~1,000 | bible-api.com |

### GitHub Repos (Clone/Download)
| Source | Content | Est. Passages | Repository |
|--------|---------|---------------|------------|
| **Perseus/Scaife** | Greek/Latin classics (Aristotle, Plato, Stoics) | ~20,000 | github.com/PerseusDL |
| **CBETA** | Chinese Buddhist Canon (Tripitaka) | ~30,000 | github.com/cltk/cbeta |
| **SuttaCentral** | Pali Canon (Theravada Buddhism) | ~10,000 | github.com/suttacentral |
| **GRETIL** | Göttingen Sanskrit texts (Vedas, Upanishads) | ~5,000 | gretil.sub.uni-goettingen.de |

### Embedded Samples (No Network Required)
| Source | Content | Passages |
|--------|---------|----------|
| Chinese Text | Confucian Analects, Tao Te Ching | 5 |
| Perseus | Aristotle, Plato, Stoics | 8 |
| Buddhist | Pali Canon, Dhammapada | 5 |
| Hindu | Upanishads | 5 |
| Roman Law | Justinian's Digest | 10 |

**Total Estimated Yield: ~130,000+ passages** (with full API access)

## 🚀 Quick Start

### Requirements
```bash
pip install requests beautifulsoup4 lxml tqdm gitpython
```

### Basic Usage

```bash
# Fetch from all sources (takes 4-8 hours with full API access)
python comprehensive_fetcher.py --all

# Fetch specific sources
python comprehensive_fetcher.py --sefaria --perseus --buddhist

# Quick test with limited passages
python comprehensive_fetcher.py --all --limit 100

# Resume interrupted fetch
python comprehensive_fetcher.py --all --resume
```

### Available Flags

| Flag | Description |
|------|-------------|
| `--all` | Fetch from all sources |
| `--sefaria` | Hebrew/Jewish texts |
| `--courtlistener` | US Case Law |
| `--islamic` | Quran & Hadith |
| `--chinese` | Confucian/Taoist texts |
| `--perseus` | Greek/Roman philosophy |
| `--buddhist` | Pali Canon |
| `--hindu` | Gita/Upanishads |
| `--bible` | Christian scriptures |
| `--roman-law` | Justinian's Digest |
| `--limit N` | Limit passages per source |
| `--output DIR` | Output directory (default: ./corpus) |
| `--rate-limit N` | Seconds between requests (default: 1.0) |
| `--resume` | Resume interrupted fetch |

## 🔑 API Keys

### Required for Full Access

**CourtListener** (free):
```bash
# Sign up at https://www.courtlistener.com/sign-in/
export COURTLISTENER_API_KEY="your-key-here"
```

**Chinese Text Project** (optional, for full ctext.org access):
```bash
# Sign up at https://ctext.org
export CTEXT_API_KEY="your-key-here"
```

## 📁 Output Structure

```
corpus/
├── sefaria/
│   └── passages.json
├── courtlistener/
│   └── passages.json
├── islamic/
│   └── passages.json
├── chinese/
│   └── passages.json
├── perseus/
│   └── passages.json
├── buddhist/
│   └── passages.json
├── hindu/
│   └── passages.json
├── bible/
│   └── passages.json
├── roman_law/
│   └── passages.json
├── combined_corpus.json    # All passages combined
└── corpus_stats.json       # Statistics
```

## 📊 Passage Schema

Each passage is a JSON object:

```json
{
  "id": "sefaria:Pirkei_Avot.1",
  "source": "sefaria",
  "ref": "Pirkei Avot 1",
  "title": "Pirkei Avot",
  "text_original": "משה קיבל תורה מסיני...",
  "text_english": "Moses received the Torah from Sinai...",
  "language": "he",
  "category": "ethics",
  "subcategory": "mishnah",
  "date_composed": "200 CE",
  "metadata": {
    "sefaria_url": "https://www.sefaria.org/Pirkei_Avot.1"
  }
}
```

## 🎯 SQND Integration

This corpus is designed for SQND (Semantic Quadrant Navigation of Deontics) analysis:

1. **Run fetcher** to build corpus
2. **Feed to SQND analyzer** for gate detection
3. **Generate baseline EM** from cross-cultural patterns

```python
from baseline_em_generator import BaselineEMGenerator
import json

# Load fetched corpus
with open("corpus/combined_corpus.json") as f:
    passages = json.load(f)

# Generate baseline
generator = BaselineEMGenerator()
baseline = generator.generate_from_corpus(passages)
```

## 📖 Source Documentation

### Sefaria API
- Base: `https://www.sefaria.org/api/`
- Docs: https://www.sefaria.org/developers
- Key endpoints: `/v3/texts/{ref}`, `/api/shape/{title}`, `/api/related/{ref}`

### CourtListener API
- Base: `https://www.courtlistener.com/api/rest/v4/`
- Docs: https://www.courtlistener.com/help/api/
- Key endpoints: `/search/`, `/opinions/{id}/`, `/clusters/{id}/`

### AlQuran Cloud API
- Base: `https://api.alquran.cloud/v1/`
- Docs: https://alquran.cloud/api
- No authentication required

### Hadith API
- Base: `https://cdn.jsdelivr.net/gh/fawazahmed0/hadith-api@1/`
- Source: github.com/fawazahmed0/hadith-api
- No authentication required

### Bible API
- Base: `https://bible-api.com/`
- No authentication required
- Format: `/{book}+{chapter}:{verse}-{verse}`

## ⚠️ Rate Limits & Ethics

- **Respect rate limits**: Default 1 second between requests
- **Cache responses**: Fetcher caches to `./cache/` directory
- **Attribute sources**: All passages retain source metadata
- **Non-commercial use**: Some APIs require attribution

## 🤝 Contributing

To add new sources:

1. Create a new `XxxFetcher` class in `comprehensive_fetcher.py`
2. Implement `fetch_all() -> List[Passage]`
3. Add to `main()` argument parser and fetch loop
4. Update this README

## 📜 License

MIT License. Individual corpus sources retain their original licenses.

---

*Part of the SQND Ethics Module Research Project*
