import streamlit as st
import pandas as pd
import psycopg2
import plotly.express as px
import os

# db_user = os.getenv('DB_USER')
# db_password = os.getenv('DB_PASSWORD')
# db_host = os.getenv('DB_HOST')
# db_port = os.getenv('DB_PORT')

st.set_page_config(
    page_title="dashboard data",
)

# logo_path = 'kominfo.png' 
# if os.path.exists(logo_path):
#     st.image(logo_path, width=50)  
# else:
#     st.error('Logo tidak ditemukan, periksa path file!')

# Menampilkan logo dan tulisan di sampingnya
logo_path = 'kominfo.png' 
with st.container():
    cols = st.columns([1, 5])  # Mengatur rasio kolom: 1 untuk logo, 5 untuk teks
    if os.path.exists(logo_path):
        cols[0].image(logo_path, width=70)  # Kolom pertama untuk logo
    else:
        cols[0].error('Logo tidak ditemukan!')  # Tampilkan pesan error jika logo tidak ditemukan
    
    # Kolom kedua untuk tulisan
    cols[1].markdown("""
    #### Dinas Komunikasi dan Informatika Sidoarjo  
    """)

st.title("Dashboard Data Call Center")

# def connect_db():
#     conn = psycopg2.connect(
#         # host=st.secrets["db_host"],
#         # database=st.secrets["db_name"],
#         # user=st.secrets["db_user"],
#         # password=st.secrets["db_password"],
#         # port=st.secrets["db_port"]

#             dbname="coba",
#             user=db_user,
#             password=db_password,
#             host=db_host,
#             port=db_port
#     )
#     return conn

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
        print(f"Error: {e}")
        return None

# Contoh penggunaan
conn = connect_db()
if conn is None:
    print("Koneksi ke database gagal!")
else:
    df = pd.read_sql_query(query, conn)


def get_data_from_db(query):
    conn = connect_db()
    df = pd.read_sql_query(query, conn)
    conn.close()
    return df

# query = "SELECT * FROM laporan"  
def get_data_from_db(query):
    conn = connect_db()
    if conn is None:
        print("Koneksi gagal!")
        return None
    try:
        df = pd.read_sql_query(query, conn)
        conn.close()  # Pastikan koneksi ditutup setelah digunakan
        return df
    except Exception as e:
        print(f"Error saat membaca data: {e}")
        return None

query = "SELECT * FROM laporan"
df = get_data_from_db(query)
if df is not None:
    print(df.head())

# Menampilkan data di Streamlit (optional, hanya jika ingin menampilkan data mentah)
# st.subheader('Data Laporan')
# st.dataframe(df)

# # Pastikan kolom 'waktu_laporan' ada dan diubah menjadi datetime
# df['waktu_laporan'] = pd.to_datetime(df['waktu_laporan'])

# # Menambahkan kolom 'bulan' untuk pengelompokan berdasarkan bulan
# df['bulan'] = df['waktu_laporan'].dt.to_period('M').astype(str)  # Mengonversi Period ke string

# Cek beberapa nilai pertama di kolom waktu_laporan
st.write(df['waktu_laporan'].head())

# Mengonversi waktu_laporan menjadi datetime, dan mengabaikan kesalahan dengan errors='coerce'
df['waktu_laporan'] = pd.to_datetime(df['waktu_laporan'], errors='coerce')

# Periksa apakah ada nilai yang gagal diubah (NaT)
st.write(df[df['waktu_laporan'].isna()])

# Menambahkan opsi "Semua Bulan" untuk melihat distribusi tipe laporan
bulan_sorted = sorted(df['bulan'].unique(), key=lambda x: pd.to_datetime(x))
# bulan_tipe_options = ["Semua Bulan"] + list(df['bulan'].unique())
bulan_tipe_options = ["Semua Bulan"] + bulan_sorted
selected_bulan_tipe = st.selectbox('Pilih Bulan untuk Melihat Distribusi Tipe Laporan:', bulan_tipe_options, key="bulan_tipe")

# Filter data berdasarkan bulan yang dipilih
if selected_bulan_tipe == "Semua Bulan":
    tipe_laporan_counts_filtered = df['tipe_laporan'].value_counts().reset_index()
else:
    tipe_laporan_counts_filtered = df[df['bulan'] == selected_bulan_tipe]['tipe_laporan'].value_counts().reset_index()

# Menamai kolom untuk visualisasi
tipe_laporan_counts_filtered.columns = ['tipe_laporan', 'jumlah_laporan']

# Membuat diagram pie untuk distribusi tipe laporan
fig_pie_tipe = px.pie(
    tipe_laporan_counts_filtered,
    names='tipe_laporan',
    values='jumlah_laporan',
    title=f'Distribusi Tipe Laporan pada Bulan {selected_bulan_tipe}' if selected_bulan_tipe != "Semua Bulan" else "Distribusi Tipe Laporan untuk Semua Bulan",
    labels={'tipe_laporan': 'Tipe Laporan', 'jumlah_laporan': 'Jumlah Laporan'}
)

# Menampilkan diagram pie untuk tipe laporan
st.plotly_chart(fig_pie_tipe)


# Mengelompokkan data berdasarkan bulan dan kategori, mengabaikan kategori "-"
kategori_counts = df[df['kategori'] != '-'].groupby(['bulan', 'kategori']).size().reset_index(name='jumlah_kategori')

# Menambahkan opsi "Semua Bulan" ke dalam filter bulan
bulan_options = ["Semua Bulan"] + list(kategori_counts['bulan'].unique())
selected_bulan = st.selectbox('Pilih Bulan untuk Melihat Distribusi Kategori:', bulan_options)

# Filter data berdasarkan bulan yang dipilih
if selected_bulan == "Semua Bulan":
    kategori_counts_filtered = kategori_counts
else:
    kategori_counts_filtered = kategori_counts[kategori_counts['bulan'] == selected_bulan]

# Membuat diagram pie untuk distribusi kategori laporan
fig_pie_kategori = px.pie(kategori_counts_filtered, names='kategori', values='jumlah_kategori', 
                          title=f'Distribusi Kategori Laporan pada Bulan {selected_bulan}' if selected_bulan != "Semua Bulan" else "Distribusi Kategori Laporan untuk Semua Bulan",
                          labels={'kategori': 'Kategori', 'jumlah_kategori': 'Jumlah Laporan'})

# Menampilkan diagram pie untuk kategori
st.plotly_chart(fig_pie_kategori)

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
