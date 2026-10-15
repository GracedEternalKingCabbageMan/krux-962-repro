#!/usr/bin/env python3
"""Verify the synthetic krux#962 repro package using krux v26.08.0's real
wallet.py + psbt.py + key.py (harness/krux/).

Stubbed (none contain policy or validation logic): urandom.py, uUR.py,
krux/krux_settings.py (translation), krux/settings.py (constants),
krux/qr.py (format constants), krux/sats_vb.py (fee display), and an empty
krux/__init__.py for CPython packaging. krux/baseconv.py is the real file.

Usage (desktop python 3.10+):
    pip install embit==0.8.1
    python3 verify_repro.py

For each of the 3 throwaway seeds:
  1. Key + Wallet.load(descriptor) must succeed (cosigner + NUMS checks)
  2. PSBTSigner(wallet, PSBT A with globals) must raise 'Invalid PSBT: policy mismatch'
  3. PSBTSigner(wallet, PSBT B stripped) must succeed
"""
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(HERE, "harness"))

from krux.key import Key, TYPE_MINISCRIPT, P2TR
from krux.wallet import Wallet
from krux.psbt import PSBTSigner
from embit.networks import NETWORKS

mnemonics = [
    line.split(": ", 1)[1].strip()
    for line in open(os.path.join(HERE, "mnemonics.txt"))
]
desc_str = open(os.path.join(HERE, "descriptor.txt")).read().strip()
psbt_a = open(os.path.join(HERE, "psbt_A_with_global_xpubs.txt")).read().strip()
psbt_b = open(os.path.join(HERE, "psbt_B_globals_stripped.txt")).read().strip()

failures = 0
for i, m in enumerate(mnemonics):
    print(f"\n===== seed {i+1} =====")
    key = Key(m, TYPE_MINISCRIPT, network=NETWORKS["main"], script_type=P2TR)
    wallet = Wallet(key)
    try:
        wallet.load(desc_str, 0)  # qr_format=FORMAT_NONE
        print("wallet.load: OK (label:", wallet.label, "| cosigners:",
              len(wallet.policy.get("cosigners", [])), ")")
    except Exception as e:
        print("wallet.load RAISED:", repr(e))
        failures += 1
        continue

    try:
        PSBTSigner(wallet, psbt_a, 0)
        print("PSBT A: UNEXPECTEDLY ACCEPTED")
        failures += 1
    except ValueError as e:
        if str(e) == "Invalid PSBT: policy mismatch":
            print("PSBT A: correctly rejected:", e)
        else:
            print("PSBT A: rejected with WRONG error:", repr(e))
            failures += 1

    try:
        s = PSBTSigner(wallet, psbt_b, 0)
        print("PSBT B: accepted; policy cosigners:", len(s.policy.get("cosigners", [])))
    except Exception as e:
        print("PSBT B: UNEXPECTEDLY RAISED:", repr(e))
        failures += 1

print("\n==== RESULT:", "ALL PASS" if failures == 0 else f"{failures} FAILURES")
sys.exit(1 if failures else 0)
