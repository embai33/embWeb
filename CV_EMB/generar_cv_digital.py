# -*- coding: utf-8 -*-
"""
Genera curriculum_salud_digital.html a partir de curriculum_vitae.html.

Fuente única de verdad: el CV general. Los méritos de salud digital / tecnología
van marcados en el CV general con la clase `dig`:
    <li class="dig">…</li>                      (viñetas)
    <p class="cv-p dig">Título: …</p> (+ 3 líneas) (estudios de investigación)

Para añadir un mérito nuevo al CV digital: en curriculum_vitae.html, añade la
clase `dig` al <li> correspondiente (o `cv-p dig` a las 4 líneas del estudio) y
vuelve a ejecutar este script:  python3 generar_cv_digital.py

El script localiza cada subsección por su atributo id (no por nº de línea), así
que es robusto frente a inserciones y reordenaciones dentro de las subsecciones.
"""
import io, re, os

BASE = os.path.dirname(os.path.abspath(__file__))
SRC = os.path.join(BASE, "curriculum_vitae.html")
OUT = os.path.join(BASE, "curriculum_salud_digital.html")

with io.open(SRC, encoding="utf-8") as f:
    full = f.read()
lines = full.split("\n")

# Todas las anclas (id) en orden de documento — definen los límites de cada rango.
ANCHORS_ORDER = [
    "formación_académica", "actividad_profesional", "méritos_científicos_y_de_investigación",
    "ponencias_mesas_redondas_conferencias", "actividad_docente", "actividad_docente_no_reglada",
    "asistencia_a_congresos_y_jornadas", "publicaciones_científicas", "publicaciones_en_revistas",
    "comunicaciones_a_congresos", "libros", "capítulos_de_libros", "otros_méritos",
    "participación_en_estudios_de_investigación", "tesis_doctorales",
    "dirección_o_coordinación_de_cursos_o_jornadas", "otros",
]

def anchor_line(aid):
    needle = 'id="%s"' % aid
    for i, ln in enumerate(lines):
        if needle in ln:
            return i
    raise SystemExit("No se encontró el ancla id=%s" % aid)

anchor_idx = {a: anchor_line(a) for a in ANCHORS_ORDER}

def range_of(aid):
    """Devuelve (start, end) índices 0-based: desde el ancla hasta la siguiente ancla."""
    start = anchor_idx[aid]
    later = [anchor_idx[a] for a in ANCHORS_ORDER if anchor_idx[a] > start]
    end = min(later) if later else len(lines)
    return start, end

def clean(s):
    return s.replace('<li class="dig">', "<li>").replace('<p class="cv-p dig">', '<p class="cv-p">')

def collect_li(aid):
    s, e = range_of(aid)
    return [clean(lines[i].strip()) for i in range(s, e) if '<li class="dig">' in lines[i]]

def collect_estudios(aid):
    s, e = range_of(aid)
    runs, cur, prev = [], [], None
    for i in range(s, e):
        if '<p class="cv-p dig">' in lines[i]:
            if prev is not None and i != prev + 1:
                runs.append(cur); cur = []
            cur.append(i); prev = i
    if cur:
        runs.append(cur)
    studies = []
    for run in runs:
        ps = []
        for i in run:
            txt = clean(lines[i].strip())
            txt = re.sub(r'(Título:\s*)\d+\.\s*', r'\1', txt)  # quita "5. " y similares
            ps.append(txt)
        studies.append(ps)
    return studies

# ---- subsecciones configuradas: (id, etiqueta salida, tipo) ----
SECTIONS = [("formación_académica", "Formación en tecnología y salud digital", "ul"),
            ("actividad_profesional", "Actividad profesional", "ul")]
SUBSECTIONS = [
    ("ponencias_mesas_redondas_conferencias", "Ponencias, mesas redondas, conferencias…", "ol"),
    ("actividad_docente", "Actividad docente (másters/cursos)", "ol"),
    ("actividad_docente_no_reglada", "Actividad docente no reglada — Talleres de IA", "ol"),
    ("publicaciones_en_revistas", "Publicaciones en revistas", "ol"),
    ("comunicaciones_a_congresos", "Comunicaciones a congresos", "ol"),
    ("libros", "Libros", "ul"),
    ("capítulos_de_libros", "Capítulos de libros", "ul"),
    ("participación_en_estudios_de_investigación", "Participación en estudios de investigación", "estudios"),
    ("dirección_o_coordinación_de_cursos_o_jornadas", "Dirección o coordinación de cursos", "ul"),
    ("otros", "Otros méritos", "ul"),
]

def li_block(items, ordered):
    tag = "ol" if ordered else "ul"
    return '<%s class="cv-list cv-list-0">\n%s\n</%s>' % (tag, "\n".join(items), tag)

def details_block(sid, label, inner, count):
    return ('<details class="cv-sub" id="%s_dig">\n  <summary>\n    %s '
            '<span class="cv-count">(%d)</span>\n    <span class="cv-chevron">▼</span>\n'
            '  </summary>\n  <div class="cv-sub-body">%s</div>\n</details>'
            % (sid, label, count, inner))

# ---- head (reutiliza <head> con todo el CSS) ----
head = full[:full.index("</head>") + len("</head>")]
head = re.sub(r'<title>.*?</title>', '<title>CV Salud Digital — Emilio Monte Boquet</title>', head, flags=re.S)

# ---- tail (modal + script) ----
tail = full[full.index('<div class="modal-overlay'):]
tail = tail.replace('<h2>\U0001F4C4 CV — Emilio Monte Boquet</h2>',
                    '<h2>\U0001F4BB CV Salud Digital — Emilio Monte Boquet</h2>')
tail = tail.replace('Versión HTML del Curriculum Vitae, generada a partir de la exportación de Notion.',
                    'Versión centrada exclusivamente en méritos de tecnología y salud digital, generada automáticamente a partir del CV general (elementos marcados con la clase «dig»).')

# ---- cuerpo ----
# localizar profile-card de forma robusta
p_start = next(i for i, ln in enumerate(lines) if 'class="profile-card"' in ln)
p_end = next(i for i in range(p_start, len(lines)) if '</div>' in lines[i] and 'print-date' in lines[i-1]) + 1
profile = "\n".join(lines[p_start:p_end])

body = []
body.append("<body>\n")
body.append('''<header>
  <div>
    <h1>\U0001F4BB Curriculum Vitae — Salud Digital</h1>
    <span class="subtitle">Emilio Monte Boquet</span>
    <div class="header-updated" id="last-updated"></div>
  </div>
  <button class="btn-pdf" onclick="printCV()">⬇ PDF</button>
  <a href="curriculum_vitae.html" class="btn-info">\U0001F4C4 CV completo</a>
  <a href="../index.html" class="btn-home">⌂ Inicio</a>
  <button class="btn-info" onclick="toggleModal(true)">ℹ Acerca de</button>
</header>
''')
body.append('<div class="container">\n')
body.append("  " + profile + "\n")
body.append('''  <div class="toc">
    <div class="toc-title">Ir a sección:</div>
    <div class="toc-links"><a href="#formacion_digital" class="toc-link" onclick="scrollToSec('formacion_digital'); return false;">\U0001F393 Formación</a> <a href="#actividad_digital" class="toc-link" onclick="scrollToSec('actividad_digital'); return false;">\U0001F3E5 Actividad profesional</a> <a href="#meritos_digital" class="toc-link" onclick="scrollToSec('meritos_digital'); return false;">\U0001F52C Méritos científicos</a></div>
  </div>
''')

# secciones de nivel superior
SEC_META = {"formación_académica": ("formacion_digital", "\U0001F393"),
            "actividad_profesional": ("actividad_digital", "\U0001F3E5")}
for sid, label, kind in SECTIONS:
    items = collect_li(sid)
    out_id, emoji = SEC_META[sid]
    body.append('''<div class="cv-section" id="%s">
  <div class="cv-section-hdr">
    <span class="cv-section-emoji">%s</span>
    <span class="cv-section-title">%s</span>
    <span class="cv-section-chevron">▼</span>
  </div>
  <div class="cv-section-body">
    %s
  </div>
</div>''' % (out_id, emoji, label, li_block(items, False)))

# méritos: construir subsecciones + stats
sub_html, stat_cards = [], []
STAT_LABEL = {
    "ponencias_mesas_redondas_conferencias": "Ponencias y conferencias",
    "actividad_docente": "Docencia másters/cursos", "actividad_docente_no_reglada": "Talleres de IA",
    "publicaciones_en_revistas": "Publicaciones", "comunicaciones_a_congresos": "Comunicaciones",
    "libros": "Libros", "capítulos_de_libros": "Capítulos de libros",
    "participación_en_estudios_de_investigación": "Estudios de investigación",
    "dirección_o_coordinación_de_cursos_o_jornadas": "Cursos dirigidos", "otros": "Otros méritos",
}
for sid, label, kind in SUBSECTIONS:
    if kind == "estudios":
        studies = collect_estudios(sid)
        inner = "\n".join("\n".join(ps) for ps in studies)
        count = len(studies)
    else:
        items = collect_li(sid)
        inner = li_block(items, kind == "ol")
        count = len(items)
    if count == 0:
        continue
    sub_html.append(details_block(sid, label, inner, count))
    stat_cards.append('<div class="stat-card"><div class="stat-number">%d</div><div class="stat-label">%s</div></div>' % (count, STAT_LABEL[sid]))

stats_html = '<div class="stats-grid">' + "".join(stat_cards) + "</div>"
body.append('''<div class="cv-section" id="meritos_digital">
  <div class="cv-section-hdr">
    <span class="cv-section-emoji">\U0001F52C</span>
    <span class="cv-section-title">Méritos científicos y de investigación</span>
    <span class="cv-section-chevron">▼</span>
  </div>
  <div class="cv-section-body">
    %s
  </div>
</div>''' % ("\n".join([stats_html] + sub_html)))

body.append("\n</div>\n\n")

out = head + "\n" + "".join(body) + tail
with io.open(OUT, "w", encoding="utf-8") as f:
    f.write(out)

total = len(collect_li("formación_académica")) + len(collect_li("actividad_profesional"))
for sid, _, kind in SUBSECTIONS:
    total += len(collect_estudios(sid)) if kind == "estudios" else len(collect_li(sid))
print("Generado:", OUT)
print("Total méritos digitales:", total)
