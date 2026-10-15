class UR:
    def __init__(self, *a, **k): pass
class Types:
    CRYPTO_PSBT_TYPE = "crypto-psbt"
    @staticmethod
    def psbt_from_cbor(cbor): return cbor
    @staticmethod
    def psbt_to_cbor(b): return b
