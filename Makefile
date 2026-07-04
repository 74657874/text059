# Makefile for Audio & Release Decoder

PYTHON = python3

.PHONY: help all setup fetch-data decode spectrals spectrals-text059 cover-analysis inspect-art clean test format

help:
	@echo "========================================================================"
	@echo "            Audio (TEXT059) Decoding Console                        "
	@echo "========================================================================"
	@echo "Available Targets:"
	@echo "  make all             - Run full pipeline (decode & spectrals for TEXT059)"
	@echo "  make setup           - Install dependencies and pre-commit hooks"
	@echo "  make format          - Format code and run pre-commit checks"
	@echo "  make test            - Run unit tests with pytest"
	@echo "  make decode          - Run unified Python decoding & metadata utility"
	@echo "  make spectrals       - Generate spectrals for TEXT059"
	@echo "  make cover-analysis  - Run LSB and FFT image analysis on cover art"
	@echo "  make inspect-art     - Inspect artwork dimensions, DPI, and metadata"
	@echo "  make fetch-data      - Verify raw web data dumps in data/"
	@echo "  make clean           - Remove generated spectrals and temporary outputs"
	@echo "========================================================================"

all: format test decode spectrals cover-analysis

setup:
	@$(PYTHON) -m pip install -r requirements.txt --break-system-packages
	@$(PYTHON) -m pre_commit install

test:
	@$(PYTHON) -m pytest utils_test.py -v

decode:
	@$(PYTHON) cli.py decode

format:
	@$(PYTHON) -m pre_commit run --all-files

spectrals:
	@$(PYTHON) cli.py spectrals

spectrals-text059:
	@$(PYTHON) cli.py spectrals TEXT059

cover-analysis:
	@$(PYTHON) cli.py cover-analysis

inspect-art:
	@$(PYTHON) cli.py inspect-art


fetch-data:
	@echo "Verifying raw web data files in data/..."
	@ls -la data/

clean:
	@rm -rf data/spectrals/TEXT059
	@echo "Spectrals cleaned."
