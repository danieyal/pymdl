# mdl

An **unofficial**, fully-typed, sync **and** async Python client for the private
MyDramaList app API (`https://app-api.mydramalist.com/v1`), reconstructed from the app's
reverse-engineered spec. Built on [curl_cffi](https://github.com/lexiforest/curl_cffi) and
[Pydantic v2](https://docs.pydantic.dev/).

Install as `mydramalist-client`; import as `mdl`.

> **Interoperability / research tool.** This library targets an **undocumented, private**
> API discovered by decompiling the MyDramaList Flutter app. Endpoint paths and field
> names are inferred from machine code and may change without notice; models tolerate
> unknown/renamed fields but nothing is guaranteed. Use responsibly and in accordance with
> MyDramaList's Terms of Service. Not affiliated with or endorsed by MyDramaList.

## Install

```bash
pip install mydramalist-client
```

## The `mdl-api-key`

Despite its name, `mdl-api-key` is **not a secret** — the app fills it with a random 20-char
string generated on each launch, and the server does not validate it. This library generates
a valid one for you, so you do not need to extract or supply anything. You may still pin a
value via `api_key=` or `MDL_API_KEY` for reproducible requests, but it is optional. See
[docs/api-key-extraction.md](docs/api-key-extraction.md).

> **Heads up — Cloudflare:** production sits behind Cloudflare bot protection that fingerprints
> the client's TLS handshake. A plain `httpx`/`requests` client is served a `403 "Just a
moment..."` challenge; only a client impersonating a real mobile/browser TLS fingerprint
> gets through. See [Transport](#transport).

## Quick start (sync)

```python
from mdl import MDLClient

with MDLClient() as client:   # api_key generated automatically
    client.auth.login("username", "password")   # title & search endpoints need a login
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
        await client.auth.login("username", "password")
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

Most endpoints need a logged-in client. Since October 2026 the API rejects anonymous
requests to title detail, credits, recommendations, search, explore feeds and every
account/sync endpoint with a bare `400 Bad Request`; the client raises
`MDLLoginRequiredError` (a subclass of `MDLAuthError`) for these. Genres, tag search,
articles, reviews and public custom lists still work without logging in.

Rejected credentials raise `MDLAuthError` — the API reports them as `400 "Invalid password
or username."`, not 401.

Tokens are held in an in-memory store by default. Persist them with `FileTokenStore`:

```python
from mdl import MDLClient, FileTokenStore

client = MDLClient(token_store=FileTokenStore("~/.mydramalist/token.json"))
```

Access tokens last 30 days. When a request gets a 401, the client exchanges the stored
refresh token for a new pair once and retries; a `FileTokenStore` saves the new pair. If
there is no refresh token or the refresh is rejected, the stored tokens are cleared and
`MDLAuthError` is raised, so log in again. Call `client.auth.refresh()` to refresh ahead of
expiry.

## Your lists

```python
from mdl import MDLClient, MDLSyncError
from mdl.models import MovieStatusType

with MDLClient() as client:
    client.auth.login("username", "password")
    for entry in client.watchlist.fetch(MovieStatusType.WATCHING):
        print(entry.title.title, entry.episode_seen, "/", entry.title.episodes)

    # Change one entry; fields you don't pass keep their current values.
    client.watchlist.update(18452, episode_seen=5)
    client.watchlist.update(18452, status=MovieStatusType.COMPLETED, rating=9.5)
    client.watchlist.update(36269, status="plantowatch")  # adds the title

    client.watchlist.remove([36269])
```

`POST /sync/mylist` takes a JSON array of entries and **replaces** each stored entry, so
a field left out of the body is reset (an omitted `rating` clears the score).
`watchlist.update()` reads the current entry first and sends it back whole;
`watchlist.save()` sends entries as given. Moving a title to Completed without an
`episode_seen` marks every episode seen, as the app does.

The endpoint answers `200` even when it rejects a title, listing it under `failed` with
a reason such as "This show has not aired yet." or "Invalid episode seen value.".
`update()` raises `MDLSyncError` for these; `save()` returns them in
`SyncWatchListResponse.failures`. An empty `note` leaves the stored note alone (the API
cannot clear a note), and the first save of a title that was once removed restores its
old progress, which `update()` corrects with a second save.

`watchlist.get_last_activities().all` changes whenever any list changes (removals
included), so you can poll it instead of refetching every list.

`client.users.get_user_stats(username)` returns watch time, episode counts and the score
distribution; `client.calendar.episodes()` returns the airing schedule for the week
starting the previous UTC day, with `add_status` set on titles in your lists.

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

| Attribute                                                                       | Area                                                              |
| ------------------------------------------------------------------------------- | ----------------------------------------------------------------- |
| `client.auth`                                                                   | login, social auth, register, reset password                      |
| `client.account`                                                                | own profile/settings, verification, devices, payments             |
| `client.users`                                                                  | other users & people pages, credits, likes                        |
| `client.titles`                                                                 | title detail, progress, reviews, recommendations, credits, genres |
| `client.search`                                                                 | title & people search                                             |
| `client.explore`                                                                | trending / top_airing / upcoming / recommended feeds              |
| `client.reviews`                                                                | review CRUD, voting                                               |
| `client.comments`                                                               | comment listing & CRUD                                            |
| `client.watchlist`                                                              | watchlist sync (add/remove/status lists)                          |
| `client.custom_lists`                                                           | custom lists, items, votes                                        |
| `client.feeds`                                                                  | activity feed, posts, embeds, uploads                             |
| `client.articles`                                                               | articles                                                          |
| `client.friends` / `client.messages` / `client.notifications` / `client.groups` | social                                                            |
| `client.subscription` / `client.flowers` / `client.awards` / `client.reports`   | misc                                                              |
| `client.calendar` / `client.leaderboard`                                        | calendar & leaderboard                                            |

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
