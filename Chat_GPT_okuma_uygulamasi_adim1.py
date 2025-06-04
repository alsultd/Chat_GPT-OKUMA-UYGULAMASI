#Chat_GPT Codex İLE PROJE ÇALIŞMASI
import streamlit as st
import random
import uuid
import os
import difflib
import time
import platform
from docx import Document
from deep_translator import GoogleTranslator
from gtts import gTTS
import speech_recognition as sr
import nltk

nltk.download('punkt', download_dir='/tmp/nltk_data')
nltk.data.path.append('/tmp/nltk_data')
from nltk.tokenize import sent_tokenize

# === Ayarlar ===
DOC_PATH = "OCR_Ana_Cikti_Guncel.docx"

# === Fonksiyonlar ===
def cevir(metin):
    try:
        return GoogleTranslator(source='en', target='tr').translate(metin)
    except Exception as e:
        return f"(Çeviri hatası: {e})"

def seslendir_metin(metin):
    try:
        tts = gTTS(text=metin, lang='en')
        dosya_adi = f"{uuid.uuid4()}.mp3"
        tts.save(dosya_adi)
        return dosya_adi
    except Exception as e:
        st.error(f"Ses oluşturulamadı: {e}")
        return None

def get_topic_text(doc_path, topic_no):
    doc = Document(doc_path)
    paragraphs = [p.text.strip() for p in doc.paragraphs if p.text.strip()]
    topics = {}
    current_no = None
    current_text = ""

    for p in paragraphs:
        if p.startswith("Konu:"):
            if current_no is not None:
                topics[current_no] = current_text.strip()
            try:
                current_no = int(p.replace("Konu:", "").strip())
            except ValueError:
                continue
            current_text = ""
        else:
            current_text += p + "\n"

    if current_no is not None:
        topics[current_no] = current_text.strip()

    return topics.get(topic_no, "Bu numarada bir konu bulunamadı.")

def mikrofondan_al(sure=45):
    r = sr.Recognizer()
    with sr.Microphone() as source:
        st.info("🎙️ Hazırlanın, 3 saniye içinde bip sesi gelecek...")
        time.sleep(3)
#------------------------------------------
        try:
            if platform.system() == "Windows":
                import winsound
                winsound.Beep(1000, 500)
            else:
                st.info("🔔 (Mobil veya desteklenmeyen platform)")
        except Exception as e:
            st.info(f"🔕 Bip sesi çalınamadı ({e})")

#----------------------------------------------------------------
        st.info(f"🎙️ Konuşun... (süre: {sure} saniye)")
        r.pause_threshold = 1.5
        r.non_speaking_duration = 1.0
        audio = r.listen(source, phrase_time_limit=sure)
    try:
        text = r.recognize_google(audio)
        return text
    except:
        return "(Ses algılanamadı)"

def karsilastir(orijinal, kullanici):
    orij_kelimeler = orijinal.lower().split()
    kul_kelimeler = kullanici.lower().split()
    farklar = list(difflib.ndiff(orij_kelimeler, kul_kelimeler))
    eksik = [x[2:] for x in farklar if x.startswith('- ')]
    fazla = [x[2:] for x in farklar if x.startswith('+ ')]
    return eksik, fazla

def temizle_mp3_dosyalari():
    for dosya in os.listdir():
        if dosya.endswith(".mp3"):
            try:
                os.remove(dosya)
            except:
                pass

# === Arayüz Başlığı ===
st.title("📘 İngilizce Okuma Uygulaması")

suggested = random.randint(1, 160)
st.markdown(f"🎲 Rastgele konu önerisi: **Konu {suggested}**")
topic_no = st.number_input("Konu numarası seçin (1–160):", min_value=1, max_value=160, value=suggested)

if st.button("📄 Metni Getir"):
    metin = get_topic_text(DOC_PATH, topic_no)
    st.session_state["tum_metin"] = metin
    st.session_state["paragraphs"] = [p.strip() for p in metin.split("\n") if p.strip()]
    st.session_state["current_index"] = 0
    st.session_state["secili_kelimeler"] = {}

if "tum_metin" in st.session_state:
    st.markdown("### 📜 Tüm Okuma Metni")
    st.text(st.session_state["tum_metin"])

if "paragraphs" in st.session_state:
    paragraphs = st.session_state["paragraphs"]
    if "current_index" not in st.session_state:
        st.session_state["current_index"] = 0
    index = st.session_state["current_index"]
    total = len(paragraphs)

    st.markdown(f"### 📌 Paragraf {index + 1} / {total}")
    st.markdown(f"**{paragraphs[index]}**")

    kelimeler = paragraphs[index].split()
    secim_key = f"secili_kelimeler_{index}"
    st.session_state.setdefault("secili_kelimeler", {})
    st.session_state["secili_kelimeler"].setdefault(index, [])

    cols = st.columns(min(len(kelimeler), 6))
    for i, kelime in enumerate(kelimeler):
        temiz_kelime = kelime.strip(".,!?;:()\"'").lower()
        col = cols[i % len(cols)]
        with col:
            if st.button(kelime, key=f"{kelime}_{index}_{i}"):
                if temiz_kelime not in st.session_state["secili_kelimeler"][index]:
                    st.session_state["secili_kelimeler"][index].append(temiz_kelime)
                st.rerun()

    if st.session_state["secili_kelimeler"].get(index):
        st.markdown("### 🔍 Seçilen Kelimeler ve Anlamları")
        for kelime in st.session_state["secili_kelimeler"][index]:
            anlam = cevir(kelime)
            st.markdown(f"- `{kelime}` → **{anlam}**")
            if st.button(f"🔊 {kelime} kelimesini seslendir", key=f"oku_{kelime}_{index}"):
                mp3_dosya = seslendir_metin(kelime)
                if mp3_dosya:
                    with open(mp3_dosya, "rb") as f:
                        st.audio(f.read(), format="audio/mp3")

    col1, col2 = st.columns(2)
    with col1:
        if st.button("⏮ Önceki Paragraf") and st.session_state["current_index"] > 0:
            st.session_state["current_index"] -= 1
            st.rerun()
    with col2:
        if st.button("Sonraki Paragraf ⏭") and st.session_state["current_index"] < total - 1:
            st.session_state["current_index"] += 1
            st.rerun()

    # === Cümle bazında çalışma ===
    st.markdown("## 🧩 Cümle Bazlı İşlem")
    cumleler = sent_tokenize(paragraphs[index])

    for i, cumle in enumerate(cumleler):
        st.markdown(f"---\n**Cümle {i+1}:** {cumle}")

        col1, col2, col3 = st.columns(3)
        with col1:
            if st.button(f"🔊 Oku {i}", key=f"oku_cumle_{i}"):
                dosya = seslendir_metin(cumle)
                if dosya:
                    with open(dosya, "rb") as f:
                        st.audio(f.read(), format="audio/mp3")

        with col2:
            if st.button(f"🌍 Çevir {i}", key=f"cevir_cumle_{i}"):
                ceviri = cevir(cumle)
                st.success(f"Tercüme: {ceviri}")

        with col3:
            if st.button(f"🎙️ Kendin Oku {i}", key=f"mik_cumle_{i}"):
                sonuc = mikrofondan_al(sure=45)
                st.markdown(f"🗣️ Algılanan: `{sonuc}`")
                eksik, fazla = karsilastir(cumle, sonuc)
                if eksik or fazla:
                    st.warning("🧾 Farklar:")
                    if eksik:
                        st.write(f"- Eksik: {', '.join(eksik)}")
                    if fazla:
                        st.write(f"- Fazla: {', '.join(fazla)}")
                else:
                    st.success("✅ Cümle doğru okundu!")

# === Çıkışta ses dosyalarını temizle ===
if st.button("🚪 Uygulamadan Çık"):
    temizle_mp3_dosyalari()
    st.success("Geçici ses dosyaları silindi. Uygulamadan güvenle çıkabilirsiniz.")















#------------------------------------------------------------------
