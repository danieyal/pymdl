# pymdl

An **unofficial**, fully-typed, sync **and** async Python client for the private
MyDramaList app API (`https://app-api.mydramalist.com/v1`), reconstructed from the app's
reverse-engineered spec. Built on [httpx](https://www.python-httpx.org/) and
[Pydantic v2](https://docs.pydantic.dev/).

Install as `pymdl`; import as `mdl`.

> **Interoperability / research tool.** This library targets an **undocumented, private**
> API discovered by decompiling the MyDramaList Flutter app. Endpoint paths and field
> names are inferred from machine code and may change without notice; models tolerate
> unknown/renamed fields but nothing is guaranteed. Use responsibly and in accordance with
> MyDramaList's Terms of Service. Not affiliated with or endorsed by MyDramaList.

## Install

```bash
pip install pymdl
```

## The `mdl-api-key`

Every request needs the app's `mdl-api-key` header. This value is **not** shipped with the
library — it is a runtime-initialized secret inside the app. You must extract it yourself
and supply it via the `api_key=` argument or the `MDL_API_KEY` environment variable. See
[docs/api-key-extraction.md](docs/api-key-extraction.md).

## Quick start (sync)

```python
from mdl import MDLClient

with MDLClient(api_key="...") as client:
    title = client.titles.get_title(686)
    print(title.title, title.rating)

    results = client.search.titles("signal")
    for movie in results:
        print(movie.id, movie.title)
```

## Quick start (async)

```python
import asyncio
from mdl import AsyncMDLClient

async def main():
    async with AsyncMDLClient(api_key="...") as client:
        title = await client.titles.get_title(686)
        print(title.title)

asyncio.run(main())
```

## Authentication

```python
with MDLClient(api_key="...") as client:
    client.auth.login("username", "password")   # password is MD5-hashed for you
    profile = client.account.get_profile()       # bearer token attached automatically
    print(profile.username)
```

Tokens are held in an in-memory store by default. Persist them with `FileTokenStore`:

```python
from mdl import MDLClient, FileTokenStore

client = MDLClient(api_key="...", token_store=FileTokenStore("~/.mydramalist/token.json"))
```

## Resource groups

The client exposes one attribute per API area, e.g.:

| Attribute | Area |
|-----------|------|
| `client.auth` | login, social auth, register, reset password |
| `client.account` | own profile/settings, verification, devices, payments |
| `client.users` | other users & people pages, credits, likes |
| `client.titles` | title detail, progress, reviews, recommendations, credits, genres |
| `client.search` | title & people search |
| `client.explore` | trending / top_airing / upcoming / recommended feeds |
| `client.reviews` | review CRUD, voting |
| `client.comments` | comment listing & CRUD |
| `client.watchlist` | watchlist sync (add/remove/status lists) |
| `client.custom_lists` | custom lists, items, votes |
| `client.feeds` | activity feed, posts, embeds, uploads |
| `client.articles` | articles |
| `client.friends` / `client.messages` / `client.notifications` / `client.groups` | social |
| `client.subscription` / `client.flowers` / `client.awards` / `client.reports` | misc |
| `client.calendar` / `client.leaderboard` | calendar & leaderboard |

## Development

The async implementation under `src/mdl/_async` is the **source of truth**; the sync
package `src/mdl/_sync` is generated from it with
[`unasync`](https://pypi.org/project/unasync/):

```bash
pip install -e ".[dev]"
python scripts/build_sync.py     # regenerate _sync after editing _async
python scripts/check_sync.py     # verify _sync is up to date (CI does this)
ruff check src tests
mypy
pytest
```

## License

MIT
