import streamlit as st
import pandas as pd
import psycopg2
import plotly.express as px
import os

# Set halaman Streamlit
st.set_page_config(page_title="Dashboard Data")

# Logo path dan tampilan
logo_path = 'kominfo.png'
with st.container():
    cols = st.columns([1, 5])
    if os.path.exists(logo_path):
        cols[0].image(logo_path, width=70)
    else:
        cols[0].error('Logo tidak ditemukan!')
    
    cols[1].markdown("#### Dinas Komunikasi dan Informatika Sidoarjo")

# Fungsi koneksi ke database
def connect_db():
    try:
        conn = psycopg2.connect(
            dbname=os.getenv('DB_NAME'),
            user=os.getenv('DB_USER'),
            password=os.getenv('DB_PASSWORD'),
            host=os.getenv('DB_HOST'),
            port=os.getenv('DB_PORT')
        )
        return conn
    except Exception as e:
        st.error(f"Koneksi gagal: {e}")
        return None

# Fungsi untuk mengambil data dari database
def get_data_from_db(query):
    conn = connect_db()
    if conn is None:
        return None
    try:
        df = pd.read_sql_query(query, conn)
        conn.close()
        return df
    except Exception as e:
        st.error(f"Error saat membaca data: {e}")
        return None

# Ambil data dari database
query = "SELECT * FROM laporan"
df = get_data_from_db(query)

# Periksa apakah data berhasil diambil
if df is not None:
    st.write("Data berhasil diambil!")
    st.write(df.head())  # Tampilkan data pertama untuk pengecekan

    # Pastikan kolom 'waktu_laporan' ada dan ubah menjadi datetime
    if 'waktu_laporan' in df.columns:
        df['waktu_laporan'] = pd.to_datetime(df['waktu_laporan'], errors='coerce')
        # Menampilkan baris dengan nilai NaT (jika ada)
        st.write("Data yang gagal dikonversi:", df[df['waktu_laporan'].isna()])
    else:
        st.error("Kolom 'waktu_laporan' tidak ditemukan!")

    # Menambahkan kolom 'bulan' untuk pengelompokan
    df['bulan'] = df['waktu_laporan'].dt.to_period('M').astype(str)

    # Pastikan kolom 'tipe_laporan' ada sebelum melanjutkan
    if 'tipe_laporan' in df.columns:
        # Menampilkan data berdasarkan bulan dan tipe laporan
        bulan_sorted = sorted(df['bulan'].unique(), key=lambda x: pd.to_datetime(x))
        bulan_tipe_options = ["Semua Bulan"] + bulan_sorted
        selected_bulan_tipe = st.selectbox('Pilih Bulan untuk Melihat Distribusi Tipe Laporan:', bulan_tipe_options)

        if selected_bulan_tipe == "Semua Bulan":
            tipe_laporan_counts_filtered = df['tipe_laporan'].value_counts().reset_index()
        else:
            tipe_laporan_counts_filtered = df[df['bulan'] == selected_bulan_tipe]['tipe_laporan'].value_counts().reset_index()

        tipe_laporan_counts_filtered.columns = ['tipe_laporan', 'jumlah_laporan']

        # Visualisasi distribusi tipe laporan
        fig_pie_tipe = px.pie(
            tipe_laporan_counts_filtered,
            names='tipe_laporan',
            values='jumlah_laporan',
            title=f'Distribusi Tipe Laporan pada Bulan {selected_bulan_tipe}' if selected_bulan_tipe != "Semua Bulan" else "Distribusi Tipe Laporan untuk Semua Bulan",
            labels={'tipe_laporan': 'Tipe Laporan', 'jumlah_laporan': 'Jumlah Laporan'}
        )
        st.plotly_chart(fig_pie_tipe)
    else:
        st.error("Kolom 'tipe_laporan' tidak ditemukan!")
else:
    st.error("Data gagal diambil dari database!")

# Pilihan untuk memilih tipe laporan atau semua
tipe_laporan_options = ['Semua'] + list(df['tipe_laporan'].unique())
tipe_laporan = st.selectbox('Pilih Tipe Laporan', tipe_laporan_options)

# Filter data berdasarkan pilihan tipe laporan
if tipe_laporan == 'Semua':
    filtered_df = df
else:
    filtered_df = df[df['tipe_laporan'] == tipe_laporan]

# Menghitung jumlah laporan per bulan dan tipe laporan
count_df = filtered_df.groupby(['bulan', 'tipe_laporan']).size().reset_index(name='jumlah_laporan')

# Membuat grafik per bulan
fig = px.bar(count_df, x='bulan', y='jumlah_laporan', color='tipe_laporan', 
             title=f'Jumlah Laporan per Bulan ({"Semua Tipe" if tipe_laporan == "Semua" else tipe_laporan})',
             labels={'bulan': 'Bulan', 'jumlah_laporan': 'Jumlah Laporan', 'tipe_laporan': 'Tipe Laporan'},
             barmode='group')

# Menampilkan grafik
st.plotly_chart(fig)

# Membandingkan jumlah tipe laporan tertentu tiap bulannya jika memilih "Semua"
if tipe_laporan == 'Semua':
    selected_tipe = ['normal', 'prank', 'information', 'ghost']
    filtered_tipe_df = df[df['tipe_laporan'].isin(selected_tipe)]

    # Menghitung jumlah laporan per bulan dan tipe laporan
    line_chart_data = filtered_tipe_df.groupby(['bulan', 'tipe_laporan']).size().reset_index(name='jumlah_laporan')

    # Membuat diagram garis
    fig_line = px.line(line_chart_data, x='bulan', y='jumlah_laporan', color='tipe_laporan', 
                       title='Perbandingan Jumlah Tipe Laporan Tiap Bulan',
                       labels={'bulan': 'Bulan', 'jumlah_laporan': 'Jumlah Laporan', 'tipe_laporan': 'Tipe Laporan'})

    # Menampilkan diagram garis
    st.plotly_chart(fig_line)
