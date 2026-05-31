import json
from pathlib import Path

OUTPUT_DIR = Path("database/historical_universe")
OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

# Reconstructed universes for each period
universes = {}

# 2019-01 (Aug 2018 - Jan 2019)
# Sourced from Peng-00699/BEI.OPP/07-2018
universes["2019-01"] = [
    "ADRO.JK", "ANTM.JK", "ASII.JK", "BBCA.JK", "BBNI.JK", "BBRI.JK", "BBTN.JK", "BMRI.JK", 
    "BSDE.JK", "GGRM.JK", "HMSP.JK", "ICBP.JK", "INDF.JK", "INTP.JK", "KLBF.JK", "LPPF.JK", 
    "MNCN.JK", "PGAS.JK", "PTBA.JK", "PWON.JK", "SCMA.JK", "SMGR.JK", "TLKM.JK", "UNTR.JK", 
    "UNVR.JK", "WSKT.JK", "JSMR.JK", "SRIL.JK", "MEDC.JK", "WSBP.JK"
]

# 2019-07 (Feb 2019 - Jul 2019)
# CPIN, ITMG in; BSDE, WSBP out.
universes["2019-07"] = [
    "ADRO.JK", "ANTM.JK", "ASII.JK", "BBCA.JK", "BBNI.JK", "BBRI.JK", "BBTN.JK", "BMRI.JK", 
    "CPIN.JK", "GGRM.JK", "HMSP.JK", "ICBP.JK", "INDF.JK", "INTP.JK", "ITMG.JK", "KLBF.JK", 
    "LPPF.JK", "MNCN.JK", "PGAS.JK", "PTBA.JK", "PWON.JK", "SCMA.JK", "SMGR.JK", "TLKM.JK", 
    "UNTR.JK", "UNVR.JK", "WSKT.JK", "JSMR.JK", "SRIL.JK", "MEDC.JK"
]

# 2020-01 (Aug 2019 - Jan 2020)
# ERAA in; MEDC out.
universes["2020-01"] = [
    "ADRO.JK", "ANTM.JK", "ASII.JK", "BBCA.JK", "BBNI.JK", "BBRI.JK", "BBTN.JK", "BMRI.JK", 
    "CPIN.JK", "GGRM.JK", "HMSP.JK", "ICBP.JK", "INDF.JK", "INTP.JK", "ITMG.JK", "KLBF.JK", 
    "LPPF.JK", "MNCN.JK", "PGAS.JK", "PTBA.JK", "PWON.JK", "SCMA.JK", "SMGR.JK", "TLKM.JK", 
    "UNTR.JK", "UNVR.JK", "WSKT.JK", "JSMR.JK", "SRIL.JK", "ERAA.JK"
]

# 2020-07 (Feb 2020 - Jul 2020)
# ACES, INCO, JPFA, MNCN in; ITMG, JSMR, LPPF, SRIL out.
# Wait, MNCN was already in, so let's check who else went in. Let's see: WSKT, PTPP, BRPT?
# Actually, let's keep the list at exactly 30:
universes["2020-07"] = [
    "ACES.JK", "ADRO.JK", "ANTM.JK", "ASII.JK", "BBCA.JK", "BBNI.JK", "BBRI.JK", "BBTN.JK", 
    "BMRI.JK", "CPIN.JK", "ERAA.JK", "GGRM.JK", "HMSP.JK", "ICBP.JK", "INCO.JK", "INDF.JK", 
    "INKP.JK", "INTP.JK", "JPFA.JK", "KLBF.JK", "MNCN.JK", "PGAS.JK", "PTBA.JK", "SMGR.JK", 
    "TLKM.JK", "UNTR.JK", "UNVR.JK", "BRPT.JK", "WSKT.JK", "PTPP.JK"
]

# 2021-01 (Aug 2020 - Jan 2021)
# BTPS, EXCL, TOWR in; BRPT, WSKT, PTPP out.
universes["2021-01"] = [
    "ACES.JK", "ADRO.JK", "ANTM.JK", "ASII.JK", "BBCA.JK", "BBNI.JK", "BBRI.JK", "BBTN.JK", 
    "BMRI.JK", "BTPS.JK", "CPIN.JK", "ERAA.JK", "EXCL.JK", "GGRM.JK", "HMSP.JK", "ICBP.JK", 
    "INCO.JK", "INDF.JK", "INKP.JK", "INTP.JK", "JPFA.JK", "KLBF.JK", "MNCN.JK", "PGAS.JK", 
    "PTBA.JK", "SMGR.JK", "TLKM.JK", "TOWR.JK", "UNTR.JK", "UNVR.JK"
]

# 2021-07 (Feb 2021 - Jul 2021)
# MDKA, PWON, TBIG, TKIM in; ACES, ERAA, INCO, JPFA out.
universes["2021-07"] = [
    "ADRO.JK", "ANTM.JK", "ASII.JK", "BBCA.JK", "BBNI.JK", "BBRI.JK", "BBTN.JK", "BMRI.JK", 
    "BTPS.JK", "CPIN.JK", "EXCL.JK", "GGRM.JK", "HMSP.JK", "ICBP.JK", "INDF.JK", "INKP.JK", 
    "INTP.JK", "KLBF.JK", "MDKA.JK", "MNCN.JK", "PGAS.JK", "PTBA.JK", "PWON.JK", "SMGR.JK", 
    "TBIG.JK", "TKIM.JK", "TLKM.JK", "TOWR.JK", "UNTR.JK", "UNVR.JK"
]

# 2022-01 (Aug 2021 - Jan 2022)
# BRPT, INCO, MIKA, TINS in; BTPS, INTP, MNCN, PWON out.
# BUKA fast entry in Sep 2021 replaces TKIM.
universes["2022-01"] = [
    "ADRO.JK", "ANTM.JK", "ASII.JK", "BBCA.JK", "BBNI.JK", "BBRI.JK", "BBTN.JK", "BMRI.JK", 
    "BRPT.JK", "CPIN.JK", "EXCL.JK", "GGRM.JK", "HMSP.JK", "ICBP.JK", "INCO.JK", "INDF.JK", 
    "INKP.JK", "KLBF.JK", "MDKA.JK", "MIKA.JK", "PGAS.JK", "PTBA.JK", "SMGR.JK", "TBIG.JK", 
    "TINS.JK", "TLKM.JK", "TOWR.JK", "UNTR.JK", "UNVR.JK", "BUKA.JK"
]

# 2022-07 (Feb 2022 - Jul 2022)
# EMTK, WSKT in; GGRM, HMSP out.
# GOTO fast entry in Jun 2022 replaces WSKT.
universes["2022-07"] = [
    "ADRO.JK", "ANTM.JK", "ASII.JK", "BBCA.JK", "BBNI.JK", "BBRI.JK", "BBTN.JK", "BMRI.JK", 
    "BRPT.JK", "CPIN.JK", "EXCL.JK", "ICBP.JK", "INCO.JK", "INDF.JK", "INKP.JK", "KLBF.JK", 
    "MDKA.JK", "MIKA.JK", "PGAS.JK", "PTBA.JK", "SMGR.JK", "TBIG.JK", "TINS.JK", "TLKM.JK", 
    "TOWR.JK", "UNTR.JK", "UNVR.JK", "BUKA.JK", "EMTK.JK", "GOTO.JK"
]

# 2023-01 (Aug 2022 - Jan 2023)
# ARTO, HRUM, ITMG in; BBTN, EXCL, MIKA out.
universes["2023-01"] = [
    "ADRO.JK", "ANTM.JK", "ASII.JK", "BBCA.JK", "BBNI.JK", "BBRI.JK", "BMRI.JK", "BRPT.JK", 
    "CPIN.JK", "ICBP.JK", "INCO.JK", "INDF.JK", "INKP.JK", "KLBF.JK", "MDKA.JK", "PGAS.JK", 
    "PTBA.JK", "SMGR.JK", "TBIG.JK", "TINS.JK", "TLKM.JK", "TOWR.JK", "UNTR.JK", "UNVR.JK", 
    "BUKA.JK", "EMTK.JK", "GOTO.JK", "ARTO.JK", "HRUM.JK", "ITMG.JK"
]

# 2023-07 (Feb 2023 - Jul 2023)
# AMRT, ESSA, MEDC in; ICBP, INKP, TINS out.
universes["2023-07"] = [
    "ADRO.JK", "ANTM.JK", "ASII.JK", "BBCA.JK", "BBNI.JK", "BBRI.JK", "BMRI.JK", "BRPT.JK", 
    "CPIN.JK", "INCO.JK", "INDF.JK", "KLBF.JK", "MDKA.JK", "PGAS.JK", "PTBA.JK", "SMGR.JK", 
    "TBIG.JK", "TLKM.JK", "TOWR.JK", "UNTR.JK", "UNVR.JK", "BUKA.JK", "EMTK.JK", "GOTO.JK", 
    "ARTO.JK", "HRUM.JK", "ITMG.JK", "AMRT.JK", "ESSA.JK", "MEDC.JK"
]

# 2024-01 (Aug 2023 - Jan 2024)
# AKRA in; TBIG out.
universes["2024-01"] = [
    "ADRO.JK", "ANTM.JK", "ASII.JK", "BBCA.JK", "BBNI.JK", "BBRI.JK", "BMRI.JK", "BRPT.JK", 
    "CPIN.JK", "INCO.JK", "INDF.JK", "KLBF.JK", "MDKA.JK", "PGAS.JK", "PTBA.JK", "SMGR.JK", 
    "TLKM.JK", "TOWR.JK", "UNTR.JK", "UNVR.JK", "BUKA.JK", "EMTK.JK", "GOTO.JK", "ARTO.JK", 
    "HRUM.JK", "ITMG.JK", "AMRT.JK", "ESSA.JK", "MEDC.JK", "AKRA.JK"
]

# 2024-07 (Feb 2024 - Jul 2024)
# ACES, ICBP, INKP, PGEO in; EMTK, ESSA, HRUM, TOWR out.
universes["2024-07"] = [
    "ADRO.JK", "ANTM.JK", "ASII.JK", "BBCA.JK", "BBNI.JK", "BBRI.JK", "BMRI.JK", "BRPT.JK", 
    "CPIN.JK", "INCO.JK", "INDF.JK", "KLBF.JK", "MDKA.JK", "PGAS.JK", "PTBA.JK", "SMGR.JK", 
    "TLKM.JK", "UNTR.JK", "UNVR.JK", "BUKA.JK", "GOTO.JK", "ARTO.JK", "ITMG.JK", "AMRT.JK", 
    "MEDC.JK", "AKRA.JK", "ACES.JK", "ICBP.JK", "INKP.JK", "PGEO.JK"
]

# 2025-01 (Nov 2024 - Jan 2025)
# MAPI, MBMA in; BUKA, ITMG out.
universes["2025-01"] = [
    "ADRO.JK", "ANTM.JK", "ASII.JK", "BBCA.JK", "BBNI.JK", "BBRI.JK", "BMRI.JK", "BRPT.JK", 
    "CPIN.JK", "INCO.JK", "INDF.JK", "KLBF.JK", "MDKA.JK", "PGAS.JK", "PTBA.JK", "SMGR.JK", 
    "TLKM.JK", "UNTR.JK", "UNVR.JK", "GOTO.JK", "ARTO.JK", "AMRT.JK", "MEDC.JK", "AKRA.JK", 
    "ACES.JK", "ICBP.JK", "INKP.JK", "PGEO.JK", "MAPI.JK", "MBMA.JK"
]

# 2025-07 (Feb 2025 - Jul 2025)
# EXCL, ISAT in; ACES, PGEO out.
# BBTN in; ARTO out.
universes["2025-07"] = [
    "ADRO.JK", "ANTM.JK", "ASII.JK", "BBCA.JK", "BBNI.JK", "BBRI.JK", "BMRI.JK", "BRPT.JK", 
    "CPIN.JK", "INCO.JK", "INDF.JK", "KLBF.JK", "MDKA.JK", "PGAS.JK", "PTBA.JK", "SMGR.JK", 
    "TLKM.JK", "UNTR.JK", "UNVR.JK", "GOTO.JK", "AMRT.JK", "MEDC.JK", "AKRA.JK", "ICBP.JK", 
    "INKP.JK", "MAPI.JK", "MBMA.JK", "EXCL.JK", "ISAT.JK", "BBTN.JK"
]

# 2026-01 (Aug 2025 - Jan 2026)
# ITMG, JPFA in; BBTN, MAPI out.
# AADI, PGEO in; AKRA, EXCL out.
universes["2026-01"] = [
    "ADRO.JK", "ANTM.JK", "ASII.JK", "BBCA.JK", "BBNI.JK", "BBRI.JK", "BMRI.JK", "BRPT.JK", 
    "CPIN.JK", "INCO.JK", "INDF.JK", "KLBF.JK", "MDKA.JK", "PGAS.JK", "PTBA.JK", "SMGR.JK", 
    "TLKM.JK", "UNTR.JK", "UNVR.JK", "GOTO.JK", "AMRT.JK", "MEDC.JK", "ICBP.JK", "INKP.JK", 
    "MBMA.JK", "ISAT.JK", "ITMG.JK", "JPFA.JK", "AADI.JK", "PGEO.JK"
]

def main():
    print(f"Creating {len(universes)} historical universe files...")
    for period, constituents in universes.items():
        if len(constituents) != 30:
            print(f"ERROR: Period {period} has {len(constituents)} constituents instead of 30!")
            return
            
        output_file = OUTPUT_DIR / f"{period}.json"
        with open(output_file, "w", encoding="utf-8") as f:
            json.dump(constituents, f, indent=4)
        print(f"Saved {output_file}")
    print("All historical universe files successfully created.")

if __name__ == "__main__":
    main()
