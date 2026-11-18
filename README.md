# Pencatat Keuangan Pribadi (CLI)

Aplikasi command line Python untuk mengolah catatan transaksi keuangan dari file CSV atau JSON: rekap bulanan, pengeluaran per kategori, pencarian, filter, dan pembersihan duplikat.

## 1. Rancangan Aplikasi

| Aspek | Penjelasan |
|---|---|
| **Masalah** | Mahasiswa/pekerja muda mencatat transaksi di spreadsheet, tetapi sulit melihat rekap bulanan, kategori terboros, dan sering ada catatan ganda. |
| **Tujuan** | Mengolah catatan transaksi menjadi laporan yang mudah dibaca dan bersih dari duplikat. |
| **Target pengguna** | Mahasiswa dan pekerja yang mencatat keuangan di Excel/Google Sheets lalu mengekspornya ke CSV. |
| **Input** | File `.csv` atau `.json` berisi transaksi. |
| **Output** | Laporan teks di terminal, serta file `.json` (rekap lengkap), `.csv` (rekap bulanan), atau `.csv`/`.json` (data bersih tanpa duplikat). |

**Fitur utama**
1. Rekap ringkasan, bulanan, dan pengeluaran per kategori (dengan persentase).
2. Pencarian kata kunci dan filter (tipe, kategori, bulan, jumlah minimum).
3. Penghapusan transaksi duplikat dan daftar kategori unik.
4. Mode menu interaktif.

### Format input

CSV (header wajib, urutan bebas):

```csv
tanggal,deskripsi,kategori,jumlah,tipe
2026-09-01,Gaji bulanan,gaji,5000000,pemasukan
2026-09-03,Makan siang,makanan,25000,pengeluaran
```

JSON: daftar objek dengan kunci yang sama (lihat `data/transaksi.json`).

Aturan: `tanggal` = `YYYY-MM-DD`; `jumlah` = angka > 0 tanpa pemisah ribuan (`1500000` atau `1500000.50`); `tipe` = `pemasukan` atau `pengeluaran`.

### Format output
- `rekap.json`: `ringkasan`, `rekap_bulanan`, `pengeluaran_per_kategori`, `persentase_pengeluaran`.
- `rekap_bulanan.csv`: kolom `bulan,pemasukan,pengeluaran,saldo`.
- `transaksi_bersih.csv`: kolom sama dengan input, tanpa duplikat.

Contoh siap pakai ada di `data/` (input) dan `output/` (hasil).

## 2. Struktur Data dan Alasannya

| Struktur | Dipakai untuk | Alasan |
|---|---|---|
| **list** | Daftar transaksi | Urutan input dipertahankan, mudah di-iterasi, difilter, dan diurutkan. |
| **dict** | Total per kategori, rekap per bulan, tiap transaksi | Akses/akumulasi per kunci O(1); kunci kategori/bulan unik secara alami. |
| **set** | Kategori unik dan deteksi duplikat | Cek keanggotaan O(1) dan otomatis menghilangkan elemen ganda. |

Fitur yang memakainya: pencarian (`cari`), filtering (`filter_transaksi`), pengelompokan (`total_per_kategori`), rekapitulasi (`rekap_bulanan`, `ringkasan`), dan penghapusan duplikat (`hapus_duplikat`).

## 3. Control Flow dan Comprehension

- **Percabangan**: `status_saldo` (if/elif/else), dispatch perintah, validasi tipe.
- **Perulangan**: `for` pada rekap dan validasi baris; `while True` pada menu interaktif.
- **List comprehension**: `cari`, `filter_transaksi`. **Dict comprehension**: `rekap_bulanan`, `persentase_per_kategori`. **Set comprehension**: `daftar_kategori`.
- **Edge case yang ditangani**: data kosong (ringkasan bernilai 0, kategori terbesar `None`), total pengeluaran 0 (persentase `{}` tanpa `ZeroDivisionError`), kata kunci kosong (hasil kosong), hasil filter kosong (pesan khusus), saldo negatif (label DEFISIT).

## 4. Struktur Proyek dan Alur Dependensi

```
keuangan_cli/
├── main.py                  # titik masuk
├── keuangan/                # package buatan sendiri
│   ├── __init__.py
│   ├── exceptions.py        # error khusus
│   ├── io_utils.py          # baca/tulis CSV & JSON + validasi
│   ├── analisis.py          # logika murni (tanpa I/O)
│   ├── laporan.py           # format teks dan struktur output
│   └── cli.py               # argumen + alur program
├── data/                    # contoh input (valid, rusak, JSON)
├── output/                  # contoh hasil
└── tests/test_keuangan.py   # unit test
```

Alur dependensi (panah = "mengimpor"):

```
main.py -> cli -> laporan -> analisis
              \-> io_utils -> exceptions
              \-> analisis
```

`analisis` tidak bergantung pada modul lain sehingga mudah diuji. `cli` adalah satu-satunya lapisan yang berbicara dengan pengguna.

### Dokumentasi function utama

| Function | Parameter -> Return |
|---|---|
| `io_utils.baca_transaksi(path)` | path file -> `(transaksi_valid, daftar_galat)` |
| `io_utils.normalisasi_baris(baris, nomor)` | dict mentah, nomor baris -> dict bersih |
| `analisis.hapus_duplikat(transaksi)` | list -> `(list_unik, jumlah_dibuang)` |
| `analisis.cari(transaksi, kata_kunci)` | list, str -> list |
| `analisis.filter_transaksi(...)` | list + filter opsional -> list |
| `analisis.total_per_kategori(transaksi, tipe)` | list, str -> dict terurut menurun |
| `analisis.rekap_bulanan(transaksi)` | list -> `{bulan: {pemasukan, pengeluaran, saldo}}` |
| `analisis.ringkasan(transaksi)` | list -> dict ringkasan |
| `laporan.teks_rekap(transaksi)` | list -> str laporan |
| `cli.main(argv)` | argumen -> kode keluar (0/1) |

Setiap function punya satu tanggung jawab: membaca, memvalidasi, menghitung, memformat, atau menyimpan dipisah ke function berbeda.

## 5. Cara Menjalankan

Tidak ada dependency eksternal (hanya library standar). Butuh **Python 3.9+**.

```bash
python main.py rekap -i data/transaksi.csv
python main.py rekap -i data/transaksi.csv -o output/rekap.json
python main.py rekap -i data/transaksi.csv -o output/rekap_bulanan.csv
python main.py cari -i data/transaksi.csv netflix
python main.py filter -i data/transaksi.csv --tipe pengeluaran --bulan 2026-10 --min 50000
python main.py bersihkan -i data/transaksi.csv -o output/transaksi_bersih.csv
python main.py kategori -i data/transaksi.json
python main.py menu -i data/transaksi.csv
python main.py --debug rekap -i tidak_ada.csv     # traceback lengkap
```

Menjalankan test: `python -m unittest discover -s tests -v`

## 6. Exception Handling dan Defensive Programming

| Kondisi | Penanganan |
|---|---|
| File tidak ditemukan | `FileNotFoundError` -> pesan `[ERROR]`, kode keluar 1 |
| Ekstensi bukan csv/json | `FormatTidakDidukungError` |
| File kosong / header kurang / JSON rusak | `DataTidakValidError` dengan lokasi baris/kolom |
| Baris tidak valid (tanggal, jumlah, tipe) | Baris **dilewati** dengan peringatan bernomor, sisa data tetap diproses |
| Semua baris rusak | Error "tidak ada baris valid" |
| Input menu ditutup (EOF) | Keluar dengan rapi |

Defensive programming: validasi di batas input (`normalisasi_baris`), tolak `nan`/`inf`/negatif/nol, `utf-8-sig` untuk BOM dari Excel, header dinormalisasi (huruf kecil, spasi dibuang), hasil perhitungan dibulatkan 2 desimal, dan error aplikasi dipisahkan dari bug lewat kelas `KeuanganError`.

## 7. Skenario Debugging yang Didokumentasikan

**Gejala.** Tes `test_baris_rusak_dilewati` gagal: baris dengan jumlah `1.000` (maksudnya seribu rupiah) dianggap valid dan hasilnya `(2, 0)`, padahal seharusnya `(1, 1)`.

**Investigasi.**
1. Jalankan `python -m unittest discover -s tests` dan baca `AssertionError: (2, 0) != (1, 1)`: tidak ada baris yang ditolak.
2. Ujicoba langsung di REPL: `float("1.000")` -> `1.0`. Python menganggap titik sebagai desimal, bukan pemisah ribuan.
3. Kesimpulan: bukan crash, tetapi **kesalahan diam-diam**: transaksi Rp 1.000 tercatat Rp 1, dan rekap menjadi keliru tanpa peringatan.

**Perbaikan.** Tambahkan pola `POLA_RIBUAN = ^\d{1,3}(\.\d{3})+$` di `io_utils.parse_jumlah` yang menolak angka bergaya pemisah ribuan dengan pesan yang menjelaskan format benar. Test dijalankan ulang dan lulus. Pengguna bisa mereproduksi dengan `python main.py rekap -i data/transaksi_rusak.csv`.

Untuk debugging error lain, jalankan dengan `--debug` agar traceback lengkap dan log `DEBUG` tampil.

## 8. Pemetaan ke Rubrik

| Komponen | Letak |
|---|---|
| Analisis masalah & rancangan | Bagian 1 |
| Struktur data & manipulasi | Bagian 2, `analisis.py` |
| Control flow & Pythonic | Bagian 3, `analisis.py`, `cli.py` |
| Function, module, package | Bagian 4, folder `keuangan/` |
| File processing CSV/JSON | `io_utils.py`, `data/`, `output/` |
| Exception, debugging, dokumentasi | Bagian 6, 7, dan README ini |

## 9. Sumber Referensi, Library, dan Bantuan AI

- **Library**: hanya library standar Python (`argparse`, `csv`, `json`, `re`, `math`, `logging`, `datetime`, `pathlib`, `unittest`). Tidak ada library pihak ketiga.
- **Referensi**: dokumentasi resmi Python (https://docs.python.org/3/), khususnya modul `argparse`, `csv`, `json`, dan `unittest`.
- **Bantuan AI**: kerangka kode, data contoh, tes, dan draf README dibuat dengan bantuan Claude (Anthropic) berdasarkan soal tugas. Hasilnya telah dijalankan dan diuji (12 unit test lulus).

## 10. Link Repository

URL repository: `https://github.com/rakhaelkafi/Keuangan-cli`
