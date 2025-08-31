# APE Splitter

A Python script that splits a single `.ape` (Monkey's Audio) audio file into individual tracks (e.g., MP3, FLAC) using the metadata from a `.cue` sheet and the powerful `ffmpeg` codec.

## Usage

1.  Place your `.ape` file and its corresponding `.cue` file in the same directory.
2.  Run the script from the command line, specifying the `.cue` file:

    ```bash
    python ape_splitter.py album.cue
    ```

    The script will automatically search for an `.ape` file with the same name as the `.cue` file.

## Command Line Arguments

| Argument | Description | Example |
| :--- | :--- | :--- |
| `--ffmpeg` | Specify a custom path to the `ffmpeg` executable. Use this if `ffmpeg` is not in your system's PATH or not installed in the default location. | `--ffmpeg "C:\Tools\ffmpeg\bin\ffmpeg.exe"` |
| `-o`, `--output` | Choose a custom directory for the output files. If not specified, tracks will be saved in the current directory. | `-o ".\My Music\Album"` |

### Examples

**Example 1:** Using a custom `ffmpeg` path and a custom output directory.
```bash
python ape_splitter.py "path\to\album.cue" --ffmpeg "C:\ffmpeg\bin\ffmpeg.exe" -o ".\Output\Album"
```
**Example 2:** Simply splitting a file when all tools are installed correctly.
```bash
python ape_splitter.py "album.cue"
```
