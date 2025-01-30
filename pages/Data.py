import streamlit as st
import pandas as pd
import psycopg2
import plotly.express as px

# Fungsi untuk koneksi ke database
def connect_db():
    conn = psycopg2.connect(
        dbname='coba',
        user='postgres',
        password='240904',
        host='localhost',
        port='5432'
    )
    return conn

# Judul aplikasi
st.title("Data Laporan Call Center")

# Pilihan status
status_options = ["Semua", "Selesai", "Proses", "Baru"]
status_filter = st.selectbox("Pilih Status:", status_options)

# Pilihan kategori
conn = connect_db()
query_kategori = "SELECT DISTINCT kategori FROM laporan_dinas_view"
kategori_options = pd.read_sql(query_kategori, conn)['kategori'].tolist()
kategori_filter = st.selectbox("Pilih Kategori:", ["Semua"] + kategori_options)

# Pilihan kecamatan
query_kecamatan = "SELECT DISTINCT kecamatan FROM laporan_dinas_view"
kecamatan_options = pd.read_sql(query_kecamatan, conn)['kecamatan'].tolist()
kecamatan_filter = st.selectbox("Pilih Kecamatan:", ["Semua"] + kecamatan_options)

# Pilihan dinas terkait
query_dinas = "SELECT DISTINCT dinas FROM laporan_dinas_view"
dinas_options = pd.read_sql(query_dinas, conn)['dinas'].tolist()
dinas_filter = st.selectbox("Pilih Dinas Terkait:", ["Semua"] + dinas_options)

# Filter tanggal (tanggal mulai dan tanggal akhir)
start_date = st.date_input("Tanggal Mulai", value=pd.to_datetime("2020-01-01"))
end_date = st.date_input("Tanggal Akhir", value=pd.to_datetime("2025-01-01"))

# Membuat query dasar
query = "SELECT * FROM laporan_dinas_view WHERE 1=1"  # Mulai dengan kondisi yang selalu benar
filters = []

# Menambahkan filter
if status_filter != "Semua":
    filters.append(f"status = '{status_filter}'")
    if status_filter == "Selesai":
        filters.append("tipe_laporan = 'normal'")

if kategori_filter != "Semua":
    filters.append(f"kategori = '{kategori_filter}'")
if kecamatan_filter != "Semua":
    filters.append(f"kecamatan = '{kecamatan_filter}'")
if dinas_filter != "Semua":
    filters.append(f"dinas = '{dinas_filter}'")

# Menambahkan filter waktu_laporan
if start_date and end_date:
    filters.append(f"waktu_laporan >= '{start_date.strftime('%Y-%m-%d')}' AND waktu_laporan <= '{end_date.strftime('%Y-%m-%d')}'")

# Memperbarui query untuk memasukkan filter
if filters:
    query += " AND " + " AND ".join(filters)

# Menambahkan pengecekan untuk memastikan "NaN" tidak ada
# query += " AND waktu_laporan != 'NaN'"

# Debugging query
# st.write(query)

# Menjalankan query untuk mengambil data
try:
    # Mengambil data dari database
    data_df = pd.read_sql(query, conn)

    # Menutup koneksi database
    conn.close()

    # Menampilkan data
    if not data_df.empty:
        st.write(f"Data untuk status yang dipilih: {', '.join([status_filter])}")
        st.dataframe(data_df)

        # Menambahkan diagram garis jumlah kejadian per kategori
        data_df['tanggal'] = pd.to_datetime(data_df['waktu_laporan']).dt.date  # Mengambil tanggal dari waktu_laporan
        category_trends = data_df.groupby(['tanggal', 'kategori']).size().reset_index(name='jumlah')

        # Membuat grafik garis
        fig = px.line(
            category_trends,
            x='tanggal',
            y='jumlah',
            color='kategori',
            title="Tren Jumlah Kejadian Per Kategori",
            labels={'jumlah': 'Jumlah Kejadian', 'tanggal': 'Tanggal', 'kategori': 'Kategori'}
        )
        st.plotly_chart(fig)
    else:
        st.write("Tidak ada data ditemukan.")
except Exception as e:
    st.error(f"Terjadi kesalahan: {e}")
    conn.close()
