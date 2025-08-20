import sys
import requests
import subprocess
import threading
import asyncio
import shutil
import tempfile

from playwright.async_api import BrowserType, async_playwright
from playwright_stealth import Stealth

from parse import parse
from colors import *


async def main():
    if not shutil.which("fzf"):
        print(RED("Error:"), "fzf not found in PATH.")
        return

    if not shutil.which("mpv"):
        print(RED("Error:"), "mpv not found in PATH.")
        return

    from fzftmdb import search_movie, search_tv

    args = parse(sys.argv[1:])

    if not args or "help" in args:
        with open('help.txt', 'r') as f:
            print(f.read())
        return

    QUERY = "query" in args and args["query"] or None
    SEASON = "season" in args and args["season"] or None
    EPISODE = "episode" in args and args["episode"] or None

    DETACH = "no-detach" not in args
    SUBS = "no-subs" not in args
    DOWNLOAD = "download" in args

    MEDIA_TYPE = args["media_type"]

    found_stream = None
    found_subs = []

    media_name = None

    if MEDIA_TYPE == "movie":
        if QUERY:
            res = search_movie(QUERY)
        else:
            res = search_movie(input(PURPLE("Movie name: ")))

        if not res:
            print(YELLOW("No movies found with that search query."))
            return

        media_name = f"{res['title']} ({res['release_date'][:4]})"

        print("\nSelected",  GREEN('"' + media_name + '"'))

        id = res['id']

        # url = f"https://hexa.watch/watch/tv/{id}/{s}/{e}"
        url = f"https://fmovies.gd/watch/movie/{id}"
        subs_url = f"https://sub.wyzie.ru/search?id={id}&format=srt&language=en"
    elif MEDIA_TYPE == "tv":
        if QUERY:
            chosen = await search_tv(QUERY, SEASON, EPISODE)
        else:
            chosen = await search_tv(input(PURPLE("Series name: ")), SEASON, EPISODE)

        if not chosen:
            print(YELLOW("No series found with that search query."))
            return

        res, s, e = chosen
        media_name = f"{res['name']} S{s} E{e}"
        print("\nSelected",  GREEN('"' + media_name + '"'))

        id = res['id']
        # url = f"https://hexa.watch/watch/tv/{id}/{s}/{e}"
        url = f"https://fmovies.gd/watch/tv/{id}/{s}/{e}"
        subs_url = f"https://sub.wyzie.ru/search?id={id}&format=srt&season={s}&episode={e}&language=en"
    else:
        print(RED("Invalid media type:"), "only [mv|movie|tv] are allowed")
        return

    if SUBS:
        try:
            subs_r = requests.get(subs_url, timeout=5)
            rj = subs_r.json()
            cnt = 0
            for i in rj:
                if cnt > 8:
                    break
                found_subs.append(i["url"])
                cnt += 1
            print(YELLOW("• Found subs:"), cnt)
        except:
            print(YELLOW("• No subs found."))


    async with Stealth().use_async(async_playwright()) as p:
        browsers = [
            (p.chromium, "chrome"),
            (p.chromium, "msedge"),
            (p.firefox, "firefox"),
            (p.chromium, None),
            (p.firefox, None),
            (p.webkit, None),
        ]

        browser = None

        async def get_browser(browser: tuple[BrowserType, str]):
            b, c = browser
            try:
                return await b.launch(channel=c, headless=True)
            except:
                return None

        for b in browsers:
            browser = await get_browser(b)
            if browser:
                break

        if not browser:
            print(RED("Error:"), "No installed browser found. Type `playwright install chromium` to install chromium.")
            return

        context = await browser.new_context()
        page = await context.new_page()

        def on_response(response):
            nonlocal found_stream
            if not found_stream and ".m3u8" in response.url:
                found_stream = response.url
                print(YELLOW("• Found stream url:"), response.url[:32] + "..." + response.url[-8:])

        page.on("response", on_response)

        await page.goto(url, wait_until="domcontentloaded")
        await page.click("button")
        await page.bring_to_front()

        for i in range(15):
            if not found_stream:
                await page.wait_for_timeout(1000)
            else:
                break

        await browser.close()

        if not found_stream:
            print(RED("Error:"), "No sources found or site timed out! Please try again.")
        else:
            if DOWNLOAD:
                if not shutil.which("yt-dlp"):
                    print(RED("Error:"), "yt-dlp not found in PATH.")
                    return

                try:
                    tempdir = tempfile.mkdtemp()
                except:
                    print(RED("Error:"), "Failed to create temp directory.")
                    return

                try:
                    print(YELLOW("• Downloading video.."))

                    media_name += ".mp4"
                    cmd = [
                        "yt-dlp", "-q", "--no-warnings", 
                        "--progress", found_stream, "-o"
                    ]

                    if SUBS:
                        cmd.append(f"{tempdir}/video.mp4")
                    else:
                        cmd.append(f"{tempdir}/{media_name}")

                    process = subprocess.run(cmd, 
                                 check=True,
                                 stderr=subprocess.DEVNULL)

                    if process.returncode != 0:
                        print(RED("error:"), "failed to download video.")
                        return

                    # download subs
                    dl_cnt = 0
                    if SUBS:
                        if not shutil.which("ffmpeg"):
                            print(RED("Error:"), "ffmpeg not found in PATH.")

                        print(YELLOW("• Downloading subs.."))

                        for i, s in enumerate(found_subs):
                            try:
                                r = requests.get(s, timeout=4)
                                if r.status_code != 200:
                                    continue
                                dl_cnt += 1
                                with open(f"{tempdir}/subs_{i}.srt", "wb") as f:
                                    f.write(r.content)
                            except:
                                pass

                        # attach subs
                        print(YELLOW("• Attaching subs to video.."))

                        cmd = [
                            "ffmpeg", "-y",
                            "-i", f"{tempdir}/video.mp4",
                        ]

                        for i in range(dl_cnt):
                            cmd.extend(["-i", f"{tempdir}/subs_{i}.srt"])

                        cmd.extend(["-map", "0:v", "-map", "0:a?"])
                        for i in range(dl_cnt):
                            cmd.extend(["-map", f"{i+1}:s:0"])

                        cmd.extend(["-c", "copy", "-c:s", "mov_text", f"{tempdir}/{media_name}"])

                        process = subprocess.run(cmd, 
                                     check=True,
                                     stdout=subprocess.DEVNULL,
                                     stderr=subprocess.DEVNULL)

                        if process.returncode != 0:
                            print(RED("error:"), "failed to attach subs, video is still downloaded.")
                            shutil.move(f"{tempdir}/video.mp4", f"{tempdir}/{media_name}")

                    print(YELLOW("\n• Finished downloading:"), '"' + media_name + '"')
                finally:
                    try:
                        shutil.move(f"{tempdir}/{media_name}", media_name)
                        shutil.rmtree(tempdir)
                    except Exception as e:
                        print(RED("Error:"), e)
            else:
                print(YELLOW("• Launching mpv"))

                process = subprocess.Popen(
                    ["mpv", found_stream, *[f"--sub-file={x}" for x in found_subs]],
                    stdout=DETACH and subprocess.DEVNULL or None,
                    stderr=DETACH and subprocess.DEVNULL or None,
                    start_new_session=DETACH
                )

                def check(proc):
                    try:
                        rc = proc.wait(timeout=10)
                        if rc != 0:
                            print("Error: Invalid stream url, please try again later")
                    except subprocess.TimeoutExpired:
                        pass

                if DETACH:
                    threading.Thread(target=check, args=(process,), daemon=True).start()
                else:
                    check(process)

if __name__ == "__main__":
    asyncio.run(main())
