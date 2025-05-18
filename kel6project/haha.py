import streamlit as st
from datetime import datetime
import os
import hashlib
import pandas as pd
import plotly.express as px 
from PIL import Image
import warnings

# Filter warnings
warnings.filterwarnings('ignore')

# Atur layout halaman
st.set_page_config(
    page_title="SiPadi - Aplikasi Petani",
    page_icon="🌾",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Set background hijau tanpa HTML
def set_background():
    st.markdown(
        """
        <style>
        .stApp {
            background-color: #e8f5e9;
        }
        .stSidebar {
            background-color: #2e7d32;
        }
        </style>
        """,
        unsafe_allow_html=True
    )

set_background()

# ---------------- Helper Functions ----------------

def hash_password(password):
    return hashlib.sha256(password.encode()).hexdigest()

def get_user_file(base_filename, username):
    # contoh: pemasukan_user1.csv
    name, ext = os.path.splitext(base_filename)
    return f"{name}_{username}{ext}"

def load_data(base_filename, username):
    filename = get_user_file(base_filename, username)
    if os.path.exists(filename):
        try:
            return pd.read_csv(filename)
        except (pd.errors.EmptyDataError, pd.errors.ParserError):
            # Jika file kosong atau error parsing, buat DataFrame kosong
            if "pemasukan" in filename:
                return pd.DataFrame(columns=["Tanggal", "Sumber", "Jumlah", "Metode", "Keterangan", "Username"])
            elif "pengeluaran" in filename:
                return pd.DataFrame(columns=["Tanggal", "Kategori", "Sub Kategori", "Jumlah", "Keterangan", "Metode", "Username"])
            elif "jurnal" in filename:
                return pd.DataFrame(columns=["Tanggal", "Akun", "Debit", "Kredit", "Keterangan"])
            else:
                return pd.DataFrame()
    else:
        # Jika file belum ada, buat DataFrame kosong dengan kolom sesuai file
        if "pemasukan" in base_filename:
            return pd.DataFrame(columns=["Tanggal", "Sumber", "Jumlah", "Metode", "Keterangan", "Username"])
        elif "pengeluaran" in base_filename:
            return pd.DataFrame(columns=["Tanggal", "Kategori", "Sub Kategori", "Jumlah", "Keterangan", "Metode", "Username"])
        elif "jurnal" in base_filename:
            return pd.DataFrame(columns=["Tanggal", "Akun", "Debit", "Kredit", "Keterangan"])
        else:
            return pd.DataFrame()

def save_data(df, base_filename, username):
    filename = get_user_file(base_filename, username)
    df.to_csv(filename, index=False)

def append_data(data, base_filename, username):
    df = load_data(base_filename, username)
    df = pd.concat([df, pd.DataFrame([data])], ignore_index=True)
    save_data(df, base_filename, username)

def buat_jurnal(tanggal, akun_debit, akun_kredit, jumlah, keterangan):
    return [
        {"Tanggal": tanggal, "Akun": akun_debit, "Debit": jumlah, "Kredit": 0, "Keterangan": keterangan},
        {"Tanggal": tanggal, "Akun": akun_kredit, "Debit": 0, "Kredit": jumlah, "Keterangan": keterangan},
    ]

def load_user_accounts():
    if os.path.exists("akun.csv"):
        try:
            return pd.read_csv("akun.csv")
        except (pd.errors.EmptyDataError, pd.errors.ParserError):
            return pd.DataFrame(columns=["Username", "Password"])
    else:
        return pd.DataFrame(columns=["Username", "Password"])

def save_user_accounts(df):
    df.to_csv("akun.csv", index=False)

def register_user(username, password):
    akun_df = load_user_accounts()
    if username in akun_df['Username'].values:
        return False  # Username sudah ada
    new_account = pd.DataFrame([{"Username": username, "Password": hash_password(password)}])
    akun_df = pd.concat([akun_df, new_account], ignore_index=True)
    save_user_accounts(akun_df)
    return True

def validate_login(username, password):
    akun_df = load_user_accounts()
    hashed_pw = hash_password(password)
    return ((akun_df['Username'] == username) & (akun_df['Password'] == hashed_pw)).any()

# ---------------- Login & Register ----------------

def login_register():
    if 'logged_in' not in st.session_state:
        st.session_state['logged_in'] = False
    if 'username' not in st.session_state:
        st.session_state['username'] = ""

    if st.session_state['logged_in']:
        return True

    st.title("🔐 Login / Daftar Akun")

    mode = st.radio("Pilih Mode", ["Login", "Daftar"], horizontal=True)
    username = st.text_input("Nama Pengguna")
    password = st.text_input("Kata Sandi", type="password")

    if mode == "Login":
        if st.button("Masuk"):
            if not username.strip() or not password.strip():
                st.error("Harap isi semua kolom.")
            elif validate_login(username, password):
                st.session_state['logged_in'] = True
                st.session_state['username'] = username
                st.success(f"Login berhasil! Selamat datang, {username}.")
                st.rerun()
            else:
                st.error("Username atau password salah.")

    else:  # Daftar
        if st.button("Daftar"):
            if not username.strip() or not password.strip():
                st.error("Harap isi semua kolom.")
            elif register_user(username, password):
                st.success("Akun berhasil dibuat. Silakan login.")
            else:
                st.error("Username sudah digunakan.")

    return False

# ---------------- Data Kategori ----------------

kategori_pengeluaran = {
    "Bibit": ["Intani", "Inpari", "Ciherang"],
    "Pupuk": ["Urea", "NPK", "Organik"],
    "Pestisida": ["Furadan", "BPMC", "Dursban"],
    "Alat Tani": ["Sabit", "Cangkul", "Karung"],
    "Tenaga Kerja": ["Upah Harian", "Borongan"],
    "Lainnya": ["Lain-lain"]
}

kategori_pemasukan = {
    "Sumber Pemasukan": ["Penjualan Padi", "Lain-lain"]
}

# ---------------- Fungsi Pemasukan ----------------

def pemasukan():
    st.subheader("Tambah Pemasukan")
    tanggal = st.date_input("Tanggal", datetime.now())
    sumber = st.selectbox("Sumber Pemasukan", kategori_pemasukan["Sumber Pemasukan"])
    jumlah = st.number_input("Jumlah (Rp)", min_value=0)
    deskripsi = st.text_area("Keterangan (opsional)") 
    metode = st.radio("Metode Penerimaan", ["Tunai", "Transfer", "Piutang", "Pelunasan Piutang"], horizontal=True)

    if st.button("✅ Simpan Pemasukan"):
        if not sumber.strip() or jumlah <= 0:
            st.error("Isi data dengan benar.")
            return
        
        waktu = tanggal.strftime("%Y-%m-%d %H:%M:%S")
        username = st.session_state['username']
        
        data = {
            "Tanggal": waktu,
            "Sumber": sumber,
            "Jumlah": jumlah,
            "Metode": metode,
            "Keterangan": deskripsi,
            "Username": username
        }
        
        try:
            append_data(data, "pemasukan.csv", username)
            
            akun_debit = {
                "Tunai": "Kas",
                "Transfer": "Bank",
                "Piutang": "Piutang Dagang",
                "Pelunasan Piutang": "Kas"
            }[metode]
            
            akun_kredit = "Pendapatan" if metode != "Pelunasan Piutang" else "Piutang Dagang"
            jurnal = buat_jurnal(waktu, akun_debit, akun_kredit, jumlah, sumber)
            
            for j in jurnal:
                append_data(j, "jurnal.csv", username)
                
            st.success("✅ Pemasukan berhasil disimpan.")
        except Exception as e:
            st.error(f"Gagal menyimpan data: {str(e)}")

# ---------------- Fungsi Pengeluaran ----------------

def pengeluaran():
    st.subheader("Tambah Pengeluaran")
    tanggal = st.date_input("Tanggal", datetime.now())
    kategori = st.selectbox("Kategori Utama", list(kategori_pengeluaran.keys()))
    sub_kategori = st.selectbox("Sub Kategori", kategori_pengeluaran[kategori])
    jumlah = st.number_input("Jumlah (Rp)", min_value=0)
    deskripsi = st.text_area("Keterangan (opsional)")
    metode = st.radio("Metode Pembayaran", ["Tunai", "Transfer", "Utang", "Pelunasan Utang"], horizontal=True)

    if st.button("✅ Simpan Pengeluaran"):
        if jumlah <= 0:
            st.error("Jumlah tidak boleh 0.")
            return
        
        waktu = tanggal.strftime("%Y-%m-%d %H:%M:%S")
        username = st.session_state['username']
        
        data = {
            "Tanggal": waktu,
            "Kategori": kategori,
            "Sub Kategori": sub_kategori,
            "Jumlah": jumlah,
            "Keterangan": deskripsi,
            "Metode": metode,
            "Username": username
        }
        
        try:
            append_data(data, "pengeluaran.csv", username)
            
            akun_kredit = {
                "Tunai": "Kas",
                "Transfer": "Bank",
                "Utang": "Utang Dagang",
                "Pelunasan Utang": "Kas"
            }[metode]
            
            akun_debit = sub_kategori if metode != "Pelunasan Utang" else "Utang Dagang"
            jurnal = buat_jurnal(waktu, akun_debit, akun_kredit, jumlah, deskripsi)
            
            for j in jurnal:
                append_data(j, "jurnal.csv", username)
                
            st.success("✅ Pengeluaran berhasil disimpan.")
        except Exception as e:
            st.error(f"Gagal menyimpan data: {str(e)}")

# ---------------- Fungsi Laporan ----------------

def laporan():
    st.header("Laporan Keuangan")
    username = st.session_state['username']

    col1, col2 = st.columns(2)
    with col1:
        mulai = st.date_input("Tanggal Mulai", datetime.now().replace(day=1))
    with col2:
        akhir = st.date_input("Tanggal Akhir", datetime.now())

    try:
        pemasukan_df = load_data("pemasukan.csv", username)
        pengeluaran_df = load_data("pengeluaran.csv", username)
        jurnal_df = load_data("jurnal.csv", username)

        # Konversi tanggal
        for df in [pemasukan_df, pengeluaran_df, jurnal_df]:
            if not df.empty and "Tanggal" in df.columns:
                df["Tanggal"] = pd.to_datetime(df["Tanggal"], errors='coerce')

        # Filter berdasarkan tanggal
        jurnal_df = jurnal_df[(jurnal_df['Tanggal'] >= pd.to_datetime(mulai)) & 
                             (jurnal_df['Tanggal'] <= pd.to_datetime(akhir))]

        tabs = st.tabs(["Ringkasan", "Jurnal Umum", "Buku Besar", "Laba Rugi", "Neraca"])

        with tabs[0]:
            st.subheader("Ringkasan Keuangan")
            
            # Hitung total pemasukan dan pengeluaran
            if not pemasukan_df.empty:
                pemasukan_df_filtered = pemasukan_df[(pemasukan_df['Tanggal'] >= pd.to_datetime(mulai)) & 
                                                    (pemasukan_df['Tanggal'] <= pd.to_datetime(akhir))]
                total_pemasukan = pemasukan_df_filtered['Jumlah'].sum()
            else:
                total_pemasukan = 0
                
            if not pengeluaran_df.empty:
                pengeluaran_df_filtered = pengeluaran_df[(pengeluaran_df['Tanggal'] >= pd.to_datetime(mulai)) & 
                                                         (pengeluaran_df['Tanggal'] <= pd.to_datetime(akhir))]
                total_pengeluaran = pengeluaran_df_filtered['Jumlah'].sum()
            else:
                total_pengeluaran = 0

            col1, col2 = st.columns(2)
            with col1:
                st.metric("Total Pemasukan", f"Rp {total_pemasukan:,.0f}")
            with col2:
                st.metric("Total Pengeluaran", f"Rp {total_pengeluaran:,.0f}")

            if total_pemasukan > 0 or total_pengeluaran > 0:
                df_sum = pd.DataFrame({
                    'Kategori': ['Pemasukan', 'Pengeluaran'],
                    'Jumlah': [total_pemasukan, total_pengeluaran]
                })
                fig = px.pie(df_sum, values='Jumlah', names='Kategori', 
                            title='Perbandingan Pemasukan dan Pengeluaran')
                st.plotly_chart(fig, use_container_width=True)

        with tabs[1]:
            st.subheader("Jurnal Umum")
            if not jurnal_df.empty:
                st.dataframe(jurnal_df, use_container_width=True)
            else:
                st.warning("Tidak ada data jurnal untuk periode ini.")

        with tabs[2]:
            st.subheader("Buku Besar")
            if not jurnal_df.empty:
                akun_list = jurnal_df['Akun'].unique()
                for akun in akun_list:
                    with st.expander(f"Akun: {akun}"):
                        df_akun = jurnal_df[jurnal_df['Akun'] == akun].copy()
                        df_akun = df_akun.sort_values("Tanggal")
                        df_akun['Saldo'] = df_akun['Debit'] - df_akun['Kredit']
                        df_akun['Saldo'] = df_akun['Saldo'].cumsum()
                        st.dataframe(df_akun, use_container_width=True)
            else:
                st.warning("Tidak ada data buku besar untuk periode ini.")

        with tabs[3]:
            st.subheader("Laporan Laba Rugi")
            
            if not jurnal_df.empty:
                pendapatan = jurnal_df[jurnal_df['Akun'].str.contains("Pendapatan", case=False)]['Kredit'].sum()
                beban = jurnal_df[~jurnal_df['Akun'].isin(['Kas', 'Bank', 'Piutang Dagang', 'Utang Dagang', 'Pendapatan'])]['Debit'].sum()
                laba_rugi = pendapatan - beban
                
                col1, col2, col3 = st.columns(3)
                with col1:
                    st.metric("Pendapatan", f"Rp {pendapatan:,.0f}")
                with col2:
                    st.metric("Beban", f"Rp {beban:,.0f}")
                with col3:
                    st.metric("Laba / Rugi", f"Rp {laba_rugi:,.0f}", 
                              delta_color="inverse" if laba_rugi < 0 else "normal")
                
                # Grafik laba rugi
                df_lr = pd.DataFrame({
                    'Kategori': ['Pendapatan', 'Beban'],
                    'Jumlah': [pendapatan, beban]
                })
                fig = px.bar(df_lr, x='Kategori', y='Jumlah', 
                            title='Perbandingan Pendapatan dan Beban',
                            color='Kategori')
                st.plotly_chart(fig, use_container_width=True)
            else:
                st.warning("Tidak ada data untuk laporan laba rugi.")

        with tabs[4]:
            st.subheader("Neraca")
            
            if not jurnal_df.empty:
                aktiva = jurnal_df[jurnal_df['Akun'].isin(['Kas', 'Bank', 'Piutang Dagang'])]['Debit'].sum() - \
                        jurnal_df[jurnal_df['Akun'].isin(['Kas', 'Bank', 'Piutang Dagang'])]['Kredit'].sum()
                
                kewajiban = jurnal_df[jurnal_df['Akun'].isin(['Utang Dagang'])]['Kredit'].sum() - \
                           jurnal_df[jurnal_df['Akun'].isin(['Utang Dagang'])]['Debit'].sum()
                
                laba_rugi = jurnal_df[jurnal_df['Akun'].str.contains("Pendapatan", case=False)]['Kredit'].sum() - \
                           jurnal_df[~jurnal_df['Akun'].isin(['Kas', 'Bank', 'Piutang Dagang', 'Utang Dagang', 'Pendapatan'])]['Debit'].sum()
                
                ekuitas = laba_rugi
                
                col1, col2, col3 = st.columns(3)
                with col1:
                    st.metric("Aktiva", f"Rp {aktiva:,.0f}")
                with col2:
                    st.metric("Kewajiban", f"Rp {kewajiban:,.0f}")
                with col3:
                    st.metric("Ekuitas", f"Rp {ekuitas:,.0f}")
                
                # Grafik neraca
                df_neraca = pd.DataFrame({
                    'Komponen': ['Aktiva', 'Kewajiban', 'Ekuitas'],
                    'Jumlah': [aktiva, kewajiban, ekuitas]
                })
                fig = px.bar(df_neraca, x='Komponen', y='Jumlah', 
                            title='Komposisi Neraca',
                            color='Komponen')
                st.plotly_chart(fig, use_container_width=True)
            else:
                st.warning("Tidak ada data untuk neraca.")

    except Exception as e:
        st.error(f"Terjadi kesalahan saat memproses laporan: {str(e)}")

# ---------------- Fungsi Logo ----------------
def tampilkan_logo():
    try:
        logo = Image.open("logo.jpg")
        st.sidebar.image(logo, width=200)
        return logo
    except FileNotFoundError:
        st.sidebar.title("SiPadi 🌾")
        return None
    except Exception as e:
        st.sidebar.warning(f"Gagal memuat logo: {str(e)}")
        st.sidebar.title("SiPadi 🌾")
        return None

# ---------------- UI Utama ----------------
def main():
    # Tampilkan logo di sidebar
    logo = tampilkan_logo()
    
    logged_in = login_register()
    if not logged_in:
        return
    
    # Header dengan logo
    col1, col2 = st.columns([1, 4])
    with col1:
        if logo:
            st.image(logo, width=80)
    with col2:
        st.title(f"Selamat datang, {st.session_state['username']}!")

    # Menu sidebar
    menu_options = ["Beranda", "Pemasukan", "Pengeluaran", "Laporan", "Logout"]
    menu = st.sidebar.radio("Menu Utama", menu_options)

    if menu == "Beranda":
        st.markdown("""
        ## Aplikasi Keuangan untuk Petani
        
        **SiPadi** adalah aplikasi keuangan khusus untuk petani dengan fitur:
        - 📈 Pencatatan pemasukan dan pengeluaran
        - 📊 Jurnal umum otomatis
        - 📚 Buku besar
        - 💰 Laporan laba rugi dan neraca
        - 📱 Tampilan responsif
        
        Gunakan menu di sebelah kiri untuk navigasi.
        """)
        
        st.markdown("---")
        
        # Statistik cepat
        try:
            username = st.session_state['username']
            pemasukan_df = load_data("pemasukan.csv", username)
            pengeluaran_df = load_data("pengeluaran.csv", username)
            
            col1, col2 = st.columns(2)
            with col1:
                total_pemasukan = pemasukan_df['Jumlah'].sum() if not pemasukan_df.empty else 0
                st.metric("Total Pemasukan", f"Rp {total_pemasukan:,.0f}")
            with col2:
                total_pengeluaran = pengeluaran_df['Jumlah'].sum() if not pengeluaran_df.empty else 0
                st.metric("Total Pengeluaran", f"Rp {total_pengeluaran:,.0f}")
        except:
            pass

    elif menu == "Pemasukan":
        pemasukan()

    elif menu == "Pengeluaran":
        pengeluaran()

    elif menu == "Laporan":
        laporan()

    elif menu == "Logout":
        st.session_state['logged_in'] = False
        st.session_state['username'] = ""
        st.success("Anda telah logout. Terima kasih!")
        st.rerun()

if __name__ == "__main__":
    main()
