# pymdl

An **unofficial**, fully-typed, sync **and** async Python client for the private
MyDramaList app API (`https://app-api.mydramalist.com/v1`), reconstructed from the app's
reverse-engineered spec. Built on [curl_cffi](https://github.com/lexiforest/curl_cffi) and
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

Despite its name, `mdl-api-key` is **not a secret** — the app fills it with a random 20-char
string generated on each launch, and the server does not validate it. This library generates
a valid one for you, so you do not need to extract or supply anything. You may still pin a
value via `api_key=` or `MDL_API_KEY` for reproducible requests, but it is optional. See
[docs/api-key-extraction.md](docs/api-key-extraction.md).

> **Heads up — Cloudflare:** production sits behind Cloudflare bot protection that fingerprints
> the client's TLS handshake. A plain `httpx`/`requests` client is served a `403 "Just a
> moment..."` challenge; only a client impersonating a real mobile/browser TLS fingerprint
> gets through. See [Transport](#transport).

## Quick start (sync)

```python
from mdl import MDLClient

with MDLClient() as client:   # api_key generated automatically
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
    async with AsyncMDLClient() as client:
        title = await client.titles.get_title(686)
        print(title.title)

asyncio.run(main())
```

## Authentication

```python
with MDLClient() as client:
    client.auth.login("username", "password")   # password is MD5-hashed for you
    profile = client.account.get_profile()       # bearer token attached automatically
    print(profile.username)
```

Tokens are held in an in-memory store by default. Persist them with `FileTokenStore`:

```python
from mdl import MDLClient, FileTokenStore

client = MDLClient(token_store=FileTokenStore("~/.mydramalist/token.json"))
```

The client clears stored tokens on 401 and raises `MDLAuthError`. Automatic
token refresh via `refresh_token` is not yet implemented — callers must
re-authenticate when the access token expires.

## Transport

Production MyDramaList sits behind **Cloudflare bot protection** that fingerprints the
client's TLS/HTTP2 handshake (JA3/JA4). This is the real access gate — not the `mdl-api-key`.

A plain `httpx`/`requests` client (a stock Python TLS stack) is served Cloudflare's
`403 "Just a moment..."` challenge on every request, regardless of headers or User-Agent.
Only a client that impersonates a real mobile/browser TLS fingerprint is allowed through — in
testing, [`curl_cffi`](https://github.com/lexiforest/curl_cffi) with `impersonate="safari_ios"`
(or `chrome`) reaches the API and returns real JSON.

If you get `403` responses with a `"Just a moment..."` HTML body, this is why: the request
never reached the API, it was stopped at Cloudflare's edge.

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
