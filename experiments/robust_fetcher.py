#!/usr/bin/env python3
"""
Robust Ethics Corpus Fetcher v2
===============================

Simpler, more robust approach:
1. Probe endpoints before fetching
2. Handle failures gracefully
3. Use working patterns only

Usage:
    python robust_fetcher.py --all
    python robust_fetcher.py --all --limit 100
"""

import argparse
import json
import logging
import os
import sys
import time
import re
from dataclasses import dataclass, asdict, field
from datetime import datetime
from pathlib import Path
from typing import List, Dict, Any, Optional

# Windows fix
if sys.platform == 'win32':
    try:
        import io
        sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')
        sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8', errors='replace')
    except:
        pass

import requests
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(sys.stdout),
        logging.FileHandler('robust_fetcher.log', encoding='utf-8', errors='replace')
    ]
)
logger = logging.getLogger(__name__)


@dataclass
class Passage:
    id: str
    source: str
    ref: str
    title: str
    text_original: str
    text_english: str
    language: str
    category: str
    subcategory: str
    date_composed: str
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass 
class Config:
    output_dir: str = "./corpus"
    rate_limit: float = 1.0
    limit_per_source: Optional[int] = None
    max_items: int = 200


class Client:
    def __init__(self, config: Config):
        self.config = config
        self.session = requests.Session()
        retry = Retry(total=3, backoff_factor=1, status_forcelist=[500, 502, 503, 504])
        self.session.mount("http://", HTTPAdapter(max_retries=retry))
        self.session.mount("https://", HTTPAdapter(max_retries=retry))
        self.session.headers['User-Agent'] = 'EthicsCorpusFetcher/7.0'
        self.last_req = 0.0
        self.cache_dir = Path(config.output_dir) / ".cache"
        self.cache_dir.mkdir(parents=True, exist_ok=True)
    
    def get(self, url: str, use_cache: bool = True) -> Optional[Any]:
        # Check cache
        cache_key = re.sub(r'[^\w\-.]', '_', url)[:150]
        cache_path = self.cache_dir / f"{cache_key}.json"
        
        if use_cache and cache_path.exists():
            try:
                return json.loads(cache_path.read_text(encoding='utf-8'))
            except:
                pass
        
        # Rate limit
        wait = self.config.rate_limit - (time.time() - self.last_req)
        if wait > 0:
            time.sleep(wait)
        self.last_req = time.time()
        
        try:
            r = self.session.get(url, timeout=30)
            if r.status_code == 429:  # Rate limited
                time.sleep(5)
                r = self.session.get(url, timeout=30)
            
            if r.status_code != 200:
                return None
            
            data = r.json()
            
            # Cache it
            if use_cache:
                try:
                    cache_path.write_text(json.dumps(data, ensure_ascii=False), encoding='utf-8')
                except:
                    pass
            
            return data
        except:
            return None


def flatten_text(obj: Any, max_len: int = 10000) -> str:
    """Extract text from any structure"""
    if obj is None:
        return ""
    if isinstance(obj, str):
        return obj[:max_len]
    if isinstance(obj, list):
        parts = [flatten_text(x, max_len // max(len(obj), 1)) for x in obj[:50]]
        return " ".join(p for p in parts if p)[:max_len]
    if isinstance(obj, dict):
        for key in ['text', 'content', 'body', 'slok', 'verse', 'he', 'en', 'english', 'translation']:
            if key in obj:
                result = flatten_text(obj[key], max_len)
                if result:
                    return result
        parts = [flatten_text(v, max_len) for v in obj.values() if isinstance(v, str)]
        return " ".join(p for p in parts if p)[:max_len]
    return ""


def save_passages(passages: List[Passage], output_dir: Path, source: str):
    """Save passages to JSON"""
    out_dir = output_dir / source
    out_dir.mkdir(parents=True, exist_ok=True)
    out_file = out_dir / "passages.json"
    out_file.write_text(
        json.dumps([asdict(p) for p in passages], indent=2, ensure_ascii=False),
        encoding='utf-8'
    )


# =============================================================================
# SEFARIA
# =============================================================================

def fetch_sefaria(client: Client, config: Config) -> List[Passage]:
    logger.info("[SEFARIA] Fetching Jewish texts...")
    
    BASE = "https://www.sefaria.org/api"
    passages = []
    
    # Get index and extract titles
    index = client.get(f"{BASE}/index")
    if not index:
        logger.warning("  Cannot fetch index")
        return passages
    
    # Extract all titles
    titles = []
    def find_titles(node):
        if isinstance(node, dict):
            if 'title' in node and isinstance(node['title'], str):
                titles.append(node['title'])
            for v in node.values():
                find_titles(v)
        elif isinstance(node, list):
            for item in node:
                find_titles(item)
    find_titles(index)
    
    # Filter to ethics-relevant
    keywords = ['avot', 'bava', 'sanhedrin', 'nedarim', 'shevuot', 'gittin', 
                'ketubot', 'kiddushin', 'ethics', 'musar', 'mishnah']
    relevant = [t for t in titles if any(k in t.lower() for k in keywords)][:30]
    
    logger.info(f"  Found {len(relevant)} relevant texts")
    
    for title in relevant:
        if config.limit_per_source and len(passages) >= config.limit_per_source:
            break
        
        safe_title = title.replace(' ', '_')
        
        # Get shape to know how many sections
        shape = client.get(f"{BASE}/shape/{safe_title}")
        num_sections = len(shape) if isinstance(shape, list) else 10
        num_sections = min(num_sections, config.max_items)
        
        text_count = 0
        for sec in range(1, num_sections + 1):
            if config.limit_per_source and len(passages) >= config.limit_per_source:
                break
            
            data = client.get(f"{BASE}/v3/texts/{safe_title}.{sec}")
            if not data:
                continue
            
            # Extract text from versions
            he_text = ""
            en_text = ""
            
            versions = data.get('versions', [])
            for v in versions:
                if isinstance(v, dict):
                    lang = v.get('language', '')
                    text = flatten_text(v.get('text', ''))
                    if lang == 'he' and not he_text:
                        he_text = text
                    elif lang == 'en' and not en_text:
                        en_text = text
            
            if not he_text and not en_text:
                continue
            
            passages.append(Passage(
                id=f"sefaria:{safe_title}.{sec}",
                source="sefaria",
                ref=data.get('ref', f"{title} {sec}"),
                title=title,
                text_original=he_text[:5000],
                text_english=en_text[:5000] if en_text else he_text[:5000],
                language="he",
                category="jewish",
                subcategory=title.split()[0].lower() if ' ' in title else title.lower(),
                date_composed="Talmudic",
                metadata={"section": sec}
            ))
            text_count += 1
        
        if text_count:
            logger.info(f"    {title}: {text_count} sections")
    
    save_passages(passages, Path(config.output_dir), "sefaria")
    logger.info(f"  [DONE] Sefaria: {len(passages)} total")
    return passages


# =============================================================================
# QURAN
# =============================================================================

def fetch_quran(client: Client, config: Config) -> List[Passage]:
    logger.info("[QURAN] Fetching Quran...")
    
    BASE = "https://api.alquran.cloud/v1"
    passages = []
    
    for surah in range(1, 115):
        if config.limit_per_source and len(passages) >= config.limit_per_source:
            break
        
        data = client.get(f"{BASE}/surah/{surah}/editions/quran-uthmani,en.sahih")
        
        if not data or data.get('code') != 200:
            continue
        
        editions = data.get('data', [])
        if len(editions) < 2:
            continue
        
        ar_data, en_data = editions[0], editions[1]
        name = ar_data.get('englishName', f'Surah {surah}')
        ar_ayahs = ar_data.get('ayahs', [])
        en_ayahs = en_data.get('ayahs', [])
        
        # Chunk into passages
        for i in range(0, len(ar_ayahs), 10):
            ar_chunk = ar_ayahs[i:i+10]
            en_chunk = en_ayahs[i:i+10] if i < len(en_ayahs) else []
            
            ar_text = " ".join(a.get('text', '') for a in ar_chunk)
            en_text = " ".join(a.get('text', '') for a in en_chunk)
            
            start = ar_chunk[0].get('numberInSurah', 1) if ar_chunk else 1
            end = ar_chunk[-1].get('numberInSurah', 1) if ar_chunk else 1
            
            passages.append(Passage(
                id=f"quran:{surah}:{start}-{end}",
                source="quran",
                ref=f"Quran {surah}:{start}-{end}",
                title=name,
                text_original=ar_text,
                text_english=en_text,
                language="ar",
                category="scripture",
                subcategory="quran",
                date_composed="610-632 CE",
                metadata={"surah": surah}
            ))
    
    save_passages(passages, Path(config.output_dir), "quran")
    logger.info(f"  [DONE] Quran: {len(passages)} passages")
    return passages


# =============================================================================
# HADITH - Probe-first approach
# =============================================================================

def fetch_hadith(client: Client, config: Config) -> List[Passage]:
    logger.info("[HADITH] Probing for working collections...")
    
    BASE = "https://cdn.jsdelivr.net/gh/fawazahmed0/hadith-api@1"
    passages = []
    
    # Collections to try
    to_try = [
        "eng-bukhari", "eng-muslim", "eng-abudawud", 
        "eng-tirmidhi", "eng-nasai", "eng-ibnmajah"
    ]
    
    # Probe each to find working ones
    working = []
    for coll in to_try:
        test = client.get(f"{BASE}/editions/{coll}/1.json")
        if test and 'hadiths' in test:
            working.append(coll)
            logger.info(f"    Found working: {coll}")
    
    if not working:
        logger.warning("  No working collections found")
        return passages
    
    logger.info(f"  {len(working)} collections available")
    
    # Fetch from each
    for coll in working:
        if config.limit_per_source and len(passages) >= config.limit_per_source:
            break
        
        name = coll.replace('eng-', '').replace('-', ' ').title()
        count = 0
        failures = 0
        
        for num in range(1, config.max_items + 1):
            if config.limit_per_source and len(passages) >= config.limit_per_source:
                break
            
            data = client.get(f"{BASE}/editions/{coll}/{num}.json")
            
            if not data:
                failures += 1
                if failures >= 5:
                    break
                continue
            
            failures = 0
            
            # Extract text
            hadiths = data.get('hadiths', [])
            if not hadiths:
                continue
            
            text = hadiths[0].get('text', '') if isinstance(hadiths[0], dict) else ''
            if not text or len(text) < 20:
                continue
            
            passages.append(Passage(
                id=f"hadith:{coll}:{num}",
                source="hadith",
                ref=f"{name} #{num}",
                title=name,
                text_original=text,
                text_english=text,
                language="en",
                category="hadith",
                subcategory=coll,
                date_composed="~850 CE",
                metadata={"number": num}
            ))
            count += 1
        
        logger.info(f"    {name}: {count} hadiths")
    
    save_passages(passages, Path(config.output_dir), "hadith")
    logger.info(f"  [DONE] Hadith: {len(passages)} total")
    return passages


# =============================================================================
# BIBLE - Probe-first approach
# =============================================================================

def fetch_bible(client: Client, config: Config) -> List[Passage]:
    logger.info("[BIBLE] Probing API and fetching...")
    
    BASE = "https://bible-api.com"
    passages = []
    
    # Test which book format works
    books_to_try = [
        ("genesis", 50), ("exodus", 40), ("leviticus", 27),
        ("deuteronomy", 34), ("psalms", 150), ("proverbs", 31),
        ("isaiah", 66), ("matthew", 28), ("mark", 16),
        ("luke", 24), ("john", 21), ("romans", 16),
        ("1 corinthians", 16), ("galatians", 6), ("james", 5),
        ("1 john", 5),
    ]
    
    for book, max_ch in books_to_try:
        if config.limit_per_source and len(passages) >= config.limit_per_source:
            break
        
        book_count = 0
        failures = 0
        
        for ch in range(1, min(max_ch + 1, config.max_items)):
            if config.limit_per_source and len(passages) >= config.limit_per_source:
                break
            
            # Try different URL formats
            url = f"{BASE}/{book.replace(' ', '+')}+{ch}"
            data = client.get(url)
            
            if not data:
                failures += 1
                if failures >= 3:
                    break
                continue
            
            failures = 0
            
            text = data.get('text', '')
            if not text:
                continue
            
            ref = data.get('reference', f"{book.title()} {ch}")
            
            passages.append(Passage(
                id=f"bible:{book.replace(' ', '_')}:{ch}",
                source="bible",
                ref=ref,
                title=book.title(),
                text_original=text,
                text_english=text,
                language="en",
                category="scripture",
                subcategory="bible",
                date_composed="Various",
                metadata={"book": book, "chapter": ch}
            ))
            book_count += 1
        
        if book_count:
            logger.info(f"    {book.title()}: {book_count} chapters")
    
    save_passages(passages, Path(config.output_dir), "bible")
    logger.info(f"  [DONE] Bible: {len(passages)} total")
    return passages


# =============================================================================
# GITA
# =============================================================================

def fetch_gita(client: Client, config: Config) -> List[Passage]:
    logger.info("[GITA] Fetching Bhagavad Gita...")
    
    BASE = "https://vedicscriptures.github.io"
    passages = []
    
    # Get chapter count
    chapters = client.get(f"{BASE}/chapters")
    num_ch = len(chapters) if isinstance(chapters, list) else 18
    
    logger.info(f"  {num_ch} chapters found")
    
    for ch in range(1, min(num_ch + 1, 19)):
        if config.limit_per_source and len(passages) >= config.limit_per_source:
            break
        
        ch_data = client.get(f"{BASE}/chapter/{ch}.json")
        if not ch_data:
            continue
        
        ch_name = ch_data.get('name', ch_data.get('translation', f'Chapter {ch}'))
        verses_count = ch_data.get('verses_count', 50)
        
        ch_count = 0
        for v in range(1, min(verses_count + 1, config.max_items)):
            if config.limit_per_source and len(passages) >= config.limit_per_source:
                break
            
            verse = client.get(f"{BASE}/slok/{ch}/{v}.json")
            if not verse:
                continue
            
            # Get Sanskrit
            sanskrit = verse.get('slok', verse.get('verse', ''))
            
            # Get English from commentators
            english = ""
            for comm in ['tej', 'spitr', 'purohit', 'chinmay', 'adi', 'gambir', 'sivananda']:
                if comm in verse and isinstance(verse[comm], dict):
                    english = verse[comm].get('et', verse[comm].get('english', ''))
                    if english:
                        break
            
            if not sanskrit and not english:
                continue
            
            passages.append(Passage(
                id=f"gita:{ch}:{v}",
                source="gita",
                ref=f"Bhagavad Gita {ch}.{v}",
                title=ch_name,
                text_original=sanskrit if sanskrit else english,
                text_english=english if english else sanskrit,
                language="sa",
                category="scripture",
                subcategory="gita",
                date_composed="~200 BCE",
                metadata={"chapter": ch, "verse": v}
            ))
            ch_count += 1
        
        logger.info(f"    Chapter {ch}: {ch_count} verses")
    
    save_passages(passages, Path(config.output_dir), "gita")
    logger.info(f"  [DONE] Gita: {len(passages)} total")
    return passages


# =============================================================================
# SUTTACENTRAL (Buddhist)
# =============================================================================

def fetch_buddhist(client: Client, config: Config) -> List[Passage]:
    logger.info("[BUDDHIST] Fetching suttas...")
    
    BASE = "https://suttacentral.net/api"
    passages = []
    
    # Try known nikayas
    for nikaya in ['dn', 'mn', 'sn', 'an']:
        if config.limit_per_source and len(passages) >= config.limit_per_source:
            break
        
        logger.info(f"  Nikaya: {nikaya.upper()}")
        
        count = 0
        failures = 0
        
        for num in range(1, config.max_items + 1):
            if config.limit_per_source and len(passages) >= config.limit_per_source:
                break
            
            sutta_id = f"{nikaya}{num}"
            
            # Get title
            plex = client.get(f"{BASE}/suttaplex/{sutta_id}")
            title = sutta_id.upper()
            if plex:
                if isinstance(plex, list) and plex:
                    plex = plex[0]
                if isinstance(plex, dict):
                    title = plex.get('translated_title') or plex.get('original_title') or title
            
            # Get text
            bilara = client.get(f"{BASE}/bilarasuttas/{sutta_id}/sujato")
            
            if not bilara:
                failures += 1
                if failures >= 5:
                    break
                continue
            
            failures = 0
            
            pali = ""
            english = ""
            
            if isinstance(bilara, dict):
                root = bilara.get('root_text', {})
                trans = bilara.get('translation_text', {})
                
                if root and isinstance(root, dict):
                    pali = " ".join(str(v) for v in root.values() if v)[:5000]
                if trans and isinstance(trans, dict):
                    english = " ".join(str(v) for v in trans.values() if v)[:5000]
            
            if not pali and not english:
                continue
            
            passages.append(Passage(
                id=f"sutta:{sutta_id}",
                source="suttacentral",
                ref=sutta_id.upper(),
                title=title,
                text_original=pali if pali else english,
                text_english=english if english else pali,
                language="pi",
                category="scripture",
                subcategory=nikaya,
                date_composed="~400 BCE",
                metadata={"nikaya": nikaya}
            ))
            count += 1
        
        logger.info(f"    {nikaya.upper()}: {count} suttas")
    
    save_passages(passages, Path(config.output_dir), "buddhist")
    logger.info(f"  [DONE] Buddhist: {len(passages)} total")
    return passages


# =============================================================================
# COURTLISTENER
# =============================================================================

def fetch_courtlistener(client: Client, config: Config) -> List[Passage]:
    logger.info("[COURTLISTENER] Searching case law...")
    
    BASE = "https://www.courtlistener.com/api/rest/v4"
    passages = []
    
    api_key = os.environ.get("COURTLISTENER_API_KEY")
    if api_key:
        client.session.headers["Authorization"] = f"Token {api_key}"
    else:
        logger.warning("  No API key - results may be limited")
    
    searches = ["contract", "negligence", "due process", "fiduciary", "fraud"]
    
    for query in searches:
        if config.limit_per_source and len(passages) >= config.limit_per_source:
            break
        
        url = f"{BASE}/search/?q={query.replace(' ', '+')}&type=o"
        
        try:
            r = client.session.get(url, timeout=30)
            data = r.json()
        except:
            continue
        
        results = data.get('results', [])
        logger.info(f"    {query}: {len(results)} results")
        
        for res in results[:20]:
            snippet = res.get('snippet', '')
            if snippet:
                snippet = re.sub(r'<[^>]+>', '', snippet)
            
            if not snippet or len(snippet) < 30:
                continue
            
            passages.append(Passage(
                id=f"cl:{res.get('id', len(passages))}",
                source="courtlistener",
                ref=res.get('caseName', 'Case'),
                title=res.get('caseName', 'Case'),
                text_original=snippet,
                text_english=snippet,
                language="en",
                category="legal",
                subcategory=query.replace(' ', '_'),
                date_composed=str(res.get('dateFiled', 'Unknown')),
                metadata={"query": query}
            ))
    
    save_passages(passages, Path(config.output_dir), "courtlistener")
    logger.info(f"  [DONE] CourtListener: {len(passages)} total")
    return passages


# =============================================================================
# EMBEDDED SAMPLES
# =============================================================================

def fetch_embedded(client: Client, config: Config) -> List[Passage]:
    logger.info("[EMBEDDED] Loading curated samples...")
    
    passages = []
    
    samples = [
        ("chinese", "Analects 12:2", "Do not do to others what you would not wish done to yourself.", "zh", "confucian"),
        ("chinese", "Analects 15:24", "Reciprocity: do not do to others what you do not want.", "zh", "confucian"),
        ("chinese", "Tao Te Ching 63", "Respond to injury with virtue.", "zh", "taoist"),
        ("greek", "Aristotle NE 1106b", "Virtue is a mean between extremes.", "grc", "aristotle"),
        ("greek", "Plato Crito 49b", "Never retaliate evil for evil.", "grc", "plato"),
        ("greek", "Epictetus Ench. 1", "Some things are in our control, others not.", "grc", "stoic"),
        ("roman", "Digest 1.1.10", "Justice is rendering each their due.", "la", "law"),
        ("roman", "Digest 1.1.10.1", "Live honestly, harm none, give each their due.", "la", "law"),
    ]
    
    for source, ref, text, lang, subcat in samples:
        passages.append(Passage(
            id=f"{source}:{ref.replace(' ', '_')}",
            source=source,
            ref=ref,
            title=ref.split()[0],
            text_original=text,
            text_english=text,
            language=lang,
            category="philosophy" if source in ["chinese", "greek"] else "legal",
            subcategory=subcat,
            date_composed="Ancient",
            metadata={"embedded": True}
        ))
    
    save_passages(passages, Path(config.output_dir), "embedded")
    logger.info(f"  [DONE] Embedded: {len(passages)} samples")
    return passages


# =============================================================================
# COMBINE
# =============================================================================

def combine_corpus(config: Config) -> Dict:
    output_dir = Path(config.output_dir)
    all_passages = []
    stats = {"sources": {}}
    
    for d in output_dir.iterdir():
        if d.is_dir() and not d.name.startswith('.'):
            f = d / "passages.json"
            if f.exists():
                data = json.loads(f.read_text(encoding='utf-8'))
                all_passages.extend(data)
                stats["sources"][d.name] = len(data)
    
    stats["total"] = len(all_passages)
    stats["timestamp"] = datetime.now().isoformat()
    
    (output_dir / "combined_corpus.json").write_text(
        json.dumps(all_passages, indent=2, ensure_ascii=False), encoding='utf-8')
    (output_dir / "corpus_stats.json").write_text(
        json.dumps(stats, indent=2), encoding='utf-8')
    
    logger.info(f"\n{'='*50}")
    logger.info(f"CORPUS COMPLETE: {stats['total']} passages")
    logger.info(f"{'='*50}")
    for src, cnt in sorted(stats["sources"].items(), key=lambda x: -x[1]):
        logger.info(f"  {src}: {cnt}")
    
    return stats


# =============================================================================
# MAIN
# =============================================================================

def main():
    parser = argparse.ArgumentParser(description="Robust Ethics Corpus Fetcher")
    parser.add_argument("--all", action="store_true")
    parser.add_argument("--sefaria", action="store_true")
    parser.add_argument("--quran", action="store_true")
    parser.add_argument("--hadith", action="store_true")
    parser.add_argument("--bible", action="store_true")
    parser.add_argument("--gita", action="store_true")
    parser.add_argument("--buddhist", action="store_true")
    parser.add_argument("--courtlistener", action="store_true")
    parser.add_argument("--embedded", action="store_true")
    parser.add_argument("--limit", type=int)
    parser.add_argument("--output", default="./corpus")
    
    args = parser.parse_args()
    
    if not any([args.all, args.sefaria, args.quran, args.hadith, args.bible,
                args.gita, args.buddhist, args.courtlistener, args.embedded]):
        parser.print_help()
        return
    
    config = Config(output_dir=args.output, limit_per_source=args.limit)
    Path(config.output_dir).mkdir(parents=True, exist_ok=True)
    client = Client(config)
    
    print("=" * 60)
    print("ROBUST ETHICS CORPUS FETCHER")
    print("=" * 60)
    
    if args.all or args.sefaria: fetch_sefaria(client, config)
    if args.all or args.quran: fetch_quran(client, config)
    if args.all or args.hadith: fetch_hadith(client, config)
    if args.all or args.bible: fetch_bible(client, config)
    if args.all or args.gita: fetch_gita(client, config)
    if args.all or args.buddhist: fetch_buddhist(client, config)
    if args.all or args.courtlistener: fetch_courtlistener(client, config)
    if args.all or args.embedded: fetch_embedded(client, config)
    
    combine_corpus(config)
    print(f"\nOutput: {config.output_dir}/combined_corpus.json")


if __name__ == "__main__":
    main()
