"""Logika analisis data transaksi. Tidak ada I/O di sini (fungsi murni).

Pilihan struktur data:
    list  : menyimpan urutan transaksi (urutan input penting, bisa diurutkan).
    dict  : pengelompokan per kategori/bulan -> akses dan agregasi O(1) per kunci.
    set   : kategori unik dan deteksi duplikat -> cek keanggotaan O(1).
"""


# ------------------------------------------------------------- duplikat (set)
def kunci_transaksi(t):
    """Identitas sebuah transaksi; dua transaksi dengan kunci sama = duplikat."""
    return (t["tanggal"], t["deskripsi"].lower(), t["kategori"], t["jumlah"], t["tipe"])


def hapus_duplikat(transaksi):
    """Buang transaksi duplikat, pertahankan kemunculan pertama.

    Returns:
        (list_unik, jumlah_dibuang)
    """
    terlihat = set()
    unik = []
    for t in transaksi:
        k = kunci_transaksi(t)
        if k in terlihat:
            continue
        terlihat.add(k)
        unik.append(t)
    return unik, len(transaksi) - len(unik)


def daftar_kategori(transaksi):
    """Kategori unik terurut (set comprehension)."""
    return sorted({t["kategori"] for t in transaksi})


# ------------------------------------------------- pencarian & filter (list)
def cari(transaksi, kata_kunci):
    """Cari transaksi yang deskripsi atau kategorinya memuat kata kunci."""
    kunci = kata_kunci.strip().lower()
    if not kunci:
        return []
    return [
        t for t in transaksi
        if kunci in t["deskripsi"].lower() or kunci in t["kategori"]
    ]


def filter_transaksi(transaksi, tipe=None, kategori=None, bulan=None, jumlah_min=None):
    """Saring transaksi; parameter None berarti tidak difilter."""
    hasil = transaksi
    if tipe is not None:
        hasil = [t for t in hasil if t["tipe"] == tipe.lower()]
    if kategori is not None:
        hasil = [t for t in hasil if t["kategori"] == kategori.lower()]
    if bulan is not None:
        hasil = [t for t in hasil if t["bulan"] == bulan]
    if jumlah_min is not None:
        hasil = [t for t in hasil if t["jumlah"] >= jumlah_min]
    return list(hasil)


# ------------------------------------------------ rekapitulasi (dictionary)
def total_per_kategori(transaksi, tipe="pengeluaran"):
    """Total jumlah per kategori untuk satu tipe, diurutkan dari terbesar."""
    total = {}
    for t in transaksi:
        if t["tipe"] == tipe:
            total[t["kategori"]] = total.get(t["kategori"], 0.0) + t["jumlah"]
    urut = sorted(total.items(), key=lambda kv: kv[1], reverse=True)
    return {k: round(v, 2) for k, v in urut}


def persentase_per_kategori(per_kategori):
    """Persentase tiap kategori terhadap total (dictionary comprehension).

    Edge case: total 0 / data kosong mengembalikan {} (hindari ZeroDivisionError).
    """
    total = sum(per_kategori.values())
    if total == 0:
        return {}
    return {k: round(v / total * 100, 1) for k, v in per_kategori.items()}


def rekap_bulanan(transaksi):
    """Pemasukan, pengeluaran, dan saldo per bulan (YYYY-MM), urut kronologis."""
    hasil = {}
    for t in transaksi:
        bulan = hasil.setdefault(t["bulan"], {"pemasukan": 0.0, "pengeluaran": 0.0})
        bulan[t["tipe"]] += t["jumlah"]
    return {
        b: {
            "pemasukan": round(v["pemasukan"], 2),
            "pengeluaran": round(v["pengeluaran"], 2),
            "saldo": round(v["pemasukan"] - v["pengeluaran"], 2),
        }
        for b, v in sorted(hasil.items())
    }


def ringkasan(transaksi):
    """Ringkasan keseluruhan. Aman untuk data kosong (edge case)."""
    pemasukan = sum(t["jumlah"] for t in transaksi if t["tipe"] == "pemasukan")
    pengeluaran = sum(t["jumlah"] for t in transaksi if t["tipe"] == "pengeluaran")
    per_kat = total_per_kategori(transaksi, "pengeluaran")

    if per_kat:
        terbesar = next(iter(per_kat))  # dict sudah terurut menurun
    else:
        terbesar = None

    return {
        "jumlah_transaksi": len(transaksi),
        "total_pemasukan": round(pemasukan, 2),
        "total_pengeluaran": round(pengeluaran, 2),
        "saldo": round(pemasukan - pengeluaran, 2),
        "kategori_pengeluaran_terbesar": terbesar,
    }


def status_saldo(saldo):
    """Percabangan bertingkat: label kondisi keuangan."""
    if saldo > 0:
        return "SURPLUS"
    elif saldo == 0:
        return "IMPAS"
    else:
        return "DEFISIT"
