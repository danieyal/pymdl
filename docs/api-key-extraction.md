# Extracting the `mdl-api-key`

Every request to the MyDramaList app API must carry two headers the app sets internally:

- `mdl-api-key` — the app's API key (`Constants.apiKey`)
- `version` — the app version string (e.g. `2.3.3`)

The library does **not** ship the key. In the decompiled app, `Constants.apiKey` is a
`static late` field **initialized at runtime**, so it is not a plain string constant you can
grep out of the binary. The reliable way to obtain it is to observe a live request.

## Option A — Frida (recommended)

The reverse-engineering artifacts include a ready-to-use Frida script,
`resources/dart_out/blutter_frida.js`, that can hook `CustomHttpClient.get/post` and log the
live URL, headers and body of every request the app makes.

1. Install Frida and set up a rooted device / emulator with the MDL app.
2. Attach Frida with the provided script and hook the HTTP client methods.
3. Trigger any action in the app (open a title, search, log in).
4. Read the `mdl-api-key` and `version` header values from the logged request.

## Option B — Proxy capture

Route the app's traffic through an intercepting proxy (mitmproxy / Charles) with the app's
certificate pinning disabled, then read the `mdl-api-key` and `version` request headers from
any captured call.

## Using the values

```python
from mdl import MDLClient

client = MDLClient(api_key="<captured-key>", app_version="2.3.3")
```

Or via environment variables:

```bash
export MDL_API_KEY="<captured-key>"
export MDL_APP_VERSION="2.3.3"
```

```python
from mdl import MDLClient
client = MDLClient()   # picks up MDL_API_KEY / MDL_APP_VERSION
```
