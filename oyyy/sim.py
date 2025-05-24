import streamlit as st
from datetime import datetime
import os
import hashlib
import pandas as pd



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
        except pd.errors.EmptyDataError:
            # Jika file kosong, buat DataFrame kosong dengan kolom sesuai file yang dipakai
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
        return pd.read_csv("akun.csv")
    else:
        return pd.DataFrame(columns=["Username", "Password"])

def save_user_accounts(df):
    df.to_csv("akun.csv", index=False)

def register_user(username, password):
    akun_df = load_user_accounts()
    if (akun_df['Username'] == username).any():
        return False  # Username sudah ada
    akun_df = pd.concat([akun_df, pd.DataFrame([{"Username": username, "Password": hash_password(password)}])], ignore_index=True)
    save_user_accounts(akun_df)
    return True

def validate_login(username, password):
    akun_df = load_user_accounts()
    hashed_pw = hash_password(password)
    return ((akun_df['Username'] == username) & (akun_df['Password'] == hashed_pw)).any()

import streamlit as st

# ---------------- Login & Register ----------------

def login_register():
    if 'logged_in' not in st.session_state:
        st.session_state['logged_in'] = False
    if 'username' not in st.session_state:
        st.session_state['username'] = ""

    if st.session_state['logged_in']:
        return True

    st.title("🔐 Login / Daftar Akun")
    
    mode = st.radio("Pilih Mode", ["Login", "Daftar"])
    username = st.text_input("Nama Pengguna")
    password = st.text_input("Kata Sandi", type="password")

    if mode == "Login":
        if st.button("Masuk"):
            if username.strip() == "" or password.strip() == "":
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
            if username.strip() == "" or password.strip() == "":
                st.error("Harap isi semua kolom.")
            elif register_user(username, password):
                st.success("Akun berhasil dibuat. Silakan login.")
            else:
                st.error("Username sudah digunakan.")

    st.stop()
    return False


# ---------------- Data Kategori ----------------

kategori_pengeluaran = {
    "Bibit": ["Intani", "Inpari", "Ciherang", "32"],
    "Pupuk": ["Urea", "NPK", "Organik", "Ponska"],
    "Pestisida": ["Debestan", "Ronsa", "Refaton", "Ema", "Plenum"],
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
    metode = st.radio("Metode Penerimaan", ["Tunai", "Transfer", "Piutang", "Pelunasan Piutang"])

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

# ---------------- Fungsi Pengeluaran ----------------

def pengeluaran():
    st.subheader("Tambah Pengeluaran")
    tanggal = st.date_input("Tanggal", datetime.now())
    kategori = st.selectbox("Kategori Utama", list(kategori_pengeluaran.keys()))
    sub_kategori = st.selectbox("Sub Kategori", kategori_pengeluaran[kategori])
    jumlah = st.number_input("Jumlah (Rp)", min_value=0)
    deskripsi = st.text_area("Keterangan (opsional)")
    metode = st.radio("Metode Pembayaran", ["Tunai", "Transfer", "Utang", "Pelunasan Utang"])

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

# ---------------- Fungsi Hapus Transaksi ----------------

def hapus_transaksi(transaksi_type, index_to_delete, username):
    if transaksi_type == "pemasukan":
        df = load_data("pemasukan.csv", username)
    elif transaksi_type == "pengeluaran":
        df = load_data("pengeluaran.csv", username)
    else:
        return False
    
    if index_to_delete in df.index:
        transaksi = df.loc[index_to_delete]
        df = df.drop(index_to_delete).reset_index(drop=True)
        save_data(df, f"{transaksi_type}.csv", username)
        
        jurnal_df = load_data("jurnal.csv", username)
        
        if transaksi_type == "pemasukan":
            if transaksi['Metode'] == "Pelunasan Piutang":
                jurnal_pembalikan = buat_jurnal(
                    datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                    "Piutang Dagang",
                    "Kas",
                    transaksi['Jumlah'],
                    f"Pembatalan: {transaksi['Keterangan']}"
                )
            else:
                akun_debit = {
                    "Tunai": "Kas",
                    "Transfer": "Bank",
                    "Piutang": "Piutang Dagang"
                }[transaksi['Metode']]
                jurnal_pembalikan = buat_jurnal(
                    datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                    "Pendapatan",
                    akun_debit,
                    transaksi['Jumlah'],
                    f"Pembatalan: {transaksi['Keterangan']}"
                )
        else:
            if transaksi['Metode'] == "Pelunasan Utang":
                jurnal_pembalikan = buat_jurnal(
                    datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                    "Kas",
                    "Utang Dagang",
                    transaksi['Jumlah'],
                    f"Pembatalan: {transaksi['Keterangan']}"
                )
            else:
                akun_kredit = {
                    "Tunai": "Kas",
                    "Transfer": "Bank",
                    "Utang": "Utang Dagang"
                }[transaksi['Metode']]
                jurnal_pembalikan = buat_jurnal(
                    datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                    akun_kredit,
                    transaksi['Sub Kategori'],
                    transaksi['Jumlah'],
                    f"Pembatalan: {transaksi['Keterangan']}"
                )
        
        for j in jurnal_pembalikan:
            append_data(j, "jurnal.csv", username)
        
        return True
    return False

# ---------------- Fungsi Laporan ----------------

def laporan():
    import plotly.express as px
    st.header("Laporan Keuangan")
    username = st.session_state['username']

    mulai = st.date_input("Tanggal Mulai", datetime.now().replace(day=1))
    akhir = st.date_input("Tanggal Akhir", datetime.now())

    pemasukan_df = load_data("pemasukan.csv", username)
    pengeluaran_df = load_data("pengeluaran.csv", username)
    jurnal_df = load_data("jurnal.csv", username)

    for df in [pemasukan_df, pengeluaran_df, jurnal_df]:
        if not df.empty and "Tanggal" in df.columns:
            df["Tanggal"] = pd.to_datetime(df["Tanggal"], errors='coerce')

    jurnal_df = jurnal_df[(jurnal_df['Tanggal'] >= pd.to_datetime(mulai)) & (jurnal_df['Tanggal'] <= pd.to_datetime(akhir))]

    tabs = st.tabs(["Ringkasan", "Jurnal Umum", "Buku Besar", "Laba Rugi", "Neraca"])

    with tabs[0]:
        total_pemasukan = pemasukan_df[(pemasukan_df['Tanggal'] >= pd.to_datetime(mulai)) & (pemasukan_df['Tanggal'] <= pd.to_datetime(akhir))]['Jumlah'].sum() if not pemasukan_df.empty else 0
        total_pengeluaran = pengeluaran_df[(pengeluaran_df['Tanggal'] >= pd.to_datetime(mulai)) & (pengeluaran_df['Tanggal'] <= pd.to_datetime(akhir))]['Jumlah'].sum() if not pengeluaran_df.empty else 0

        st.metric("Total Pemasukan", f"Rp {total_pemasukan:,.0f}")
        st.metric("Total Pengeluaran", f"Rp {total_pengeluaran:,.0f}")

        if total_pemasukan > 0 or total_pengeluaran > 0:
            df_sum = pd.DataFrame({
                'Kategori': ['Pemasukan', 'Pengeluaran'],
                'Jumlah': [total_pemasukan, total_pengeluaran]
            })
            fig = px.pie(df_sum, values='Jumlah', names='Kategori')
            

    with tabs[1]:
        st.markdown("### Jurnal Umum")
        st.dataframe(jurnal_df if not jurnal_df.empty else pd.DataFrame())

    with tabs[2]:
        if not jurnal_df.empty:
            akun_list = jurnal_df['Akun'].unique()
            for akun in akun_list:
                st.subheader(f"Akun: {akun}")
                df_akun = jurnal_df[jurnal_df['Akun'] == akun].copy()
                df_akun = df_akun.sort_values("Tanggal")
                df_akun['Saldo'] = df_akun['Debit'] - df_akun['Kredit']
                df_akun['Saldo'] = df_akun['Saldo'].cumsum()
                st.dataframe(df_akun)

    with tabs[3]:
        pendapatan = jurnal_df[jurnal_df['Akun'].str.contains("Pendapatan")]['Kredit'].sum() if not jurnal_df.empty else 0
        beban = jurnal_df[~jurnal_df['Akun'].isin(['Kas', 'Bank', 'Piutang Dagang', 'Utang Dagang', 'Pendapatan'])]['Debit'].sum() if not jurnal_df.empty else 0
        laba_rugi = pendapatan - beban
        st.metric("Pendapatan", f"Rp {pendapatan:,.0f}")
        st.metric("Beban", f"Rp {beban:,.0f}")
        st.metric("Laba / Rugi", f"Rp {laba_rugi:,.0f}")

    with tabs[4]:
        aktiva = jurnal_df[jurnal_df['Akun'].isin(['Kas', 'Bank', 'Piutang Dagang'])]['Debit'].sum() - jurnal_df[jurnal_df['Akun'].isin(['Kas', 'Bank', 'Piutang Dagang'])]['Kredit'].sum() if not jurnal_df.empty else 0
        kewajiban = jurnal_df[jurnal_df['Akun'].isin(['Utang Dagang'])]['Kredit'].sum() - jurnal_df[jurnal_df['Akun'].isin(['Utang Dagang'])]['Debit'].sum() if not jurnal_df.empty else 0
        ekuitas = laba_rugi
        st.metric("Aktiva", f"Rp {aktiva:,.0f}")
        st.metric("Kewajiban", f"Rp {kewajiban:,.0f}")
        st.metric("Ekuitas", f"Rp {ekuitas:,.0f}")
    
    if not pemasukan_df.empty and 'Username' in pemasukan_df.columns:
        pemasukan_df = pemasukan_df[pemasukan_df['Username'] == username]
    if not pengeluaran_df.empty and 'Username' in pengeluaran_df.columns:
        pengeluaran_df = pengeluaran_df[pengeluaran_df['Username'] == username]
    if not jurnal_df.empty and 'Username' in jurnal_df.columns:
        jurnal_df = jurnal_df[jurnal_df['Username'] == username]

# ---------------- UI Utama ----------------

def main():
    st.set_page_config(layout="wide")  # Pastikan ada konfigurasi dasar
   
    # Logo kecil di header (ganti dengan URL/logo sendiri jika ada)
    st.sidebar.title("Menu")
    
    logged_in = login_register()
    if not logged_in:
        return

    
    menu = st.sidebar.radio("Pilih Menu", ["Beranda", "Pemasukan", "Pengeluaran", "Laporan", "Logout"])

    if menu == "Beranda":
        st.title(f"Selamat datang, {st.session_state['username']}!")
        st.markdown("Ini adalah aplikasi keuangan untuk petani dengan fitur lengkap.")
        st.markdown("- Tambah pemasukan dan pengeluaran")
        st.markdown("- Jurnal umum otomatis")
        st.markdown("- Buku besar")
        st.markdown("- Laporan laba rugi dan neraca")
        st.markdown("Gunakan menu di sebelah kiri untuk navigasi.")

    elif menu == "Pemasukan":
        pemasukan()

    elif menu == "Pengeluaran":
        pengeluaran()

    elif menu == "Laporan":
        laporan() # Grafik Plotly hanya ada di fungsi laporan()

    elif menu == "Logout":
        st.session_state['logged_in'] = False
        st.session_state['username'] = ""
        st.rerun()

if _name_ == "_main_":
    main()
