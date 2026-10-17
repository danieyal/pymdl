# mdl

An **unofficial**, fully-typed, sync **and** async Python client for the private
MyDramaList app API, built on curl_cffi and Pydantic v2. Install as `mydramalist-client`; import
as `mdl`.

!!! warning "Interoperability / research tool"
This library targets an **undocumented, private** API discovered by decompiling the
MyDramaList Flutter app. Paths and field names may change without notice. Use
responsibly and in accordance with MyDramaList's Terms of Service. Not affiliated with
or endorsed by MyDramaList.

## Install

```bash
pip install mydramalist-client
```

The `mdl-api-key` is a client-generated nonce, not a secret — one is generated for you. Note
that production is behind Cloudflare TLS fingerprinting; see
[the `mdl-api-key` notes](api-key-extraction.md).

## Sync

```python
from mdl import MDLClient

with MDLClient() as client:
    client.auth.login("username", "password")   # title & search endpoints need a login
    title = client.titles.get_title(686)
    print(title.title, title.rating)
```

## Async

```python
import asyncio
from mdl import AsyncMDLClient

async def main():
    async with AsyncMDLClient() as client:
        await client.auth.login("username", "password")
        print((await client.titles.get_title(686)).title)

asyncio.run(main())
```

## Authentication

```python
with MDLClient() as client:
    client.auth.login("username", "password")   # MD5-hashed automatically
    print(client.account.get_profile().username)
```

On a 401 the client exchanges the stored refresh token for a new pair once and retries
the request. `client.auth.refresh()` does the same on demand.

## Errors

All errors derive from `mdl.MDLError`. HTTP failures raise `MDLNetworkError`
subclasses (`MDLAuthError` for 401, `MDLNotFoundError` for 404, `MDLRateLimitedError` for
429, `MDLServerError` for 5xx), each carrying `.status_code`, `.message`, and `.body`.

`MDLAuthError` is also raised when `auth.login()` is given bad credentials (the API reports
these as 400). Anonymous requests to login-only endpoints — title detail, credits,
recommendations, search, explore feeds, account and sync — raise `MDLLoginRequiredError`,
a subclass of `MDLAuthError`.

## Pagination

List endpoints accept `page` / `limit`. Where the API reports a grand total via the
`x-pagination-total` header (e.g. comment counts), it is surfaced through the `Page` helper.
