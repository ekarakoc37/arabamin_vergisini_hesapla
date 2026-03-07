import streamlit as st
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import io

# 1. SAYFA AYARLARI VE BAŞLIK
st.set_page_config(page_title="Arabamın Vergisini Hesapla", layout="wide")

st.markdown("""
    <meta name="google" content="notranslate">
    <script>document.documentElement.lang = 'tr';</script>
    <style>
    h1 a, h2 a, h3 a, h4 a, h5 a, h6 a { display: none !important; }
    </style>
    """, unsafe_allow_html=True)

st.title("🌱 Arabamın Vergisini Hesapla")
st.markdown("Bu uygulama, araçların matrah ve emisyon değerlerine göre optimize edilmiş net vergi (Z) tutarını hesaplar ve çevreci alternatifler sunar.")

# 2. EVRENSEL VERGİ (Z) HESAPLAMA ALGORİTMASI
def calculate_Z_universal(B0, t0, e0, E, T, X, e_bar):
    t_e = t0 + (e0 - E) / E
    lambda_val = (e_bar - E) / e_bar
    
    B = B0 * (1 - (t_e - T)**2) + X
    G = B * t_e
    R = B * lambda_val
    
    return G - R

# 3. YAN MENÜ (SIDEBAR) - KULLANICI PARAMETRE GİRİŞLERİ
st.sidebar.header("⚙️ Yasal Parametre Ayarları")
E_HEDEF = st.sidebar.number_input("İdeal Emisyon Hedefi (E)", value=95)
E_BAR_UST = st.sidebar.number_input("Maksimum Emisyon Sınırı (ē)", value=180)
T_TOLERANS = st.sidebar.slider("Tolerans Katsayısı (T)", min_value=1.0, max_value=5.0, value=1.5, step=0.1) 
X_SABIT = st.sidebar.number_input("Sabit Karbon Maliyeti (X)", value=100000)

# 4. BELGE EKLEME ALANI
st.subheader("Veri Belgesi Ekleme") 
yuklenen_dosya = st.file_uploader("Lütfen araçların bulunduğu Excel veya CSV belgesini seçin:", type=['xlsx', 'csv'])

if yuklenen_dosya is not None:
    try:
        if yuklenen_dosya.name.endswith('.csv'):
            veritabani = pd.read_csv(yuklenen_dosya)
        else:
            veritabani = pd.read_excel(yuklenen_dosya)
            
        veritabani = veritabani.rename(columns={
            'Marka_Model': 'Marka/Model',
            'Motor_Tipi': 'Motor Tipi',
            'B0_Matrah': 'Matrah(B0)',
            'e0_Emisyon': 'Emisyon(e0)',
            't0_Katsayi': 'Katsayı (t0)'
        })
            
        if 'Marka/Model' in veritabani.columns:
            veritabani = veritabani.sort_values(by='Marka/Model').reset_index(drop=True)
            
        veritabani.index = veritabani.index + 1
            
        st.success(f"Veriler başarıyla eklendi! ({len(veritabani)} araç bulundu)")
        
        with st.expander("Tabloyu Görüntüle"):
            st.dataframe(veritabani)

        # 5. ARAÇ SEÇİMİ VE ANALİZ BÖLÜMÜ
        st.subheader("Araç Analizi ve Karşılaştırma")
        arac_listesi = veritabani['Marka/Model'].tolist()
        secilen_araclar = st.multiselect("Analiz edilecek araçları seçin:", arac_listesi)
        
        if st.button("Analizi Başlat") and secilen_araclar:
            st.markdown("---")
            hesaplanan_sonuclar = []
            
            # YENİ: IZGARA (GRID) SİSTEMİ - Arayüz çökmesin diye her satıra max 3 araç
            sutun_sayisi = 3
            for i in range(0, len(secilen_araclar), sutun_sayisi):
                kolonlar = st.columns(sutun_sayisi)
                
                for j in range(sutun_sayisi):
                    if i + j < len(secilen_araclar):
                        arac_adi = secilen_araclar[i + j]
                        arac = veritabani[veritabani['Marka/Model'] == arac_adi].iloc[0]
                        
                        z_vergi = calculate_Z_universal(
                            B0=arac['Matrah(B0)'], t0=arac['Katsayı (t0)'], e0=arac['Emisyon(e0)'],
                            E=E_HEDEF, T=T_TOLERANS, X=X_SABIT, e_bar=E_BAR_UST
                        )
                        
                        toplam_fiyat = arac['Matrah(B0)'] + z_vergi
                        
                        hesaplanan_sonuclar.append({
                            'Model': arac['Marka/Model'],
                            'Matrah (TL)': arac['Matrah(B0)'],
                            'Emisyon (g/km)': arac['Emisyon(e0)'],
                            'Vergi': z_vergi,
                            'Anahtar Teslim (TL)': toplam_fiyat
                        })
                        
                        fiyat_alt = arac['Matrah(B0)'] * 0.85
                        fiyat_ust = arac['Matrah(B0)'] * 1.15
                        alternatifler = veritabani[
                            (veritabani['Matrah(B0)'] >= fiyat_alt) & 
                            (veritabani['Matrah(B0)'] <= fiyat_ust) & 
                            (veritabani['Emisyon(e0)'] < arac['Emisyon(e0)'])
                        ]
                        
                        with kolonlar[j]:
                            st.markdown(f"#### 🚗 {arac['Marka/Model']}")
                            st.metric(label="Hesaplanan Vergi (Z)", value=f"{z_vergi:,.0f} TL", delta=f"{arac['Emisyon(e0)']} g/km Emisyon", delta_color="inverse")
                            
                            if z_vergi < 0:
                                st.success("🎁 **Teşvik Kazandınız!** Seçiminizle çevreye en duyarlı araçlardan birini seçtiniz, dolayısıyla size vergi yerine devlet teşviki uygulanacaktır.")
                            
                            st.write(f"**Matrah (Çıplak Fiyat):** {arac['Matrah(B0)']:,.0f} TL")
                            st.info(f"🏷️ **Anahtar Teslim:** {toplam_fiyat:,.0f} TL")
                            
                            if arac['Emisyon(e0)'] == 0:
                                st.success("🌟 **Mükemmel Seçim!** Bu araç SIFIR emisyonlu olduğu için sistemdeki en çevreci seçenektir.")
                            elif not alternatifler.empty:
                                oneriler = alternatifler.sort_values(by='Emisyon(e0)').head(2)
                                oneri_metni = "\n".join([f"- {row['Marka/Model']} ({row['Emisyon(e0)']} g/km)" for _, row in oneriler.iterrows()])
                                
                                if arac['Emisyon(e0)'] > E_HEDEF:
                                    st.warning(f"🌍 **Geleceğimiz için bir adım atın:** Bütçenize uygun ancak doğaya çok daha az zarar veren şu çevreci araçları tercih edebilirsiniz:\n{oneri_metni}")
                                else:
                                    st.success(f"🌱 **Daha Çevreci Alternatifler:**\n{oneri_metni}")
                            else:
                                st.info("👍 Bu fiyat bandındaki en düşük emisyonlu seçeneklerden birine bakıyorsunuz.")
                
                # Her 3 araçtan sonra araya ince bir çizgi çeker
                st.markdown("---")

            # 6. GRAFİK ÇİZİMİ
            if len(secilen_araclar) > 1:
                st.markdown("### Vergi (Z) Tutarı Karşılaştırması")
                modeller = [item['Model'] for item in hesaplanan_sonuclar]
                vergiler = [item['Vergi'] for item in hesaplanan_sonuclar]
                
                # YENİ: Esnek Grafik Genişliği (Araç sayısına göre uzar)
                grafik_genislik = max(10, len(modeller) * 0.7)
                fig, ax = plt.subplots(figsize=(grafik_genislik, 6))
                
                cubuklar = ax.bar(modeller, vergiler, color='#2c3e50')
                ax.set_ylabel('Net Vergi Tutarı (TL)')
                ax.get_yaxis().set_major_formatter(plt.FuncFormatter(lambda x, p: format(int(x), ',').replace(',', '.')))
                
                # YENİ: İsimler birbirine girmesin diye açılı yazdırıldı
                plt.xticks(rotation=45, ha='right')
                ax.grid(axis='y', linestyle='--', alpha=0.5)
                
                # YENİ: Kalabalıkta çubuk tepesindeki sayıları 45 derece eğik yaz (veya 15'ten çok araç varsa gizle)
                if len(modeller) <= 15:
                    for cubuk in cubuklar:
                        yval = cubuk.get_height()
                        # Eğer sayı negatifse yazıyı çubuğun altına it
                        dikey_hiza = 'bottom' if yval >= 0 else 'top'
                        ax.text(cubuk.get_x() + cubuk.get_width()/2, yval, f'{int(yval):,}', ha='center', va=dikey_hiza, rotation=45 if len(modeller)>5 else 0, fontsize=9)
                
                # Grafiğin alt yazıları kesilmesin diye sıkıştırma ayarı
                plt.tight_layout()
                st.pyplot(fig)
                
            # 7. EXCEL OLARAK İNDİRME BÖLÜMÜ
            if len(hesaplanan_sonuclar) > 0:
                st.subheader("Raporu İndir")
                
                df_rapor = pd.DataFrame(hesaplanan_sonuclar)
                df_rapor.rename(columns={'Model': 'Araç Modeli', 'Vergi': 'Hesaplanan Vergi (TL)'}, inplace=True)
                
                df_rapor['Matrah (TL)'] = df_rapor['Matrah (TL)'].apply(lambda x: f"{x:,.0f}".replace(',', '.'))
                df_rapor['Hesaplanan Vergi (TL)'] = df_rapor['Hesaplanan Vergi (TL)'].apply(lambda x: f"{x:,.0f}".replace(',', '.'))
                df_rapor['Anahtar Teslim (TL)'] = df_rapor['Anahtar Teslim (TL)'].apply(lambda x: f"{x:,.0f}".replace(',', '.'))
                
                buffer = io.BytesIO()
                with pd.ExcelWriter(buffer, engine='openpyxl') as writer:
                    df_rapor.to_excel(writer, index=False, sheet_name='Vergi_Analizi')
                    worksheet = writer.sheets['Vergi_Analizi']
                    
                    for i, col in enumerate(df_rapor.columns):
                        column_letter = chr(65 + i) 
                        max_len = max(df_rapor[col].astype(str).map(len).max(), len(str(col))) + 4
                        worksheet.column_dimensions[column_letter].width = max_len
                
                st.download_button(
                    label="📊 Sonuçları Excel Olarak İndir",
                    data=buffer.getvalue(),
                    file_name="arac_vergi_raporu.xlsx",
                    mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
                )
                
    except Exception as e:
        st.error(f"Belge okunurken bir hata oluştu. Hata detayı: {e}")
            
else:
    st.info("👆 Lütfen analize başlamak için sol üstten Excel veya CSV belgenizi seçin.")