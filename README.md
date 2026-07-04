# Audio Analysis CLI

**Author**: [`74657874`](https://github.com/74657874) (`⣎⡇ꉺლ༽இ•̛)ྀ◞ ༎ຶ ༽ৣৢ؞ৢ؞ؖ ꉺლ`)
Tooling and analysis for decoding Unicode/Kaomoji metadata, catalog releases, and generating spectral PNGs (based on [Gazelle specs](https://gitlab.com/_mclovin/gazelle-specs)).


## Features

1. **Track Title Decoding**:
   - Strips Zalgo combining marks (`unicodedata.category`) to reveal hidden ASCII fragments (`vȯ`, `oOo`, `VVV`).
   - Parses Kaomoji facial expressions (`(ㅍㅍ)ა`, `(*ㅇ△ Φ☆)ノ`), Tibetan beat notations (`● ࿀ ●`), and Braille symbols.

2. **Spectrogram Generator**:
   - **Full Track Spectrograms** (`3000x513` px): Linear 0–22.05 kHz scale, 120 dB dynamic range (`vmin=-120, vmax=0`), Kaiser window ($\beta=14$).
   - **Zoomed Cutoff Spectrograms** (`500x1025` px): High vertical resolution 3-second snapshot window to inspect high-frequency compression cutoffs.

3. **Cover Artwork Forensic Analyzer**:
   - Performs LSB bitplane extraction and 2D Fast Fourier Transform (FFT) analysis on digital and vinyl cover artwork saved in `data/art/`.

## Project Structure

```
music-forensics/
├── REPORT.md                  # Comprehensive forensic decoding & audio research report
├── README.md                  # Project documentation and usage guide
├── Makefile                   # Automation console (make all, make spectrals, etc.)
├── cli.py                     # Unified CLI entrypoint (decode, spectrals, cover-analysis, inspect-art)
├── utils.py                   # Python utilities (decoding, tags, spectrals, & image analysis)
├── data/                      # Raw web dumps, artwork, and analysis outputs
│   ├── art/                   # High-res digital, vinyl sleeve, & variant artwork + LSB/FFT plots
│   │   ├── crops/             # Manual 1-to-1 track mapping image crops
│   │   └── analysis/          # Spectral and forensic image analysis plots
│   ├── spectrals/             # Audio spectrogram PNGs
│   ├── music/                 # FLAC release audio directories
│   └── pages/                 # HTML web dumps
│       ├── discogs_text059.html   # Discogs TEXT059 release page
│       ├── discogs_label_text.html# Discogs Text Records catalog page
│       ├── fourtet_bandcamp.html  # Four Tet Bandcamp discography
│       └── wikipedia_discography.html
```
```

## Usage

### Run via Makefile
```bash
# Display help and target commands
make help

# Run full pipeline (decode, spectrals, and cover analysis)
make all
```

### Run via Python
```bash
python3 cli.py -h
```

## Development

This project uses `pytest` for unit testing and `pre-commit` for maintaining code health (via `yapf` formatting and `isort`). A GitHub Actions CI pipeline is also included to automatically test and format code on pull requests and pushes to `main`.

**Setup for local development:**
```bash
# Install dependencies and setup pre-commit hooks
make setup

# Run the unit test suite
make test

# Manually trigger the code formatter
make format
```
