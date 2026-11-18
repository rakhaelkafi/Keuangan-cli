"""Pemformatan teks laporan untuk terminal dan struktur data untuk file output."""

from . import analisis


def format_rupiah(angka):
    """1500000.5 -> 'Rp 1.500.000,50' (tanpa desimal jika bilangan bulat)."""
    if float(angka).is_integer():
        teks = f"{int(angka):,}".replace(",", ".")
    else:
        teks = f"{angka:,.2f}".replace(",", "X").replace(".", ",").replace("X", ".")
    return f"Rp {teks}"


def tabel_transaksi(transaksi):
    """Teks tabel transaksi; pesan khusus jika kosong."""
    if not transaksi:
        return "(tidak ada transaksi yang cocok)"
    baris = [f"{'TANGGAL':<11}{'TIPE':<12}{'KATEGORI':<14}{'JUMLAH':>16}  DESKRIPSI"]
    baris += [
        f"{t['tanggal']:<11}{t['tipe']:<12}{t['kategori']:<14}"
        f"{format_rupiah(t['jumlah']):>16}  {t['deskripsi']}"
        for t in transaksi
    ]
    return "\n".join(baris)


def teks_rekap(transaksi):
    """Laporan rekap lengkap sebagai teks."""
    r = analisis.ringkasan(transaksi)
    baris = [
        "=== RINGKASAN ===",
        f"Jumlah transaksi  : {r['jumlah_transaksi']}",
        f"Total pemasukan   : {format_rupiah(r['total_pemasukan'])}",
        f"Total pengeluaran : {format_rupiah(r['total_pengeluaran'])}",
        f"Saldo             : {format_rupiah(r['saldo'])} [{analisis.status_saldo(r['saldo'])}]",
        "",
        "=== REKAP BULANAN ===",
    ]
    for bulan, v in analisis.rekap_bulanan(transaksi).items():
        baris.append(
            f"{bulan}  masuk {format_rupiah(v['pemasukan']):>14}  "
            f"keluar {format_rupiah(v['pengeluaran']):>14}  "
            f"saldo {format_rupiah(v['saldo']):>14}"
        )

    per_kat = analisis.total_per_kategori(transaksi, "pengeluaran")
    persen = analisis.persentase_per_kategori(per_kat)
    baris += ["", "=== PENGELUARAN PER KATEGORI ==="]
    if not per_kat:
        baris.append("(belum ada pengeluaran)")
    for kat, total in per_kat.items():
        baris.append(f"{kat:<14}{format_rupiah(total):>16}  {persen[kat]:>5}%")
    return "\n".join(baris)


def data_rekap(transaksi):
    """Struktur dict untuk disimpan ke file keluaran JSON."""
    per_kat = analisis.total_per_kategori(transaksi, "pengeluaran")
    return {
        "ringkasan": analisis.ringkasan(transaksi),
        "rekap_bulanan": analisis.rekap_bulanan(transaksi),
        "pengeluaran_per_kategori": per_kat,
        "persentase_pengeluaran": analisis.persentase_per_kategori(per_kat),
    }


def baris_rekap_bulanan(transaksi):
    """Rekap bulanan sebagai list of dict (datar) untuk keluaran CSV."""
    return [{"bulan": b, **v} for b, v in analisis.rekap_bulanan(transaksi).items()]
