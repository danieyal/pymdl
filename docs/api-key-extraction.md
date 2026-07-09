# The `mdl-api-key` header

**You do not need to extract anything.** Despite its name, `mdl-api-key` is not a secret and
is not issued by the server — it is a **client-generated nonce**. This library generates a
valid one for you automatically.

## What it actually is

Reverse engineering the app (see the Blutter disassembly under `resources/dart_out/`) shows
the following chain:

- The HTTP layer sends `mdl-api-key: Constants.apiKey` on every request
  (`services/custom_http_client.dart`).
- `Constants.apiKey` is a `late` field whose initializer returns `AppManager.shared`'s key
  field (`config/constants.dart`).
- That field is written exactly once, at startup in `main()`, to the result of
  `Utils.getRandomString()` (`main.dart`).
- `Utils.getRandomString()` builds a **20-character string from `[a-zA-Z0-9]`** using
  `Random._secureRandom` (`utils/utils.dart`).

So the value is random, regenerated on every app launch, and never compared against anything
server-side.

## Verified against production

Live requests to `https://app-api.mydramalist.com/v1` confirm it:

- A freshly generated random key → `200 OK` with real data.
- **No `mdl-api-key` header at all → also `200 OK`.**
- The value has no effect on the response.

The real edge gate is **Cloudflare bot protection**, which fingerprints the client's TLS/HTTP2
handshake (JA3/JA4) — not the `mdl-api-key`. A plain Python HTTP client is challenged with a
`403 "Just a moment..."` page regardless of headers; a client that impersonates a real
mobile/browser TLS fingerprint passes. See the transport notes in the README.

## Using it

Nothing to do — just construct the client:

```python
from mdl import MDLClient

client = MDLClient()   # a valid mdl-api-key is generated automatically
```

You may still pin a specific value if you want reproducible requests, via `api_key=` or the
`MDL_API_KEY` environment variable, but it is optional and carries no security meaning.
