"""
SET (Stock Exchange of Thailand) ticker universe.
Yahoo Finance uses .BK suffix for all SET-listed stocks.
"""

# Full SET universe grouped by sector
SET_TICKERS = {
    "ENERGY": [
        "PTT", "PTTEP", "PTTGC", "TOP", "IRPC", "BCP", "ESSO", "SPRC", "TASCO",
        "BANPU", "RATCH", "EGCO", "GPSC", "EA", "GUNKUL", "TPIPP", "GULF", "CKP",
        "DEMCO", "BGRIM", "WHAUP", "EASTW",
    ],
    "BANKING": [
        "KBANK", "SCB", "BBL", "KTB", "TTB", "TISCO", "KKP", "TCAP",
    ],
    "FINANCE": [
        "AEONTS", "MTC", "SAWAD", "JMT", "TIDLOR", "KTC", "THANI", "MFC",
        "PHATRA", "TKT", "TBANK",
    ],
    "INDUSTRIAL": [
        "SCC", "SCCC", "IVL", "HANA", "DELTA", "KCE", "SVI", "FORTH",
        "COH", "AEC", "ICC", "INOX", "JSP", "SMT", "ESTAR",
    ],
    "PROPERTY": [
        "LH", "QH", "SPALI", "SIRI", "AP", "ORI", "SC", "PSH", "NOBLE",
        "ANAN", "LALIN", "PRUKSA", "SUPALAI", "LPN", "COTTO", "GRAND",
        "PLANET", "KOOL", "RICHY", "MJD",
    ],
    "PFREIT": [
        "CPNREIT", "FTREIT", "GOLDPF", "LHPF", "TICON", "WHART", "TREIT",
        "AIMIRT", "DIF", "FUTUREPF", "POPF", "SSPF",
    ],
    "FOOD_BEVERAGE": [
        "CPF", "TU", "GFPT", "OISHI", "CBG", "OSP", "TKN", "NRF",
        "SAPPE", "TIPCO", "UAC", "SFP", "KASET", "CM",
    ],
    "RETAIL": [
        "CPALL", "MAKRO", "BJC", "CPN", "HMPRO", "CRC", "DOHOME",
        "BEAUTY", "MK", "MINT", "ERW", "CENTEL",
    ],
    "HEALTHCARE": [
        "BDMS", "BCH", "BH", "VIBHA", "CHG", "THCA", "PR9", "EKH",
        "LPH", "RAM", "PHOL",
    ],
    "TELECOM_TECH": [
        "ADVANC", "TRUE", "INTUCH", "JAS", "THCOM", "DTAC",
        "INET", "SIS", "MSC", "CS", "IT",
    ],
    "TRANSPORT": [
        "AOT", "BTS", "BEM", "THAI", "AAV", "BA", "NOK",
        "PSL", "TTA", "WICE", "LEO",
    ],
    "MEDIA": [
        "VGI", "MAJOR", "RS", "BEC", "MONO", "MCOT",
        "WORK", "PLANB", "JMART",
    ],
    "MATERIALS": [
        "STA", "STGT", "TPBI", "UVAN", "NPP", "AGE",
        "PANEL", "SYNTEC", "CK", "ITD", "SEAFCO",
    ],
    "AGRI": [
        "TFG", "CFRESH", "TVO", "SORKON", "CHUO", "MILL",
    ],
}

# Flat list of all tickers (adds .BK for Yahoo Finance)
def get_all_tickers(add_bk_suffix=True):
    tickers = []
    for sector_tickers in SET_TICKERS.values():
        for t in sector_tickers:
            tickers.append(f"{t}.BK" if add_bk_suffix else t)
    return list(dict.fromkeys(tickers))  # deduplicate preserving order

def get_tickers_by_sector(sector, add_bk_suffix=True):
    tickers = SET_TICKERS.get(sector, [])
    if add_bk_suffix:
        return [f"{t}.BK" for t in tickers]
    return tickers

def ticker_to_sector(ticker):
    base = ticker.replace(".BK", "")
    for sector, tickers in SET_TICKERS.items():
        if base in tickers:
            return sector
    return "OTHER"

ALL_TICKERS = get_all_tickers()

if __name__ == "__main__":
    print(f"Total SET tickers in universe: {len(ALL_TICKERS)}")
    for sector, tickers in SET_TICKERS.items():
        print(f"  {sector}: {len(tickers)} tickers")
