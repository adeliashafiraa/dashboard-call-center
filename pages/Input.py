import streamlit as st
import pandas as pd
import psycopg2
from psycopg2 import sql
from psycopg2.extras import execute_values
from io import StringIO

# Fungsi untuk menghubungkan ke database PostgreSQL
def connect_db():
    conn = psycopg2.connect(
        dbname='coba',
        user='postgres',
        password='240904',
        host='localhost',
        port='5432'
    )
    return conn

st.title("Input Data")

# Pilihan tabel untuk input
page = st.selectbox(
    "Pilih Tabel untuk Input:",
    ["Tabel Laporan", "Tabel Tiket Dinas", "Tabel Log Dinas"]
)

# Mengecek apakah data sudah ada di database sebelum dimasukkan
def check_if_exists(conn, table_name, columns, data):
    cur = conn.cursor()
    # Membuat query untuk mengecek duplikasi berdasarkan kolom tertentu
    select_query = sql.SQL("""
    SELECT COUNT(*) FROM {} WHERE ({}) = %s
    """).format(
        sql.Identifier(table_name),
        sql.SQL(', ').join(map(sql.Identifier, columns))
    )
    cur.execute(select_query, (data,))
    result = cur.fetchone()
    cur.close()
    return result[0] > 0

# Fungsi untuk memasukkan data CSV ke PostgreSQL
def insert_csv_to_db(csv_file, table_name, columns, column_mapping=None, unique_columns=None):
    stringio = StringIO(csv_file.getvalue().decode("utf-8"))
    df = pd.read_csv(stringio)

    # Bersihkan kolom berdasarkan mapping
    if column_mapping:
        df.rename(columns=column_mapping, inplace=True)

    # Drop duplikat dalam file CSV
    df = df.drop_duplicates()

    # Koneksi ke database
    conn = connect_db()
    cur = conn.cursor()

    # Validasi kolom unik
    if not unique_columns or not all(col in columns for col in unique_columns):
        st.error(f"Kolom unik untuk tabel {table_name} tidak valid atau tidak ditemukan.")
        return

    # Ambil data unik dari database berdasarkan unique_columns
    where_clause = " AND ".join([f"{col} = %s" for col in unique_columns])
    select_query = f"SELECT {', '.join(unique_columns)} FROM {table_name}"
    cur.execute(select_query)
    existing_rows = {tuple(row) for row in cur.fetchall()}

    # Filter data baru
    new_data = [
        tuple(row[col] for col in columns)
        for _, row in df.iterrows()
        if tuple(row[col] for col in unique_columns) not in existing_rows
    ]

    # Masukkan data baru ke database
    if new_data:
        insert_query = sql.SQL("""
        INSERT INTO {} ({} )
        VALUES %s
        """).format(
            sql.Identifier(table_name),
            sql.SQL(', ').join(map(sql.Identifier, columns))
        )
        execute_values(cur, insert_query, new_data)
        conn.commit()
        st.success(f"Data berhasil dimasukkan ke tabel {table_name}!")
    else:
        st.info("Tidak ada data baru yang perlu dimasukkan.")

    cur.close()
    conn.close()


# Halaman untuk Tabel Laporan
if page == "Tabel Laporan":
    st.header("Unggah Data ke Tabel Laporan")
    uploaded_file = st.file_uploader("Pilih file CSV untuk Laporan", type=["csv"])

    if uploaded_file is not None:
        st.write("Preview Data CSV:", pd.read_csv(uploaded_file).head())
        if st.button("Masukkan Data ke Tabel Laporan"):
            columns = [
                "nomor", "uid", "no_laporan", "tipe_saluran", "waktu_laporan",
                "agent_L1", "tipe_laporan", "pelapor", "no_telp", "kategori",
                "sub_kategori1", "sub_kategori2", "deskripsi", "lokasi_kejadian",
                "kecamatan", "kelurahan", "catatan_lokasi", "latitude", "longitude",
                "waktu_selesai", "ditutup_oleh", "status", "dinas_terkait", "durasi_pengerjaan"
            ]
            column_mapping = {
                "NO": "nomor",
                "UID": "uid",
                "NO LAPORAN": "no_laporan",
                "TIPE SALURAN": "tipe_saluran",
                "WAKTU LAPOR": "waktu_laporan",
                "AGENT L1": "agent_L1",
                "TIPE LAPORAN": "tipe_laporan",
                "PELAPOR": "pelapor",
                "NO TELP": "no_telp",
                "KATEGORI": "kategori",
                "SUB KATEGORI 1": "sub_kategori1",
                "SUB KATEGORI 2": "sub_kategori2",
                "DESKRIPSI": "deskripsi",
                "LOKASI KEJADIAN": "lokasi_kejadian",
                "KECAMATAN": "kecamatan",
                "KELURAHAN": "kelurahan", 
                "CATATAN LOKASI": "catatan_lokasi",
                "LATITUDE": "latitude", 
                "LONGITUDE": "longitude",
                "WAKTU SELESAI": "waktu_selesai", 
                "DITUTUP OLEH": "ditutup_oleh",
                "STATUS": "status",
                "DINAS TERKAIT": "dinas_terkait",
                "DURASI PENGERJAAN": "durasi_pengerjaan"
            }
            unique_columns = ["uid"]  # Primary key menggunakan uid
            insert_csv_to_db(uploaded_file, "laporan", columns, column_mapping, unique_columns)

# Halaman untuk Tabel Tiket Dinas
elif page == "Tabel Tiket Dinas":
    st.header("Unggah Data ke Tabel Tiket Dinas")
    uploaded_file = st.file_uploader("Pilih file CSV untuk Tiket Dinas", type=["csv"])

    if uploaded_file is not None:
        st.write("Preview Data CSV:", pd.read_csv(uploaded_file).head())
        if st.button("Masukkan Data ke Tabel Tiket Dinas"):
            columns = [
                "nomor", "nomor_laporan", "uid_dinas", "nomor_tiket_dinas",
                "dinas", "l2_notes", "status", "tiket_dibuat",
                "tiket_selesai", "durasi_penanganan"
            ]
            column_mapping = {
                "NO": "nomor",
                "NO.LAPORAN": "nomor_laporan",
                "UID DINAS": "uid_dinas",
                "NO.TIKET DINAS": "nomor_tiket_dinas",
                "DINAS": "dinas", 
                "L2 NOTES": "l2_notes", 
                "STATUS": "status", 
                "TIKET DIBUAT": "tiket_dibuat",
                "TIKET SELESAI": "tiket_selesai",
                "DURASI PENANGANAN": "durasi_penanganan"
            }
            unique_columns = ["uid_dinas"]  # Primary key menggunakan uid_dinas
            insert_csv_to_db(uploaded_file, "tiket_dinas", columns, column_mapping, unique_columns)

# Halaman untuk Tabel Log Dinas
elif page == "Tabel Log Dinas":
    st.header("Unggah Data ke Tabel Log Dinas")
    uploaded_file = st.file_uploader("Pilih file CSV untuk Log Dinas", type=["csv"])

    if uploaded_file is not None:
        st.write("Preview Data CSV:", pd.read_csv(uploaded_file).head())
        if st.button("Masukkan Data ke Tabel Log Dinas"):
            columns = [
                "nomor", "nomor_laporan", "nomor_tiket_dinas", "dinas",
                "agent_lt2", "status", "waktu_proses", "durasi_penanganan", 
                "catatan", "foto1", "foto2", "foto3"
            ]
            column_mapping = {
                "NO": "nomor",
                "NO.LAPORAN": "nomor_laporan",
                "NO.TIKET DINAS": "nomor_tiket_dinas",
                "DINAS": "dinas",
                "AGENT L2": "agent_lt2",
                "STATUS": "status",
                "WAKTU PROSES": "waktu_proses",
                "DURASI PENANGANAN": "durasi_penanganan",
                "CATATAN": "catatan",
                "FOTO 1": "foto1",
                "FOTO 2": "foto2",
                "FOTO 3": "foto3"
            }
            unique_columns = ["nomor_tiket_dinas", "status", "catatan"]  # Kolom unik berdasarkan kombinasi
            insert_csv_to_db(uploaded_file, "log_dinas", columns, column_mapping, unique_columns)
