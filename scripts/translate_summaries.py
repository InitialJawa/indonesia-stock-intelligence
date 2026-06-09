import json

file = r"data/state/company_profiles.json"
with open(file, "r", encoding="utf-8") as f:
    data = json.load(f)

summaries_id = {
    "ADRO": "Perusahaan tambang batu bara terbesar di Indonesia. Memproduksi batu bara termal untuk pasar domestik dan ekspor.",
    "AKRA": "Mendistribusikan bahan bakar, bahan kimia, dan barang industri di seluruh Indonesia. Juga mengembangkan kawasan industri.",
    "AMMN": "Mengoperasikan tambang tembaga dan emas Batu Hijau di Sumbawa Barat. Salah satu produsen tembaga terbesar di Indonesia.",
    "ANTM": "Perusahaan tambang milik negara yang memproduksi emas, nikel, dan bauksit. Mengoperasikan tambang emas Pongkor.",
    "ASII": "Konglomerat terbesar di Indonesia. Mendominasi otomotif (Toyota/Daihatsu/Honda), alat berat, dan jasa keuangan.",
    "BBCA": "Bank swasta terbesar di Indonesia berdasarkan kapitalisasi pasar. Dikenal dengan perbankan ritel, inovasi digital, dan kualitas kredit yang kuat.",
    "BBNI": "Bank milik negara yang fokus pada perbankan korporasi dan internasional. Kuat dalam trade finance dan treasury.",
    "BBRI": "Bank terbesar di Indonesia berdasarkan aset. Mendominasi sektor mikro melalui 7.000+ BRI Unit di seluruh Nusantara.",
    "BMRI": "Bank milik negara terbesar berdasarkan aset. Kuat dalam perbankan korporasi, treasury, dan transaksi wholesale.",
    "BRPT": "Produsen petrokimia utama melalui anak usaha Chandra Asri. Juga memiliki kepentingan di perkebunan dan properti.",
    "CPIN": "Produsen pakan ternak terbesar di Indonesia. Bisnis unggas terintegrasi vertikal dari pakan hingga daging ayam olahan.",
    "ESSA": "Mengoperasikan pabrik pemrosesan gas alam di Jawa Barat. Memproduksi LPG dan kondensat dari gas alam.",
    "EXCL": "Operator jaringan seluler besar. Bagian dari Axiata Group Malaysia. Kuat dalam layanan data dan digital.",
    "GOTO": "Platform digital terbesar di Indonesia. Menggabungkan layanan on-demand (Gojek) dan e-commerce (Tokopedia) dengan jasa keuangan.",
    "HEAL": "Mengoperasikan 40+ rumah sakit di seluruh Indonesia dengan merek Hermina. Jaringan rumah sakit swasta terbesar berdasarkan pendapatan.",
    "ICBP": "Divisi barang konsumsi kemasan dari Indofood. Memproduksi mi instan (Indomie), susu, camilan, dan minuman.",
    "INDF": "Perusahaan makanan terbesar di Indonesia. Memproduksi mi instan Indomie, memiliki perkebunan (Bogasari), dan operasi CPO.",
    "INTP": "Produsen semen terbesar kedua di Indonesia. Bagian dari HeidelbergCement Group. Mengoperasikan 13 pabrik semen.",
    "ITMG": "Perusahaan tambang batu bara dengan operasi di Kalimantan. Memproduksi batu bara termal untuk pasar ekspor.",
    "KLBF": "Perusahaan farmasi terbesar di Indonesia berdasarkan pendapatan. Memproduksi obat resep, kesehatan konsumen, dan nutrisi.",
    "MAPI": "Peritel gaya hidup terbesar di Indonesia. Mengoperasikan Sports Station, Sogo, Starbucks, Zara, dan 3.000+ gerai ritel.",
    "MDKA": "Perusahaan tambang yang berkembang pesat dengan operasi emas, tembaga, dan nikel. Memiliki tambang emas Tujuh Bukit dan proyek nikel.",
    "MIKA": "Mengoperasikan 16+ rumah sakit di kota-kota besar Indonesia dengan merek Mitra Keluarga. Fokus pada layanan kesehatan kelas menengah.",
    "PGAS": "Perusahaan gas milik negara. Mendistribusikan gas alam melalui jaringan pipa 10.000+ km di seluruh Indonesia.",
    "PTBA": "Perusahaan tambang batu bara milik negara. Mengoperasikan tambang Tanjung Enim di Sumatera Selatan. Memproduksi batu bara termal.",
    "SIDO": "Produsen obat herbal terbesar di Indonesia. Memproduksi Tolak Angin, Kuku Bima, dan ramuan tradisional lainnya.",
    "SMGR": "Produsen semen terbesar di Indonesia (milik negara). Beroperasi dengan merek Semen Gresik, Semen Padang, dan Semen Tonasa.",
    "TLKM": "Perusahaan telekomunikasi terbesar di Indonesia. Memiliki Telkomsel (seluler), IndiHome (broadband), dan infrastruktur serat optik.",
    "TPIA": "Perusahaan petrokimia terintegrasi terbesar di Indonesia. Memproduksi nafta, etilena, polietilena, dan polipropilena.",
    "UNTR": "Mendistribusikan alat berat Komatsu, mengoperasikan tambang batu bara, dan menjalankan kontraktor tambang melalui Pamapersada Nusantara."
}

for ticker, summary in summaries_id.items():
    if ticker in data:
        data[ticker]["summary"] = summary

with open(file, "w", encoding="utf-8") as f:
    json.dump(data, f, indent=2, ensure_ascii=False)

print("Updated", len(summaries_id), "summaries to Indonesian")
