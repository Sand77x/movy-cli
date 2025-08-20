# Movy-cli

Your personal movie / tv show streamer CLI  

**Dev:** Aug. 14, 2025 - Aug 20, 2025  

---
Movy is written in Python3 and uses [Playwright](https://playwright.dev/) to webscrape [fmovies.gd](https://www.fmovies.gd/). Small project I made since I love CLIs and doing everything in the terminal. Heavily inspired by [ani-cli](https://github.com/pystardust/ani-cli).
## Quickstart
```sh
python3 movy.py --help
python movy.py --help
movy --help # if executable
```
## Requirements
- Create account in [themoviedb.org](https://www.themoviedb.org/login)
- Copy [API KEY](https://www.themoviedb.org/settings/api)
- See installation guide below
## Install on Linux (Bash)
Replace api_key with tmdb api key
```sh
git clone https://github.com/Sand77x/movy-cli.git
cd movy-cli
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
echo 'TMDB_API=api_key' > .env
```
## Make Executable
Replace /path/to/movy-cli with location of source 
```sh
echo -e '#!/bin/bash\nMOVY_DIR=/path/to/movy-cli\n"$MOVY_DIR/venv/bin/python" "$MOVY_DIR/movy.py" "$@"' > movy
chmod +x movy
```
## Install on Windows (Powershell)
Replace api_key with tmdb api key
```sh
git clone https://github.com/Sand77x/movy-cli.git
cd movy-cli
python -m venv venv
.\venv\Script\activate
pip install -r requirements.txt
echo 'TMDB_API=api_key' > .env
```
## Dependencies
- [fzf](https://github.com/junegunn/fzf)
- [mpv](https://mpv.io/)
- Chrome / Firefox / Edge (if error, run `playwright install chromium`)
- [yt-dlp](https://github.com/yt-dlp/yt-dlp) (if downloading)
- [ffmpeg](https://ffmpeg.org/) (if downloading w/ subtitles)
## Future Features (if I have time)
- Add `--headful`, `--quality`, `--separate-subs`, `--outdir` options
- Add menu for playing next / prev episode in a series
- Use tmdb api for more stuff
