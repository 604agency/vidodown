from flask import Flask, request, jsonify, send_file, render_template_string
import yt_dlp, os, tempfile, threading, uuid, re

app = Flask(__name__)
jobs = {}

def get_cookies_file():
    cookies_content = os.environ.get("COOKIES_CONTENT", "")
    if cookies_content:
        tmp = tempfile.NamedTemporaryFile(mode="w", suffix=".txt", delete=False)
        tmp.write(cookies_content)
        tmp.close()
        return tmp.name
    return None

def download_job(job_id, url, mode):
    jobs[job_id] = {"status": "downloading", "progress": 0, "filename": None, "error": None, "display_name": None}
    tmpdir = tempfile.mkdtemp()
    cookies_file = get_cookies_file()

    def progress_hook(d):
        if d.get("status") == "downloading":
            raw = re.sub(r'\x1b\[[0-9;]*m', '', d.get("_percent_str", "0%")).replace("%","").strip()
            try:
                jobs[job_id]["progress"] = int(float(raw))
            except:
                pass
        elif d.get("status") == "finished":
            jobs[job_id]["progress"] = 95

    base_opts = {
        "outtmpl": os.path.join(tmpdir, "%(title)s.%(ext)s"),
        "progress_hooks": [progress_hook],
        "quiet": True,
        "no_warnings": True,
    }
    if cookies_file:
        base_opts["cookiefile"] = cookies_file

    if mode == "audio":
        ydl_opts = {**base_opts,
            "format": "bestaudio/best",
            "postprocessors": [{"key": "FFmpegExtractAudio", "preferredcodec": "mp3", "preferredquality": "192"}],
        }
    else:
        ydl_opts = {**base_opts,
            "format": "best[ext=mp4]/best",
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


HTML = """<!DOCTYPE html>
<html lang="tr" id="htmlRoot">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<meta name="theme-color" content="#0b0b12">
<title>Vido Down — 604 Agency</title>
<style>
@import url('https://fonts.googleapis.com/css2?family=JetBrains+Mono:wght@400;700&family=Syne:wght@400;700;800&display=swap');
:root{--bg:#0b0b12;--card:#1a1a28;--border:#2a2a3e;--accent:#7c3aed;--green:#06d6a0;--text:#e8e8f5;--muted:#55556a}
*{margin:0;padding:0;box-sizing:border-box;-webkit-tap-highlight-color:transparent}
body{background:var(--bg);color:var(--text);font-family:'Syne',sans-serif;min-height:100vh;display:flex;flex-direction:column;align-items:center}
body::before{content:'';position:fixed;inset:0;pointer-events:none;z-index:0;
  background:radial-gradient(ellipse 70% 40% at 20% 0%,rgba(124,58,237,.18) 0%,transparent 60%),
  radial-gradient(ellipse 50% 50% at 80% 90%,rgba(6,214,160,.1) 0%,transparent 60%)}
.wrap{width:100%;max-width:600px;padding:40px 20px 60px;position:relative;z-index:1}

/* Lang bar */
.lang-bar{display:flex;flex-wrap:wrap;gap:6px;justify-content:center;margin-bottom:28px}
.lang-btn{background:rgba(255,255,255,.05);border:1px solid var(--border);border-radius:999px;
  padding:5px 12px;font-size:12px;color:var(--muted);cursor:pointer;transition:all .2s;font-family:'Syne',sans-serif}
.lang-btn.active{background:var(--accent);border-color:var(--accent);color:#fff}

/* Logo */
.logo{display:flex;flex-direction:column;align-items:center;margin-bottom:36px}
.logo-icon{width:72px;height:72px;background:var(--accent);border-radius:20px;display:flex;align-items:center;justify-content:center;font-size:32px;margin-bottom:14px;box-shadow:0 0 40px rgba(124,58,237,.4);animation:pulse 3s ease-in-out infinite}
@keyframes pulse{0%,100%{box-shadow:0 0 40px rgba(124,58,237,.4)}50%{box-shadow:0 0 60px rgba(124,58,237,.7)}}
.logo h1{font-size:2rem;font-weight:800;background:linear-gradient(135deg,#fff 0%,#a78bfa 60%,#06d6a0 100%);-webkit-background-clip:text;-webkit-text-fill-color:transparent;background-clip:text}
.logo .agency{font-family:'JetBrains Mono',monospace;font-size:11px;letter-spacing:3px;color:var(--muted);text-transform:uppercase;margin-top:4px}

/* Cards */
.card{background:var(--card);border:1px solid var(--border);border-radius:20px;padding:24px;margin-bottom:14px}
.label{font-size:11px;font-weight:700;color:var(--muted);letter-spacing:1px;text-transform:uppercase;margin-bottom:10px}
input[type=text]{width:100%;background:var(--bg);border:1.5px solid var(--border);border-radius:12px;padding:14px 16px;color:var(--text);font-family:'JetBrains Mono',monospace;font-size:13px;outline:none;transition:border-color .2s}
input[type=text]:focus{border-color:var(--accent)}
input::placeholder{color:var(--muted)}
.toggle{display:flex;gap:10px;margin-top:14px}
.toggle-btn{flex:1;padding:11px;border:1.5px solid var(--border);border-radius:12px;background:transparent;color:var(--muted);font-family:'Syne',sans-serif;font-size:13px;font-weight:700;cursor:pointer;transition:all .2s;text-align:center}
.toggle-btn.active{background:var(--accent);border-color:var(--accent);color:#fff}
.btn-dl{width:100%;padding:16px;background:var(--accent);border:none;border-radius:14px;color:#fff;font-family:'Syne',sans-serif;font-size:16px;font-weight:800;cursor:pointer;transition:all .2s;margin-top:4px;box-shadow:0 4px 24px rgba(124,58,237,.35)}
.btn-dl:hover{background:#6d28d9;transform:translateY(-1px)}
.btn-dl:disabled{background:var(--border);color:var(--muted);box-shadow:none;cursor:not-allowed;transform:none}

/* Progress */
.prog-wrap{margin-top:14px;display:none}
.prog-bar{height:6px;background:var(--border);border-radius:3px;overflow:hidden;margin-bottom:8px}
.prog-fill{height:100%;width:0%;border-radius:3px;transition:width .3s;background:linear-gradient(90deg,var(--accent),var(--green))}
.prog-txt{font-family:'JetBrains Mono',monospace;font-size:12px;color:var(--muted)}

/* Result / Error */
.result{background:rgba(6,214,160,.08);border:1px solid rgba(6,214,160,.25);border-radius:14px;padding:20px;margin-top:14px;display:none;text-align:center}
.result h3{color:var(--green);font-weight:800;margin-bottom:8px}
.result p{color:#6a9a8a;font-size:13px;margin-bottom:16px}
.btn-save{display:inline-block;background:var(--green);color:#0a2a20;padding:12px 28px;border-radius:10px;font-weight:800;font-size:14px;text-decoration:none;transition:all .2s}
.btn-save:hover{background:#05c490}
.err{background:rgba(247,37,133,.08);border:1px solid rgba(247,37,133,.25);border-radius:14px;padding:16px;margin-top:14px;display:none;color:#f72585;font-size:13px;line-height:1.6}

/* Sites */
.sites{display:flex;flex-wrap:wrap;gap:8px;margin-top:12px}
.site{background:rgba(255,255,255,.04);border:1px solid var(--border);border-radius:999px;padding:4px 12px;font-size:12px;color:var(--muted)}

/* About */
.about{margin-top:28px}
.about-head{text-align:center;margin-bottom:20px}
.about-head h2{font-size:1.4rem;font-weight:800;background:linear-gradient(135deg,#fff,#a78bfa);-webkit-background-clip:text;-webkit-text-fill-color:transparent;background-clip:text;margin-bottom:8px}
.about-head p{color:var(--muted);font-size:.88rem;line-height:1.7;font-weight:400}
.about-grid{display:grid;grid-template-columns:1fr 1fr;gap:12px}
@media(max-width:480px){.about-grid{grid-template-columns:1fr}}
.about-card{background:var(--card);border:1px solid var(--border);border-radius:16px;padding:18px}
.about-card h3{font-size:.9rem;font-weight:800;color:var(--text);margin-bottom:10px}
.about-card ul{list-style:none;display:flex;flex-direction:column;gap:7px}
.about-card ul li{font-size:.82rem;color:var(--muted);display:flex;align-items:flex-start;gap:7px;line-height:1.5}
.about-card ul li::before{content:'→';color:var(--accent);flex-shrink:0;font-weight:700}
.full{grid-column:1/-1}

/* Social */
.social{margin-top:24px;text-align:center}
.social-lbl{font-family:'JetBrains Mono',monospace;font-size:10px;letter-spacing:2px;color:var(--muted);text-transform:uppercase;margin-bottom:12px}
.social-links{display:flex;justify-content:center;gap:10px;flex-wrap:wrap}
.social-a{display:flex;align-items:center;gap:8px;background:var(--card);border:1px solid var(--border);border-radius:12px;padding:10px 18px;color:var(--text);text-decoration:none;font-size:13px;font-weight:700;transition:all .2s}
.social-a:hover{border-color:var(--accent);background:rgba(124,58,237,.1);color:#a78bfa}

footer{text-align:center;margin-top:32px;padding-top:20px;border-top:1px solid var(--border)}
footer p{font-family:'JetBrains Mono',monospace;font-size:11px;color:var(--muted);letter-spacing:1px}
footer a{color:var(--accent);text-decoration:none}
</style>
</head>
<body>
<div class="wrap">

<div class="lang-bar" id="langBar"></div>

<div class="logo">
  <div class="logo-icon">🎬</div>
  <h1>Vido Down</h1>
  <span class="agency">604 Agency</span>
</div>

<div class="card">
  <div class="label" id="t_link">Video Linki</div>
  <input type="text" id="urlInput" placeholder="https://youtube.com/watch?v=...">
  <div class="toggle">
    <button class="toggle-btn active" id="btnV" onclick="setMode('video')">🎬 Video (MP4)</button>
    <button class="toggle-btn" id="btnA" onclick="setMode('audio')">🎵 Ses (MP3)</button>
  </div>
</div>

<button class="btn-dl" id="dlBtn" onclick="startDl()">⬇ İNDİR</button>

<div class="prog-wrap" id="progWrap">
  <div class="prog-bar"><div class="prog-fill" id="progFill"></div></div>
  <div class="prog-txt" id="progTxt"></div>
</div>

<div class="result" id="resultBox">
  <h3 id="t_done">✅ Hazır!</h3>
  <p id="resultName"></p>
  <a class="btn-save" id="resultLink" href="#">⬇ Dosyayı İndir</a>
</div>
<div class="err" id="errBox"></div>

<div class="card" style="margin-top:8px">
  <div class="label" id="t_supported">Desteklenen Siteler</div>
  <div class="sites">
    <span class="site">▶ YouTube</span><span class="site">📸 Instagram</span>
    <span class="site">🐦 Twitter/X</span><span class="site">🎵 TikTok</span>
    <span class="site">📘 Facebook</span><span class="site">🎬 Vimeo</span>
    <span class="site">🎮 Twitch</span><span class="site">🟠 Reddit</span>
    <span class="site">+1000 site</span>
  </div>
</div>

<div class="about">
  <div class="about-head">
    <h2 id="t_about_title">604 Ajans Hakkında</h2>
    <p id="t_about_slogan">Markaları sadece görünür değil — algılanır, hatırlanır ve tercih edilir yapar.</p>
  </div>
  <div class="about-grid">
    <div class="about-card">
      <h3 id="t_what">🎬 Ne Yapıyoruz?</h3>
      <ul id="l_what"></ul>
    </div>
    <div class="about-card">
      <h3 id="t_diff">🧠 Farkımız</h3>
      <ul id="l_diff"></ul>
    </div>
    <div class="about-card full">
      <h3 id="t_who">🎯 Kime Hitap Ediyoruz?</h3>
      <ul id="l_who"></ul>
    </div>
  </div>
  <div class="social">
    <div class="social-lbl" id="t_follow">Bizi Takip Edin</div>
    <div class="social-links">
      <a class="social-a" href="https://www.instagram.com/604.agency/" target="_blank">📸 Instagram</a>
    </div>
  </div>
</div>

<footer><p id="t_footer">Made with ❤️ by <a href="https://www.instagram.com/604.agency/" target="_blank">604 Agency</a></p></footer>
</div>

<script>
const T = {
  tr:{flag:"🇹🇷",name:"Türkçe",link:"Video Linki",ph:"https://youtube.com/watch?v=...",vbtn:"🎬 Video (MP4)",abtn:"🎵 Ses (MP3)",dl:"⬇ İNDİR",prep:"Hazırlanıyor...",downloading:"İndiriliyor...",done:"✅ Hazır!",save:"⬇ Dosyayı İndir",sup:"Desteklenen Siteler",about:"604 Ajans Hakkında",slogan:"Markaları sadece görünür değil — algılanır, hatırlanır ve tercih edilir yapar.",what:"🎬 Ne Yapıyoruz?",what_i:["Video Prodüksiyon","Profesyonel Fotoğraf","Video Editörlük","Grafik Tasarım","Reklam Kampanyaları","Sosyal Medya Yönetimi","Marka Konumlandırma"],diff:"🧠 Farkımız",diff_i:["Klişe değil güçlü konseptler","Tasarım odaklı stratejik bakış","Görselliği marka algısı için","Minimal ama etkili iletişim"],who:"🎯 Kime Hitap Ediyoruz?",who_i:["Büyümek isteyen yerel markalara","Profesyonel görünmek isteyen işletmelere","Fark edilmek isteyenlere"],follow:"Bizi Takip Edin",footer:"Made with ❤️ by",rtl:false},
  en:{flag:"🇬🇧",name:"English",link:"Video Link",ph:"https://youtube.com/watch?v=...",vbtn:"🎬 Video (MP4)",abtn:"🎵 Audio (MP3)",dl:"⬇ DOWNLOAD",prep:"Preparing...",downloading:"Downloading...",done:"✅ Ready!",save:"⬇ Download File",sup:"Supported Sites",about:"About 604 Agency",slogan:"We don't just make brands visible — we make them perceived, remembered and preferred.",what:"🎬 What We Do",what_i:["Video Production","Professional Photography","Video Editing","Graphic Design","Ad Campaigns","Social Media Management","Brand Positioning"],diff:"🧠 Our Difference",diff_i:["Strong concepts, not clichés","Design-focused strategic vision","Visuals for brand perception","Minimal but effective communication"],who:"🎯 Who We Serve",who_i:["Local brands that want to grow","Businesses that want to look professional","Those who want to be noticed"],follow:"Follow Us",footer:"Made with ❤️ by",rtl:false},
  es:{flag:"🇪🇸",name:"Español",link:"Enlace de Video",ph:"https://youtube.com/watch?v=...",vbtn:"🎬 Video (MP4)",abtn:"🎵 Audio (MP3)",dl:"⬇ DESCARGAR",prep:"Preparando...",downloading:"Descargando...",done:"✅ ¡Listo!",save:"⬇ Descargar",sup:"Sitios Compatibles",about:"Sobre 604 Agency",slogan:"No solo hacemos marcas visibles — las hacemos percibidas, recordadas y preferidas.",what:"🎬 ¿Qué Hacemos?",what_i:["Producción de Video","Fotografía Profesional","Edición de Video","Diseño Gráfico","Campañas Publicitarias","Gestión de Redes Sociales","Posicionamiento de Marca"],diff:"🧠 Nuestra Diferencia",diff_i:["Conceptos fuertes, no clichés","Visión estratégica y de diseño","Visuales para percepción de marca","Comunicación mínima pero eficaz"],who:"🎯 ¿A Quién?",who_i:["Marcas locales que quieren crecer","Empresas que quieren verse profesionales","Quienes quieren ser notados"],follow:"Síguenos",footer:"Hecho con ❤️ por",rtl:false},
  fr:{flag:"🇫🇷",name:"Français",link:"Lien Vidéo",ph:"https://youtube.com/watch?v=...",vbtn:"🎬 Vidéo (MP4)",abtn:"🎵 Audio (MP3)",dl:"⬇ TÉLÉCHARGER",prep:"Préparation...",downloading:"Téléchargement...",done:"✅ Prêt!",save:"⬇ Télécharger",sup:"Sites Supportés",about:"À propos de 604 Agency",slogan:"Nous rendons les marques perçues, mémorisées et préférées.",what:"🎬 Ce que nous faisons",what_i:["Production Vidéo","Photographie Pro","Montage Vidéo","Design Graphique","Campagnes Pub","Gestion Réseaux Sociaux","Positionnement Marque"],diff:"🧠 Notre Différence",diff_i:["Concepts forts pas clichés","Vision design et stratégique","Visuels pour la marque","Communication efficace"],who:"🎯 Pour Qui?",who_i:["Marques locales en croissance","Entreprises pro","Ceux qui veulent être remarqués"],follow:"Suivez-nous",footer:"Fait avec ❤️ par",rtl:false},
  de:{flag:"🇩🇪",name:"Deutsch",link:"Video-Link",ph:"https://youtube.com/watch?v=...",vbtn:"🎬 Video (MP4)",abtn:"🎵 Audio (MP3)",dl:"⬇ HERUNTERLADEN",prep:"Vorbereitung...",downloading:"Herunterladen...",done:"✅ Fertig!",save:"⬇ Herunterladen",sup:"Unterstützte Seiten",about:"Über 604 Agency",slogan:"Wir machen Marken nicht nur sichtbar — wahrnehmbar, einprägsam und bevorzugt.",what:"🎬 Was wir tun",what_i:["Videoproduktion","Profifotografie","Videobearbeitung","Grafikdesign","Werbekampagnen","Social-Media-Management","Markenpositionierung"],diff:"🧠 Unser Unterschied",diff_i:["Starke Konzepte statt Klischees","Design und Strategie","Visuals für Markenwahrnehmung","Effektive Kommunikation"],who:"🎯 Für wen?",who_i:["Lokale Marken","Professionelle Unternehmen","Die auffallen wollen"],follow:"Folge uns",footer:"Mit ❤️ gemacht von",rtl:false},
  ar:{flag:"🇸🇦",name:"العربية",link:"رابط الفيديو",ph:"https://youtube.com/watch?v=...",vbtn:"🎬 فيديو",abtn:"🎵 صوت MP3",dl:"⬇ تحميل",prep:"جاري التحضير...",downloading:"جاري التحميل...",done:"✅ جاهز!",save:"⬇ تحميل الملف",sup:"المواقع المدعومة",about:"عن 604 Agency",slogan:"نجعل العلامات التجارية محسوسة ومحفورة في الذاكرة ومفضلة.",what:"🎬 ماذا نفعل؟",what_i:["إنتاج الفيديو","التصوير الاحترافي","تحرير الفيديو","التصميم الجرافيكي","حملات إعلانية","إدارة وسائل التواصل","تموضع العلامة"],diff:"🧠 ما يميزنا",diff_i:["مفاهيم قوية","رؤية استراتيجية","صور لإدراك العلامة","تواصل فعّال"],who:"🎯 لمن نحن؟",who_i:["العلامات المحلية","الشركات الاحترافية","من يريد أن يُلاحَظ"],follow:"تابعنا",footer:"صُنع بـ ❤️ من قِبل",rtl:true},
  ja:{flag:"🇯🇵",name:"日本語",link:"動画リンク",ph:"https://youtube.com/watch?v=...",vbtn:"🎬 動画 MP4",abtn:"🎵 音声 MP3",dl:"⬇ ダウンロード",prep:"準備中...",downloading:"ダウンロード中...",done:"✅ 完了！",save:"⬇ ファイルをDL",sup:"対応サイト",about:"604 Agencyについて",slogan:"ブランドを認識され、記憶され、選ばれる存在にします。",what:"🎬 サービス",what_i:["映像制作","プロ写真","動画編集","グラフィックデザイン","広告","SNS管理","ブランド戦略"],diff:"🧠 私たちの違い",diff_i:["強いコンセプト","戦略的デザイン","ブランド認知のビジュアル","効果的なコミュニケーション"],who:"🎯 対象",who_i:["成長したいブランド","プロに見せたい企業","注目されたい方"],follow:"フォローする",footer:"❤️ で作られました by",rtl:false},
  pt:{flag:"🇧🇷",name:"Português",link:"Link do Vídeo",ph:"https://youtube.com/watch?v=...",vbtn:"🎬 Vídeo MP4",abtn:"🎵 Áudio MP3",dl:"⬇ BAIXAR",prep:"Preparando...",downloading:"Baixando...",done:"✅ Pronto!",save:"⬇ Baixar Arquivo",sup:"Sites Suportados",about:"Sobre 604 Agency",slogan:"Tornamos marcas percebidas, lembradas e preferidas.",what:"🎬 O que fazemos",what_i:["Produção de Vídeo","Fotografia Pro","Edição de Vídeo","Design Gráfico","Campanhas","Gestão Social","Posicionamento"],diff:"🧠 Nossa Diferença",diff_i:["Conceitos fortes","Visão estratégica","Visuais para marca","Comunicação eficaz"],who:"🎯 Para quem?",who_i:["Marcas locais","Empresas profissionais","Quem quer ser notado"],follow:"Siga-nos",footer:"Feito com ❤️ por",rtl:false},
  ru:{flag:"🇷🇺",name:"Русский",link:"Ссылка на видео",ph:"https://youtube.com/watch?v=...",vbtn:"🎬 Видео MP4",abtn:"🎵 Аудио MP3",dl:"⬇ СКАЧАТЬ",prep:"Подготовка...",downloading:"Скачивание...",done:"✅ Готово!",save:"⬇ Скачать",sup:"Поддерживаемые сайты",about:"О 604 Agency",slogan:"Делаем бренды воспринимаемыми, запоминающимися и предпочтительными.",what:"🎬 Что мы делаем",what_i:["Видеопроизводство","Фотография","Видеомонтаж","Дизайн","Реклама","Соцсети","Позиционирование"],diff:"🧠 Наше отличие",diff_i:["Сильные концепции","Стратегический дизайн","Визуалы для бренда","Эффективная коммуникация"],who:"🎯 Для кого?",who_i:["Местные бренды","Профессиональные компании","Те кто хочет быть замеченным"],follow:"Подписывайтесь",footer:"Сделано с ❤️ от",rtl:false},
  zh:{flag:"🇨🇳",name:"中文",link:"视频链接",ph:"https://youtube.com/watch?v=...",vbtn:"🎬 视频 MP4",abtn:"🎵 音频 MP3",dl:"⬇ 下载",prep:"准备中...",downloading:"下载中...",done:"✅ 完成！",save:"⬇ 下载文件",sup:"支持的网站",about:"关于 604 Agency",slogan:"我们让品牌被感知、被记住、被优先选择。",what:"🎬 我们做什么",what_i:["视频制作","专业摄影","视频剪辑","平面设计","广告投放","社交媒体","品牌定位"],diff:"🧠 我们的不同",diff_i:["强大概念","战略设计","品牌视觉","高效沟通"],who:"🎯 服务对象",who_i:["本地品牌","专业企业","想被注意的人"],follow:"关注我们",footer:"由 ❤️ 制作",rtl:false}
};

let lang="tr", mode="video", poll=null;

function buildLangBar(){
  const bar=document.getElementById("langBar");
  Object.keys(T).forEach(c=>{
    const b=document.createElement("button");
    b.className="lang-btn"+(c==="tr"?" active":"");
    b.textContent=T[c].flag+" "+T[c].name;
    b.onclick=()=>switchLang(c);
    bar.appendChild(b);
  });
}

function switchLang(c){
  lang=c; const t=T[c];
  document.querySelectorAll(".lang-btn").forEach((b,i)=>b.classList.toggle("active",Object.keys(T)[i]===c));
  document.getElementById("htmlRoot").setAttribute("dir",t.rtl?"rtl":"ltr");
  document.getElementById("t_link").textContent=t.link;
  document.getElementById("urlInput").placeholder=t.ph;
  document.getElementById("btnV").textContent=t.vbtn;
  document.getElementById("btnA").textContent=t.abtn;
  document.getElementById("dlBtn").textContent=t.dl;
  document.getElementById("t_done").textContent=t.done;
  document.getElementById("resultLink").textContent=t.save;
  document.getElementById("t_supported").textContent=t.sup;
  document.getElementById("t_about_title").textContent=t.about;
  document.getElementById("t_about_slogan").textContent=t.slogan;
  document.getElementById("t_what").textContent=t.what;
  document.getElementById("t_diff").textContent=t.diff;
  document.getElementById("t_who").textContent=t.who;
  document.getElementById("t_follow").textContent=t.follow;
  document.getElementById("t_footer").innerHTML=t.footer+' <a href="https://www.instagram.com/604.agency/" target="_blank">604 Agency</a>';
  [["l_what","what_i"],["l_diff","diff_i"],["l_who","who_i"]].forEach(([id,key])=>{
    const ul=document.getElementById(id); ul.innerHTML="";
    t[key].forEach(item=>{const li=document.createElement("li");li.textContent=item;ul.appendChild(li);});
  });
}

function setMode(m){
  mode=m;
  document.getElementById("btnV").classList.toggle("active",m==="video");
  document.getElementById("btnA").classList.toggle("active",m==="audio");
}

async function startDl(){
  const url=document.getElementById("urlInput").value.trim();
  if(!url){showErr("❌ Link gir!");return;}
  hideAll();
  document.getElementById("dlBtn").disabled=true;
  document.getElementById("progWrap").style.display="block";
  document.getElementById("progTxt").textContent=T[lang].prep;
  const r=await fetch("/start",{method:"POST",headers:{"Content-Type":"application/json"},body:JSON.stringify({url,mode})});
  const d=await r.json();
  if(d.error){showErr(d.error);return;}
  pollStatus(d.job_id);
}

function pollStatus(id){
  poll=setInterval(async()=>{
    const r=await fetch("/status/"+id);
    const d=await r.json();
    document.getElementById("progFill").style.width=d.progress+"%";
    document.getElementById("progTxt").textContent=d.progress+"% — "+(d.status==="done"?T[lang].done:T[lang].downloading);
    if(d.status==="done"){clearInterval(poll);showResult(id,d.display_name);}
    else if(d.status==="error"){clearInterval(poll);showErr(d.error);}
  },800);
}

function showResult(id,name){
  document.getElementById("dlBtn").disabled=false;
  document.getElementById("resultName").textContent=name;
  document.getElementById("resultLink").href="/download/"+id;
  document.getElementById("resultLink").textContent=T[lang].save;
  document.getElementById("resultBox").style.display="block";
}

function showErr(msg){
  document.getElementById("dlBtn").disabled=false;
  document.getElementById("progWrap").style.display="none";
  document.getElementById("errBox").textContent="❌ "+msg;
  document.getElementById("errBox").style.display="block";
}

function hideAll(){
  document.getElementById("resultBox").style.display="none";
  document.getElementById("errBox").style.display="none";
}

buildLangBar();
switchLang("tr");
</script>
</body>
</html>"""


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
def download_file(job_id):
    job = jobs.get(job_id)
    if not job or job.get("status") != "done":
        return "Dosya bulunamadı.", 404
    return send_file(job["filename"], as_attachment=True, download_name=job["display_name"])

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port)
