import argparse

import utils


def main():
  """CLI entrypoint for audio analysis tools."""
  parser = argparse.ArgumentParser(description="CLI")
  subparsers = parser.add_subparsers(dest="command", help="Available commands")

  # Decode command
  decode_parser = subparsers.add_parser(
      "decode", help="Decode metadata and print alternate titles")
  decode_parser.add_argument(
      "albums",
      nargs="*",
      default=["TEXT059"],
      help="Albums to decode (e.g. TEXT059)",
  )

  # Spectrals command
  spectrals_parser = subparsers.add_parser("spectrals",
                                           help="Generate music spectrals")
  spectrals_parser.add_argument(
      "albums",
      nargs="*",
      default=["TEXT059"],
      help="Albums to process (e.g. TEXT059)",
  )
  spectrals_parser.add_argument(
      "--zoomed",
      action="store_true",
      help="Also generate zoomed cutoff spectrals (disabled by default)",
  )

  # Cover analysis command
  cover_parser = subparsers.add_parser(
      "cover-analysis", help="Perform LSB & FFT analysis on cover art")

  # Inspect artwork command
  inspect_parser = subparsers.add_parser(
      "inspect-art", help="Inspect artwork dimensions, DPI, and metadata")


  # Scrape bandcamp command
  scrape_parser = subparsers.add_parser(
      "scrape-bandcamp", help="Scrape Wingdings Bandcamp releases")

  args = parser.parse_args()

  print("=================================================================")
  print("                              CLI                                ")
  print("=================================================================")

  if args.command == "decode":
    for album in args.albums:
      utils.decode_album_metadata(album)
    utils.suggest_alternate_titles()

  elif args.command == "spectrals":
    for album in args.albums:
      utils.process_album_spectrals(album, generate_zoomed=args.zoomed)

  elif args.command == "cover-analysis":
    utils.fetch_artwork_variants()
    utils.analyze_cover_artwork()

  elif args.command == "inspect-art":
    utils.inspect_artwork_metadata()


  elif args.command == "scrape-bandcamp":
    utils.scrape_bandcamp_releases()

  else:
    parser.print_help()


if __name__ == "__main__":
  main()
