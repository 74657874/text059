import io
import struct
from unittest import mock

import numpy as np
import pytest

import utils


@pytest.mark.parametrize("raw, expected", [
    ("v̴̢͚͚͎ȯ̶", "vȯ"),
    ("● ࿀ ●", "● ࿀ ●"),
    ("ʅ͡͡͡͡͡͡͡͡͡͡͡(̸̢̛̼̞̭͋ͅ)", "ʅ()"),
    ("hello world", "hello world"),
    ("", ""),
    ("T̸H̴I̷S̵ ̷I̷S̶ ̵F̶I̷N̴E̷", "THIS IS FINE"), # Additional string ops
])
def test_strip_combining_marks(raw, expected):
    """Test stripping Unicode combining marks."""
    assert utils.strip_combining_marks(raw) == expected

def test_parse_flac_metadata_invalid_header(tmp_path):
    """Test that parse_flac_metadata returns empty dict for invalid file."""
    f = tmp_path / "fake.flac"
    f.write_bytes(b"RIFF")
    tags = utils.parse_flac_metadata(str(f))
    assert tags == {}

def test_parse_flac_metadata_valid_header(tmp_path):
    """Test valid flac metadata parsing using struct."""
    f = tmp_path / "valid.flac"

    # Construct a valid FLAC vorbis comment block
    # 4 bytes: fLaC
    # Block header: type=4 (VORBIS_COMMENT), last_block_flag=1 (0x80 | 4 = 0x84)
    # Length: 24-bit (just make it match)

    vendor_string = b"reference libFLAC 1.3.2 20170101"
    vendor_len = struct.pack("<I", len(vendor_string))

    comment = b"TITLE=hello"
    comment_len = struct.pack("<I", len(comment))
    comment_list_length = struct.pack("<I", 1) # 1 comment

    block_data = vendor_len + vendor_string + comment_list_length + comment_len + comment
    block_header = struct.pack(">I", (0x84 << 24) | len(block_data))

    f.write_bytes(b"fLaC" + block_header + block_data)

    tags = utils.parse_flac_metadata(str(f))
    assert tags == {"TITLE": "hello"}

@mock.patch("utils.subprocess.Popen")
def test_extract_mono_pcm(mock_popen):
    """Test extracting mono PCM audio using a mocked FFmpeg subprocess."""
    mock_process = mock.Mock()
    dummy_audio = np.array([0.0, 0.5, -0.5, 1.0], dtype=np.float32)
    mock_process.communicate.return_value = (dummy_audio.tobytes(), b"")
    mock_popen.return_value = mock_process

    result = utils.extract_mono_pcm("fake.flac", start_s=10.5, duration_s=5.0)

    assert result.shape == (4,)
    np.testing.assert_array_equal(result, dummy_audio)
    mock_popen.assert_called_once()

    args, kwargs = mock_popen.call_args
    assert args[0] == ["ffmpeg", "-ss", "10.5", "-t", "5.0", "-i", "fake.flac", "-f", "f32le", "-ac", "1", "-ar", "44100", "-"]

@mock.patch("utils.plt.savefig")
@mock.patch("utils.extract_mono_pcm")
def test_generate_full_spectrogram(mock_extract, mock_savefig):
    """Test full spectrogram generation."""
    mock_extract.return_value = np.zeros(1024, dtype=np.float32)
    utils.generate_full_spectrogram("dummy.flac", "out.png", "Title")
    mock_savefig.assert_called_once()
    assert mock_extract.call_count == 1

@mock.patch("utils.plt.savefig")
@mock.patch("utils.extract_mono_pcm")
def test_generate_zoomed_spectrogram(mock_extract, mock_savefig):
    """Test zoomed spectrogram generation."""
    mock_extract.return_value = np.zeros(4096, dtype=np.float32)
    utils.generate_zoomed_spectrogram("dummy.flac", "out.png", "Title")
    mock_savefig.assert_called_once()
    assert mock_extract.call_count == 1

@mock.patch("utils.generate_zoomed_spectrogram")
@mock.patch("utils.generate_full_spectrogram")
@mock.patch("utils.os.listdir")
@mock.patch("utils.os.path.exists")
def test_process_album_spectrals(mock_exists, mock_listdir, mock_full, mock_zoomed):
    """Test batch processing of spectrals."""
    mock_exists.return_value = True
    mock_listdir.return_value = ["track1.flac", "not_audio.txt", "track2.flac"]

    utils.process_album_spectrals("TEXT059", generate_zoomed=True)

    assert mock_full.call_count == 2
    assert mock_zoomed.call_count == 2

@mock.patch("utils.plt.savefig")
@mock.patch("utils.Image.open")
def test_analyze_single_image(mock_img_open, mock_savefig):
    """Test image analysis (LSB & FFT)."""
    mock_img = mock.Mock()
    # Create fake RGB array 10x10x3
    mock_img.convert.return_value = mock_img
    mock_img.__array__ = lambda *args, **kwargs: np.zeros((10, 10, 3), dtype=np.uint8)

    # Need to return fake gray array as well for FFT
    mock_gray = mock.Mock()
    mock_gray.convert.return_value = mock_gray
    mock_gray.__array__ = lambda *args, **kwargs: np.zeros((10, 10), dtype=float)
    mock_img_open.side_effect = [mock_img, mock_gray]

    utils.analyze_single_image("fake.jpg", "/tmp/dest")
    assert mock_savefig.call_count == 2

@mock.patch("utils.urllib.request.urlopen")
def test_fetch_artwork_variants(mock_urlopen):
    """Test fetching artwork from remote."""
    mock_response = mock.Mock()
    mock_response.read.return_value = b"fake_image_data"
    mock_response.__enter__ = mock.Mock(return_value=mock_response)
    mock_response.__exit__ = mock.Mock()
    mock_urlopen.return_value = mock_response

    with mock.patch("builtins.open", mock.mock_open()) as m_open:
        with mock.patch("utils.os.path.exists", return_value=False):
            utils.fetch_artwork_variants("/tmp/art")

    assert m_open.call_count == 2 # 2 variants
    assert mock_urlopen.call_count == 2

@mock.patch("utils.Image.open")
@mock.patch("utils.os.path.getsize")
@mock.patch("utils.os.listdir")
@mock.patch("utils.os.path.exists")
def test_inspect_artwork_metadata(mock_exists, mock_listdir, mock_getsize, mock_img_open):
    """Test metadata inspection."""
    mock_exists.return_value = True
    mock_listdir.return_value = ["cover.jpg", "back.jpg", "cover_lsb.png"]
    mock_getsize.return_value = 1048576 # 1MB

    mock_img = mock.Mock()
    mock_img.size = (1000, 1000)
    mock_img.mode = "RGB"
    mock_img.info = {"dpi": (300, 300)}
    mock_img.getexif.return_value = {1: "test"}
    mock_img_open.return_value = mock_img

    utils.inspect_artwork_metadata("/tmp/art")

    assert mock_img_open.call_count == 2 # cover.jpg, back.jpg (skips _lsb.png)
