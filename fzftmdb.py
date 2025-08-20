import asyncio
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path

from pyfzf.pyfzf import FzfPrompt
import tmdbsimple as tmdb

fzf = FzfPrompt()

MOVY_DIR = Path(__file__).parent

with open(f'{MOVY_DIR}/API_KEY') as f:
    tmdb.API_KEY = f.read().rstrip("\n")

executor = ThreadPoolExecutor()

async def fetch_seasons(r):
    try:
        loop = asyncio.get_event_loop()
        info = await asyncio.wait_for(loop.run_in_executor(executor, lambda: tmdb.TV(r['id']).info()), timeout=4)
        r['number_of_seasons'] = info['number_of_seasons']
    except asyncio.TimeoutError:
        r['number_of_seasons'] = "?"

def search_movie(q):
    search = tmdb.Search()
    results = search.movie(query=q)['results']
    results.sort(key=lambda x:-x['popularity'])

    ret = fzf.prompt(
        map(
            lambda x: f"{str(x[0] + 1)} {x[1]['title']} ({x[1]['release_date'][:4]})", 
            enumerate(results)
        ),
        "--layout=reverse --prompt=\"Select movie: \""
    )

    if not ret:
        return None

    chosen = int(ret[0].split(' ')[0]) - 1
    return results[chosen]

async def search_tv(q, s, e):
    search = tmdb.Search()
    results = search.tv(query=q)['results']
    results.sort(key=lambda x:-x['popularity'])

    await asyncio.gather(*[fetch_seasons(r) for r in results])

    ret = fzf.prompt(
        map(
            lambda x: f"{str(x[0] + 1)} {x[1]['name']} ({x[1]['number_of_seasons']} seasons)", 
            enumerate(results)
        ),
        "--layout=reverse --prompt=\"Select series: \""
    )

    if not ret:
        return None

    chosen = int(ret[0].split(' ')[0]) - 1
    se_map = get_season_episode_counts(results[chosen]['id'])
    se_chosen = prompt_season_episode(se_map, s, e)

    if not se_chosen:
        return None

    return (results[chosen], *se_chosen)

def get_season_episode_counts(id):
    se_map = {}
    response = tmdb.TV(id)

    for s in response.info()['seasons']:
        if s['episode_count'] > 0 and s['season_number'] > 0:
            se_map[int(s['season_number'])] = s['episode_count']
    return se_map

def prompt_season_episode(se_map, s, e):

    try:
        s = s and int(s) or int(fzf.prompt(se_map.keys(), "--layout=reverse --prompt=\"Select season: \"")[0])
        e = e and int(e) or int(fzf.prompt(range(1, se_map[int(s)] + 1), "--layout=reverse --prompt=\"Select episode: \"")[0])
    except (ValueError, TypeError):
        return None

    if s not in se_map or not (1 <= e <= se_map[s]):
        return None

    return (s, e)
