from flask import Flask, request, jsonify, send_file, render_template_string
import yt_dlp
import os
import tempfile
import threading
import uuid
import re

app = Flask(__name__)
jobs = {}

def download_job(job_id, url, mode):
    jobs[job_id] = {"status": "downloading", "progress": 0, "filename": None, "error": None}
    tmpdir = tempfile.mkdtemp()

    def progress_hook(d):
        if d.get("status") == "downloading":
            raw = re.sub(r'\x1b\[[0-9;]*m', '', d.get("_percent_str", "0%")).replace("%","").strip()
            try:
                jobs[job_id]["progress"] = int(float(raw))
            except:
                pass
        elif d.get("status") == "finished":
            jobs[job_id]["progress"] = 95

    if mode == "audio":
        ydl_opts = {
            "format": "bestaudio/best",
            "postprocessors": [{"key": "FFmpegExtractAudio", "preferredcodec": "mp3", "preferredquality": "0"}],
            "outtmpl": os.path.join(tmpdir, "%(title)s.%(ext)s"),
            "progress_hooks": [progress_hook],
            "quiet": True,
        }
    else:
        ydl_opts = {
            "format": "best[ext=mp4]/best",
            "outtmpl": os.path.join(tmpdir, "%(title)s.%(ext)s"),
            "progress_hooks": [progress_hook],
            "quiet": True,
        }

    try:
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            ydl.download([url])
        files = os.listdir(tmpdir)
        if files:
            jobs[job_id]["status"] = "done"
            jobs[job_id]["progress"] = 100
            jobs[job_id]["filename"] = os.path.join(tmpdir, files[0])
            jobs[job_id]["display_name"] = files[0]
        else:
            jobs[job_id]["status"] = "error"
            jobs[job_id]["error"] = "Dosya oluşturulamadı."
    except Exception as e:
        jobs[job_id]["status"] = "error"
        jobs[job_id]["error"] = str(e)


TRANSLATIONS = {
    "tr": {
        "lang_name": "Türkçe", "flag": "🇹🇷",
        "video_link": "Video Linki",
        "placeholder": "https://youtube.com/watch?v=...",
        "video_btn": "🎬 Video (MP4)",
        "audio_btn": "🎵 Ses (MP3)",
        "download_btn": "⬇ İNDİR",
        "preparing": "Hazırlanıyor...",
        "downloading": "İndiriliyor...",
        "done_title": "✅ Hazır!",
        "download_file": "⬇ Dosyayı İndir",
        "supported": "Desteklenen Siteler",
        "about_title": "604 Ajans Hakkında",
        "about_slogan": "Markaları sadece görünür değil — algılanır, hatırlanır ve tercih edilir yapar.",
        "what_title": "🎬 Ne Yapıyoruz?",
        "what_items": ["Video Prodüksiyon", "Profesyonel Fotoğraf", "Video Editörlük", "Grafik Tasarım", "Reklam Kampanyaları", "Sosyal Medya Yönetimi", "Marka Konumlandırma"],
        "diff_title": "🧠 Farkımız",
        "diff_items": ["Klişe cümleler değil, güçlü konseptler", "Tasarım odaklı ama stratejik bakış", "Görselliği trend için değil marka algısı için", "Minimal ama etkili iletişim dili"],
        "who_title": "🎯 Kime Hitap Ediyoruz?",
        "who_items": ["Büyümek isteyen yerel markalara", "Profesyonel görünmek isteyen işletmelere", "Fark edilmek isteyenlere"],
        "follow": "Bizi Takip Edin",
        "made_by": "Made with ❤️ by",
    },
    "en": {
        "lang_name": "English", "flag": "🇬🇧",
        "video_link": "Video Link",
        "placeholder": "https://youtube.com/watch?v=...",
        "video_btn": "🎬 Video (MP4)",
        "audio_btn": "🎵 Audio (MP3)",
        "download_btn": "⬇ DOWNLOAD",
        "preparing": "Preparing...",
        "downloading": "Downloading...",
        "done_title": "✅ Ready!",
        "download_file": "⬇ Download File",
        "supported": "Supported Sites",
        "about_title": "About 604 Agency",
        "about_slogan": "We don't just make brands visible — we make them perceived, remembered and preferred.",
        "what_title": "🎬 What We Do",
        "what_items": ["Video Production", "Professional Photography", "Video Editing", "Graphic Design", "Ad Campaigns", "Social Media Management", "Brand Positioning"],
        "diff_title": "🧠 Our Difference",
        "diff_items": ["Strong concepts, not clichés", "Design-focused but strategic thinking", "Visuals for brand perception, not trends", "Minimal but effective communication"],
        "who_title": "🎯 Who We Serve",
        "who_items": ["Local brands that want to grow", "Businesses that want to look professional", "Those who want to be noticed, not just present"],
        "follow": "Follow Us",
        "made_by": "Made with ❤️ by",
    },
    "es": {
        "lang_name": "Español", "flag": "🇪🇸",
        "video_link": "Enlace de Video",
        "placeholder": "https://youtube.com/watch?v=...",
        "video_btn": "🎬 Video (MP4)",
        "audio_btn": "🎵 Audio (MP3)",
        "download_btn": "⬇ DESCARGAR",
        "preparing": "Preparando...",
        "downloading": "Descargando...",
        "done_title": "✅ ¡Listo!",
        "download_file": "⬇ Descargar Archivo",
        "supported": "Sitios Compatibles",
        "about_title": "Sobre 604 Agency",
        "about_slogan": "No solo hacemos marcas visibles — las hacemos percibidas, recordadas y preferidas.",
        "what_title": "🎬 ¿Qué Hacemos?",
        "what_items": ["Producción de Video", "Fotografía Profesional", "Edición de Video", "Diseño Gráfico", "Campañas Publicitarias", "Gestión de Redes Sociales", "Posicionamiento de Marca"],
        "diff_title": "🧠 Nuestra Diferencia",
        "diff_items": ["Conceptos fuertes, no clichés", "Enfoque de diseño con visión estratégica", "Visuales para la percepción de marca", "Comunicación mínima pero efectiva"],
        "who_title": "🎯 ¿A Quién Nos Dirigimos?",
        "who_items": ["Marcas locales que quieren crecer", "Empresas que quieren verse profesionales", "Quienes quieren ser notados"],
        "follow": "Síguenos",
        "made_by": "Hecho con ❤️ por",
    },
    "fr": {
        "lang_name": "Français", "flag": "🇫🇷",
        "video_link": "Lien Vidéo",
        "placeholder": "https://youtube.com/watch?v=...",
        "video_btn": "🎬 Vidéo (MP4)",
        "audio_btn": "🎵 Audio (MP3)",
        "download_btn": "⬇ TÉLÉCHARGER",
        "preparing": "Préparation...",
        "downloading": "Téléchargement...",
        "done_title": "✅ Prêt!",
        "download_file": "⬇ Télécharger",
        "supported": "Sites Supportés",
        "about_title": "À propos de 604 Agency",
        "about_slogan": "Nous ne rendons pas seulement les marques visibles — nous les rendons perçues, mémorisées et préférées.",
        "what_title": "🎬 Ce que nous faisons",
        "what_items": ["Production Vidéo", "Photographie Pro", "Montage Vidéo", "Design Graphique", "Campagnes Publicitaires", "Gestion des Réseaux Sociaux", "Positionnement de Marque"],
        "diff_title": "🧠 Notre Différence",
        "diff_items": ["Des concepts forts, pas des clichés", "Vision design et stratégique", "Visuels pour la perception de marque", "Communication minimale mais efficace"],
        "who_title": "🎯 Pour Qui?",
        "who_items": ["Marques locales qui veulent grandir", "Entreprises qui veulent paraître professionnelles", "Ceux qui veulent être remarqués"],
        "follow": "Suivez-nous",
        "made_by": "Fait avec ❤️ par",
    },
    "de": {
        "lang_name": "Deutsch", "flag": "🇩🇪",
        "video_link": "Video-Link",
        "placeholder": "https://youtube.com/watch?v=...",
        "video_btn": "🎬 Video (MP4)",
        "audio_btn": "🎵 Audio (MP3)",
        "download_btn": "⬇ HERUNTERLADEN",
        "preparing": "Vorbereitung...",
        "downloading": "Herunterladen...",
        "done_title": "✅ Fertig!",
        "download_file": "⬇ Datei herunterladen",
        "supported": "Unterstützte Seiten",
        "about_title": "Über 604 Agency",
        "about_slogan": "Wir machen Marken nicht nur sichtbar — wir machen sie wahrnehmbar, einprägsam und bevorzugt.",
        "what_title": "🎬 Was wir tun",
        "what_items": ["Videoproduktion", "Profifotografie", "Videobearbeitung", "Grafikdesign", "Werbekampagnen", "Social-Media-Management", "Markenpositionierung"],
        "diff_title": "🧠 Unser Unterschied",
        "diff_items": ["Starke Konzepte statt Klischees", "Designorientiert und strategisch", "Visuals für Markenwahrnehmung", "Minimale aber effektive Kommunikation"],
        "who_title": "🎯 Für wen?",
        "who_items": ["Lokale Marken die wachsen wollen", "Unternehmen die professionell wirken wollen", "Die die auffallen wollen"],
        "follow": "Folge uns",
        "made_by": "Mit ❤️ gemacht von",
    },
    "ar": {
        "lang_name": "العربية", "flag": "🇸🇦",
        "video_link": "رابط الفيديو",
        "placeholder": "https://youtube.com/watch?v=...",
        "video_btn": "🎬 فيديو (MP4)",
        "audio_btn": "🎵 صوت (MP3)",
        "download_btn": "⬇ تحميل",
        "preparing": "جاري التحضير...",
        "downloading": "جاري التحميل...",
        "done_title": "✅ جاهز!",
        "download_file": "⬇ تحميل الملف",
        "supported": "المواقع المدعومة",
        "about_title": "عن 604 Agency",
        "about_slogan": "نحن لا نجعل العلامات التجارية مرئية فحسب — بل نجعلها محسوسة وتُحفظ في الذاكرة ومفضلة.",
        "what_title": "🎬 ماذا نفعل؟",
        "what_items": ["إنتاج الفيديو", "التصوير الاحترافي", "تحرير الفيديو", "التصميم الجرافيكي", "حملات إعلانية", "إدارة وسائل التواصل", "تموضع العلامة التجارية"],
        "diff_title": "🧠 ما يميزنا",
        "diff_items": ["مفاهيم قوية لا كليشيهات", "رؤية تصميمية واستراتيجية", "صور لإدراك العلامة التجارية", "تواصل بسيط لكن فعّال"],
        "who_title": "🎯 لمن نحن؟",
        "who_items": ["العلامات المحلية التي تريد النمو", "الشركات التي تريد مظهراً احترافياً", "من يريد أن يُلاحَظ لا أن يكون موجوداً فقط"],
        "follow": "تابعنا",
        "made_by": "صُنع بـ ❤️ من قِبل",
    },
    "ja": {
        "lang_name": "日本語", "flag": "🇯🇵",
        "video_link": "動画リンク",
        "placeholder": "https://youtube.com/watch?v=...",
        "video_btn": "🎬 動画 (MP4)",
        "audio_btn": "🎵 音声 (MP3)",
        "download_btn": "⬇ ダウンロード",
        "preparing": "準備中...",
        "downloading": "ダウンロード中...",
        "done_title": "✅ 完了！",
        "download_file": "⬇ ファイルをダウンロード",
        "supported": "対応サイト",
        "about_title": "604 Agency について",
        "about_slogan": "ブランドを見えるだけでなく、認識され、記憶され、選ばれる存在にします。",
        "what_title": "🎬 サービス内容",
        "what_items": ["映像制作", "プロ写真撮影", "動画編集", "グラフィックデザイン", "広告キャンペーン", "SNS管理", "ブランドポジショニング"],
        "diff_title": "🧠 私たちの違い",
        "diff_items": ["陳腐な言葉ではなく強いコンセプト", "デザイン重視かつ戦略的視点", "トレンドではなくブランド認知のためのビジュアル", "シンプルだが効果的なコミュニケーション"],
        "who_title": "🎯 対象",
        "who_items": ["成長したいローカルブランド", "プロフェッショナルに見せたい企業", "存在するだけでなく注目されたい方"],
        "follow": "フォローする",
        "made_by": "❤️ で作られました by",
    },
    "pt": {
        "lang_name": "Português", "flag": "🇧🇷",
        "video_link": "Link do Vídeo",
        "placeholder": "https://youtube.com/watch?v=...",
        "video_btn": "🎬 Vídeo (MP4)",
        "audio_btn": "🎵 Áudio (MP3)",
        "download_btn": "⬇ BAIXAR",
        "preparing": "Preparando...",
        "downloading": "Baixando...",
        "done_title": "✅ Pronto!",
        "download_file": "⬇ Baixar Arquivo",
        "supported": "Sites Suportados",
        "about_title": "Sobre a 604 Agency",
        "about_slogan": "Não apenas tornamos marcas visíveis — as tornamos percebidas, lembradas e preferidas.",
        "what_title": "🎬 O que fazemos",
        "what_items": ["Produção de Vídeo", "Fotografia Profissional", "Edição de Vídeo", "Design Gráfico", "Campanhas Publicitárias", "Gestão de Redes Sociais", "Posicionamento de Marca"],
        "diff_title": "🧠 Nossa Diferença",
        "diff_items": ["Conceitos fortes, não clichês", "Foco em design e visão estratégica", "Visuais para percepção de marca", "Comunicação mínima mas eficaz"],
        "who_title": "🎯 Para quem?",
        "who_items": ["Marcas locais que querem crescer", "Empresas que querem parecer profissionais", "Quem quer ser notado"],
        "follow": "Siga-nos",
        "made_by": "Feito com ❤️ por",
    },
    "ru": {
        "lang_name": "Русский", "flag": "🇷🇺",
        "video_link": "Ссылка на видео",
        "placeholder": "https://youtube.com/watch?v=...",
        "video_btn": "🎬 Видео (MP4)",
        "audio_btn": "🎵 Аудио (MP3)",
        "download_btn": "⬇ СКАЧАТЬ",
        "preparing": "Подготовка...",
        "downloading": "Скачивание...",
        "done_title": "✅ Готово!",
        "download_file": "⬇ Скачать файл",
        "supported": "Поддерживаемые сайты",
        "about_title": "О 604 Agency",
        "about_slogan": "Мы не просто делаем бренды видимыми — мы делаем их воспринимаемыми, запоминающимися и предпочтительными.",
        "what_title": "🎬 Что мы делаем",
        "what_items": ["Видеопроизводство", "Профессиональная фотография", "Видеомонтаж", "Графический дизайн", "Рекламные кампании", "Управление соцсетями", "Позиционирование бренда"],
        "diff_title": "🧠 Наше отличие",
        "diff_items": ["Сильные концепции, а не клише", "Дизайн-ориентированный и стратегический подход", "Визуалы для восприятия бренда", "Минимальная, но эффективная коммуникация"],
        "who_title": "🎯 Для кого?",
        "who_items": ["Местные бренды, желающие расти", "Компании, желающие выглядеть профессионально", "Те, кто хочет быть замеченным"],
        "follow": "Подписывайтесь",
        "made_by": "Сделано с ❤️ от",
    },
    "zh": {
        "lang_name": "中文", "flag": "🇨🇳",
        "video_link": "视频链接",
        "placeholder": "https://youtube.com/watch?v=...",
        "video_btn": "🎬 视频 (MP4)",
        "audio_btn": "🎵 音频 (MP3)",
        "download_btn": "⬇ 下载",
        "preparing": "准备中...",
        "downloading": "下载中...",
        "done_title": "✅ 完成！",
        "download_file": "⬇ 下载文件",
        "supported": "支持的网站",
        "about_title": "关于 604 Agency",
        "about_slogan": "我们不只让品牌可见——我们让品牌被感知、被记住、被优先选择。",
        "what_title": "🎬 我们做什么",
        "what_items": ["视频制作", "专业摄影", "视频剪辑", "平面设计", "广告投放", "社交媒体管理", "品牌定位"],
        "diff_title": "🧠 我们的不同",
        "diff_items": ["强大的概念，而非陈词滥调", "设计驱动且具战略眼光", "视觉服务于品牌认知", "简洁但高效的沟通方式"],
        "who_title": "🎯 服务对象",
        "who_items": ["想要成长的本地品牌", "想要专业形象的企业", "想被注意而不只是存在的人"],
        "follow": "关注我们",
        "made_by": "由 ❤️ 制作",
    },
}

HTML = '''<!DOCTYPE html>
<html lang="tr" id="htmlRoot">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<meta name="theme-color" content="#0b0b12">
<meta name="apple-mobile-web-app-capable" content="yes">
<meta name="apple-mobile-web-app-title" content="Vido Down">
<title>Vido Down — 604 Agency</title>
<style>
@import url('https://fonts.googleapis.com/css2?family=JetBrains+Mono:wght@400;700&family=Syne:wght@400;700;800&display=swap');
:root {
  --bg:#0b0b12; --surface:#13131e; --card:#1a1a28;
  --border:#2a2a3e; --accent:#7c3aed; --green:#06d6a0;
  --text:#e8e8f5; --muted:#55556a;
}
*{margin:0;padding:0;box-sizing:border-box;-webkit-tap-highlight-color:transparent}
body{background:var(--bg);color:var(--text);font-family:'Syne',sans-serif;min-height:100vh;display:flex;flex-direction:column;align-items:center}
body::before{content:'';position:fixed;inset:0;pointer-events:none;z-index:0;
  background:radial-gradient(ellipse 70% 40% at 20% 0%,rgba(124,58,237,.18) 0%,transparent 60%),
  radial-gradient(ellipse 50% 50% at 80% 90%,rgba(6,214,160,.1) 0%,transparent 60%)}
.wrap{width:100%;max-width:600px;padding:40px 20px 60px;position:relative;z-index:1}

/* Lang switcher */
.lang-bar{display:flex;flex-wrap:wrap;gap:6px;justify-content:center;margin-bottom:32px}
.lang-btn{background:rgba(255,255,255,.05);border:1px solid var(--border);border-radius:999px;
  padding:5px 12px;font-size:12px;color:var(--muted);cursor:pointer;transition:all .2s;font-family:'Syne',sans-serif}
.lang-btn:hover,.lang-btn.active{background:var(--accent);border-color:var(--accent);color:#fff}

/* Logo */
.logo{display:flex;flex-direction:column;align-items:center;margin-bottom:40px}
.logo-icon{width:72px;height:72px;background:var(--accent);border-radius:20px;display:flex;
  align-items:center;justify-content:center;font-size:32px;margin-bottom:16px;
  box-shadow:0 0 40px rgba(124,58,237,.4);animation:pulse 3s ease-in-out infinite}
@keyframes pulse{0%,100%{box-shadow:0 0 40px rgba(124,58,237,.4)}50%{box-shadow:0 0 60px rgba(124,58,237,.7)}}
.logo h1{font-size:2rem;font-weight:800;background:linear-gradient(135deg,#fff 0%,#a78bfa 60%,#06d6a0 100%);
  -webkit-background-clip:text;-webkit-text-fill-color:transparent;background-clip:text}
.logo .agency{font-family:'JetBrains Mono',monospace;font-size:11px;letter-spacing:3px;color:var(--muted);text-transform:uppercase;margin-top:4px}

/* Card */
.card{background:var(--card);border:1px solid var(--border);border-radius:20px;padding:24px;margin-bottom:14px}
.label{font-size:11px;font-weight:700;color:var(--muted);letter-spacing:1px;text-transform:uppercase;margin-bottom:10px}
input[type=text]{width:100%;background:var(--bg);border:1.5px solid var(--border);border-radius:12px;
  padding:14px 16px;color:var(--text);font-family:'JetBrains Mono',monospace;font-size:13px;outline:none;transition:border-color .2s}
input[type=text]:focus{border-color:var(--accent)}
input::placeholder{color:var(--muted)}
.toggle{display:flex;gap:10px;margin-top:14px}
.toggle-btn{flex:1;padding:11px;border:1.5px solid var(--border);border-radius:12px;background:transparent;
  color:var(--muted);font-family:'Syne',sans-serif;font-size:13px;font-weight:700;cursor:pointer;transition:all .2s;text-align:center}
.toggle-btn.active{background:var(--accent);border-color:var(--accent);color:#fff}
.btn-download{width:100%;padding:16px;background:var(--accent);border:none;border-radius:14px;
  color:#fff;font-family:'Syne',sans-serif;font-size:16px;font-weight:800;cursor:pointer;
  transition:all .2s;margin-top:4px;box-shadow:0 4px 24px rgba(124,58,237,.35)}
.btn-download:hover{background:#6d28d9;transform:translateY(-1px)}
.btn-download:disabled{background:var(--border);color:var(--muted);box-shadow:none;cursor:not-allowed;transform:none}
.progress-wrap{margin-top:14px;display:none}
.progress-bar{height:6px;background:var(--border);border-radius:3px;overflow:hidden;margin-bottom:8px}
.progress-fill{height:100%;width:0%;border-radius:3px;transition:width .3s ease;background:linear-gradient(90deg,var(--accent),var(--green))}
.progress-text{font-family:'JetBrains Mono',monospace;font-size:12px;color:var(--muted)}
.result{background:rgba(6,214,160,.08);border:1px solid rgba(6,214,160,.25);border-radius:14px;
  padding:20px;margin-top:14px;display:none;text-align:center}
.result .r-title{color:var(--green);font-weight:800;font-size:1rem;margin-bottom:8px}
.result .r-sub{color:#6a9a8a;font-size:13px;margin-bottom:16px;font-weight:400}
.btn-dl-file{display:inline-block;background:var(--green);color:#0a2a20;padding:12px 28px;
  border-radius:10px;font-weight:800;font-size:14px;text-decoration:none;transition:all .2s}
.btn-dl-file:hover{background:#05c490}
.error-box{background:rgba(247,37,133,.08);border:1px solid rgba(247,37,133,.25);border-radius:14px;
  padding:16px;margin-top:14px;display:none;color:#f72585;font-size:13px;line-height:1.6}
.sites{display:flex;flex-wrap:wrap;gap:8px;margin-top:12px}
.site{background:rgba(255,255,255,.04);border:1px solid var(--border);border-radius:999px;padding:4px 12px;font-size:12px;color:var(--muted)}

/* About section */
.about{margin-top:32px}
.about-header{text-align:center;margin-bottom:24px}
.about-header h2{font-size:1.5rem;font-weight:800;background:linear-gradient(135deg,#fff,#a78bfa);
  -webkit-background-clip:text;-webkit-text-fill-color:transparent;background-clip:text;margin-bottom:8px}
.about-header p{color:var(--muted);font-size:.92rem;line-height:1.7;font-weight:400}
.about-grid{display:grid;grid-template-columns:1fr 1fr;gap:14px}
@media(max-width:480px){.about-grid{grid-template-columns:1fr}}
.about-card{background:var(--card);border:1px solid var(--border);border-radius:16px;padding:20px}
.about-card h3{font-size:.95rem;font-weight:800;color:var(--text);margin-bottom:12px}
.about-card ul{list-style:none;display:flex;flex-direction:column;gap:7px}
.about-card ul li{font-size:.84rem;color:var(--muted);font-weight:400;display:flex;align-items:flex-start;gap:8px;line-height:1.5}
.about-card ul li::before{content:'→';color:var(--accent);flex-shrink:0;font-weight:700}

/* Social */
.social-section{margin-top:28px;text-align:center}
.social-label{font-family:'JetBrains Mono',monospace;font-size:11px;letter-spacing:2px;color:var(--muted);text-transform:uppercase;margin-bottom:14px}
.social-links{display:flex;justify-content:center;gap:12px;flex-wrap:wrap}
.social-btn{display:flex;align-items:center;gap:8px;background:var(--card);border:1px solid var(--border);
  border-radius:12px;padding:10px 18px;color:var(--text);text-decoration:none;font-size:13px;font-weight:700;transition:all .2s}
.social-btn:hover{border-color:var(--accent);background:rgba(124,58,237,.1);color:#a78bfa}

/* Footer */
footer{text-align:center;margin-top:40px;padding-top:24px;border-top:1px solid var(--border)}
footer p{font-family:'JetBrains Mono',monospace;font-size:11px;color:var(--muted);letter-spacing:1px}
footer a{color:var(--accent);text-decoration:none}
</style>
</head>
<body>
<div class="wrap">

  <!-- Dil seçici -->
  <div class="lang-bar" id="langBar"></div>

  <!-- Logo -->
  <div class="logo">
    <div class="logo-icon">🎬</div>
    <h1>Vido Down</h1>
    <span class="agency">604 Agency</span>
  </div>

  <!-- İndirici -->
  <div class="card">
    <div class="label" id="lbl_video_link">Video Linki</div>
    <input type="text" id="urlInput" placeholder="https://youtube.com/watch?v=...">
    <div class="toggle">
      <button class="toggle-btn active" id="btnVideo" onclick="setMode('video')">🎬 Video (MP4)</button>
      <button class="toggle-btn" id="btnAudio" onclick="setMode('audio')">🎵 Ses (MP3)</button>
    </div>
  </div>

  <button class="btn-download" id="dlBtn" onclick="startDownload()">⬇ İNDİR</button>

  <div class="progress-wrap" id="progressWrap">
    <div class="progress-bar"><div class="progress-fill" id="progressFill"></div></div>
    <div class="progress-text" id="progressText">Hazırlanıyor...</div>
  </div>
  <div class="result" id="resultBox">
    <div class="r-title" id="lbl_done_title">✅ Hazır!</div>
    <div class="r-sub" id="resultName"></div>
    <a class="btn-dl-file" id="resultLink" href="#">⬇ Dosyayı İndir</a>
  </div>
  <div class="error-box" id="errorBox"></div>

  <!-- Desteklenen siteler -->
  <div class="card" style="margin-top:8px">
    <div class="label" id="lbl_supported">Desteklenen Siteler</div>
    <div class="sites">
      <span class="site">▶ YouTube</span><span class="site">📸 Instagram</span>
      <span class="site">🐦 Twitter/X</span><span class="site">🎵 TikTok</span>
      <span class="site">📘 Facebook</span><span class="site">🎬 Vimeo</span>
      <span class="site">🎮 Twitch</span><span class="site">🟠 Reddit</span>
      <span class="site">+1000 site</span>
    </div>
  </div>

  <!-- Hakkında -->
  <div class="about">
    <div class="about-header">
      <h2 id="lbl_about_title">604 Ajans Hakkında</h2>
      <p id="lbl_about_slogan">Markaları sadece görünür değil — algılanır, hatırlanır ve tercih edilir yapar.</p>
    </div>
    <div class="about-grid">
      <div class="about-card">
        <h3 id="lbl_what_title">🎬 Ne Yapıyoruz?</h3>
        <ul id="list_what"></ul>
      </div>
      <div class="about-card">
        <h3 id="lbl_diff_title">🧠 Farkımız</h3>
        <ul id="list_diff"></ul>
      </div>
      <div class="about-card" style="grid-column:1/-1">
        <h3 id="lbl_who_title">🎯 Kime Hitap Ediyoruz?</h3>
        <ul id="list_who"></ul>
      </div>
    </div>

    <!-- Sosyal medya -->
    <div class="social-section">
      <div class="social-label" id="lbl_follow">Bizi Takip Edin</div>
      <div class="social-links">
        <a class="social-btn" href="https://www.instagram.com/604.agency/" target="_blank">
          <span>📸</span><span>Instagram</span>
        </a>
      </div>
    </div>
  </div>

  <footer>
    <p><span id="lbl_made_by">Made with ❤️ by</span> <a href="https://www.instagram.com/604.agency/" target="_blank">604 Agency</a></p>
  </footer>
</div>

<script>
const T = ''' + str(TRANSLATIONS).replace("'", '"') + ''';
let currentLang = 'tr';
let mode = 'video';
let pollInterval = null;

function buildLangBar() {
  const bar = document.getElementById('langBar');
  Object.keys(T).forEach(code => {
    const btn = document.createElement('button');
    btn.className = 'lang-btn' + (code === 'tr' ? ' active' : '');
    btn.textContent = T[code].flag + ' ' + T[code].lang_name;
    btn.onclick = () => switchLang(code);
    bar.appendChild(btn);
  });
}

function switchLang(code) {
  currentLang = code;
  const t = T[code];
  document.querySelectorAll('.lang-btn').forEach((b,i) => b.classList.toggle('active', Object.keys(T)[i] === code));
  document.getElementById('lbl_video_link').textContent = t.video_link;
  document.getElementById('urlInput').placeholder = t.placeholder;
  document.getElementById('btnVideo').textContent = t.video_btn;
  document.getElementById('btnAudio').textContent = t.audio_btn;
  document.getElementById('dlBtn').textContent = t.download_btn;
  document.getElementById('lbl_done_title').textContent = t.done_title;
  document.getElementById('resultLink').textContent = t.download_file;
  document.getElementById('lbl_supported').textContent = t.supported;
  document.getElementById('lbl_about_title').textContent = t.about_title;
  document.getElementById('lbl_about_slogan').textContent = t.about_slogan;
  document.getElementById('lbl_what_title').textContent = t.what_title;
  document.getElementById('lbl_diff_title').textContent = t.diff_title;
  document.getElementById('lbl_who_title').textContent = t.who_title;
  document.getElementById('lbl_follow').textContent = t.follow;
  document.getElementById('lbl_made_by').textContent = t.made_by;
  ['what','diff','who'].forEach(key => {
    const ul = document.getElementById('list_'+key);
    ul.innerHTML = '';
    t[key+'_items'].forEach(item => { const li = document.createElement('li'); li.textContent = item; ul.appendChild(li); });
  });
  const isRTL = code === 'ar';
  document.getElementById('htmlRoot').setAttribute('dir', isRTL ? 'rtl' : 'ltr');
}

function setMode(m) {
  mode = m;
  document.getElementById('btnVideo').classList.toggle('active', m==='video');
  document.getElementById('btnAudio').classList.toggle('active', m==='audio');
}

async function startDownload() {
  const url = document.getElementById('urlInput').value.trim();
  if (!url) { showError('❌ ' + (T[currentLang].video_link) + '!'); return; }
  hideAll();
  document.getElementById('dlBtn').disabled = true;
  document.getElementById('progressWrap').style.display = 'block';
  document.getElementById('progressText').textContent = T[currentLang].preparing;
  const resp = await fetch('/start', {method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({url,mode})});
  const data = await resp.json();
  if (data.error) { showError(data.error); return; }
  pollStatus(data.job_id);
}

function pollStatus(jobId) {
  pollInterval = setInterval(async () => {
    const resp = await fetch('/status/'+jobId);
    const data = await resp.json();
    document.getElementById('progressFill').style.width = data.progress+'%';
    document.getElementById('progressText').textContent = data.progress+'% — '+(data.status==='done'?T[currentLang].done_title:T[currentLang].downloading);
    if (data.status==='done') { clearInterval(pollInterval); showResult(jobId,data.display_name); }
    else if (data.status==='error') { clearInterval(pollInterval); showError(data.error); }
  }, 800);
}

function showResult(jobId, name) {
  document.getElementById('dlBtn').disabled = false;
  document.getElementById('resultName').textContent = name;
  document.getElementById('resultLink').href = '/download/'+jobId;
  document.getElementById('resultLink').textContent = T[currentLang].download_file;
  document.getElementById('resultBox').style.display = 'block';
}

function showError(msg) {
  document.getElementById('dlBtn').disabled = false;
  document.getElementById('progressWrap').style.display = 'none';
  document.getElementById('errorBox').textContent = msg;
  document.getElementById('errorBox').style.display = 'block';
}

function hideAll() {
  document.getElementById('resultBox').style.display = 'none';
  document.getElementById('errorBox').style.display = 'none';
}

buildLangBar();
switchLang('tr');
</script>
</body>
</html>'''


@app.route("/")
def index():
    return render_template_string(HTML)

@app.route("/manifest.json")
def manifest():
    return jsonify({"name":"Vido Down — 604 Agency","short_name":"Vido Down","start_url":"/","display":"standalone","background_color":"#0b0b12","theme_color":"#7c3aed"})

@app.route("/start", methods=["POST"])
def start():
    data = request.get_json()
    url = data.get("url","").strip()
    mode = data.get("mode","video")
    if not url:
        return jsonify({"error":"Link boş olamaz."})
    job_id = str(uuid.uuid4())
    threading.Thread(target=download_job, args=(job_id,url,mode), daemon=True).start()
    return jsonify({"job_id": job_id})

@app.route("/status/<job_id>")
def status(job_id):
    job = jobs.get(job_id, {"status":"not_found","progress":0})
    return jsonify({"status":job.get("status"),"progress":job.get("progress",0),"display_name":job.get("display_name",""),"error":job.get("error","")})

@app.route("/download/<job_id>")
def download(job_id):
    job = jobs.get(job_id)
    if not job or job.get("status") != "done":
        return "Dosya bulunamadı.", 404
    return send_file(job["filename"], as_attachment=True, download_name=job["display_name"])

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port)
