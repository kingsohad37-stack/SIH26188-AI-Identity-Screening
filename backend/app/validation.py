from datetime import date

def _mrz_date(value: str):
    if len(value) != 6 or not value.isdigit(): return None
    yy, mm, dd = int(value[:2]), int(value[2:4]), int(value[4:6]); current = date.today().year % 100
    year = 2000 + yy if yy <= current + 10 else 1900 + yy
    try: return date(year, mm, dd)
    except ValueError: return None

def validate_mrz(mrz: dict) -> dict:
    if mrz.get("format") != "TD3": return {"status":"not_evaluated","reasons":["TD3 passport MRZ not detected"]}
    reasons=[]; checks={"passport_number_checksum":bool(mrz.get("passport_number_checksum_valid")),"date_of_birth_checksum":bool(mrz.get("date_of_birth_checksum_valid")),"expiry_date_checksum":bool(mrz.get("expiry_date_checksum_valid"))}
    for name, ok in checks.items():
        if not ok: reasons.append(f"{name}_failed")
    dob=_mrz_date(mrz.get("date_of_birth","")); expiry=_mrz_date(mrz.get("expiry_date",""))
    if dob is None: reasons.append("date_of_birth_invalid")
    if expiry is None: reasons.append("expiry_date_invalid")
    if expiry and expiry < date.today(): reasons.append("document_expired")
    if dob and dob > date.today(): reasons.append("date_of_birth_in_future")
    return {"status":"passed" if not reasons else "failed","checksum_checks":checks,"reasons":reasons,"expired":bool(expiry and expiry < date.today())}

def assess_forensics(forensics: list[dict]) -> dict:
    if not forensics: return {"status":"not_evaluated","flags":[]}
    flags=[]
    for i,item in enumerate(forensics):
        if not item.get("available"): continue
        ela=item.get("ela",{})
        if ela.get("available") and ela.get("high_error_area_ratio",0)>0.08 and ela.get("p95_error",0)>18:
            flags.append({"page":i+1,"code":"LOCALIZED_RECOMPRESSION_DIFFERENCE","severity":"warning"})
        for flag in item.get("quality_flags",[]): flags.append({"page":i+1,"code":flag.upper(),"severity":"info"})
    return {"status":"suspicious" if any(f["severity"]=="warning" for f in flags) else "passed","flags":flags}
