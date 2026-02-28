import warnings
warnings.filterwarnings("ignore", message="urllib3.*doesn't match a supported version")

import flet as ft
import threading
import os
import time
from datetime import datetime

import downloader
import transcriber
import analyzer
import vault

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DOWNLOADS_DIR = os.path.join(BASE_DIR, "downloads")

DEFAULT_ANALYSIS_PROMPT = """\
Przeanalizuj tę transkrypcję wideo o technologii/AI. Podaj:

1. **Ocena treści** — czy materiał jest wartościowy, czy to głównie hype? Jakość argumentów.
2. **Kluczowe insighty** — co nowego lub interesującego wnosi? Główne tezy.
3. **Praktyczne zastosowania** — konkretne use cases, narzędzia, techniki.
4. **Realne możliwości vs. obietnice** — co naprawdę działa, a co jest przesadzone?
5. **Wymagane kompetencje** — jakie ludzkie umiejętności są potrzebne, żeby skorzystać?
6. **Wnioski** — czy warto się tym zająć? Dla kogo jest ten materiał?

Bądź konkretny i krytyczny. Nie powtarzaj treści — analizuj i oceniaj."""


def _versioned_path(base_path, suffix=""):
    """
    Generate a versioned file path: <name><suffix>_YYYYMMDD_HHmm.txt
    Example: downloads/Video Title_analiza_20260228_1430.txt
    """
    stem = os.path.splitext(base_path)[0]
    timestamp = datetime.now().strftime("%Y%m%d_%H%M")
    return f"{stem}{suffix}_{timestamp}.txt"


def main(page: ft.Page):
    page.title = "Audio Studio"
    page.window = ft.Window(width=1060, height=700, resizable=False, maximizable=False,
                             icon="assets/icon.png")
    page.theme_mode = ft.ThemeMode.LIGHT
    page.bgcolor = "#F4F5F7"
    page.padding = 0

    # ── Palette ──
    ACC = "#6366F1"
    ACC2 = "#8B5CF6"
    SURF = "#FFFFFF"
    T1 = "#111827"
    T2 = "#6B7280"
    T3 = "#9CA3AF"
    BRD = "#E5E7EB"
    OK = "#10B981"
    ERR = "#EF4444"

    page.fonts = {
        "Inter": "https://github.com/rsms/inter/raw/master/docs/font-files/Inter-Regular.woff2",
        "Inter-Medium": "https://github.com/rsms/inter/raw/master/docs/font-files/Inter-Medium.woff2",
        "Inter-Bold": "https://github.com/rsms/inter/raw/master/docs/font-files/Inter-Bold.woff2",
        "Mono": "https://github.com/JetBrains/JetBrainsMono/raw/master/fonts/webfonts/JetBrainsMono-Regular.woff2",
    }
    page.theme = ft.Theme(font_family="Inter", color_scheme_seed=ACC)

    is_processing = False
    current_transcript = ""
    current_analysis = ""
    last_mp3_path = ""

    # ── Helpers ──
    # Note: UI-facing strings (labels, hints, status text) are in Polish.
    def label_row(text):
        return ft.Text(text, size=10, weight=ft.FontWeight.W_600, color=T3,
                       font_family="Inter-Medium", style=ft.TextStyle(letter_spacing=0.4))

    def _hover(e, c):
        c.scale = 1.01 if e.data == "true" else 1.0
        c.update()

    def make_btn(text, icon, on_click, colors=None):
        if not colors:
            colors = [ACC, ACC2]
        return ft.Container(
            content=ft.Row([
                ft.Icon(icon, color="white", size=14),
                ft.Text(text, color="white", size=12, weight=ft.FontWeight.W_600, font_family="Inter-Bold")
            ], alignment=ft.MainAxisAlignment.CENTER, spacing=5),
            gradient=ft.LinearGradient(begin=ft.Alignment(-1, 0), end=ft.Alignment(1, 0), colors=colors),
            height=38, border_radius=8, on_click=on_click,
            animate_opacity=ft.Animation(200, "easeOut"),
            animate_scale=ft.Animation(80, "easeOutCubic"),
            on_hover=lambda e: _hover(e, e.control),
        )

    # ══════════════════════════════════════════
    #  SIDEBAR
    # ══════════════════════════════════════════

    # ── API Key ──
    saved_key = vault.load_key()
    key_input = ft.TextField(
        value=saved_key, password=True, can_reveal_password=True,
        hint_text="sk-or-...", border_radius=6, border_color="#D1D5DB",
        focused_border_color=ACC, bgcolor="#F9FAFB", focused_bgcolor=SURF,
        content_padding=ft.Padding(left=10, right=4, top=8, bottom=8),
        text_size=11, hint_style=ft.TextStyle(color=T3, size=11),
        on_change=lambda _: update_key_status(),
        on_blur=lambda _: save_api_key(),
        on_submit=lambda _: save_api_key(),
    )
    key_status = ft.Text("✓ Zapisany" if saved_key else "", size=10, color=OK)

    def save_api_key():
        k = key_input.value.strip()
        if not k:
            return
        # Validate key format — OpenRouter keys start with "sk-or-"
        if not k.startswith("sk-or-"):
            saved = vault.load_key()
            if saved:
                key_input.value = saved
                key_status.value = "⚠ To nie klucz API — przywrócono"
                key_status.color = ERR
            else:
                key_input.value = ""
                key_status.value = "⚠ Klucz musi zaczynać się od sk-or-"
                key_status.color = ERR
            page.update()
            return
        saved = vault.load_key()
        if k != saved:
            vault.save_key(k)
        key_status.value = "✓ Zapisany"
        key_status.color = OK
        page.update()

    def update_key_status():
        k = key_input.value.strip()
        saved = vault.load_key()
        if k and k == saved:
            key_status.value = "✓ Zapisany"
            key_status.color = OK
        elif k and not k.startswith("sk-or-"):
            key_status.value = "⚠ Klucz musi zaczynać się od sk-or-"
            key_status.color = ERR
        elif k:
            key_status.value = "Niezapisany — kliknij poza pole"
            key_status.color = T3
        else:
            key_status.value = ""
        page.update()

    # ── Source controls ──
    url_input = ft.TextField(
        hint_text="https://youtube.com/watch?v=...",
        border_radius=8, border_color="#D1D5DB", focused_border_color=ACC,
        bgcolor="#F9FAFB", focused_bgcolor=SURF,
        content_padding=ft.Padding(left=12, right=12, top=10, bottom=10),
        text_size=13, prefix_icon=ft.Icons.LINK,
        hint_style=ft.TextStyle(color=T3, size=12),
    )
    lang_dd = ft.Dropdown(
        value="auto", border_radius=8, border_color="#D1D5DB", focused_border_color=ACC,
        content_padding=8, text_size=12, height=44, expand=True,
        options=[ft.dropdown.Option("auto", "Auto"), ft.dropdown.Option("pl", "Polski"), ft.dropdown.Option("en", "English")],
        label="Język", label_style=ft.TextStyle(size=11, color=T3),
    )
    model_dd = ft.Dropdown(
        value="base", border_radius=8, border_color="#D1D5DB", focused_border_color=ACC,
        content_padding=8, text_size=12, height=44, expand=True,
        options=[ft.dropdown.Option("base", "Szybki"), ft.dropdown.Option("small", "Średni"), ft.dropdown.Option("medium", "Dokładny")],
        label="Jakość", label_style=ft.TextStyle(size=11, color=T3),
    )
    context_input = ft.TextField(
        hint_text="Nazwy własne, slang... (opcjonalnie)",
        border_radius=8, border_color="#D1D5DB", focused_border_color=ACC,
        bgcolor="#F9FAFB", focused_bgcolor=SURF,
        content_padding=ft.Padding(left=12, right=12, top=8, bottom=8),
        text_size=11, hint_style=ft.TextStyle(color=T3, size=11),
    )

    transcribe_btn = make_btn("Transkrybuj", ft.Icons.MIC_ROUNDED, lambda _: run_transcribe())

    # ── Analysis prompt ──
    analysis_prompt = ft.TextField(
        hint_text="Domyślnie: ocena, insighty, use cases, krytyka...\nWpisz własne polecenie, żeby zastąpić.",
        border_radius=8, border_color="#D1D5DB", focused_border_color=ACC,
        bgcolor="#F9FAFB", focused_bgcolor=SURF,
        content_padding=ft.Padding(left=12, right=12, top=8, bottom=8),
        text_size=11, multiline=True, min_lines=2, max_lines=4,
        hint_style=ft.TextStyle(color=T3, size=11),
    )
    analyze_btn = make_btn("Opracuj z AI", ft.Icons.AUTO_AWESOME, lambda _: run_analysis(), colors=["#8B5CF6", "#A78BFA"])

    # ── Step tracker ──
    STEP_PENDING = 0
    STEP_ACTIVE = 1
    STEP_DONE = 2
    STEP_ERROR = 3

    def make_step_row(name):
        icon = ft.Icon(ft.Icons.CIRCLE_OUTLINED, color=BRD, size=10)
        text = ft.Text(name, size=11, color=T3)
        detail = ft.Text("", size=10, color=T3)
        return {"icon": icon, "text": text, "detail": detail,
                "row": ft.Row([icon, text, detail], spacing=6)}

    step_download = make_step_row("Pobieranie")
    step_transcribe = make_step_row("Transkrypcja")
    step_analyze = make_step_row("Analiza AI")
    steps = [step_download, step_transcribe, step_analyze]

    def set_step(step, state, detail=""):
        s = steps[step]
        s["detail"].value = detail
        if state == STEP_PENDING:
            s["icon"].name = ft.Icons.CIRCLE_OUTLINED
            s["icon"].color = BRD
            s["text"].color = T3
            s["detail"].color = T3
        elif state == STEP_ACTIVE:
            s["icon"].name = ft.Icons.PENDING
            s["icon"].color = ACC
            s["text"].color = T1
            s["detail"].color = T3
        elif state == STEP_DONE:
            s["icon"].name = ft.Icons.CHECK_CIRCLE
            s["icon"].color = OK
            s["text"].color = T2
            s["detail"].color = OK
        elif state == STEP_ERROR:
            s["icon"].name = ft.Icons.ERROR_OUTLINE
            s["icon"].color = ERR
            s["text"].color = ERR
            s["detail"].color = ERR

    def reset_steps():
        for i in range(3):
            set_step(i, STEP_PENDING)

    step_section = ft.Container(
        content=ft.Column([
            ft.Divider(height=1, color=BRD),
            ft.Container(height=8),
            step_download["row"],
            step_transcribe["row"],
            step_analyze["row"],
        ], spacing=4),
    )

    # ── Sidebar layout ──
    sidebar = ft.Container(
        content=ft.Column([
            # API Key — compact
            ft.Row([
                ft.Icon(ft.Icons.KEY_ROUNDED, color=T3, size=12),
                label_row("KLUCZ OPENROUTER"),
            ], spacing=4),
            ft.Container(height=4),
            key_input,
            ft.Container(content=key_status, padding=ft.Padding(left=2, right=0, top=2, bottom=0)),

            ft.Container(height=12),
            ft.Divider(height=1, color=BRD),
            ft.Container(height=12),

            # Source
            label_row("ŹRÓDŁO"),
            ft.Container(height=5),
            url_input,
            ft.Container(height=6),
            ft.Row([lang_dd, model_dd], spacing=8),
            ft.Container(height=6),
            context_input,
            ft.Container(height=10),
            transcribe_btn,

            ft.Container(height=12),
            ft.Divider(height=1, color=BRD),
            ft.Container(height=12),

            # Analysis
            label_row("POLECENIE DLA AI"),
            ft.Container(height=5),
            analysis_prompt,
            ft.Container(height=8),
            analyze_btn,

            # Push steps to bottom
            ft.Container(expand=True),
            step_section,
        ], spacing=0, expand=True, scroll=ft.ScrollMode.AUTO),
        width=310, bgcolor=SURF,
        padding=ft.Padding(left=16, right=16, top=14, bottom=12),
        border=ft.Border(right=ft.BorderSide(1, BRD)),
    )

    # ══════════════════════════════════════════
    #  MAIN AREA
    # ══════════════════════════════════════════
    active_tab = 0

    # ── Transcript view ──
    transcript_field = ft.TextField(
        value="", read_only=True, multiline=True,
        min_lines=20, max_lines=200, expand=True,
        border_radius=0, border_color="transparent",
        text_size=14, text_style=ft.TextStyle(height=1.7),
        bgcolor="transparent", content_padding=0,
    )
    transcript_view = ft.Container(content=transcript_field, expand=True, visible=True,
                                   padding=ft.Padding(left=4, right=4, top=0, bottom=0))

    # ── Analysis view ──
    analysis_field = ft.TextField(
        value="", read_only=True, multiline=True,
        min_lines=20, max_lines=200, expand=True,
        border_radius=0, border_color="transparent",
        text_size=14, text_style=ft.TextStyle(height=1.7),
        bgcolor="transparent", content_padding=0,
    )
    analysis_view = ft.Container(content=analysis_field, expand=True, visible=False,
                                  padding=ft.Padding(left=4, right=4, top=0, bottom=0))

    # ── Empty state ──
    empty_state = ft.Container(
        content=ft.Column([
            ft.Icon(ft.Icons.GRAPHIC_EQ_ROUNDED, color=BRD, size=40),
            ft.Container(height=8),
            ft.Text("Wklej link i kliknij Transkrybuj", size=14, color=T3, weight=ft.FontWeight.W_500),
            ft.Text("Wynik pojawi się tutaj.", size=12, color=T3),
        ], alignment=ft.MainAxisAlignment.CENTER, horizontal_alignment=ft.CrossAxisAlignment.CENTER, spacing=3),
        expand=True, alignment=ft.alignment.Alignment(0, 0),
    )

    analysis_empty = ft.Container(
        content=ft.Column([
            ft.Icon(ft.Icons.AUTO_AWESOME, color=BRD, size=40),
            ft.Container(height=8),
            ft.Text("Wpisz polecenie i kliknij Opracuj z AI", size=14, color=T3, weight=ft.FontWeight.W_500),
            ft.Text("Analiza transkrypcji pojawi się tutaj.", size=12, color=T3),
        ], alignment=ft.MainAxisAlignment.CENTER, horizontal_alignment=ft.CrossAxisAlignment.CENTER, spacing=3),
        expand=True, alignment=ft.alignment.Alignment(0, 0), visible=False,
    )

    # ── Tab switch ──
    def make_tab_btn(label, idx):
        t = ft.Text(label, size=12, weight=ft.FontWeight.W_600, color=T1 if idx == 0 else T3)
        c = ft.Container(
            content=t, padding=ft.Padding(left=14, right=14, top=7, bottom=7),
            border_radius=6, bgcolor=SURF if idx == 0 else "transparent",
            on_click=lambda _: switch_tab(idx), ink=True,
            animate=ft.Animation(150, "easeOut"),
        )
        return {"text": t, "container": c}

    tab_transcript = make_tab_btn("Transkrypcja", 0)
    tab_analysis = make_tab_btn("Opracowanie", 1)

    def switch_tab(idx):
        nonlocal active_tab
        active_tab = idx
        # Tab visuals
        tab_transcript["text"].color = T1 if idx == 0 else T3
        tab_transcript["container"].bgcolor = SURF if idx == 0 else "transparent"
        tab_analysis["text"].color = T1 if idx == 1 else T3
        tab_analysis["container"].bgcolor = SURF if idx == 1 else "transparent"
        # Content
        transcript_view.visible = (idx == 0)
        analysis_view.visible = (idx == 1)
        empty_state.visible = (idx == 0 and not current_transcript)
        analysis_empty.visible = (idx == 1 and not current_analysis)
        # Meta
        char_count.value = f"{len(current_transcript):,} zn.".replace(",", " ") if idx == 0 and current_transcript else \
                           f"{len(current_analysis):,} zn.".replace(",", " ") if idx == 1 and current_analysis else ""
        copy_btn.visible = bool(current_transcript if idx == 0 else current_analysis)
        export_btn.visible = bool(current_transcript if idx == 0 else current_analysis)
        page.update()

    tab_bar = ft.Container(
        content=ft.Row([tab_transcript["container"], tab_analysis["container"]], spacing=2),
        bgcolor="#F3F4F6", border_radius=8, padding=3,
    )

    # ── Header actions ──
    char_count = ft.Text("", size=10, color=T3)
    copy_btn = ft.Container(
        content=ft.Row([ft.Icon(ft.Icons.COPY_ROUNDED, color=T3, size=13),
                        ft.Text("Kopiuj", size=11, color=T3, weight=ft.FontWeight.W_500)], spacing=4, tight=True),
        on_click=lambda _: do_copy(), ink=True, border_radius=6,
        padding=ft.Padding(left=8, right=8, top=4, bottom=4), visible=False,
    )
    export_btn = ft.Container(
        content=ft.Row([ft.Icon(ft.Icons.SAVE_ALT_ROUNDED, color=T3, size=13),
                        ft.Text("Eksport .txt", size=11, color=T3, weight=ft.FontWeight.W_500)], spacing=4, tight=True),
        on_click=lambda _: do_export(), ink=True, border_radius=6,
        padding=ft.Padding(left=8, right=8, top=4, bottom=4), visible=False,
    )

    def do_copy():
        text = current_transcript if active_tab == 0 else current_analysis
        if text:
            page.set_clipboard(text)
            copy_btn.content.controls[1].value = "✓"
            copy_btn.content.controls[1].color = OK
            page.update()
            def reset(_=None):
                copy_btn.content.controls[1].value = "Kopiuj"
                copy_btn.content.controls[1].color = T3
                page.update()
            threading.Thread(target=lambda: (time.sleep(1), page.run_thread(reset)), daemon=True).start()

    def do_export():
        text = current_transcript if active_tab == 0 else current_analysis
        suffix = "" if active_tab == 0 else "_analiza"
        if text and last_mp3_path:
            path = _versioned_path(last_mp3_path, suffix)
            with open(path, "w", encoding="utf-8") as f:
                f.write(text)
            export_btn.content.controls[1].value = f"✓ {os.path.basename(path)}"
            export_btn.content.controls[1].color = OK
            page.update()
            def reset(_=None):
                export_btn.content.controls[1].value = "Eksport .txt"
                export_btn.content.controls[1].color = T3
                page.update()
            threading.Thread(target=lambda: (time.sleep(2), page.run_thread(reset)), daemon=True).start()

    # ── Main header ──
    main_header = ft.Container(
        content=ft.Row([
            tab_bar,
            ft.Row([char_count, copy_btn, export_btn], spacing=6),
        ], alignment=ft.MainAxisAlignment.SPACE_BETWEEN, vertical_alignment=ft.CrossAxisAlignment.CENTER),
        padding=ft.Padding(left=16, right=12, top=10, bottom=8),
        border=ft.Border(bottom=ft.BorderSide(1, BRD)),
    )

    main_area = ft.Container(
        content=ft.Column([
            main_header,
            ft.Container(
                content=ft.Stack([empty_state, analysis_empty, transcript_view, analysis_view], expand=True),
                expand=True, padding=ft.Padding(left=20, right=20, top=10, bottom=10),
            ),
        ], spacing=0, expand=True),
        expand=True, bgcolor=SURF,
    )

    # ══════════════════════════════════════════
    #  LOGIC
    # ══════════════════════════════════════════
    def set_processing(active):
        nonlocal is_processing
        is_processing = active
        transcribe_btn.opacity = 0.5 if active else 1.0
        analyze_btn.opacity = 0.5 if active else 1.0
        page.update()

    def run_transcribe():
        if is_processing:
            return
        url = url_input.value.strip()
        if not url:
            set_step(0, STEP_ERROR, "Brak URL")
            page.update()
            return

        nonlocal current_transcript, last_mp3_path
        set_processing(True)
        reset_steps()
        current_transcript = ""
        transcript_field.value = ""
        empty_state.visible = True
        transcript_view.visible = True
        copy_btn.visible = False
        export_btn.visible = False
        char_count.value = ""
        switch_tab(0)

        def work():
            nonlocal current_transcript, last_mp3_path
            timer_running = threading.Event()
            # Shared phase text — only timer reads it and calls page.update()
            phase_text = [""]

            def set_phase(msg):
                """Set current phase description (timer merges it with elapsed time)."""
                phase_text[0] = msg

            def start_timer(step_idx):
                """Live elapsed timer — sole owner of detail updates + page.update()."""
                timer_running.set()
                t_start = time.time()
                def tick():
                    while timer_running.is_set():
                        elapsed = int(time.time() - t_start)
                        phase = phase_text[0]
                        if phase:
                            steps[step_idx]["detail"].value = f"{phase} · {elapsed}s"
                        else:
                            steps[step_idx]["detail"].value = f"{elapsed}s"
                        try:
                            page.update()
                        except Exception:
                            break
                        time.sleep(1)
                threading.Thread(target=tick, daemon=True).start()
                return t_start

            def stop_timer():
                timer_running.clear()

            # Step 1: Download
            set_step(0, STEP_ACTIVE)
            set_phase("Connecting...")
            page.update()
            t0 = start_timer(0)

            download_error_msg = ""

            def on_download_progress(pct, msg):
                set_phase(msg)

            def on_download_log(msg):
                nonlocal download_error_msg
                if "error" in msg.lower() or "Error" in msg:
                    download_error_msg = msg

            mp3 = downloader.download_audio_as_mp3(
                url, output_path=DOWNLOADS_DIR,
                log_fn=on_download_log,
                progress_fn=on_download_progress,
            )
            stop_timer()
            dt = f"{time.time() - t0:.0f}s"
            if not mp3:
                detail = download_error_msg or "Nie udało się"
                set_step(0, STEP_ERROR, detail)
                page.run_thread(set_processing, False)
                return
            set_step(0, STEP_DONE, dt)
            last_mp3_path = mp3
            page.update()

            # Step 2: Transcribe
            set_step(1, STEP_ACTIVE)
            set_phase("Starting...")
            page.update()
            t0 = start_timer(1)
            lang_val = None if lang_dd.value == "auto" else lang_dd.value
            ctx = context_input.value.strip() or None

            def on_transcribe_phase(msg):
                set_phase(msg)

            text = transcriber.transcribe_audio(
                mp3, language=lang_val, model_size=model_dd.value,
                initial_prompt=ctx, phase_fn=on_transcribe_phase,
            )
            stop_timer()
            dt = f"{time.time() - t0:.0f}s"
            if not text:
                set_step(1, STEP_ERROR, "Brak wyniku")
                page.run_thread(set_processing, False)
                return
            set_step(1, STEP_DONE, dt)

            current_transcript = text
            transcript_field.value = text
            empty_state.visible = False
            copy_btn.visible = True
            export_btn.visible = True
            char_count.value = f"{len(text):,} zn.".replace(",", " ")

            # Auto-save transcript (versioned with date)
            txt_path = _versioned_path(mp3)
            with open(txt_path, "w", encoding="utf-8") as f:
                f.write(text)

            page.run_thread(set_processing, False)

        threading.Thread(target=work, daemon=True).start()

    def run_analysis():
        if is_processing:
            return
        if not current_transcript:
            set_step(2, STEP_ERROR, "Najpierw transkrybuj")
            page.update()
            return
        prompt = analysis_prompt.value.strip() or DEFAULT_ANALYSIS_PROMPT
        api_key = key_input.value.strip()
        if not api_key:
            set_step(2, STEP_ERROR, "Brak klucza API")
            page.update()
            return

        nonlocal current_analysis
        set_processing(True)
        txt_len = f"{len(current_transcript):,}".replace(",", " ")
        set_step(2, STEP_ACTIVE)
        page.update()

        def work():
            nonlocal current_analysis
            timer_running = threading.Event()
            phase_text = [""]

            def set_phase(msg):
                phase_text[0] = msg

            timer_running.set()
            t0 = time.time()
            def tick():
                while timer_running.is_set():
                    elapsed = int(time.time() - t0)
                    phase = phase_text[0]
                    if phase:
                        steps[2]["detail"].value = f"{phase} · {elapsed}s"
                    else:
                        steps[2]["detail"].value = f"{elapsed}s"
                    try:
                        page.update()
                    except Exception:
                        break
                    time.sleep(1)
            threading.Thread(target=tick, daemon=True).start()

            set_phase(f"Sending {txt_len} chars...")

            def on_analyze_log(msg):
                if "Sending" in msg:
                    set_phase("Waiting for response...")
                elif "Response" in msg:
                    set_phase("Processing...")

            result = analyzer.analyze_text(current_transcript, prompt, api_key, log_fn=on_analyze_log)
            timer_running.clear()
            dt = f"{time.time() - t0:.1f}s"
            if not result:
                set_step(2, STEP_ERROR, "Błąd API")
                page.run_thread(set_processing, False)
                return
            set_step(2, STEP_DONE, dt)
            current_analysis = result
            analysis_field.value = result
            analysis_empty.visible = False

            # Auto-save analysis (versioned with date)
            if last_mp3_path:
                path = _versioned_path(last_mp3_path, "_analiza")
                with open(path, "w", encoding="utf-8") as f:
                    f.write(result)

            page.run_thread(set_processing, False)
            page.run_thread(switch_tab, 1)

        threading.Thread(target=work, daemon=True).start()

    # ── Layout ──
    body = ft.Row([sidebar, main_area], expand=True, spacing=0)
    page.add(body)


if __name__ == "__main__":
    ft.run(main)
