#!/usr/bin/env python3
"""
Convierte el CV exportado de Notion (Markdown) a HTML con estilo EMB.
Estructura real del MD:
  # Curriculum vitae
  ### Nombre: ...
  ... info personal ...
  ## Relación de méritos
  - Formación académica        <- main section (indent=0)
      - item...                <- 4-space indent = content
  - Actividad profesional      <- main section
      - item...
  - Méritos científicos y de investigación
      - Resumen                <- sub-section at 4-space
          - stat
      - Ponencias...           <- collapsible sub-sections
          1. item
"""
import re, html, sys
from pathlib import Path

# ── Inline Markdown ───────────────────────────────────────────────────────────

def esc(s):
    return html.escape(str(s))

def md_inline(s):
    s = esc(s)
    s = re.sub(r'\*{3}(.+?)\*{3}', r'<strong><em>\1</em></strong>', s)
    s = re.sub(r'\*{2}(.+?)\*{2}', r'<strong>\1</strong>', s)
    s = re.sub(r'\*(.+?)\*', r'<em>\1</em>', s)
    s = re.sub(r'\[([^\]]+)\]\(([^)]+)\)',
               r'<a href="\2" target="_blank" rel="noopener">\1</a>', s)
    return s

# ── Parse raw lines into tokens ───────────────────────────────────────────────

def parse_line(raw):
    """Returns (indent, type, text) — type: 'li', 'li_num', 'h1'–'h4', 'blank', 'p'"""
    line = raw.rstrip('\n')
    stripped = line.strip()
    if not stripped:
        return (0, 'blank', '')
    ind = len(line) - len(line.lstrip(' '))
    # Heading
    m = re.match(r'^(#{1,4})\s+(.*)', stripped)
    if m:
        return (0, f'h{len(m.group(1))}', m.group(2))
    # Numbered list
    m = re.match(r'^(\d+)\.\s+(.*)', stripped)
    if m:
        return (ind, 'li_num', m.group(2))
    # Bullet list
    m = re.match(r'^[-*]\s+(.*)', stripped)
    if m:
        return (ind, 'li', m.group(1))
    return (ind, 'p', stripped)

# ── Render a nested block of tokens to HTML ───────────────────────────────────

def render_block(tokens):
    """Renders tokens to HTML, handling nested lists by indent."""
    out = []
    stack = []  # (indent, ordered)

    def close_until(target_ind):
        while stack and stack[-1][0] >= target_ind:
            lv, od = stack.pop()
            out.append(f'</{"ol" if od else "ul"}>')

    for ind, typ, text in tokens:
        if typ == 'blank':
            continue

        if typ in ('h2', 'h3', 'h4'):
            close_until(0)
            lvl = int(typ[1]) + 1
            out.append(f'<h{lvl} class="cv-sub">{md_inline(text)}</h{lvl}>')
            continue

        if typ == 'p':
            out.append(f'<p class="cv-p">{md_inline(text)}</p>')
            continue

        if typ in ('li', 'li_num'):
            ordered = (typ == 'li_num')
            if not stack or stack[-1][0] < ind:
                depth = len(stack)
                tag = 'ol' if ordered else 'ul'
                out.append(f'<{tag} class="cv-list cv-list-{depth}">')
                stack.append((ind, ordered))
            elif stack[-1][0] > ind:
                close_until(ind)
            out.append(f'<li>{md_inline(text)}</li>')

    close_until(-1)
    return '\n'.join(out)

# ── CSS ───────────────────────────────────────────────────────────────────────

CSS = '''
    :root {
      --azul:       #1a5276;
      --azul-claro: #2980b9;
      --gris-fondo: #f4f6f9;
      --gris-borde: #dce1e8;
      --blanco:     #ffffff;
      --texto:      #2c3e50;
      --texto-sec:  #5d6d7e;
      --verde:      #27ae60;
      --radius:     8px;
    }
    *, *::before, *::after { box-sizing: border-box; margin: 0; padding: 0; }
    body {
      font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif;
      background: var(--gris-fondo);
      color: var(--texto);
      line-height: 1.6;
      -webkit-text-size-adjust: 100%;
    }
    header {
      background: var(--azul);
      color: white;
      padding: 1rem 2rem;
      display: flex;
      align-items: center;
      gap: 1rem;
      box-shadow: 0 2px 8px rgba(0,0,0,0.18);
      position: sticky;
      top: 0;
      z-index: 200;
    }
    header h1 { font-size: 1.2rem; font-weight: 600; }
    header .subtitle { font-size: 0.8rem; opacity: 0.8; }
    .btn-info {
      margin-left: auto;
      flex-shrink: 0;
      background: rgba(255,255,255,0.18);
      border: 1px solid rgba(255,255,255,0.35);
      color: white;
      padding: 0.35rem 0.9rem;
      border-radius: var(--radius);
      cursor: pointer;
      font-size: 0.85rem;
    }
    .btn-info:hover { background: rgba(255,255,255,0.3); }
    .container { max-width: 900px; margin: 0 auto; padding: 1.5rem; }

    /* Profile */
    .profile-card {
      background: var(--blanco);
      border-radius: var(--radius);
      padding: 1.75rem 2rem;
      box-shadow: 0 1px 4px rgba(0,0,0,0.08);
      margin-bottom: 1.5rem;
      border-top: 4px solid var(--azul);
    }
    .profile-name {
      font-size: 1.6rem;
      font-weight: 700;
      color: var(--azul);
      margin-bottom: 0.75rem;
    }
    .profile-detail {
      font-size: 0.88rem;
      color: var(--texto-sec);
      margin-bottom: 0.3rem;
      line-height: 1.5;
    }
    .profile-detail strong { color: var(--texto); }
    .profile-links { margin-top: 1rem; display: flex; gap: 0.6rem; flex-wrap: wrap; }
    .link-chip {
      display: inline-block;
      padding: 0.3rem 0.85rem;
      background: var(--gris-fondo);
      border: 1px solid var(--gris-borde);
      border-radius: 20px;
      font-size: 0.78rem;
      font-weight: 600;
      color: var(--azul-claro);
      text-decoration: none;
      transition: background 0.15s;
    }
    .link-chip:hover { background: #d6eaf8; }

    /* TOC */
    .toc {
      background: var(--blanco);
      border-radius: var(--radius);
      padding: 1rem 1.25rem;
      box-shadow: 0 1px 4px rgba(0,0,0,0.08);
      margin-bottom: 1.5rem;
    }
    .toc-title { font-weight: 700; color: var(--azul); margin-bottom: 0.5rem; font-size: 0.85rem; }
    .toc-links { display: flex; flex-wrap: wrap; gap: 0.4rem; }
    .toc-link {
      padding: 0.2rem 0.65rem;
      border-radius: 12px;
      border: 1px solid var(--gris-borde);
      color: var(--texto-sec);
      text-decoration: none;
      font-size: 0.75rem;
      transition: all 0.15s;
    }
    .toc-link:hover { border-color: var(--azul-claro); color: var(--azul-claro); }

    /* Main section */
    .cv-section {
      background: var(--blanco);
      border-radius: var(--radius);
      box-shadow: 0 1px 4px rgba(0,0,0,0.07);
      margin-bottom: 1.25rem;
      overflow: hidden;
    }
    .cv-section-hdr {
      display: flex;
      align-items: center;
      gap: 0.7rem;
      padding: 1rem 1.25rem;
      background: var(--azul);
      color: white;
    }
    .cv-section-emoji { font-size: 1.1rem; }
    .cv-section-title { font-size: 1rem; font-weight: 700; }
    .cv-section-body { padding: 1.25rem; }

    /* Collapsible sub-section */
    details.cv-sub {
      border: 1px solid var(--gris-borde);
      border-radius: var(--radius);
      margin-bottom: 0.75rem;
      overflow: hidden;
    }
    details.cv-sub summary {
      display: flex;
      align-items: center;
      gap: 0.5rem;
      padding: 0.7rem 1rem;
      background: var(--gris-fondo);
      cursor: pointer;
      font-weight: 600;
      font-size: 0.88rem;
      color: var(--azul);
      list-style: none;
      user-select: none;
    }
    details.cv-sub summary::-webkit-details-marker { display: none; }
    .cv-count {
      background: var(--azul-claro);
      color: white;
      padding: 0.1rem 0.4rem;
      border-radius: 10px;
      font-size: 0.72rem;
      font-weight: 700;
    }
    .cv-chevron { margin-left: auto; font-size: 0.75rem; transition: transform 0.2s; }
    details[open] .cv-chevron { transform: rotate(180deg); }
    .cv-sub-body { padding: 0.75rem 1rem; }

    /* Open sub-section */
    .cv-sub-open {
      border: 1px solid var(--gris-borde);
      border-radius: var(--radius);
      margin-bottom: 0.75rem;
      overflow: hidden;
    }
    .cv-sub-open-hdr {
      padding: 0.7rem 1rem;
      background: var(--gris-fondo);
      font-weight: 600;
      font-size: 0.88rem;
      color: var(--azul);
    }
    .cv-sub-open-body { padding: 0.75rem 1rem; }

    /* Stats grid */
    .stats-grid {
      display: grid;
      grid-template-columns: repeat(auto-fill, minmax(180px, 1fr));
      gap: 0.6rem;
      margin-bottom: 1rem;
    }
    .stat-card {
      background: var(--gris-fondo);
      border: 1px solid var(--gris-borde);
      border-radius: var(--radius);
      padding: 0.6rem 0.9rem;
      text-align: center;
    }
    .stat-number { font-size: 1.5rem; font-weight: 700; color: var(--azul); line-height: 1.2; }
    .stat-label { font-size: 0.72rem; color: var(--texto-sec); margin-top: 0.15rem; }

    /* Content */
    .cv-list { padding-left: 1.4rem; font-size: 0.84rem; line-height: 1.65; color: var(--texto); }
    .cv-list li { margin-bottom: 0.45rem; }
    .cv-list-0 { padding-left: 1.2rem; }
    .cv-list-1 { padding-left: 2rem; margin-top: 0.3rem; list-style-type: circle; }
    .cv-list-2 { padding-left: 2.8rem; margin-top: 0.2rem; list-style-type: disc; }
    .cv-sub { font-size: 0.9rem; font-weight: 600; color: var(--azul); margin: 0.9rem 0 0.4rem; }
    .cv-p { font-size: 0.84rem; color: var(--texto-sec); margin-bottom: 0.4rem; }

    /* Modal */
    .modal-overlay {
      position: fixed; inset: 0;
      background: rgba(0,0,0,0.45);
      display: flex; align-items: center; justify-content: center;
      z-index: 1000; padding: 1rem;
    }
    .modal-overlay.hidden { display: none !important; }
    .modal-box {
      background: var(--blanco);
      border-radius: var(--radius);
      max-width: 420px; width: 100%;
      padding: 1.5rem;
      box-shadow: 0 8px 30px rgba(0,0,0,0.22);
    }
    .modal-box h2 { font-size: 1.05rem; color: var(--azul); margin-bottom: 0.75rem; }
    .modal-box p { font-size: 0.86rem; color: var(--texto-sec); margin-bottom: 0.5rem; line-height: 1.5; }
    .modal-footer {
      margin-top: 1rem; padding-top: 0.75rem;
      border-top: 1px solid var(--gris-borde);
      display: flex; align-items: center; justify-content: space-between;
      font-size: 0.82rem; color: var(--texto-sec);
    }
    .modal-footer a { color: var(--azul-claro); text-decoration: none; }
    .btn-close {
      background: var(--gris-borde); border: none;
      padding: 0.4rem 1rem; border-radius: var(--radius);
      cursor: pointer; font-size: 0.85rem; color: var(--texto);
    }
    .btn-close:hover { background: #c5ccd6; }

    @media (max-width: 600px) {
      header { padding: 0.75rem 1rem; }
      header h1 { font-size: 1rem; }
      .container { padding: 0.9rem; }
      .profile-name { font-size: 1.2rem; }
      .stats-grid { grid-template-columns: repeat(2, 1fr); }
    }
'''

# ── Main logic ────────────────────────────────────────────────────────────────

def build_html(md_path):
    raw_lines = Path(md_path).read_text('utf-8').splitlines(keepends=True)

    # ── 1. Extract personal info block (before first ## ) ─────────────────────
    info_lines = []
    section_start = 0
    for i, raw in enumerate(raw_lines):
        if raw.startswith('## '):
            section_start = i
            break
        info_lines.append(raw.rstrip('\n').strip())

    personal = {}
    detail_items = []
    for line in info_lines:
        if not line or re.match(r'^#', line):
            continue
        m = re.match(r'^###?\s+Nombre:\s*\*{1,2}(.+?)\*{0,2}\s*$', line)
        if m:
            personal['name'] = m.group(1).strip()
            continue
        m = re.match(r'^\[?\*{0,2}(ORCID|LinkedIn|Google\s+Acad[eé]mico|Google\s+Scholar)\*{0,2}\]?\(([^)]+)\)', line)
        if m:
            label = re.sub(r'Acad[eé]mico', 'Scholar', m.group(1)).replace('Google Scholar', 'Google Scholar')
            personal[label] = m.group(2)
            continue
        if 'emiliomonteb@gmail.com' in line:
            personal['email'] = 'emiliomonteb@gmail.com'
            continue
        if line:
            detail_items.append(line)

    # ── 2. Parse remaining into top-level section blocks ──────────────────────
    remaining = raw_lines[section_start:]
    main_sections = []
    current = None
    for raw in remaining:
        line = raw.rstrip('\n')
        m = re.match(r'^- (.+)', line)
        if m:
            if current is not None:
                main_sections.append(current)
            title = re.sub(r'\*{1,3}', '', m.group(1)).strip()
            current = {'title': title, 'lines': []}
            continue
        if current is not None:
            current['lines'].append(raw)
    if current:
        main_sections.append(current)

    # ── 3. Render each main section ───────────────────────────────────────────

    SECTION_EMOJIS = {
        'Formación académica': '🎓',
        'Actividad profesional': '🏥',
        'Méritos científicos y de investigación': '🔬',
    }

    # These 4-space sub-sections are collapsed by default
    COLLAPSED_SUBS = {
        'Ponencias, mesas redondas, conferencias…',
        'Ponencias, mesas redondas, conferencias',
        'Actividad docente',
        'Actividad docente no reglada',
        'Asistencia a Congresos y Jornadas',
    }
    # These 4-space sub-sections contain 8-space sub-sub-sections;
    # show as open container, with each sub-sub individually collapsible
    CONTAINER_SUBS = {'Publicaciones Científicas', 'Otros méritos'}
    # Within container subs, collapse those with many items (>5)
    COLLAPSED_SUBSUBS = {
        'Publicaciones en revistas',
        'Comunicaciones a congresos',
        'Libros',
        'Capítulos de libros',
        'Participación en estudios de investigación',
        'Dirección o coordinación de cursos o jornadas',
    }

    STATS_MAP = {
        'Ponencias': 'Ponencias y conferencias',
        'Actividad docente en Masters': 'Docencia Masters/Cursos',
        'Actividad docente no reglada': 'Docencia no reglada',
        'Publicaciones en revistas': 'Publicaciones',
        'Comunicaciones a congresos': 'Comunicaciones',
        'Capítulos de libros': 'Capítulos de libros',   # must precede 'Libros'
        'Libros': 'Libros',
        'Participación en estudios': 'Estudios investigación',
        'Dirección o coordinación': 'Cursos dirigidos',
    }

    sections_html = []
    toc_items = []

    for sec in main_sections:
        title = sec['title']
        emoji = SECTION_EMOJIS.get(title, '📌')
        sec_id = re.sub(r'\W+', '_', title.lower()).strip('_')
        toc_items.append((sec_id, emoji, title))

        if title == 'Méritos científicos y de investigación':
            sub_sections = []
            cur_sub = None
            for raw in sec['lines']:
                line = raw.rstrip('\n')
                m = re.match(r'^    - (.+)', line)
                if m:
                    if cur_sub is not None:
                        sub_sections.append(cur_sub)
                    sub_title = re.sub(r'\*{1,3}', '', m.group(1)).strip()
                    cur_sub = {'title': sub_title, 'lines': []}
                    continue
                if cur_sub is not None:
                    cur_sub['lines'].append(raw)
            if cur_sub:
                sub_sections.append(cur_sub)

            meritos_html = []

            for sub in sub_sections:
                sub_title = sub['title']
                item_count = sum(
                    1 for r in sub['lines']
                    if re.match(r'^\s+\d+\.', r) or re.match(r'^        - ', r)
                )

                if sub_title == 'Resumen':
                    stats_cards = []
                    for raw in sub['lines']:
                        line = raw.strip()
                        m = re.match(r'^[-*]\s+(.+?):\s*(\d+)', line)
                        if m:
                            label_raw = m.group(1).strip()
                            count = m.group(2)
                            label_display = label_raw
                            for key, lbl in STATS_MAP.items():
                                if key.lower() in label_raw.lower():
                                    label_display = lbl
                                    break
                            stats_cards.append(
                                f'<div class="stat-card">'
                                f'<div class="stat-number">{count}</div>'
                                f'<div class="stat-label">{esc(label_display)}</div>'
                                f'</div>'
                            )
                    meritos_html.append(
                        f'<div class="stats-grid">{"".join(stats_cards)}</div>'
                    )
                    continue

                tokens = [parse_line(r) for r in sub['lines']]
                content_html = render_block(tokens)
                count_span = (f' <span class="cv-count">({item_count})</span>'
                              if item_count > 0 else '')
                sub_id = re.sub(r'\W+', '_', sub_title.lower()).strip('_')

                if sub_title in CONTAINER_SUBS:
                    # Split at 8-space bullets that are sub-sub-section headers
                    subsub_sections = []
                    cur_ss = None
                    for raw in sub['lines']:
                        line = raw.rstrip('\n')
                        # 8-space bullet = potential sub-sub header
                        m = re.match(r'^        - (.+)', line)
                        if m:
                            text = m.group(1).strip()
                            # Sub-sub header: short, not bold/quoted, not a list item
                            is_header = (
                                len(text) < 70
                                and not text.startswith('**')
                                and not text.startswith('"')
                                and not re.match(r'^\d', text)
                            )
                            if is_header:
                                if cur_ss is not None:
                                    subsub_sections.append(cur_ss)
                                cur_ss = {'title': text, 'lines': []}
                                continue
                        if cur_ss is not None:
                            cur_ss['lines'].append(raw)
                    if cur_ss:
                        subsub_sections.append(cur_ss)

                    subsub_html = []
                    for ss in subsub_sections:
                        ss_title = ss['title']
                        ss_items = sum(1 for r in ss['lines']
                                       if re.match(r'^\s+\d+\.', r)
                                       or re.match(r'^\s+- .', r))
                        ss_tokens = [parse_line(r) for r in ss['lines']]
                        ss_content = render_block(ss_tokens)
                        ss_count = (f' <span class="cv-count">({ss_items})</span>'
                                    if ss_items > 0 else '')
                        ss_id = re.sub(r'\W+', '_', ss_title.lower()).strip('_')
                        if ss_title in COLLAPSED_SUBSUBS:
                            subsub_html.append(f'''
<details class="cv-sub" id="{ss_id}">
  <summary>
    {esc(ss_title)}{ss_count}
    <span class="cv-chevron">▼</span>
  </summary>
  <div class="cv-sub-body">{ss_content}</div>
</details>''')
                        else:
                            subsub_html.append(f'''
<div class="cv-sub-open" id="{ss_id}">
  <div class="cv-sub-open-hdr">{esc(ss_title)}</div>
  <div class="cv-sub-open-body">{ss_content}</div>
</div>''')

                    meritos_html.append(f'''
<div class="cv-sub-open" id="{sub_id}">
  <div class="cv-sub-open-hdr">{esc(sub_title)}</div>
  <div class="cv-sub-open-body">{"".join(subsub_html)}</div>
</div>''')

                elif sub_title in COLLAPSED_SUBS:
                    meritos_html.append(f'''
<details class="cv-sub" id="{sub_id}">
  <summary>
    {esc(sub_title)}{count_span}
    <span class="cv-chevron">▼</span>
  </summary>
  <div class="cv-sub-body">{content_html}</div>
</details>''')
                else:
                    meritos_html.append(f'''
<div class="cv-sub-open" id="{sub_id}">
  <div class="cv-sub-open-hdr">{esc(sub_title)}</div>
  <div class="cv-sub-open-body">{content_html}</div>
</div>''')

            body_html = '\n'.join(meritos_html)

        else:
            tokens = [parse_line(r) for r in sec['lines']]
            body_html = render_block(tokens)

        sections_html.append(f'''
<div class="cv-section" id="{sec_id}">
  <div class="cv-section-hdr">
    <span class="cv-section-emoji">{emoji}</span>
    <span class="cv-section-title">{esc(title)}</span>
  </div>
  <div class="cv-section-body">
    {body_html}
  </div>
</div>''')

    # ── 4. Profile + TOC ──────────────────────────────────────────────────────
    name = personal.get('name', 'EMILIO MONTE BOQUET')
    detail_html = '\n'.join(
        f'<p class="profile-detail">{md_inline(d)}</p>'
        for d in detail_items if d.strip()
    )
    links_html = ''
    for label, key in [('🔬 ORCID', 'ORCID'), ('💼 LinkedIn', 'LinkedIn'), ('🎓 Google Scholar', 'Google Scholar')]:
        if key in personal:
            links_html += f'<a href="{esc(personal[key])}" class="link-chip" target="_blank" rel="noopener">{label}</a>\n'
    if 'email' in personal:
        links_html += f'<a href="mailto:{personal["email"]}" class="link-chip">✉ {personal["email"]}</a>\n'

    toc_html = ' '.join(
        f'<a href="#{sid}" class="toc-link" onclick="scrollToSec(\'{sid}\'); return false;">{em} {esc(t)}</a>'
        for sid, em, t in toc_items
    )

    # ── 5. Full HTML ──────────────────────────────────────────────────────────
    return f'''<!DOCTYPE html>
<html lang="es">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0, maximum-scale=1.0, user-scalable=no, viewport-fit=cover">
  <title>CV — Emilio Monte Boquet</title>
  <style>
{CSS}
  </style>
</head>
<body>

<header>
  <div>
    <h1>📄 Curriculum Vitae</h1>
    <span class="subtitle">Emilio Monte Boquet</span>
  </div>
  <button class="btn-info" onclick="toggleModal(true)">ℹ Acerca de</button>
</header>

<div class="container">

  <div class="profile-card">
    <div class="profile-name">{esc(name)}</div>
    {detail_html}
    <div class="profile-links">
      {links_html}
    </div>
  </div>

  <div class="toc">
    <div class="toc-title">Ir a sección:</div>
    <div class="toc-links">{toc_html}</div>
  </div>

  {''.join(sections_html)}

</div>

<div class="modal-overlay hidden" id="modal" onclick="if(event.target===this) toggleModal(false)">
  <div class="modal-box">
    <h2>📄 CV — Emilio Monte Boquet</h2>
    <p>Versión HTML del Curriculum Vitae, generada a partir de la exportación de Notion.</p>
    <p>Las secciones con listados extensos (ponencias, publicaciones, comunicaciones…) están <strong>colapsadas por defecto</strong>. Haz clic en cada encabezado para expandirlas.</p>
    <div class="modal-footer">
      <span>Creado por <a href="https://www.linkedin.com/in/emilio-monte-boquet" target="_blank" rel="noopener">EMB</a></span>
      <button class="btn-close" onclick="toggleModal(false)">Cerrar</button>
    </div>
  </div>
</div>

<script>
function toggleModal(show) {{
  document.getElementById('modal').classList.toggle('hidden', !show);
}}
function scrollToSec(id) {{
  const el = document.getElementById(id);
  if (el) el.scrollIntoView({{behavior: 'smooth', block: 'start'}});
}}
document.addEventListener('keydown', e => {{ if (e.key === 'Escape') toggleModal(false); }});
</script>
</body>
</html>'''

if __name__ == '__main__':
    md = sys.argv[1] if len(sys.argv) > 1 else \
        '/Users/emiliom/Archivos de trabajo/CV_EMB/Curriculum vitae 523dcee5a9f14081a01edb55dd7f9ef2.md'
    out = Path(md).parent / 'curriculum_vitae.html'
    html_content = build_html(md)
    out.write_text(html_content, 'utf-8')
    kb = len(html_content) // 1024
    print(f'✓ Generado: {out}  ({kb} KB)')
