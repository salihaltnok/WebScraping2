import requests
from bs4 import BeautifulSoup
import pandas as pd
import matplotlib.pyplot as plt
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
import seaborn as sns
import re
from datetime import datetime
import time
import random
import threading
import tkinter as tk
from tkinter import ttk, filedialog, messagebox, scrolledtext
import webbrowser
import os

# Global değişkenler
THEME_COLOR_PRIMARY = "#1e88e5"
THEME_COLOR_BG = "#f5f5f7"
THEME_COLOR_TEXT = "#333333"


class FiyatKarsilastirma:
    def __init__(self, pencere):
        # Ana pencereyi ayarla
        self.pencere = pencere
        self.pencere.title("Fiyat Karşılaştırma Aracı")
        self.pencere.geometry("900x700")
        self.pencere.minsize(900, 700)
        # Değişkenler
        self.urunler = []  # topladığımız ürünleri tutacak
        self.site_tipi = ""  # hangi sitede olduğumuzu takip etmek için
        self.veri_toplaniyor = False
        self.analiz_sonuclari = None
        # UI elemanlarını oluştur
        self.arayuz_olustur()
        # URL örneği ekle
        self.url_entry.insert(0, "https://www.itopya.com/notebook_k14")
        # URL değiştiğinde site tipini otomatik algıla
        self.url_entry.bind("<FocusOut>", self.site_tipini_algila)
        # Site tipini başlangıçta algıla
        self.site_tipini_algila()

    def arayuz_olustur(self):
        # Ana çerçeve
        self.ana_frame = ttk.Frame(self.pencere, padding=10)
        self.ana_frame.pack(fill=tk.BOTH, expand=True)

        # Başlık
        baslik = ttk.Label(self.ana_frame,
                           text="Web Tabanlı Ürün Fiyat Karşılaştırma",
                           font=('Arial', 16, 'bold'))
        baslik.pack(pady=10)

        # Giriş alanı
        giris_frame = ttk.Frame(self.ana_frame)
        giris_frame.pack(fill=tk.X, pady=10)

        # URL girişi
        url_label = ttk.Label(giris_frame, text="Ürün Arama URL'si:")
        url_label.grid(row=0, column=0, padx=5, pady=5, sticky=tk.W)
        self.url_entry = ttk.Entry(giris_frame, width=70)
        self.url_entry.grid(row=0, column=1, padx=5, pady=5, sticky=tk.W + tk.E)

        # Site bilgisi
        site_label = ttk.Label(giris_frame, text="Algılanan Site:")
        site_label.grid(row=1, column=0, padx=5, pady=5, sticky=tk.W)
        self.site_info = ttk.Label(giris_frame, text="Henüz algılanmadı")
        self.site_info.grid(row=1, column=1, padx=5, pady=5, sticky=tk.W)

        # Sayfa sayısı
        sayfa_label = ttk.Label(giris_frame, text="Toplam Sayfa Sayısı:")
        sayfa_label.grid(row=2, column=0, padx=5, pady=5, sticky=tk.W)
        self.sayfa_spinbox = ttk.Spinbox(giris_frame, from_=1, to=10, width=5)
        self.sayfa_spinbox.grid(row=2, column=1, padx=5, pady=5, sticky=tk.W)
        self.sayfa_spinbox.set(1)

        # Fiyat Filtreleme Alanı Ekle - YENI
        filtre_frame = ttk.LabelFrame(self.ana_frame, text="Fiyat Filtreleme")
        filtre_frame.pack(fill=tk.X, pady=(0, 10), padx=10)

        # Minimum Fiyat
        min_fiyat_label = ttk.Label(filtre_frame, text="Minimum Fiyat (TL):")
        min_fiyat_label.grid(row=0, column=0, padx=5, pady=5, sticky=tk.W)
        self.min_fiyat_entry = ttk.Entry(filtre_frame, width=10)
        self.min_fiyat_entry.grid(row=0, column=1, padx=5, pady=5, sticky=tk.W)
        self.min_fiyat_entry.insert(0, "0")

        # Maksimum Fiyat
        max_fiyat_label = ttk.Label(filtre_frame, text="Maksimum Fiyat (TL):")
        max_fiyat_label.grid(row=0, column=2, padx=5, pady=5, sticky=tk.W)
        self.max_fiyat_entry = ttk.Entry(filtre_frame, width=10)
        self.max_fiyat_entry.grid(row=0, column=3, padx=5, pady=5, sticky=tk.W)
        self.max_fiyat_entry.insert(0, "100000")

        # Filtreleme butonu
        self.filtrele_button = ttk.Button(filtre_frame, text="Filtrele", command=self.urunleri_filtrele,
                                          state=tk.DISABLED)
        self.filtrele_button.grid(row=0, column=4, padx=15, pady=5)

        # Sıfırlama butonu
        self.sifirla_button = ttk.Button(filtre_frame, text="Sıfırla", command=self.filtreleri_sifirla,
                                         state=tk.DISABLED)
        self.sifirla_button.grid(row=0, column=5, padx=5, pady=5)

        # Filtreleme bilgisi
        self.filtre_info = ttk.Label(filtre_frame, text="Filtreleme yok", foreground="gray")
        self.filtre_info.grid(row=0, column=6, padx=5, pady=5, sticky=tk.W)

        # Bilgi notu
        info_label = ttk.Label(giris_frame,
                               text="Not: Çok fazla veri toplarken site kullanım koşullarına dikkat edin.",
                               font=('Arial', 8), foreground='gray')
        info_label.grid(row=3, column=0, columnspan=2, padx=5, pady=5, sticky=tk.W)

        # Butonlar
        buton_frame = ttk.Frame(self.ana_frame)
        buton_frame.pack(fill=tk.X, pady=10)
        self.topla_button = ttk.Button(buton_frame,
                                       text="Verileri Topla",
                                       command=self.veri_toplamaya_basla)
        self.topla_button.pack(side=tk.LEFT, padx=5)
        self.kaydet_button = ttk.Button(buton_frame,
                                        text="CSV Olarak Kaydet",
                                        command=self.csv_kaydet,
                                        state=tk.DISABLED)
        self.kaydet_button.pack(side=tk.LEFT, padx=5)
        self.grafik_button = ttk.Button(buton_frame,
                                        text="Grafikleri Göster",
                                        command=self.grafikleri_goster,
                                        state=tk.DISABLED)
        self.grafik_button.pack(side=tk.LEFT, padx=5)

        # İlerleme çubuğu
        ilerleme_label = ttk.Label(self.ana_frame, text="İlerleme:")
        ilerleme_label.pack(anchor=tk.W, pady=(10, 0))
        self.ilerleme_cubugu = ttk.Progressbar(self.ana_frame, orient=tk.HORIZONTAL,
                                               length=100, mode='determinate')
        self.ilerleme_cubugu.pack(fill=tk.X, pady=(0, 10))

        # Notebook (sekmeler)
        self.notebook = ttk.Notebook(self.ana_frame)
        self.notebook.pack(fill=tk.BOTH, expand=True, pady=10)

        # Veri sekmesi
        self.veri_frame = ttk.Frame(self.notebook)
        self.notebook.add(self.veri_frame, text="Veri Görünümü")

        # Veri tablosu
        self.tablo_frame = ttk.Frame(self.veri_frame)
        self.tablo_frame.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)

        # Treeview için sütunlar
        self.sutunlar = ("baslik", "fiyat", "fiyat_sayisal", "satici", "stok", "kargo")
        self.treeview = ttk.Treeview(self.tablo_frame, columns=self.sutunlar, show="headings")

        # Sütunları ayarla
        self.treeview.heading("baslik", text="Ürün Adı")
        self.treeview.heading("fiyat", text="Fiyat")
        self.treeview.heading("fiyat_sayisal", text="Sayısal Fiyat")
        self.treeview.heading("satici", text="Satıcı")
        self.treeview.heading("stok", text="Stok Durumu")
        self.treeview.heading("kargo", text="Kargo")

        # Sütun genişlikleri
        self.treeview.column("baslik", width=250, minwidth=150)
        self.treeview.column("fiyat", width=100, minwidth=80)
        self.treeview.column("fiyat_sayisal", width=80, minwidth=80)
        self.treeview.column("satici", width=120, minwidth=100)
        self.treeview.column("stok", width=100, minwidth=80)
        self.treeview.column("kargo", width=120, minwidth=80)

        # Kaydırma çubukları
        scrollbar_y = ttk.Scrollbar(self.tablo_frame, orient=tk.VERTICAL, command=self.treeview.yview)
        self.treeview.configure(yscrollcommand=scrollbar_y.set)
        scrollbar_x = ttk.Scrollbar(self.tablo_frame, orient=tk.HORIZONTAL, command=self.treeview.xview)
        self.treeview.configure(xscrollcommand=scrollbar_x.set)

        # Yerleştirme
        self.treeview.grid(row=0, column=0, sticky="nsew")
        scrollbar_y.grid(row=0, column=1, sticky="ns")
        scrollbar_x.grid(row=1, column=0, sticky="ew")
        self.tablo_frame.grid_rowconfigure(0, weight=1)
        self.tablo_frame.grid_columnconfigure(0, weight=1)

        # Analiz sekmesi
        self.analiz_frame = ttk.Frame(self.notebook)
        self.notebook.add(self.analiz_frame, text="Analiz Sonuçları")

        # Analiz metin kutusu
        self.analiz_text = scrolledtext.ScrolledText(self.analiz_frame, wrap=tk.WORD, width=80, height=25)
        self.analiz_text.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)

        # Grafik sekmesi
        self.grafik_frame = ttk.Frame(self.notebook)
        self.notebook.add(self.grafik_frame, text="Grafikler")

        # Log sekmesi
        self.log_frame = ttk.Frame(self.notebook)
        self.notebook.add(self.log_frame, text="Log")

        # Log metin kutusu
        self.log_text = scrolledtext.ScrolledText(self.log_frame, wrap=tk.WORD, width=80, height=25)
        self.log_text.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)

    def urunleri_filtrele(self):
        """Tabloyu belirtilen fiyat aralığına göre filtreler"""
        if not self.urunler:
            messagebox.showwarning("Uyarı", "Filtrelenecek ürün bulunmamaktadır!")
            return

        try:
            # Fiyat değerlerini al ve kontrol et
            min_fiyat = float(self.min_fiyat_entry.get().replace(',', '.'))
            max_fiyat = float(self.max_fiyat_entry.get().replace(',', '.'))

            if min_fiyat < 0 or max_fiyat < 0:
                messagebox.showerror("Hata", "Fiyatlar negatif olamaz!")
                return

            if min_fiyat > max_fiyat:
                messagebox.showerror("Hata", "Minimum fiyat, maksimum fiyattan büyük olamaz!")
                return

            # Tabloyu temizle
            self.treeview.delete(*self.treeview.get_children())

            # Filtrelenmiş ürünleri bul
            filtrelenmis_urunler = [
                urun for urun in self.urunler
                if min_fiyat <= urun['price_numeric'] <= max_fiyat
            ]

            # Filtrelenmiş sayı bilgisini güncelle
            self.filtre_info.config(
                text=f"Filtrelendi: {len(filtrelenmis_urunler)} / {len(self.urunler)} ürün",
                foreground="blue"
            )

            # Sıralama yapalım: En ucuz -> En pahalı
            filtrelenmis_urunler = sorted(filtrelenmis_urunler, key=lambda x: x['price_numeric'])

            # Ürünleri tabloya ekle
            self.tabloyu_guncelle(filtrelenmis_urunler)

            self.log_yaz(
                f"Ürünler {min_fiyat} TL - {max_fiyat} TL aralığında filtrelendi. {len(filtrelenmis_urunler)} ürün gösteriliyor.")

        except ValueError:
            messagebox.showerror("Hata", "Lütfen geçerli sayısal değerler girin!")
        except Exception as e:
            messagebox.showerror("Hata", f"Filtreleme sırasında hata oluştu: {str(e)}")

    def filtreleri_sifirla(self):
        """Filtreleri sıfırlar ve tüm ürünleri gösterir"""
        if not self.urunler:
            return

        # Varsayılan değerleri ayarla
        self.min_fiyat_entry.delete(0, tk.END)
        self.min_fiyat_entry.insert(0, "0")
        self.max_fiyat_entry.delete(0, tk.END)
        self.max_fiyat_entry.insert(0, "100000")

        # Tabloyu temizle ve tüm ürünleri göster
        self.treeview.delete(*self.treeview.get_children())
        self.tabloyu_guncelle(self.urunler)

        # Filtre bilgisini güncelle
        self.filtre_info.config(text="Filtreleme yok", foreground="gray")

        self.log_yaz("Filtreler sıfırlandı, tüm ürünler gösteriliyor.")

    def log_yaz(self, mesaj):
        """Log mesajı ekler"""
        zaman = datetime.now().strftime("%H:%M:%S")
        log_mesaji = f"[{zaman}] {mesaj}\n"
        print(log_mesaji.strip())  # Konsola da yazdır
        # Log metin kutusuna ekle
        self.log_text.insert(tk.END, log_mesaji)
        self.log_text.see(tk.END)  # Otomatik kaydır

    def site_tipini_algila(self, event=None):
        """URL'den site tipini algılar"""
        url = self.url_entry.get().strip()
        if not url:
            return
        if "itopya.com" in url:
            self.site_tipi = "itopya"
            self.site_info.config(text="İtopya")
            self.log_yaz("Site algılandı: İtopya")
        elif "robotistan.com" in url:
            self.site_tipi = "robotistan"
            self.site_info.config(text="Robotistan")
            self.log_yaz("Site algılandı: Robotistan")
        elif "direnc.net" in url:
            self.site_tipi = "direnc"
            self.site_info.config(text="Direnc.net")
            self.log_yaz("Site algılandı: Direnc.net")
        else:
            self.site_tipi = ""
            self.site_info.config(text="Desteklenmeyen site")
            self.log_yaz("Desteklenmeyen site algılandı")

    def veri_toplamaya_basla(self):
        """Veri toplama işlemini başlatır"""
        url = self.url_entry.get().strip()
        if not url:
            messagebox.showerror("Hata", "Lütfen bir URL girin!")
            return

        # URL düzeltme
        if not url.startswith("http"):
            url = "https://" + url

        # Site tipini kontrol et
        self.site_tipini_algila()
        if not self.site_tipi:
            messagebox.showerror("Hata", "Bu site şu anda desteklenmiyor!")
            return

        # Sayfa sayısını al
        try:
            sayfa_sayisi = int(self.sayfa_spinbox.get())
        except:
            sayfa_sayisi = 1

        # Arayüzü devre dışı bırak
        self.arayuz_durumu_degistir(False)

        # İlerleme çubuğunu sıfırla
        self.ilerleme_cubugu["value"] = 0

        # Verileri temizle
        self.urunler = []
        self.analiz_sonuclari = None
        self.treeview.delete(*self.treeview.get_children())
        self.analiz_text.delete(1.0, tk.END)
        self.log_text.delete(1.0, tk.END)

        # Grafik alanını temizle
        for widget in self.grafik_frame.winfo_children():
            widget.destroy()

        # Veri toplama işlemini ayrı bir thread'de başlat
        self.veri_toplama_thread = threading.Thread(target=self.veri_topla, args=(url, sayfa_sayisi))
        self.veri_toplama_thread.daemon = True
        self.veri_toplama_thread.start()

    def veri_topla(self, url, sayfa_sayisi):
        """Verileri toplar ve analizleri yapar"""
        try:
            self.veri_toplaniyor = True
            tum_urunler = []
            for sayfa in range(1, sayfa_sayisi + 1):
                # İlerleme çubuğunu güncelle
                ilerleme = ((sayfa - 1) / sayfa_sayisi * 100)
                self.pencere.after(0, lambda p=ilerleme: self.ilerleme_cubugu.configure(value=p))

                # Sayfa URL'sini ayarla
                if sayfa > 1:
                    sayfa_url = self.sayfa_url_ekle(url, sayfa)
                else:
                    sayfa_url = url
                self.log_yaz(f"Sayfa {sayfa} için URL: {sayfa_url}")

                # Sayfa içeriğini al
                sayfa_icerigi = self.sayfa_icerigi_al(sayfa_url)
                if not sayfa_icerigi:
                    self.log_yaz(f"Sayfa {sayfa} için içerik alınamadı!")
                    continue

                # HTML içeriğini debug için kaydet
                with open(f"debug_sayfa{sayfa}.html", "w", encoding="utf-8") as f:
                    f.write(sayfa_icerigi)

                # Ürünleri ayrıştır
                sayfa_urunleri = self.urunleri_ayristir(sayfa_icerigi)
                if sayfa_urunleri:
                    self.log_yaz(f"Sayfa {sayfa}'de {len(sayfa_urunleri)} ürün bulundu")
                    tum_urunler.extend(sayfa_urunleri)
                    # Her sayfadan sonra tabloyu güncelle
                    self.pencere.after(0, lambda urunler=sayfa_urunleri: self.tabloyu_guncelle(urunler))
                else:
                    self.log_yaz(f"Sayfa {sayfa}: Hiç ürün bulunamadı")

                # İki istek arasında bekle
                time.sleep(random.uniform(1.0, 2.0))

            self.urunler = tum_urunler
            self.log_yaz(f"Toplam {len(tum_urunler)} ürün toplandı")

            # İlerleme çubuğunu tamamla
            self.pencere.after(0, lambda: self.ilerleme_cubugu.configure(value=100))

            # Ürün analizi yap
            if self.urunler:
                self.analiz_sonuclari = self.urunleri_analiz_et()
                # Sonuçları göster
                self.pencere.after(0, self.analiz_sonuclarini_goster)
                # Butonları etkinleştir
                self.pencere.after(0, lambda: self.kaydet_button.configure(state=tk.NORMAL))
                self.pencere.after(0, lambda: self.grafik_button.configure(state=tk.NORMAL))
                self.pencere.after(0, lambda: self.filtrele_button.configure(state=tk.NORMAL))
                self.pencere.after(0, lambda: self.sifirla_button.configure(state=tk.NORMAL))
                # Bilgi mesajı göster
                self.pencere.after(0, lambda: messagebox.showinfo("Bilgi",
                                                                  f"Veri toplama işlemi tamamlandı! Toplam {len(self.urunler)} ürün."))
            else:
                self.log_yaz("Hiç ürün bulunamadı!")
                self.pencere.after(0, lambda: messagebox.showwarning("Uyarı", "Hiç ürün bulunamadı!"))
        except Exception as e:
            # Hata durumunda
            import traceback
            hata_detay = traceback.format_exc()
            self.log_yaz(f"HATA: {str(e)}\n{hata_detay}")
            self.pencere.after(0, lambda: messagebox.showerror("Hata", f"Veri toplama hatası: {str(e)}"))
        finally:
            self.veri_toplaniyor = False
            self.pencere.after(0, lambda: self.arayuz_durumu_degistir(True))

    def sayfa_icerigi_al(self, url):
        """Web sayfasının içeriğini indirir"""
        # Tarayıcı gibi davranan HTTP başlıkları
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) Chrome/96.0.4664.110',
            'Accept': 'text/html,application/xhtml+xml',
            'Accept-Language': 'tr-TR,tr;q=0.9,en-US;q=0.8,en;q=0.7',
        }
        try:
            # İstek yapmadan önce biraz bekle
            time.sleep(random.uniform(1.0, 2.0))
            # İstek yap
            response = requests.get(url, headers=headers, timeout=30)
            # Başarılı mı kontrol et
            if response.status_code == 200:
                self.log_yaz(f"Sayfa başarıyla indirildi. Boyut: {len(response.text)} karakter")
                return response.text
            else:
                self.log_yaz(f"HTTP Hatası: {response.status_code}")
                self.pencere.after(0, lambda: messagebox.showerror("Hata", f"HTTP Hatası: {response.status_code}"))
                return None
        except Exception as e:
            self.log_yaz(f"Bağlantı hatası: {str(e)}")
            self.pencere.after(0, lambda: messagebox.showerror("Hata", f"Bağlantı hatası: {str(e)}"))
            return None

    def sayfa_url_ekle(self, url, sayfa_no):
        """URL'ye sayfa parametresi ekler"""
        # Site tipine göre farklı sayfalama yapıları
        if self.site_tipi == "itopya":
            if "?" in url:
                if "page=" in url:
                    # page parametresi varsa güncelle
                    return re.sub(r'page=\d+', f'page={sayfa_no}', url)
                else:
                    # page parametresi yoksa ekle
                    return f"{url}&page={sayfa_no}"
            else:
                # Soru işareti bile yoksa ekle
                if url.endswith("/"):
                    return f"{url}?page={sayfa_no}"
                else:
                    return f"{url}/?page={sayfa_no}"
        elif self.site_tipi == "robotistan":
            # Robotistan sayfalama benzer şekilde
            if "?" in url:
                if "page=" in url:
                    return re.sub(r'page=\d+', f'page={sayfa_no}', url)
                else:
                    return f"{url}&page={sayfa_no}"
            else:
                if url.endswith("/"):
                    return f"{url}?page={sayfa_no}"
                else:
                    return f"{url}/?page={sayfa_no}"
        elif self.site_tipi == "direnc":
            # Direnc.net sayfalama
            if "?" in url:
                if "page=" in url:
                    return re.sub(r'page=\d+', f'page={sayfa_no}', url)
                else:
                    return f"{url}&page={sayfa_no}"
            else:
                return f"{url}?page={sayfa_no}"
        # Bilinmeyen siteler için URL'yi değiştirmeden döndür
        return url

    def urunleri_ayristir(self, html_icerigi):
        """HTML içeriğinden ürünleri ayıklar"""
        urunler = []
        try:
            # BeautifulSoup ile HTML ayrıştırması
            soup = BeautifulSoup(html_icerigi, 'html.parser')
            if self.site_tipi == "itopya":
                # İtopya ürün kartlarını bul
                urun_kartlari = soup.select('div.product-block')
                self.log_yaz(f"İtopya: {len(urun_kartlari)} ürün kartı bulundu")
                for kart in urun_kartlari:
                    # Ürün başlığı
                    baslik_element = kart.select_one('div.product-block-body a')
                    baslik = ""
                    if baslik_element and baslik_element.has_attr('title'):
                        baslik = baslik_element['title']
                    else:
                        baslik_element = kart.select_one('div.product-block-body h5') or kart.select_one(
                            'div.product-block-body a')
                        baslik = baslik_element.text.strip() if baslik_element else "Başlık bulunamadı"

                    # Ürün fiyatı
                    fiyat_element = kart.select_one('div.col-12.price-col')
                    fiyat_text = fiyat_element.text.strip() if fiyat_element else "0 TL"

                    # Sayısal fiyat değeri
                    fiyat_sayisal = 0.0
                    try:
                        # Fiyat metinden sayısal değeri çıkar
                        fiyat_eslesmesi = re.search(r'[\d.,]+', fiyat_text)
                        if fiyat_eslesmesi:
                            fiyat_temiz = fiyat_eslesmesi.group(0).replace('.', '').replace(',', '.')
                            fiyat_sayisal = float(fiyat_temiz)
                    except:
                        self.log_yaz(f"Fiyat dönüştürme hatası: {fiyat_text}")

                    # Satıcı/Marka
                    marka_element = kart.select_one('div.brand-logo img')
                    satici = marka_element['alt'] if marka_element and marka_element.has_attr('alt') else "İtopya"

                    # Stok durumu - varsayılan olarak stokta
                    stok = "Stokta"

                    # Ürün linki
                    link_element = kart.select_one('div.product-block-body a')
                    link = link_element['href'] if link_element and link_element.has_attr('href') else ""
                    if link and not link.startswith('http'):
                        link = "https://www.itopya.com" + link

                    # Kargo
                    kargo = "Standart Kargo"

                    # Ürün bilgilerini sözlüğe ekle
                    urun = {
                        'title': baslik,
                        'price': fiyat_text,
                        'price_numeric': fiyat_sayisal,
                        'seller': satici,
                        'stock': stok,
                        'shipping': kargo,
                        'link': link
                    }
                    self.log_yaz(f"Ürün ayrıştırıldı: {baslik} - {fiyat_text}")
                    urunler.append(urun)
            elif self.site_tipi == "robotistan":
                # Robotistan için farklı seçiciler deneyelim
                seciciler = [
                    'div.product-item-box',
                    'div.product-item',
                    'div.product-box'
                ]

                urun_kartlari = []
                for secici in seciciler:
                    kartlar = soup.select(secici)
                    if kartlar:
                        self.log_yaz(f"'{secici}' seçicisiyle {len(kartlar)} ürün bulundu")
                        urun_kartlari = kartlar
                        break

                for kart in urun_kartlari:
                    # Ürün başlığı
                    baslik_seciciler = ['a.product-name', 'h4.name', 'div.name', 'a.product-title']
                    baslik = "Başlık bulunamadı"
                    for secici in baslik_seciciler:
                        baslik_element = kart.select_one(secici)
                        if baslik_element:
                            baslik = baslik_element.text.strip()
                            break

                    # Ürün fiyatı
                    fiyat_seciciler = ['div.current-price', 'span.price', 'div.price', 'div.product-price']
                    fiyat_text = "0 TL"
                    for secici in fiyat_seciciler:
                        fiyat_element = kart.select_one(secici)
                        if fiyat_element:
                            fiyat_text = fiyat_element.text.strip()
                            break

                    # Sayısal fiyat
                    fiyat_sayisal = 0.0
                    try:
                        fiyat_temiz = re.sub(r'[^\d,.]', '', fiyat_text.replace('.', '').replace(',', '.'))
                        fiyat_sayisal = float(fiyat_temiz)
                    except:
                        pass

                    # Satıcı
                    satici = "Robotistan"

                    # Stok durumu
                    stok = "Stokta"

                    # Ürün linki
                    link = ""
                    link_seciciler = ['a.product-name', 'a.name', 'a.product-link', 'a']
                    for secici in link_seciciler:
                        link_element = kart.select_one(secici)
                        if link_element and 'href' in link_element.attrs:
                            link = link_element['href']
                            break
                    if link and not link.startswith('http'):
                        link = "https://www.robotistan.com" + link

                    # Kargo
                    kargo = "Standart Kargo"

                    # Ürün bilgilerini sözlüğe ekle
                    urun = {
                        'title': baslik,
                        'price': fiyat_text,
                        'price_numeric': fiyat_sayisal,
                        'seller': satici,
                        'stock': stok,
                        'shipping': kargo,
                        'link': link
                    }
                    self.log_yaz(f"Ürün ayrıştırıldı: {baslik} - {fiyat_text}")
                    urunler.append(urun)
            elif self.site_tipi == "direnc":
                # Direnc.net için ayrıştırma
                urun_kartlari = soup.select('div.product-layout') or soup.select('div.product-grid')
                for kart in urun_kartlari:
                    # Ürün başlığı
                    baslik_element = kart.select_one('h4') or kart.select_one('div.name') or kart.select_one(
                        'a.product-title')
                    baslik = baslik_element.text.strip() if baslik_element else "Başlık bulunamadı"

                    # Ürün fiyatı
                    fiyat_element = kart.select_one('div.price') or kart.select_one('span.price-new')
                    fiyat_text = fiyat_element.text.strip() if fiyat_element else "0 TL"

                    # Sayısal fiyat
                    fiyat_sayisal = 0.0
                    try:
                        fiyat_temiz = re.sub(r'[^\d,.]', '', fiyat_text.replace('.', '').replace(',', '.'))
                        fiyat_sayisal = float(fiyat_temiz)
                    except:
                        pass

                    # Satıcı
                    satici = "Direnc.net"

                    # Stok durumu
                    stok = "Stokta"

                    # Ürün linki
                    link_element = kart.select_one('a.product-title') or kart.select_one('h4 a')
                    link = link_element['href'] if link_element and 'href' in link_element.attrs else ""

                    # Kargo
                    kargo = "Standart Kargo"

                    # Ürün bilgilerini sözlüğe ekle
                    urun = {
                        'title': baslik,
                        'price': fiyat_text,
                        'price_numeric': fiyat_sayisal,
                        'seller': satici,
                        'stock': stok,
                        'shipping': kargo,
                        'link': link
                    }
                    urunler.append(urun)
        except Exception as e:
            self.log_yaz(f"Ürün ayrıştırma hatası: {str(e)}")
        return urunler

    def tabloyu_guncelle(self, urunler):
        """Treeview'a ürünleri ekler"""
        for urun in urunler:
            # Satır değerlerini oluştur (sütunlarla uyumlu sırada)
            degerler = (
                urun['title'],
                urun['price'],
                f"{urun['price_numeric']:.2f}",
                urun['seller'],
                urun['stock'],
                urun['shipping']
            )
            # Treeview'a ekle
            self.treeview.insert('', tk.END, values=degerler)

    def urunleri_analiz_et(self):
        """Ürünleri analiz eder"""
        if not self.urunler:
            return None

        # Geçerli fiyatları al
        gecerli_fiyatlar = [u['price_numeric'] for u in self.urunler if u['price_numeric'] > 0]
        if not gecerli_fiyatlar:
            return {
                'toplam_urun': len(self.urunler),
                'ortalama_fiyat': 0,
                'fiyat_araligi': (0, 0),
                'en_ucuz': [],
                'en_pahali': []
            }

        # Temel istatistikler
        ortalama_fiyat = sum(gecerli_fiyatlar) / len(gecerli_fiyatlar)
        min_fiyat = min(gecerli_fiyatlar)
        max_fiyat = max(gecerli_fiyatlar)

        # Fiyata göre sırala
        fiyata_gore_sirali = sorted(self.urunler, key=lambda x: x['price_numeric'])

        # Fiyatı 0'dan büyük olanları filtrele
        gecerli_urunler = [u for u in fiyata_gore_sirali if u['price_numeric'] > 0]

        # En ucuz 5 ürün
        en_ucuz = gecerli_urunler[:5] if len(gecerli_urunler) >= 5 else gecerli_urunler

        # En pahalı 5 ürün
        en_pahali = gecerli_urunler[-5:][::-1] if len(gecerli_urunler) >= 5 else gecerli_urunler[::-1]

        return {
            'toplam_urun': len(self.urunler),
            'ortalama_fiyat': ortalama_fiyat,
            'fiyat_araligi': (min_fiyat, max_fiyat),
            'en_ucuz': en_ucuz,
            'en_pahali': en_pahali
        }

    def analiz_sonuclarini_goster(self):
        """Analiz sonuçlarını analiz sekmesinde gösterir"""
        if not self.analiz_sonuclari:
            return

        analiz = self.analiz_sonuclari
        sonuc_metin = f"""
{'=' * 50}
ÜRÜN ANALİZ SONUÇLARI (Toplam: {analiz['toplam_urun']} ürün)
{'=' * 50}
EN UCUZ 5 ÜRÜN:
{'-' * 50}
"""
        # En ucuz ürünleri ekle
        for i, urun in enumerate(analiz['en_ucuz'], 1):
            sonuc_metin += f"{i}. {urun['title']}\n"
            sonuc_metin += f"   Fiyat: {urun['price']} ({urun['price_numeric']:.2f} TL)\n"
            sonuc_metin += f"   Satıcı: {urun['seller']}\n"
            sonuc_metin += f"   Stok Durumu: {urun['stock']}\n"
            sonuc_metin += f"   Kargo: {urun['shipping']}\n"
            if 'link' in urun and urun['link']:
                sonuc_metin += f"   Link: {urun['link']}\n"
            sonuc_metin += f"{'-' * 30}\n"

        sonuc_metin += f"""
EN PAHALI 5 ÜRÜN:
{'-' * 50}
"""
        # En pahalı ürünleri ekle
        for i, urun in enumerate(analiz['en_pahali'], 1):
            sonuc_metin += f"{i}. {urun['title']}\n"
            sonuc_metin += f"   Fiyat: {urun['price']} ({urun['price_numeric']:.2f} TL)\n"
            sonuc_metin += f"   Satıcı: {urun['seller']}\n"
            sonuc_metin += f"   Stok Durumu: {urun['stock']}\n"
            sonuc_metin += f"   Kargo: {urun['shipping']}\n"
            if 'link' in urun and urun['link']:
                sonuc_metin += f"   Link: {urun['link']}\n"
            sonuc_metin += f"{'-' * 30}\n"

        sonuc_metin += f"""
FİYAT ANALİZİ:
{'-' * 50}
Ortalama Fiyat: {analiz['ortalama_fiyat']:.2f} TL
Fiyat Aralığı: {analiz['fiyat_araligi'][0]:.2f} TL - {analiz['fiyat_araligi'][1]:.2f} TL
{'=' * 50}
"""
        # Metni analiz alanına ekle
        self.analiz_text.delete(1.0, tk.END)
        self.analiz_text.insert(tk.END, sonuc_metin)

        # Analiz sekmesine geç
        self.notebook.select(self.analiz_frame)

    def grafikleri_goster(self):
        """Grafikleri oluşturur ve gösterir"""
        if not self.urunler:
            messagebox.showwarning("Uyarı", "Grafik oluşturmak için veri toplamış olmanız gerekir!")
            return

        # Grafik alanını temizle
        for widget in self.grafik_frame.winfo_children():
            widget.destroy()

        # Grafik başlığı
        baslik = ttk.Label(self.grafik_frame, text="Ürün Fiyat Grafikleri", font=("Arial", 12, "bold"))
        baslik.pack(pady=(0, 10))

        # Tab control for graphs
        grafik_notebook = ttk.Notebook(self.grafik_frame)
        grafik_notebook.pack(fill=tk.BOTH, expand=True)

        # Fiyat dağılımı grafiği
        fiyat_frame = ttk.Frame(grafik_notebook)
        grafik_notebook.add(fiyat_frame, text="Fiyat Dağılımı")

        fig_fiyat = plt.Figure(figsize=(8, 5), dpi=100)
        ax_fiyat = fig_fiyat.add_subplot(111)

        # Verileri DataFrame'e dönüştür
        df = pd.DataFrame(self.urunler)
        df_numeric = df[df['price_numeric'] > 0]

        if not df_numeric.empty:
            # Histogram grafiği çiz
            sns.histplot(df_numeric['price_numeric'], kde=True, ax=ax_fiyat)
            ax_fiyat.set_title('Ürün Fiyatları Dağılımı')
            ax_fiyat.set_xlabel('Fiyat (TL)')
            ax_fiyat.set_ylabel('Ürün Sayısı')

            # Canvas'a ekle
            canvas_fiyat = FigureCanvasTkAgg(fig_fiyat, fiyat_frame)
            canvas_fiyat.draw()
            canvas_fiyat.get_tk_widget().pack(fill=tk.BOTH, expand=True)

        # Stok durumu grafiği
        stok_frame = ttk.Frame(grafik_notebook)
        grafik_notebook.add(stok_frame, text="Stok Durumu")

        fig_stok = plt.Figure(figsize=(8, 5), dpi=100)
        ax_stok = fig_stok.add_subplot(111)

        if not df.empty:
            # Stok durumu sayılarını hesapla
            stok_sayilari = df['stock'].value_counts()

            # Pasta grafiği
            stok_sayilari.plot(kind='pie', autopct='%1.1f%%', ax=ax_stok)
            ax_stok.set_title('Ürünlerin Stok Durumu')
            ax_stok.set_ylabel('')

            # Canvas'a ekle
            canvas_stok = FigureCanvasTkAgg(fig_stok, stok_frame)
            canvas_stok.draw()
            canvas_stok.get_tk_widget().pack(fill=tk.BOTH, expand=True)

        # Grafik sekmesine geç
        self.notebook.select(self.grafik_frame)

    def csv_kaydet(self):
        """Verileri CSV dosyasına kaydeder"""
        if not self.urunler:
            messagebox.showwarning("Uyarı", "Kaydedilecek veri yok!")
            return

        # Dosya adı önerisi
        zaman = datetime.now().strftime("%Y%m%d_%H%M%S")
        site_adi = self.site_tipi if self.site_tipi else "bilinmeyen"
        dosya_adi = f"{site_adi}_urunler_{zaman}.csv"

        # Dosya kaydetme diyaloğu
        dosya_yolu = filedialog.asksaveasfilename(
            defaultextension=".csv",
            filetypes=[("CSV dosyaları", "*.csv"), ("Tüm dosyalar", "*.*")],
            initialfile=dosya_adi
        )

        if not dosya_yolu:
            return

        try:
            # DataFrame oluştur
            df = pd.DataFrame(self.urunler)

            # Sütun sırasını ayarla
            istenen_sutunlar = ['title', 'price', 'price_numeric', 'seller', 'stock', 'shipping', 'link']
            mevcut_sutunlar = [s for s in istenen_sutunlar if s in df.columns]

            # Sütun adlarını Türkçeleştir
            sutun_adlari = {
                'title': 'Ürün Adı',
                'price': 'Fiyat',
                'price_numeric': 'Sayısal Fiyat',
                'seller': 'Satıcı',
                'stock': 'Stok Durumu',
                'shipping': 'Kargo',
                'link': 'Ürün Linki'
            }

            # CSV'ye kaydet
            df[mevcut_sutunlar].rename(columns=sutun_adlari).to_csv(
                dosya_yolu,
                index=False,
                encoding='utf-8-sig'  # Türkçe karakterler için
            )

            messagebox.showinfo("Bilgi", f"Veriler başarıyla {dosya_yolu} dosyasına kaydedildi.")

            # CSV dosyasını aç
            try:
                if os.path.exists(dosya_yolu):
                    os.startfile(dosya_yolu)  # Windows'ta varsayılan programla açar
            except:
                pass  # Dosya açılamazsa sessizce devam et
        except Exception as e:
            messagebox.showerror("Hata", f"Dosya kaydedilirken bir hata oluştu: {str(e)}")

    def arayuz_durumu_degistir(self, etkin):
        """Arayüz elemanlarının durumunu değiştirir"""
        durum = tk.NORMAL if etkin else tk.DISABLED
        self.url_entry.configure(state=durum)
        self.sayfa_spinbox.configure(state=durum)
        self.topla_button.configure(state=durum)

        # Filtreleme butonlarını da duruma göre ayarla
        if not etkin or not self.urunler:
            self.filtrele_button.configure(state=tk.DISABLED)
            self.sifirla_button.configure(state=tk.DISABLED)
        elif etkin and self.urunler:
            self.filtrele_button.configure(state=tk.NORMAL)
            self.sifirla_button.configure(state=tk.NORMAL)


# Ana program
if __name__ == "__main__":
    pencere = tk.Tk()
    app = FiyatKarsilastirma(pencere)
    pencere.mainloop()