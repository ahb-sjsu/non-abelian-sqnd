#!/usr/bin/env python3
"""
Longitudinal Ethics Corpus - Bulk Downloader
=============================================

Direct HTTP/FTP downloads instead of API calls.
Much faster, gets complete datasets.

Sources with bulk downloads:
- Reddit AITA: Pushshift dumps (torrent/HTTP)
- Gutenberg: Bulk mirrors
- Court Listener: Bulk data downloads
- Internet Archive: Direct file access
- Academic datasets: Zenodo, Kaggle, etc.

Usage:
    python bulk_downloader.py --all
    python bulk_downloader.py --reddit
    python bulk_downloader.py --list   # Show available downloads
"""

import argparse
import json
import gzip
import os
import sys
import re
from pathlib import Path
from datetime import datetime
from typing import List, Dict, Optional
from collections import defaultdict
from dataclasses import dataclass, asdict, field

# Windows fix
if sys.platform == 'win32':
    try:
        import io
        sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')
        sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8', errors='replace')
    except:
        pass

import requests

# =============================================================================
# CONFIGURATION
# =============================================================================

@dataclass
class Config:
    output_dir: str = "./longitudinal_corpus"
    chunk_size: int = 8192 * 1024  # 8MB chunks for downloads


# =============================================================================
# BULK DOWNLOAD SOURCES
# =============================================================================

BULK_SOURCES = {
    # =========================================================================
    # REDDIT AITA - Pushshift dumps
    # =========================================================================
    "reddit_aita": {
        "description": "Reddit r/AmItheAsshole (2013-2023)",
        "format": "JSONL (gzipped)",
        "size": "~2-5 GB compressed",
        "temporal_span": "2013-2023",
        "urls": [
            # Pushshift files.pushshift.io - monthly dumps
            # These are the actual Pushshift Reddit dumps
            "https://files.pushshift.io/reddit/submissions/RS_2019-01.zst",
            "https://files.pushshift.io/reddit/submissions/RS_2020-01.zst",
            # Academic Torrents mirror (more reliable)
            "https://academictorrents.com/details/7c0645c94321311bb05f7c0a5f3d0b77a1e8ed8e",
        ],
        "alt_sources": [
            # The-Eye archive
            "https://the-eye.eu/redarcs/",
            # Arctic Shift (newer Pushshift successor)
            "https://arctic-shift.photon-reddit.com/download",
        ],
        "filter": "subreddit == 'AmItheAsshole'",
        "notes": """
To download Reddit AITA data:

Option 1: Arctic Shift (recommended, recent data)
    https://arctic-shift.photon-reddit.com/
    - Select subreddit: AmItheAsshole
    - Download submissions (posts)
    - Format: JSONL

Option 2: Academic Torrents (complete historical)
    magnet:?xt=urn:btih:7c0645c94321311bb05f7c0a5f3d0b77a1e8ed8e
    - Full Pushshift Reddit dump
    - Filter for AmItheAsshole after download

Option 3: Kaggle datasets
    https://www.kaggle.com/datasets/timbaney/aita-reddit-data
    - Pre-filtered AITA data
    - CSV format, easy to use
"""
    },
    
    # =========================================================================
    # ADVICE COLUMNS - Newspaper archives
    # =========================================================================
    "advice_columns": {
        "description": "Dear Abby, Ann Landers, Miss Manners",
        "format": "Various",
        "size": "Variable",
        "temporal_span": "1956-present",
        "urls": [],  # No direct bulk download available
        "alt_sources": [
            # Newspaper archives
            "https://www.newspapers.com/",  # Subscription
            "https://chroniclingamerica.loc.gov/",  # Free, historical
            "https://news.google.com/newspapers",  # Google News Archive
        ],
        "notes": """
Advice columns require newspaper archive access:

Option 1: Chronicling America (FREE, 1789-1963)
    https://chroniclingamerica.loc.gov/
    - Search: "Dear Abby" OR "Ann Landers"
    - Download OCR text directly
    - Limited to pre-1963

Option 2: Newspapers.com (subscription, 1956-present)
    - Most complete Dear Abby archive
    - Export as text/PDF

Option 3: University library access
    - ProQuest Historical Newspapers
    - NewsBank

Option 4: Internet Archive newspaper scans
    https://archive.org/details/newspapers
"""
    },
    
    # =========================================================================
    # COURT OPINIONS - CourtListener bulk
    # =========================================================================
    "court_opinions": {
        "description": "US Court Opinions bulk data",
        "format": "JSON/XML",
        "size": "~50-100 GB total, can filter",
        "temporal_span": "1754-present",
        "urls": [
            "https://www.courtlistener.com/api/bulk-info/",
        ],
        "alt_sources": [
            # Direct bulk downloads (no API key needed for bulk)
            "https://www.courtlistener.com/api/bulk/opinions/",
            "https://com-courtlistener-storage.s3-us-west-2.amazonaws.com/bulk-data/",
            # Case.law (Harvard)
            "https://case.law/bulk/download/",
        ],
        "notes": """
Court opinions bulk downloads:

Option 1: CourtListener Bulk Data (FREE)
    https://www.courtlistener.com/api/bulk-info/
    - Download by court or jurisdiction
    - JSON format
    - No API key for bulk downloads!
    
Option 2: Case.law (Harvard Law)
    https://case.law/
    - Free account for bulk access
    - All US case law digitized
    
Option 3: RECAP Archive
    https://www.courtlistener.com/recap/
    - Federal court documents
"""
    },
    
    # =========================================================================
    # JEWISH RESPONSA - Sefaria exports
    # =========================================================================
    "responsa": {
        "description": "Jewish Responsa literature",
        "format": "JSON",
        "size": "~500 MB",
        "temporal_span": "900 CE - present",
        "urls": [
            # Sefaria has a full database export!
            "https://github.com/Sefaria/Sefaria-Export",
        ],
        "alt_sources": [
            "https://storage.googleapis.com/sefaria-export/",
        ],
        "notes": """
Sefaria full text export:

Option 1: GitHub Export (BEST)
    git clone https://github.com/Sefaria/Sefaria-Export.git
    - Complete database in JSON
    - ~1.5 GB
    - Responsa in: json/Halakhah/Responsa/

Option 2: Google Cloud Storage
    https://storage.googleapis.com/sefaria-export/
    - Same data, direct download

Filter for Responsa (Teshuvot/She'elot):
    - Rambam's Responsa
    - Rashba's Responsa  
    - Igrot Moshe
    - etc.
"""
    },
    
    # =========================================================================
    # PHILOSOPHY TEXTS - Gutenberg bulk
    # =========================================================================
    "philosophy": {
        "description": "Philosophy/Ethics texts (public domain)",
        "format": "Plain text",
        "size": "~60 GB full, ~1 GB filtered",
        "temporal_span": "Ancient - 1927",
        "urls": [
            # Gutenberg mirrors with rsync/wget access
            "https://www.gutenberg.org/robot/harvest",
            "https://www.gutenberg.org/MIRRORS.ALL",
            # Direct catalog
            "https://www.gutenberg.org/cache/epub/feeds/rdf-files.tar.bz2",
        ],
        "alt_sources": [
            # Gutenberg mirrors
            "rsync://aleph.gutenberg.org/gutenberg/",
            "ftp://ftp.ibiblio.org/pub/docs/books/gutenberg/",
            # Standard Ebooks (curated, better formatted)
            "https://standardebooks.org/bulk-downloads",
        ],
        "notes": """
Project Gutenberg bulk download:

Option 1: Wget robot access
    wget -w 2 -m -H "https://www.gutenberg.org/robot/harvest?filetypes[]=txt&langs[]=en"
    - Respects robots.txt
    - Gets all English plain text

Option 2: Rsync (fastest)
    rsync -av --del aleph.gutenberg.org::gutenberg ./gutenberg/
    - Full mirror
    - Then filter for philosophy/ethics

Option 3: Standard Ebooks (RECOMMENDED for quality)
    https://standardebooks.org/bulk-downloads
    - Curated, cleaned texts
    - Philosophy section available
    - Much smaller, higher quality

Filter by subject:
    Philosophy, Ethics, Religion, Political Science
"""
    },
    
    # =========================================================================
    # NY TIMES ETHICIST - Archive.org
    # =========================================================================
    "ethicist": {
        "description": "NY Times 'The Ethicist' column",
        "format": "HTML/Text",
        "size": "~50 MB",
        "temporal_span": "1999-present",
        "urls": [],
        "alt_sources": [
            "https://web.archive.org/web/*/nytimes.com/column/the-ethicist*",
        ],
        "notes": """
The Ethicist via Wayback Machine:

Option 1: Wayback Machine CDX API
    https://web.archive.org/cdx/search/cdx?url=nytimes.com/column/the-ethicist&output=json
    - Lists all archived URLs
    - Then fetch each snapshot

Option 2: waybackpack tool
    pip install waybackpack
    waybackpack nytimes.com/column/the-ethicist -d ./ethicist/

Option 3: NYT API (official, limited)
    https://developer.nytimes.com/
    - Article Search API
    - Query: "the ethicist"
"""
    },
    
    # =========================================================================
    # ETHICS DATASETS - Academic
    # =========================================================================
    "academic_ethics": {
        "description": "Academic ethics/moral datasets",
        "format": "CSV/JSON",
        "size": "Variable",
        "temporal_span": "Various",
        "urls": [
            # ETHICS dataset (Hendrycks et al.)
            "https://github.com/hendrycks/ethics",
            # Moral Stories
            "https://github.com/demelin/moral_stories",
            # Social Chemistry
            "https://github.com/mbforbes/social-chemistry-101",
            # Scruples
            "https://github.com/allenai/scruples",
            # Delphi
            "https://github.com/liweijiang/delphi",
        ],
        "notes": """
Pre-built ethics/moral reasoning datasets:

1. ETHICS Benchmark (Hendrycks)
   git clone https://github.com/hendrycks/ethics
   - Justice, Deontology, Virtue, Utilitarianism
   - ~130K examples

2. Moral Stories
   git clone https://github.com/demelin/moral_stories  
   - Situations + moral judgments
   - ~12K stories

3. Social Chemistry 101
   git clone https://github.com/mbforbes/social-chemistry-101
   - Rules-of-thumb from AITA
   - 292K social norms

4. Scruples (Allen AI)
   git clone https://github.com/allenai/scruples
   - Ethical dilemmas + judgments
   - From Reddit AITA

These are PERFECT for your temporal analysis if they have timestamps!
"""
    },
}


# =============================================================================
# DOWNLOADER
# =============================================================================

def download_file(url: str, dest: Path, chunk_size: int = 8192) -> bool:
    """Download a file with progress"""
    try:
        r = requests.get(url, stream=True, timeout=30)
        r.raise_for_status()
        
        total = int(r.headers.get('content-length', 0))
        downloaded = 0
        
        with open(dest, 'wb') as f:
            for chunk in r.iter_content(chunk_size=chunk_size):
                f.write(chunk)
                downloaded += len(chunk)
                if total:
                    pct = downloaded * 100 // total
                    print(f"\r  Downloading: {pct}% ({downloaded//1024//1024} MB)", end='')
        
        print()
        return True
    except Exception as e:
        print(f"  Error: {e}")
        return False


def clone_repo(url: str, dest: Path) -> bool:
    """Clone a git repository"""
    import subprocess
    try:
        subprocess.run(['git', 'clone', '--depth', '1', url, str(dest)], check=True)
        return True
    except:
        print(f"  Git clone failed. Install git or download manually from: {url}")
        return False


# =============================================================================
# HELPER SCRIPTS GENERATOR
# =============================================================================

def generate_download_scripts(config: Config):
    """Generate shell scripts for each data source"""
    
    scripts_dir = Path(config.output_dir) / "download_scripts"
    scripts_dir.mkdir(parents=True, exist_ok=True)
    
    # Reddit AITA
    (scripts_dir / "download_reddit_aita.sh").write_text("""#!/bin/bash
# Download Reddit AITA data

# Option 1: Kaggle (easiest - need kaggle CLI)
# pip install kaggle
# kaggle datasets download -d timbaney/aita-reddit-data

# Option 2: Arctic Shift (manual)
echo "Visit: https://arctic-shift.photon-reddit.com/"
echo "Select: AmItheAsshole subreddit"
echo "Download submissions"

# Option 3: Pushshift monthly dumps
# Uncomment and modify date range as needed:
# for year in 2019 2020 2021 2022 2023; do
#     for month in 01 02 03 04 05 06 07 08 09 10 11 12; do
#         wget "https://files.pushshift.io/reddit/submissions/RS_${year}-${month}.zst"
#     done
# done
# Then filter: zstdcat RS_*.zst | grep '"subreddit":"AmItheAsshole"' > aita.jsonl
""")
    
    # Sefaria/Responsa
    (scripts_dir / "download_sefaria.sh").write_text("""#!/bin/bash
# Download Sefaria texts (includes Responsa)

git clone --depth 1 https://github.com/Sefaria/Sefaria-Export.git

# Responsa are in:
# Sefaria-Export/json/Halakhah/Responsa/

echo "Done! Responsa texts are in Sefaria-Export/json/Halakhah/Responsa/"
""")
    
    # CourtListener
    (scripts_dir / "download_courtlistener.sh").write_text("""#!/bin/bash
# Download CourtListener bulk data

# Get list of available bulk files
curl -s "https://www.courtlistener.com/api/bulk-info/" | python3 -m json.tool

# Download Supreme Court opinions (example)
# wget "https://www.courtlistener.com/api/bulk/opinions/?court=scotus"

# Or use their S3 bucket directly:
# aws s3 sync s3://com-courtlistener-storage/bulk-data/ ./courtlistener/ --no-sign-request

echo "Visit https://www.courtlistener.com/api/bulk-info/ for download links"
""")
    
    # Gutenberg Philosophy
    (scripts_dir / "download_gutenberg_philosophy.sh").write_text("""#!/bin/bash
# Download philosophy texts from Project Gutenberg

# Create output directory
mkdir -p gutenberg_philosophy

# Method 1: Standard Ebooks (recommended - curated, clean)
# wget -r -np -nH --cut-dirs=2 -A "*.epub" https://standardebooks.org/ebooks/subject/philosophy

# Method 2: Specific Gutenberg texts (philosophy/ethics)
TEXTS=(
    "1497"   # Plato - Republic
    "1656"   # Plato - Apology
    "8438"   # Aristotle - Nicomachean Ethics
    "45109"  # Marcus Aurelius - Meditations
    "3794"   # Epictetus - Enchiridion
    "5684"   # Kant - Metaphysics of Morals
    "7370"   # Mill - Utilitarianism
    "3207"   # Hobbes - Leviathan
    "3800"   # Spinoza - Ethics
    "4363"   # Nietzsche - Beyond Good and Evil
)

for id in "${TEXTS[@]}"; do
    wget -nc "https://www.gutenberg.org/cache/epub/${id}/pg${id}.txt" -P gutenberg_philosophy/
    sleep 2  # Be nice to the server
done

echo "Done! Texts in gutenberg_philosophy/"
""")
    
    # Wayback Ethicist
    (scripts_dir / "download_ethicist.sh").write_text("""#!/bin/bash
# Download NY Times Ethicist via Wayback Machine

pip install waybackpack

# Download all archived versions
waybackpack "nytimes.com/column/the-ethicist" -d ./ethicist_archive/

# Or use CDX API to get URL list first:
# curl "https://web.archive.org/cdx/search/cdx?url=nytimes.com/column/the-ethicist*&output=json" > ethicist_urls.json
""")
    
    # Academic datasets
    (scripts_dir / "download_academic_ethics.sh").write_text("""#!/bin/bash
# Download academic ethics datasets

mkdir -p academic_datasets
cd academic_datasets

# ETHICS benchmark
git clone --depth 1 https://github.com/hendrycks/ethics

# Moral Stories
git clone --depth 1 https://github.com/demelin/moral_stories

# Social Chemistry (Reddit rules-of-thumb)
git clone --depth 1 https://github.com/mbforbes/social-chemistry-101

# Scruples (AITA-based)
git clone --depth 1 https://github.com/allenai/scruples

echo "Done! Check each repo for data files."
""")
    
    # Master download script
    (scripts_dir / "download_all.sh").write_text("""#!/bin/bash
# Master download script

echo "=== Longitudinal Ethics Corpus Downloader ==="
echo ""
echo "This will download several GB of data."
echo "Press Ctrl+C to cancel, Enter to continue..."
read

./download_sefaria.sh
./download_gutenberg_philosophy.sh
./download_academic_ethics.sh

echo ""
echo "=== Manual steps required ==="
echo "1. Reddit AITA: Visit https://arctic-shift.photon-reddit.com/"
echo "2. CourtListener: Visit https://www.courtlistener.com/api/bulk-info/"
echo "3. Ethicist: Run ./download_ethicist.sh (requires waybackpack)"
""")
    
    # Make executable
    for script in scripts_dir.glob("*.sh"):
        script.chmod(0o755)
    
    print(f"Download scripts generated in: {scripts_dir}")
    return scripts_dir


# =============================================================================
# DATA PROCESSORS
# =============================================================================

def process_reddit_jsonl(input_file: Path, output_dir: Path, limit: int = None):
    """Process Reddit JSONL dump into structured format"""
    
    output_dir.mkdir(parents=True, exist_ok=True)
    entries = []
    
    # Handle gzip/zstd/plain
    if str(input_file).endswith('.gz'):
        import gzip
        opener = gzip.open
    elif str(input_file).endswith('.zst'):
        try:
            import zstandard as zstd
            opener = lambda f: zstd.open(f, 'rt')
        except ImportError:
            print("Install zstandard: pip install zstandard")
            return
    else:
        opener = open
    
    with opener(input_file, 'rt', encoding='utf-8', errors='replace') as f:
        for i, line in enumerate(f):
            if limit and i >= limit:
                break
            
            try:
                post = json.loads(line)
            except:
                continue
            
            # Filter for AITA
            if post.get('subreddit', '').lower() != 'amitheasshole':
                continue
            
            title = post.get('title', '')
            selftext = post.get('selftext', '')
            
            if not selftext or selftext in ['[removed]', '[deleted]']:
                continue
            
            created = post.get('created_utc', 0)
            date = datetime.fromtimestamp(created).strftime('%Y-%m-%d') if created else None
            year = datetime.fromtimestamp(created).year if created else None
            
            entries.append({
                'id': post.get('id'),
                'date': date,
                'year': year,
                'decade': f"{(year // 10) * 10}s" if year else None,
                'title': title,
                'text': selftext[:5000],
                'score': post.get('score', 0),
                'flair': post.get('link_flair_text', ''),
                'num_comments': post.get('num_comments', 0),
            })
    
    # Save
    out_file = output_dir / "aita_processed.json"
    with open(out_file, 'w', encoding='utf-8') as f:
        json.dump(entries, f, indent=2, ensure_ascii=False)
    
    print(f"Processed {len(entries)} AITA posts -> {out_file}")
    
    # Also save by decade
    by_decade = defaultdict(list)
    for e in entries:
        if e['decade']:
            by_decade[e['decade']].append(e)
    
    for decade, items in by_decade.items():
        dec_file = output_dir / f"aita_{decade}.json"
        with open(dec_file, 'w', encoding='utf-8') as f:
            json.dump(items, f, indent=2, ensure_ascii=False)
        print(f"  {decade}: {len(items)} posts")


def process_sefaria_responsa(sefaria_dir: Path, output_dir: Path):
    """Process Sefaria export for Responsa texts"""
    
    output_dir.mkdir(parents=True, exist_ok=True)
    
    responsa_dir = sefaria_dir / "json" / "Halakhah" / "Responsa"
    if not responsa_dir.exists():
        print(f"Responsa directory not found: {responsa_dir}")
        return
    
    entries = []
    
    for resp_file in responsa_dir.rglob("*.json"):
        try:
            with open(resp_file, 'r', encoding='utf-8') as f:
                data = json.load(f)
        except:
            continue
        
        # Extract text
        title = data.get('title', resp_file.stem)
        text = data.get('text', [])
        
        # Flatten nested text
        def flatten(t):
            if isinstance(t, str):
                return t
            if isinstance(t, list):
                return ' '.join(flatten(x) for x in t)
            return ''
        
        flat_text = flatten(text)
        
        if len(flat_text) < 100:
            continue
        
        # Try to determine era from title/path
        era = "medieval"  # default
        if any(x in title.lower() for x in ['modern', 'contemporary', '20th']):
            era = "modern"
        elif any(x in title.lower() for x in ['geonic', 'gaon']):
            era = "geonic"
        
        entries.append({
            'id': resp_file.stem,
            'title': title,
            'text': flat_text[:5000],
            'era': era,
            'source_file': str(resp_file.relative_to(sefaria_dir)),
        })
    
    out_file = output_dir / "responsa_processed.json"
    with open(out_file, 'w', encoding='utf-8') as f:
        json.dump(entries, f, indent=2, ensure_ascii=False)
    
    print(f"Processed {len(entries)} responsa texts -> {out_file}")


# =============================================================================
# MAIN
# =============================================================================

def main():
    parser = argparse.ArgumentParser(
        description="Longitudinal Ethics Corpus - Bulk Downloader",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
    python bulk_downloader.py --list              # Show available sources
    python bulk_downloader.py --scripts           # Generate download scripts
    python bulk_downloader.py --process-reddit aita.jsonl
    python bulk_downloader.py --process-sefaria ./Sefaria-Export/
        """
    )
    
    parser.add_argument("--list", action="store_true", help="List available bulk sources")
    parser.add_argument("--scripts", action="store_true", help="Generate download helper scripts")
    parser.add_argument("--process-reddit", type=str, metavar="FILE", help="Process Reddit JSONL file")
    parser.add_argument("--process-sefaria", type=str, metavar="DIR", help="Process Sefaria export")
    parser.add_argument("--output", default="./longitudinal_corpus", help="Output directory")
    parser.add_argument("--limit", type=int, help="Limit entries when processing")
    
    args = parser.parse_args()
    
    config = Config(output_dir=args.output)
    Path(config.output_dir).mkdir(parents=True, exist_ok=True)
    
    if args.list:
        print("="*70)
        print("AVAILABLE BULK DATA SOURCES")
        print("="*70)
        for name, info in BULK_SOURCES.items():
            print(f"\n[{name}]")
            print(f"  Description: {info['description']}")
            print(f"  Time span:   {info['temporal_span']}")
            print(f"  Format:      {info['format']}")
            print(f"  Size:        {info['size']}")
            print(f"\n  Notes:\n{info['notes']}")
        return
    
    if args.scripts:
        generate_download_scripts(config)
        return
    
    if args.process_reddit:
        process_reddit_jsonl(
            Path(args.process_reddit),
            Path(config.output_dir) / "reddit_aita",
            limit=args.limit
        )
        return
    
    if args.process_sefaria:
        process_sefaria_responsa(
            Path(args.process_sefaria),
            Path(config.output_dir) / "responsa"
        )
        return
    
    # Default: show help
    parser.print_help()
    print("\n" + "="*70)
    print("QUICK START")
    print("="*70)
    print("""
1. Generate download scripts:
   python bulk_downloader.py --scripts
   
2. Run the scripts you need:
   cd longitudinal_corpus/download_scripts/
   ./download_sefaria.sh
   ./download_academic_ethics.sh
   
3. Process downloaded data:
   python bulk_downloader.py --process-sefaria ./Sefaria-Export/
   python bulk_downloader.py --process-reddit ./aita_dump.jsonl
""")


if __name__ == "__main__":
    main()
