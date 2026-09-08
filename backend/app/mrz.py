import re

MRZ_CHARS = set("ABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789<")

def normalize_lines(text: str) -> list[str]:
    lines = []
    for raw in text.splitlines():
        s = re.sub(r"\s+", "", raw.upper())
        if len(s) >= 25 and sum(c in MRZ_CHARS for c in s) / len(s) > 0.88:
            lines.append(s)
    return lines

def check_digit(value: str) -> int:
    weights = [7, 3, 1]; total = 0
    for i, ch in enumerate(value):
        v = 0 if ch == '<' else int(ch) if ch.isdigit() else ord(ch) - 55
        total += v * weights[i % 3]
    return total % 10

def parse_mrz(text: str) -> dict:
    lines = normalize_lines(text); candidates = [x for x in lines if len(x) >= 40]
    for i in range(len(candidates) - 1):
        a, b = candidates[i][:44].ljust(44, '<'), candidates[i + 1][:44].ljust(44, '<')
        if a.startswith(('P<', 'V<')) and len(b) >= 44:
            passport_no = b[0:9]; dob = b[13:19]; expiry = b[21:27]
            return {"format":"TD3","line1":a,"line2":b,"passport_number":passport_no.replace('<',''),"date_of_birth":dob,"expiry_date":expiry,"nationality":b[10:13].replace('<',''),"sex":b[20],"passport_number_checksum_valid":passport_no[-1].isdigit() and check_digit(passport_no[:-1]) == int(passport_no[-1]),"date_of_birth_checksum_valid":dob[-1].isdigit() and check_digit(dob[:-1]) == int(dob[-1]),"expiry_date_checksum_valid":expiry[-1].isdigit() and check_digit(expiry[:-1]) == int(expiry[-1])}
    return {"format":None,"lines_detected":len(lines)}
