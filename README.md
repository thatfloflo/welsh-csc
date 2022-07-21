# Welsh Controlled Speech Corpus Utility (welsh-csc)

*welsh-csc* is a Python utility to work with the audio and metadata files for the Welsh Controlled Speech Corpus (available from https://data.ling101.com/welsh-csc/data).

## Usage
**General:** `python -m welsh-csc [OPTIONS] COMMAND [ARGS]...`

**For help:** `python -m welsh-csc --help`

### Commands

#### `chop-data`: Chop raw audio session files into per-stimulus files.

Chops any **.wav* files found in the *raw-1ch* and *raw-2ch* subdirectories of the data directory (set by `--path`, default *./data*) using the ProRec annotations in the corresponding **.txt* file with the same name.

The chopped files will be placed in the *chopped-1ch* and *chopped-2ch* subdirectories.

Uses Mark Huckvale's ProChop utility if installed (and found on the *PATH*) for efficiecy, otherwise falls back to ProChopPy to chop the audio files.

**Usage:** `python -m welsh-csc chop-data [OPTIONS]`

| Option          | Parameters    | Description                              |
|-----------------|---------------|------------------------------------------|
| `--help`        |               | Show help message and exit               |
| `-p, --path`    | DIRECTORY     | The directory where the data files are stored. [default: ./data] |
| `-c, --channel` | 1 \| 2 \| 1+2 | Whether to chop the audio-only (1 ch), audio and lx (2 ch), or both (1+2 ch) versions. [default: 1+2] |


#### `get-data`: Retrieve the Welsh CSC data from remote host.

Downloads the data files (audio and corresponding annotations/labels) from a remote host (specified by `--remote`, default *https://data.ling101.com/welsh-csc/data*) and places
them in the local data directory (set by `--path`, default *./data*).

Expects one of the arguments *all*, *raw*, or *chopped*. With *raw* only the unprocessed original recrdings (and corrsponding ProRec labels) will be downloaded; with *chopped* only the pre-processed, chopped (cf. the `chop-data` command) recordings (and corresponding labels and annotations) will be downloaded; with *all* specified both the raw and chopped data will be downloaded.

By default all data will be downloaded both in the 1-channel mono audio format and the 2-channel audio + lx format. This can be modified with the `--channel` option.

**Note:** The data set is quite large (10s of GBs), so it is highly recommended that you make use of the options *raw*/*chopped* and `--channel 1` / `--channel 2` to download only the data you need, rather than just downloading everything.

You can in principle generate all the data available from just the *2-channel raw* files plus the metadata (cf. the `get-meta` command), by using the tools provided here and the ProsodyLab aligner for forced alignment. However, if you need the TextGrids from the forced aligner it's probably easier to just download one of the *chopped* sets, as the aligner relies on the restrictivey licensed HTK libraries which can make this difficult to set up and run locally.

**Usage:** `python -m welsh-csc get-data [OPTIONS] {all|raw|chopped}`

| Option          | Parameters    | Description                              |
|-----------------|---------------|------------------------------------------|
| `--help`        |               | Show help message and exit               |
| `-p, --path`    | DIRECTORY     | The directory where the data files are stored. [default: ./data] |
| `-r, --remote`  | URL           | URL for the remote server from which to fetch data. [default: https://data.ling101.com] |
| `-c, --channel` | 1 \| 2 \| 1+2 | Whether to chop the audio-only (1 ch), audio and lx (2 ch), or both (1+2 ch) versions. [default: 1+2] |


#### `get-meta`: Retrieve metadata for the Welsh CSC data from remote host.

Downloads the metadata (participant background questionnaires, stimuli list, etc.) from a remote host (specified by `--remote`, default *https://data.ling101.com/welsh-csc/data*) and places them in the local data directory (set by `--path`, default *./data*).

**Usage:** `python -m welsh-csc get-meta [OPTIONS]`

| Option          | Parameters    | Description                              |
|-----------------|---------------|------------------------------------------|
| `--help`        |               | Show help message and exit               |
| `-p, --path`    | DIRECTORY     | The directory where the data files are stored. [default: ./data] |
| `-r, --remote`  | URL           | URL for the remote server from which to fetch data. [default: https://data.ling101.com] |


#### `make-labels`: Make labels for chopped data files.

Uses the list of stimuli to makes a set of **.lab* label files which are needed for forced alignment with the ProsodyLab Aligner. The label files are stored inside the
metadata subdirectory (e.g. *./data/meta/labels*) of the data directory (set by `--path`, default *./data*) and also added to any chopped data inside the data directory.

Assumes that the file *meta/stimuli.txt* already exists inside the data directory. If this is not the case, use the `get-meta` command to obtain it first.

**Usage:** `python -m welsh-csc make-labels [OPTIONS]`

| Option          | Parameters    | Description                              |
|-----------------|---------------|------------------------------------------|
| `--help`        |               | Show help message and exit               |
| `-p, --path`    | DIRECTORY     | The directory where the data files are stored. [default: ./data] |


#### `make-mono`: Extract mono voice-tracks from 2 channel audio files.

Takes the 2-channel wave files containing audio and lx and converts them to audio-only 1-channel mono wave files. Mono wave files are needed for some analysis or processing tools and are sometimes easier to handle than 2-channel wave files containing non-audio data (which might be interpreted naively as a stero channel or similar and appear like a lot of noise).

With the argument *raw* only the files in the subdirectory *raw-2ch* will be converted an stored in the *raw-1ch* subdirectory. With *chopped* only the files in the *chopped-2ch* subdirectory will be converted and stored in the *chopped-1ch* directory. With *all* both *raw-2ch* and *chopped-2ch* will be converted. All data and subdirectorie are assumed to be contained inside the data directory (set by `--path`, default *./data*).

**Usage:** `python -m welsh-csc make-mono [OPTIONS] {all|raw|chopped}`

| Option          | Parameters    | Description                              |
|-----------------|---------------|------------------------------------------|
| `--help`        |               | Show help message and exit               |
| `-p, --path`    | DIRECTORY     | The directory where the data files are stored. [default: ./data] |
