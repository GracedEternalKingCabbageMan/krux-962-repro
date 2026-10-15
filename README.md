# Repro package for krux#962

Taproot miniscript PSBT rejected with `Invalid PSBT: policy mismatch` when the PSBT
carries `PSBT_GLOBAL_XPUB` fields — because `PSBTSigner.xpubs()` then never consults the
loaded descriptor and drops the origin-less internal (NUMS) key. (Present in v26.08.0 and
still in v26.09.0 / `main` as of this writing.)

Everything in this package is throwaway: the three mnemonics below were generated solely
for this repro and are published in full. **Never send funds to this wallet.** (The PSBT's
destination is an unrelated third-party address that already exists on-chain — irrelevant
here because the input UTXO is fabricated and nothing can ever be broadcast, but don't
reuse any of this for anything real.)

## Contents

- `mnemonics.txt` — three throwaway 12-word BIP39 mnemonics (mainnet)
- `descriptor.txt` — wallet descriptor: `tr(<origin-less NUMS-wrapped xpub>/<0;1>/*, {multi_a(2, [3 cosigner keys @ m/48'/0'/0'/2']/<0;1>/*)})`
- `psbt_A_with_global_xpubs.txt` — base64 PSBT spending a hypothetical UTXO at the
  wallet's address 0, carrying 3 `PSBT_GLOBAL_XPUB` entries (the coordinator behavior
  that triggers the bug)
- `psbt_B_globals_stripped.txt` — byte-identical except the global-xpub records are removed
- `verify_repro.py` — desktop harness runner (see below)
- `harness/` — krux v26.08.0's **real** `psbt.py`, `wallet.py`, `key.py` (byte-identical
  to the release tag) plus stubs for modules that can't run on desktop Python

## On-device / simulator repro

1. Load seed 1 from `mnemonics.txt` on the device (or simulator). Any of the three seeds
   works — all are cosigners.
2. Load `descriptor.txt` as the wallet. Krux accepts it — the internal key is provably
   unspendable (BIP-341 NUMS point), which Krux checks at load. Note: if the key was
   loaded with the default single-sig policy, you'll first get a normal
   "Wallet mismatch … Change wallet?" prompt — accept it.
3. Import **PSBT A** as you normally would (QR or SD card).
   **Expected:** rejected with `Invalid PSBT: policy mismatch`. On hardware the screen
   shows `Error:\nValueError('Invalid PSBT: policy mismatch',)` (MicroPython repr, with
   trailing comma); in the desktop simulator the same error shows without the trailing
   comma.
4. Import **PSBT B** the same way.
   **Expected:** accepted; cosigner policy matches the loaded wallet; the signing flow
   proceeds. Note: the fee is deliberately oversized (11.2%), so a normal
   "Warning: High fees!" prompt appears — accept it to continue.

## Desktop harness repro (no device needed)

Requires Python 3.10+ and `pip install embit==0.8.1` (code-identical to the embit
`fff7ffa` vendored by krux v26.08.0).

```
python3 verify_repro.py
```

Expected output: for each seed, `wallet.load: OK`,
`PSBT A: correctly rejected: Invalid PSBT: policy mismatch`, `PSBT B: accepted`.

The harness runs krux's real `wallet.py`, `key.py` and `psbt.py` from v26.08.0. Stubbed
(none of them contain policy or validation logic): `urandom.py` and `uUR.py`
(MicroPython/native modules), `krux/krux_settings.py` (translation `t()`; real module
imports `board`), `krux/settings.py` (constants; real module imports `ujson`),
`krux/qr.py` (format constants; real module imports `qrcode`), `krux/sats_vb.py`
(fee-display helper), plus an empty `krux/__init__.py` for CPython packaging.
`krux/baseconv.py` (PSBT text decoding) is the **real** file, not a stub.

## What was verified about this package before posting

- All three seeds load the descriptor through krux's real `Wallet.load()` (cosigner match,
  NUMS unspendability check, network check) — pass.
- PSBT A → `Invalid PSBT: policy mismatch`; PSBT B → accepted, with cosigner policy equal
  to the wallet's (4 cosigners incl. the origin-less NUMS xpub) — via krux's real
  `PSBTSigner`, for all three seeds.
- The PSBT's taproot data is cryptographically consistent: control block + leaf script +
  internal key reconstruct the exact output key of the spent `witness_utxo`
  scriptPubKey (independent BIP-341 recomputation).
- PSBT B is genuinely signable: a BIP-341 tapscript signature for its input was produced
  and verified with seed 1's leaf key (`m/48'/0'/0'/2'/0/0`).
- A and B serialize the identical unsigned transaction; they differ only in the 3
  `PSBT_GLOBAL_XPUB` records.
