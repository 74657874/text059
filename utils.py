"""Alter ego decoder and audio analyzer utilities.

This module provides reusable functionality for extracting, parsing, and cleaning
FLAC Vorbis metadata tags, and generating compliant
spectrograms for visual forensic analysis.

Follows Google Python Style Guide.
"""

import os
import struct
import subprocess
import unicodedata

import matplotlib
import numpy as np

matplotlib.use('Agg')
import urllib.request

import matplotlib.pyplot as plt
from PIL import Image

BASE_DIR = os.path.dirname(os.path.abspath(__file__))

ALBUM_PATHS = {
    "TEXT059":
        os.path.join(
            BASE_DIR, "data", "music", "⣎⡇ꉺლ༽இ•̛)ྀ◞ ༎ຶ ༽ৣৢ؞ৢ؞ؖ ꉺლ",
            "⣎⡇ꉺლ༽இ•̛)ྀ◞ ༎ຶ ༽ৣৢ؞ৢ؞ؖ ꉺლ - ʅ͡͡͡͡͡͡͡͡͡͡͡(̸̢̛̼̞̭͋ͅ)̸͚̰͛̔̾̀̿͒͂-̴͓̞̑̌̂̆̊͋̀-̸͎̟̯̂̓̌ ҉ ͡ ͞ ͞ (2026) - WEB FLAC"
        )
}

SPECTRALS_DIR = os.path.join(BASE_DIR, "data", "spectrals")
ART_DIR = os.path.join(BASE_DIR, "data", "art")


def strip_combining_marks(text: str) -> str:
  """Strips Unicode combining diacritics and Zalgo marks from text.

  Args:
    text: String containing combining Unicode characters.

  Returns:
    String with all combining mark categories ('M') removed.
  """
  return "".join(
      [ch for ch in text if not unicodedata.category(ch).startswith("M")])


def parse_flac_metadata(filepath: str) -> dict:
  """Extracts Vorbis comment tags from a FLAC file.

  Args:
    filepath: Absolute path to the .flac file.

  Returns:
    Dictionary mapping tag keys to tag values.
  """
  tags = {}
  with open(filepath, "rb") as f:
    header = f.read(4)
    if header != b"fLaC":
      return tags

    is_last = False
    while not is_last:
      bheader = f.read(4)
      if len(bheader) < 4:
        break
      is_last = (bheader[0] & 0x80) != 0
      block_type = bheader[0] & 0x7F
      length = (bheader[1] << 16) | (bheader[2] << 8) | bheader[3]
      data = f.read(length)

      if block_type == 4:  # VORBIS_COMMENT
        offset = 0
        vendor_len = struct.unpack("<I", data[offset:offset + 4])[0]
        offset += 4 + vendor_len
        comment_count = struct.unpack("<I", data[offset:offset + 4])[0]
        offset += 4

        for _ in range(comment_count):
          c_len = struct.unpack("<I", data[offset:offset + 4])[0]
          offset += 4
          comment = data[offset:offset + c_len].decode("utf-8", "ignore")
          offset += c_len
          if "=" in comment:
            k, v = comment.split("=", 1)
            tags[k.upper()] = v
  return tags


def decode_album_metadata(album_key: str) -> None:
  """Parses and prints decoded FLAC metadata for a given album.

  Args:
    album_key: Album identifier key ('TEXT059').
  """
  src_dir = ALBUM_PATHS.get(album_key)
  if not src_dir or not os.path.exists(src_dir):
    return

  flac_files = sorted([f for f in os.listdir(src_dir) if f.endswith(".flac")])
  print(f"\n--- Decoding Metadata for {album_key} ---")

  for filename in flac_files:
    flac_path = os.path.join(src_dir, filename)
    tags = parse_flac_metadata(flac_path)
    track_num = tags.get("TRACKNUMBER", "?")
    title = tags.get("TITLE", "?")
    clean_title = strip_combining_marks(title)

    print(f"Track {track_num}:")
    print(f"  Raw: {title}")
    print(f"  Clean: {clean_title}")
    print(f"  Length (raw): {len(title)} | Length (clean): {len(clean_title)}")


def suggest_alternate_titles() -> None:
  """Prints suggested alternate, human-readable titles based on analysis."""
  print("\n--- Suggested Alternate Titles ---")
  print("Artist: Crying Creature / Tearful Kaomoji")
  print("\nAlbum: TEXT059 - Glitch Kaomoji & Loops / Self-Titled (2026)")
  print("  Track 01: Vocal Chop Loop (vȯ / OOOOOOooo)")
  print("  Track 02: Side-Eye Kaomoji (ㅍㅍ)ა")
  print("  Track 03: Teardrop Face & Sparkles")
  print("  Track 04: Sun & Orbs Motif (☼⃝)")
  print("  Track 05: Shocked Kaomoji (*ㅇ△ Φ☆)ノ / Waveform")
  print("  Track 06: 11-Bar Glitch Loop (࿃ूੂ)")
  print("  Track 07: Double Vocal Panning (VVV / vȯ)")
  print("  Track 08: Heavy Beat Trigger Grid (● ࿀ ●)")


def extract_mono_pcm(filepath: str,
                     start_s: float = 0,
                     duration_s: float = None,
                     sample_rate: int = 44100) -> np.ndarray:
  """Extracts mono 32-bit floating point PCM audio using FFmpeg.

  Args:
    filepath: Absolute path to the input audio file.
    start_s: Start offset in seconds.
    duration_s: Segment duration in seconds (optional).
    sample_rate: Output sampling rate in Hz (default 44100).

  Returns:
    NumPy array of 32-bit float audio samples.
  """
  cmd = ["ffmpeg", "-ss", str(start_s)]
  if duration_s:
    cmd.extend(["-t", str(duration_s)])
  cmd.extend(
      ["-i", filepath, "-f", "f32le", "-ac", "1", "-ar",
       str(sample_rate), "-"])
  process = subprocess.Popen(cmd,
                             stdout=subprocess.PIPE,
                             stderr=subprocess.DEVNULL)
  data, _ = process.communicate()
  return np.frombuffer(data, dtype=np.float32)


def generate_full_spectrogram(filepath: str, out_path: str,
                              track_title: str) -> None:
  """Generates full track spectrogram (3000x513 px).

  Args:
    filepath: Path to input FLAC audio file.
    out_path: Target output PNG filepath.
    track_title: Title overlay string.
  """
  audio = extract_mono_pcm(filepath)
  sr = 44100

  fig = plt.figure(figsize=(30, 5.13), dpi=100, facecolor="#111111")
  ax = fig.add_axes([0.05, 0.12, 0.93, 0.78], facecolor="#000000")

  nfft = 2048
  noverlap = 1024
  ax.specgram(
      audio,
      NFFT=nfft,
      Fs=sr,
      noverlap=noverlap,
      window=np.kaiser(nfft, 14),
      cmap="inferno",
      vmin=-120,
      vmax=0,
  )

  ax.set_ylim(0, sr / 2.0)
  ax.set_ylabel("Frequency (Hz)", color="#cccccc", fontsize=12)
  ax.set_xlabel("Time (s)", color="#cccccc", fontsize=12)
  ax.tick_params(colors="#aaaaaa", labelsize=10)

  yticks = [0, 5000, 10000, 15000, 20000, 22050]
  ax.set_yticks(yticks)
  ax.set_yticklabels(
      ["0 Hz", "5 kHz", "10 kHz", "15 kHz", "20 kHz", "22.05 kHz"])

  fig.text(
      0.05,
      0.93,
      f"{track_title} (Full 3000x513)",
      color="#ffffff",
      fontsize=14,
      fontweight="bold",
  )

  plt.savefig(out_path,
              dpi=100,
              facecolor=fig.get_facecolor(),
              edgecolor="none")
  plt.close(fig)


def generate_zoomed_spectrogram(filepath: str, out_path: str,
                                track_title: str) -> None:
  """Generates zoomed cutoff spectrogram (500x1025 px).

  Args:
    filepath: Path to input FLAC audio file.
    out_path: Target output PNG filepath.
    track_title: Title overlay string.
  """
  audio = extract_mono_pcm(filepath, start_s=25, duration_s=3)
  sr = 44100

  fig = plt.figure(figsize=(5, 10.25), dpi=100, facecolor="#111111")
  ax = fig.add_axes([0.22, 0.08, 0.72, 0.84], facecolor="#000000")

  nfft = 4096
  noverlap = 3584
  ax.specgram(
      audio,
      NFFT=nfft,
      Fs=sr,
      noverlap=noverlap,
      window=np.kaiser(nfft, 14),
      cmap="inferno",
      vmin=-120,
      vmax=0,
  )

  ax.set_ylim(0, sr / 2.0)
  ax.set_ylabel("Frequency (Hz)", color="#cccccc", fontsize=10)
  ax.set_xlabel("Time (s)", color="#cccccc", fontsize=10)
  ax.tick_params(colors="#aaaaaa", labelsize=9)

  yticks = [0, 5000, 10000, 15000, 18000, 20000, 21000, 22050]
  ax.set_yticks(yticks)
  ax.set_yticklabels(["0", "5k", "10k", "15k", "18k", "20k", "21k", "22.05k"])

  fig.text(
      0.05,
      0.95,
      f"{track_title} Zoomed (500x1025)",
      color="#ffffff",
      fontsize=11,
      fontweight="bold",
  )

  plt.savefig(out_path,
              dpi=100,
              facecolor=fig.get_facecolor(),
              edgecolor="none")
  plt.close(fig)


def process_album_spectrals(album_key: str,
                            generate_zoomed: bool = False) -> None:
  """Generates full and zoomed spectrals for a given album.

  Args:
    album_key: Album identifier key ('TEXT059').
    generate_zoomed: Whether to generate zoomed high-frequency cutoff spectrals.
  """
  src_dir = ALBUM_PATHS.get(album_key)
  if not src_dir or not os.path.exists(src_dir):
    print(f"Directory for {album_key} not found: {src_dir}")
    return

  dest_dir = SPECTRALS_DIR
  os.makedirs(dest_dir, exist_ok=True)

  flac_files = sorted([f for f in os.listdir(src_dir) if f.endswith(".flac")])
  print(f"\nProcessing {len(flac_files)} tracks for album {album_key}...")

  for idx, filename in enumerate(flac_files, 1):
    flac_path = os.path.join(src_dir, filename)
    base_name = os.path.splitext(filename)[0]
    track_id = f"{idx:02d}"

    out_full = os.path.join(dest_dir, f"{track_id}_full.png")
    out_zoomed = os.path.join(dest_dir, f"{track_id}_zoomed.png")

    print(
        f" [{idx:02d}/{len(flac_files):02d}] Generating spectrals: {base_name[:30]}..."
    )
    generate_full_spectrogram(flac_path, out_full, base_name[:30])
    if generate_zoomed:
      generate_zoomed_spectrogram(flac_path, out_zoomed, base_name[:30])

  print(f"Successfully generated spectrals for {album_key} in {dest_dir}")


def analyze_single_image(img_path: str, dest_dir: str) -> None:
  """Runs LSB bitplane extraction and 2D FFT transform on a single image file."""
  base = os.path.splitext(os.path.basename(img_path))[0]

  # 1. LSB Analysis
  img_rgb = Image.open(img_path).convert("RGB")
  arr = np.array(img_rgb)
  lsb_r = (arr[:, :, 0] & 1) * 255
  lsb_g = (arr[:, :, 1] & 1) * 255
  lsb_b = (arr[:, :, 2] & 1) * 255

  fig, axes = plt.subplots(1, 3, figsize=(15, 5), facecolor="#111111")
  for ax in axes:
    ax.set_facecolor("#111111")

  axes[0].imshow(lsb_r, cmap="gray")
  axes[0].set_title("Red Channel LSB Bitplane", color="#ffffff", fontsize=10)
  axes[0].axis("off")

  axes[1].imshow(lsb_g, cmap="gray")
  axes[1].set_title("Green Channel LSB Bitplane", color="#ffffff", fontsize=10)
  axes[1].axis("off")

  axes[2].imshow(lsb_b, cmap="gray")
  axes[2].set_title("Blue Channel LSB Bitplane", color="#ffffff", fontsize=10)
  axes[2].axis("off")

  plt.tight_layout()
  lsb_out = os.path.join(dest_dir, f"{base}_lsb.png")
  plt.savefig(lsb_out, dpi=150, facecolor=fig.get_facecolor(), edgecolor="none")
  plt.close(fig)

  # 2. 2D FFT Analysis
  img_gray = Image.open(img_path).convert("L")
  arr_gray = np.array(img_gray, dtype=float)
  f_transform = np.fft.fft2(arr_gray)
  f_shift = np.fft.fftshift(f_transform)
  magnitude_spectrum = 20 * np.log(np.abs(f_shift) + 1e-5)

  fig, ax = plt.subplots(figsize=(8, 8), facecolor="#111111")
  ax.set_facecolor("#111111")
  ax.imshow(magnitude_spectrum, cmap="inferno")
  ax.set_title(f"2D FFT Spectrum - {base}", color="#ffffff", fontsize=12)
  ax.axis("off")

  plt.tight_layout()
  fft_out = os.path.join(dest_dir, f"{base}_fft.png")
  plt.savefig(fft_out, dpi=150, facecolor=fig.get_facecolor(), edgecolor="none")
  plt.close(fig)
  print(
      f" Analyzed {base}: saved LSB ({os.path.basename(lsb_out)}) & FFT ({os.path.basename(fft_out)})"
  )


def analyze_cover_artwork(art_dir: str = None) -> None:
  """Performs LSB bitplane extraction and 2D FFT analysis on all album art files.

  Args:
    art_dir: Target artwork directory (default: data/art/).
  """
  if art_dir is None:
    art_dir = ART_DIR

  if not os.path.exists(art_dir):
    print(f"Artwork directory not found: {art_dir}")
    return

  print(f"\n--- Analyzing Album Artwork in: {art_dir} ---")
  targets = [
      "text059_digital.jpg", "text059_vinyl_front.jpg", "text059_vinyl_back.jpg"
  ]
  dest_dir = os.path.join(art_dir, "analysis")
  os.makedirs(dest_dir, exist_ok=True)

  for filename in targets:
    img_path = os.path.join(art_dir, filename)
    if os.path.exists(img_path):
      analyze_single_image(img_path, dest_dir)


def fetch_artwork_variants(art_dir: str = None) -> None:
  """Scrapes and saves additional artwork variants from web sources.

  Args:
    art_dir: Output artwork directory (default: data/art/).
  """
  if art_dir is None:
    art_dir = ART_DIR

  os.makedirs(art_dir, exist_ok=True)
  print("\n--- Scraping Artwork Variants ---")

  headers = {"User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7)"}
  variants = {
      "text059_bandcamp.jpg":
          "https://f4.bcbits.com/img/a0396562816_10.jpg",
      "text059_discogs.jpg":
          "https://i.discogs.com/nlqmqXdcoQo4mvkCry_yyXs3LaMK5DZJeuNXfbwYyg8/rs:fit/g:sm/q:90/h:225/w:225/czM6Ly9kaXNjb2dz/LWRhdGFiYXNlLWlt/YWdlcy9SLTM3NjQy/NTI3LTE3ODE2MTQw/NDAtNDQ1NS5qcGVn.jpeg"
  }

  for filename, url in variants.items():
    out_path = os.path.join(art_dir, filename)
    if not os.path.exists(out_path):
      req = urllib.request.Request(url, headers=headers)
      try:
        with urllib.request.urlopen(req) as resp, open(out_path, "wb") as f:
          f.write(resp.read())
        print(f"Fetched variant artwork: {out_path}")
      except Exception as e:
        print(f"Failed to fetch {url}: {e}")
    else:
      print(f"Variant artwork already exists: {out_path}")


def inspect_artwork_metadata(art_dir: str = None) -> None:
  """Inspects and prints dimensions, DPI, color modes, and EXIF/XMP info for artwork files.

  Args:
    art_dir: Target artwork directory (default: data/art/).
  """
  if art_dir is None:
    art_dir = ART_DIR

  if not os.path.exists(art_dir):
    print(f"Artwork directory not found: {art_dir}")
    return

  print(f"\n--- Inspecting Artwork Metadata in: {art_dir} ---")
  for filename in sorted(os.listdir(art_dir)):
    if filename.endswith((".jpg", ".jpeg", ".png")) and not filename.endswith(
        ("_lsb.png", "_fft.png")):
      filepath = os.path.join(art_dir, filename)
      img = Image.open(filepath)
      size_mb = os.path.getsize(filepath) / (1024 * 1024)
      print(f"File: {filename}")
      print(f"  Dimensions: {img.size[0]} x {img.size[1]} px")
      print(f"  Color Mode: {img.mode}")
      print(f"  File Size: {size_mb:.2f} MB")
      dpi = img.info.get("dpi")
      if dpi:
        print(f"  DPI: {dpi}")
      exif = img.getexif()
      if exif:
        print(f"  EXIF Tags: {len(exif)} found")
      print()


def scrape_bandcamp_releases(html_path: str = None, output_dir: str = None) -> None:
    """Scrapes bandcamp releases into markdown and downloads cover arts."""
    import os

    import bs4
    import requests

    if html_path is None:
        html_path = '/Users/jakegarrison/.gemini/jetski/brain/b2cf5308-b8cb-4929-a5b3-7eaddb52076d/.system_generated/steps/2112/content.md'
    if output_dir is None:
        output_dir = 'data/bandcamp'

    os.makedirs(output_dir, exist_ok=True)

    RELEASE_DATES = {
        '--5': 'July 2026',
        'ooo-ooo': 'October 2025',
        'v': 'October 2024',
        'v-v': 'August 2022',
        'ooo-o-0': 'May 2020',
        '--1': 'October 2019',
        '--6': 'March 2018',
        '--2': 'October 2017',
        '-': 'October 2017'
    }

    try:
        with open(html_path, 'r') as f:
            html = f.read()
    except FileNotFoundError:
        print(f"HTML file not found: {html_path}")
        return

    soup = bs4.BeautifulSoup(html, 'html.parser')
    releases = soup.find_all('li', class_='music-grid-item')

    # Reverse to process chronologically
    releases = list(reversed(releases))

    for idx, release in enumerate(releases, 1):
        a_tag = release.find('a')
        href = a_tag['href'] if a_tag else ''
        if not href:
            continue

        slug = href.split('/')[-1]
        full_link = f"https://00000ooooo.bandcamp.com{href}"

        title_tag = release.find('p', class_='title')
        title_text = title_tag.text.strip() if title_tag else 'Unknown'

        img_tag = release.find('img')
        img_url = ''
        if img_tag:
            if 'data-original' in img_tag.attrs:
                img_url = img_tag['data-original']
            elif 'src' in img_tag.attrs:
                img_url = img_tag['src']

        date_str = RELEASE_DATES.get(slug, 'Unknown')
        year = date_str.split(' ')[-1] if ' ' in date_str else date_str

        file_prefix = f"{idx:02d}_{year}_{slug}"

        print(f"Scraping release: {file_prefix}...")

        if img_url:
            try:
                img_resp = requests.get(img_url)
                if img_resp.status_code == 200:
                    img_path_full = os.path.join(output_dir, f"{file_prefix}.png")
                    with open(img_path_full, 'wb') as img_f:
                        img_f.write(img_resp.content)
            except Exception as e:
                print(f"Failed to download image for {slug}: {e}")

        # Fetch individual album page for tracklist and tags
        tracks = []
        tags = []
        try:
            album_resp = requests.get(full_link)
            if album_resp.status_code == 200:
                album_soup = bs4.BeautifulSoup(album_resp.content, 'html.parser')
                for tr in album_soup.find_all('tr', class_='track_row_view'):
                    t_span = tr.find('span', class_='track-title')
                    time_span = tr.find('span', class_='time')
                    if t_span:
                        t_title = t_span.text.strip()
                        t_time = time_span.text.strip() if time_span else ''
                        tracks.append(f"- {t_title} ({t_time})")

                for tag in album_soup.find_all('a', class_='tag'):
                    tags.append(tag.text.strip())
        except Exception as e:
            print(f"Failed to fetch {full_link}: {e}")

        tracks_md = "\n".join(tracks) if tracks else "*(No tracks found)*"
        tags_md = ", ".join(tags) if tags else "*(No tags found)*"

        md_content = f"""# Release: {slug}

**Title:** `{title_text}`
**Date:** {date_str}
**Link:** [{full_link}]({full_link})

## Cover Art
![Cover Art]({file_prefix}.png)

## Tracklist
{tracks_md}

## Tags
{tags_md}
"""
        md_path = os.path.join(output_dir, f"{file_prefix}.md")
        with open(md_path, 'w') as f:
            f.write(md_content)
    print(f"Successfully scraped releases into {output_dir}")

if __name__ == '__main__':
    # Test scraping functionality
    print("Testing Bandcamp scraper...")
    scrape_bandcamp_releases()
