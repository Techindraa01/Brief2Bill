"""Repair defaults for last-resort field fixes"""
def repair_bundle(bundle: dict) -> dict:
    if "drafts" not in bundle:
        bundle["drafts"] = []
    return bundle
