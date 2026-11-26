#!/usr/bin/env python3
"""
Kinetic 24fps Motion-Graphics Video Renderer for EC Grammar Studio (Packet 4)
Uses:
  - edge-tts (zh-CN-XiaoxiaoNeural) for natural neural AI voiceover (SAPI5 fallback if offline)
  - Pillow + NumPy for real frame-by-frame 24fps motion graphics:
      * Physics-driven sliding word blocks (combine_slide)
      * Animated Bezier arrows, red strikethroughs & morphing relative pronouns
      * Trap shake + crimson X + emerald fix (trap_smash)
      * Animated option-by-option scanner (multi_scanner)
      * Branching animated mind-map curves (mindmap_grow)
      * Real-time audio-reactive waveform visualizer + synced subtitle captions
  - FFmpeg rawvideo pipe -> compact H.264/AAC MP4 saved to static/videos/ and docs/videos/
"""

import argparse
import asyncio
import math
import os
import re
import shutil
import subprocess
import sys
import tempfile
import wave
import numpy as np
from PIL import Image, ImageDraw, ImageFont

W, H = 960, 540
FPS = 24
FONT_REG = "C:/Windows/Fonts/msyh.ttc"
FONT_BOLD = "C:/Windows/Fonts/msyhbd.ttc"
STATIC_VIDEOS_DIR = os.path.join("static", "videos")
DOCS_VIDEOS_DIR = os.path.join("docs", "videos")

# ----------------- Easing & Math Helpers -----------------
def clamp01(x):
    return 0.0 if x < 0.0 else (1.0 if x > 1.0 else x)

def ease_out_cubic(t):
    t = clamp01(t)
    return 1.0 - (1.0 - t) ** 3

def ease_in_out_cubic(t):
    t = clamp01(t)
    return 4 * t * t * t if t < 0.5 else 1 - ((-2 * t + 2) ** 3) / 2

def ease_out_back(t):
    t = clamp01(t)
    c1 = 1.70158
    c3 = c1 + 1
    return 1 + c3 * ((t - 1) ** 3) + c1 * ((t - 1) ** 2)

def lerp(a, b, t):
    return a + (b - a) * t

def seg_p(progress, start, end):
    if end <= start:
        return 1.0
    return clamp01((progress - start) / (end - start))

def load_font(path, size):
    try:
        return ImageFont.truetype(path, size)
    except Exception:
        return ImageFont.load_default()

F_XXS = load_font(FONT_REG, 12)
F_XS = load_font(FONT_REG, 14)
F_XS_B = load_font(FONT_BOLD, 14)
F_SM = load_font(FONT_REG, 16)
F_SM_B = load_font(FONT_BOLD, 16)
F_MD = load_font(FONT_REG, 20)
F_MD_B = load_font(FONT_BOLD, 20)
F_LG_B = load_font(FONT_BOLD, 24)
F_XL_B = load_font(FONT_BOLD, 28)

def fit_font(draw, text, fonts, max_w):
    for fnt in fonts:
        if text_size(draw, text, fnt)[0] <= max_w:
            return fnt
    return fonts[-1]

def make_orb_sprite(radius, color_rgb, max_alpha):
    size = radius * 2
    yy, xx = np.mgrid[0:size, 0:size]
    dist = np.sqrt((xx - radius) ** 2 + (yy - radius) ** 2) / float(radius)
    falloff = np.clip(1.0 - dist, 0.0, 1.0) ** 2.2
    alpha = (falloff * max_alpha).astype(np.uint8)
    rgb = np.zeros((size, size, 3), dtype=np.uint8)
    rgb[:, :, 0] = color_rgb[0]
    rgb[:, :, 1] = color_rgb[1]
    rgb[:, :, 2] = color_rgb[2]
    return Image.fromarray(rgb, mode="RGB"), Image.fromarray(alpha, mode="L")

ORB_BLUE_RGB, ORB_BLUE_A = make_orb_sprite(190, (56, 189, 248), 42)
ORB_GREEN_RGB, ORB_GREEN_A = make_orb_sprite(170, (16, 185, 129), 34)
ORB_PURPLE_RGB, ORB_PURPLE_A = make_orb_sprite(150, (139, 92, 246), 28)

def text_size(draw, text, font):
    bb = draw.textbbox((0, 0), text, font=font)
    return (bb[2] - bb[0], bb[3] - bb[1])

def wrap_text(draw, text, font, max_w):
    lines = []
    for raw in str(text).split("\n"):
        if not raw:
            lines.append("")
            continue
        tokens = re.findall(r"[A-Za-z0-9'\"().,!?;:\[\]/\-]+|\s+|.", raw)
        cur = ""
        for tok in tokens:
            test = cur + tok
            w, _ = text_size(draw, test, font)
            if w <= max_w or not cur:
                cur = test
            else:
                lines.append(cur.strip())
                cur = tok.lstrip()
        if cur.strip():
            lines.append(cur.strip())
    return lines

def make_base_bg():
    y = np.linspace(0, 1, H)[:, None]
    x = np.linspace(0, 1, W)[None, :]
    r = (10 + 14 * (1 - y) + 6 * (1 - x)).astype(np.uint8)
    g = (15 + 18 * (1 - y) + 10 * (1 - x)).astype(np.uint8)
    b = (30 + 34 * (1 - y) + 18 * x).astype(np.uint8)
    arr = np.stack([np.broadcast_to(r, (H, W)), np.broadcast_to(g, (H, W)), np.broadcast_to(b, (H, W))], axis=-1).copy()
    # Subtle dot grid
    arr[72::36, 24::36] = np.clip(arr[72::36, 24::36].astype(int) + 18, 0, 255).astype(np.uint8)
    return Image.fromarray(arr, mode="RGB")

BASE_BG = make_base_bg()

# ----------------- Audio Synthesis & Waveform Analysis -----------------
async def _edge_tts_save(text, out_mp3, voice="zh-CN-XiaoxiaoNeural", rate="+6%"):
    import edge_tts
    comm = edge_tts.Communicate(text, voice=voice, rate=rate)
    await comm.save(out_mp3)

def synthesize_audio_wav(text, out_wav):
    ffmpeg_bin = shutil.which("ffmpeg")
    if not ffmpeg_bin:
        raise RuntimeError("ffmpeg not found in PATH")

    # Try Edge Neural TTS first (human-sounding bilingual voice!) with strict 15s timeout
    try:
        with tempfile.TemporaryDirectory() as tmp:
            mp3_path = os.path.join(tmp, "voice.mp3")
            asyncio.run(asyncio.wait_for(_edge_tts_save(text, mp3_path), timeout=15))
            if os.path.exists(mp3_path) and os.path.getsize(mp3_path) > 500:
                subprocess.run(
                    [ffmpeg_bin, "-y", "-loglevel", "error", "-i", mp3_path, "-ar", "24000", "-ac", "1", "-c:a", "pcm_s16le", out_wav],
                    stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, check=True
                )
                return _wav_info(out_wav)
    except Exception as e:
        print(f"  [tts] edge-tts fallback to Windows SAPI5 ({type(e).__name__}: {e})", flush=True)

    # Fallback: Windows SAPI5
    ps_script = """
param([string]$TextFile, [string]$OutWav)
Add-Type -AssemblyName System.Speech
$synth = New-Object System.Speech.Synthesis.SpeechSynthesizer
try { $synth.SelectVoice("Microsoft Huihui Desktop") } catch {}
$synth.Rate = 1
$synth.SetOutputToWaveFile($OutWav)
$synth.Speak([System.IO.File]::ReadAllText($TextFile, [System.Text.Encoding]::UTF8))
$synth.Dispose()
"""
    with tempfile.TemporaryDirectory() as tmp:
        ps_p = os.path.join(tmp, "tts.ps1")
        tx_p = os.path.join(tmp, "t.txt")
        raw_wav = os.path.join(tmp, "raw.wav")
        with open(ps_p, "w", encoding="utf-8") as f:
            f.write(ps_script)
        with open(tx_p, "w", encoding="utf-8") as f:
            f.write(text)
        subprocess.run(["powershell", "-NoProfile", "-ExecutionPolicy", "Bypass", "-File", ps_p, tx_p, raw_wav],
                       stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, check=True)
        subprocess.run([ffmpeg_bin, "-y", "-i", raw_wav, "-ar", "24000", "-ac", "1", "-c:a", "pcm_s16le", out_wav],
                       stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, check=True)
    return _wav_info(out_wav)

def _wav_info(wav_path):
    with wave.open(wav_path, "rb") as wf:
        sr = wf.getframerate()
        n = wf.getnframes()
        raw = wf.readframes(n)
    samples = np.frombuffer(raw, dtype=np.int16).astype(np.float32) / 32768.0
    dur = n / float(sr)
    # Build per-frame RMS energy envelope for live visualizer
    total_frames = max(1, int(math.ceil((dur + 0.5) * FPS)))
    spf = max(1, int(sr / FPS))
    env = []
    for fidx in range(total_frames):
        s0 = fidx * spf
        s1 = min(len(samples), s0 + spf)
        if s0 < len(samples) and s1 > s0:
            rms = float(np.sqrt(np.mean(samples[s0:s1] ** 2)))
            env.append(min(1.0, rms * 4.5))
        else:
            env.append(0.0)
    return dur, env

# ----------------- Vector Drawing Primitives -----------------
def draw_chip(draw, x, y, text, font, bg, border, fg="#f8fafc", pad_x=14, pad_y=9, radius=10, border_w=2):
    bb = draw.textbbox((0, 0), text, font=font)
    tw, th = bb[2] - bb[0], bb[3] - bb[1]
    w = tw + pad_x * 2
    h = th + pad_y * 2
    draw.rounded_rectangle([x, y, x + w, y + h], radius=radius, fill=bg, outline=border, width=border_w)
    draw.text((x + pad_x - bb[0], y + pad_y - bb[1]), text, font=font, fill=fg)
    return w, h

def draw_bezier_arrow(draw, p0, p1, p2, progress, color="#38bdf8", width=3):
    progress = clamp01(progress)
    if progress <= 0.01:
        return
    steps = max(4, int(36 * progress))
    pts = []
    for i in range(steps + 1):
        u = (i / 36.0)
        if u > progress:
            u = progress
        x = (1 - u) ** 2 * p0[0] + 2 * (1 - u) * u * p1[0] + (u ** 2) * p2[0]
        y = (1 - u) ** 2 * p0[1] + 2 * (1 - u) * u * p1[1] + (u ** 2) * p2[1]
        pts.append((x, y))
    if len(pts) >= 2:
        draw.line(pts, fill=color, width=width)
        # Arrowhead
        ax, ay = pts[-1]
        px, py = pts[-2]
        ang = math.atan2(ay - py, ax - px)
        ah = 11
        p_left = (ax - ah * math.cos(ang - 0.5), ay - ah * math.sin(ang - 0.5))
        p_right = (ax - ah * math.cos(ang + 0.5), ay - ah * math.sin(ang + 0.5))
        draw.polygon([(ax, ay), p_left, p_right], fill=color)

def draw_animated_x(draw, x0, y0, x1, y1, progress, color="#ef4444", width=4):
    p1 = seg_p(progress, 0.0, 0.5)
    p2 = seg_p(progress, 0.5, 1.0)
    if p1 > 0:
        draw.line([(x0, y0), (lerp(x0, x1, p1), lerp(y0, y1, p1))], fill=color, width=width)
    if p2 > 0:
        draw.line([(x1, y0), (lerp(x1, x0, p2), lerp(y0, y1, p2))], fill=color, width=width)

def draw_animated_check(draw, cx, cy, size, progress, color="#10b981", width=4):
    p1 = seg_p(progress, 0.0, 0.45)
    p2 = seg_p(progress, 0.45, 1.0)
    a = (cx - size * 0.45, cy)
    b = (cx - size * 0.1, cy + size * 0.38)
    c = (cx + size * 0.52, cy - size * 0.38)
    if p1 > 0:
        draw.line([a, (lerp(a[0], b[0], p1), lerp(a[1], b[1], p1))], fill=color, width=width)
    if p2 > 0:
        draw.line([b, (lerp(b[0], c[0], p2), lerp(b[1], c[1], p2))], fill=color, width=width)

def draw_ambient_bg(img, global_progress):
    # Smooth soft-glow ambient orbs pasted BEFORE scene content (fast + crisp text)
    ox1 = int(60 + 620 * global_progress)
    oy1 = int(-80 + 40 * math.sin(global_progress * math.pi * 2))
    img.paste(ORB_BLUE_RGB, (ox1 - 190, oy1), ORB_BLUE_A)

    ox2 = int(W - 80 - 520 * global_progress)
    oy2 = int(H - 250 + 30 * math.cos(global_progress * math.pi * 2))
    img.paste(ORB_GREEN_RGB, (ox2 - 170, oy2), ORB_GREEN_A)

    ox3 = int(W * 0.5 + 180 * math.sin(global_progress * math.pi * 2))
    oy3 = int(120 + 60 * math.cos(global_progress * math.pi * 2))
    img.paste(ORB_PURPLE_RGB, (ox3 - 150, oy3), ORB_PURPLE_A)

def draw_chrome(draw, kp_label, scene_idx, total_scenes, global_progress, rms_energy, caption_text, rule_text, rule_alpha=1.0):
    # Top header bar
    draw.rectangle([0, 0, W, 56], fill="#0b1222")
    draw.line([(0, 56), (W, 56)], fill="#1e293b", width=2)
    draw.rounded_rectangle([24, 12, 238, 44], radius=8, fill="#2563eb")
    draw.text((38, 17), "EC Grammar · Packet 4", font=F_SM_B, fill="#ffffff")
    draw.text((254, 17), kp_label, font=F_SM_B, fill="#cbd5e1")

    # Live Audio-Reactive Waveform Visualizer (top right)
    num_bars = 16
    base_x = W - 24 - num_bars * 8
    for i in range(num_bars):
        wave_mod = 0.45 + 0.55 * abs(math.sin(global_progress * 38.0 + i * 0.65))
        bar_h = int(4 + 26 * rms_energy * wave_mod)
        bx = base_x + i * 8
        by0 = 28 - bar_h // 2
        by1 = 28 + bar_h // 2
        col = "#38bdf8" if i % 2 == 0 else "#34d399"
        draw.rounded_rectangle([bx, by0, bx + 4, by1], radius=2, fill=col)

    # Global progress track under header
    draw.rectangle([0, 54, W, 58], fill="#1e293b")
    px_prog = int(W * clamp01(global_progress))
    if px_prog > 0:
        draw.rectangle([0, 54, px_prog, 58], fill="#38bdf8")
        draw.ellipse([px_prog - 4, 52, px_prog + 4, 60], fill="#7dd3fc")

    # Scene indicator pills
    if total_scenes > 1:
        sx = W - 24 - num_bars * 8 - 18 - total_scenes * 28
        for i in range(total_scenes):
            px = sx + i * 28
            fill = "#2563eb" if i == scene_idx else ("#065f46" if i < scene_idx else "#1e293b")
            draw.rounded_rectangle([px, 16, px + 22, 38], radius=6, fill=fill)
            draw.text((px + 6, 18), str(i + 1), font=F_XS, fill="#ffffff")

    # Bottom synced caption & rule bar
    if rule_text and rule_alpha > 0.05:
        ry = int(lerp(H + 10, H - 96, ease_out_cubic(rule_alpha)))
        draw.rounded_rectangle([32, ry, W - 32, ry + 38], radius=8, fill="#3b1d06", outline="#f59e0b", width=2)
        rule_str = f"RULE: {rule_text}"
        rf = fit_font(draw, rule_str, [F_SM_B, F_XS_B, F_XXS], W - 96)
        _, rh = text_size(draw, rule_str, rf)
        draw.text((48, ry + (38 - rh) // 2 - 1), rule_str, font=rf, fill="#fde68a")

    if caption_text:
        draw.rectangle([0, H - 48, W, H], fill="#090d16")
        draw.line([(0, H - 48), (W, H - 48)], fill="#1e293b", width=1)
        cf = fit_font(draw, caption_text, [F_SM, F_XS, F_XXS], W - 64)
        cw, ch = text_size(draw, caption_text, cf)
        draw.text(((W - cw) // 2, H - 48 + (48 - ch) // 2 - 1), caption_text, font=cf, fill="#e2e8f0")

# ----------------- Kinetic Scene Renderers -----------------
def render_combine_slide(draw, scene, p):
    # Badge + Heading
    p_head = ease_out_cubic(seg_p(p, 0.0, 0.14))
    hy = int(lerp(96, 72, p_head))
    hf = fit_font(draw, scene["heading"], [F_LG_B, F_MD_B, F_SM_B], W - 72)
    draw.text((36, hy), scene["heading"], font=hf, fill="#f8fafc")

    # Word blocks for Sentence 1 & Sentence 2
    s1_pre = scene.get("s1_pre", "")
    s1_ant = scene["s1_ant"]
    s1_post = scene.get("s1_post", "")
    s2_pre = scene.get("s2_pre", "")
    s2_rep = scene["s2_rep"]
    s2_post = scene.get("s2_post", "")
    rel_word = scene["rel_word"]
    commas = scene.get("commas", False)

    # Build clean merged clause text (no stray period inside the middle of Sentence 1!)
    core_clause = f"{rel_word} {s2_pre} {s2_post}".replace("  ", " ").strip()
    if s1_post:
        core_clause = core_clause.rstrip(".")
    if commas:
        clause_text = f", {core_clause}," if s1_post else f", {core_clause}"
    else:
        clause_text = core_clause

    # Auto-pick font & padding so merged Row 1 ALWAYS fits comfortably inside W - 64
    font_use, pad_x, gap = F_MD_B, 11, 10
    for f_cand, px_cand, g_cand in [(F_MD_B, 11, 10), (F_SM_B, 9, 8), (F_XS_B, 7, 6), (F_XXS, 6, 5)]:
        def _cw(t, f=f_cand, px=px_cand):
            return (text_size(draw, t, f)[0] + px * 2) if t else 0
        w_pre, w_ant, w_post, w_clause = _cw(s1_pre), _cw(s1_ant), _cw(s1_post), _cw(clause_text)
        total_m = w_pre + (g_cand if w_pre else 0) + w_ant + g_cand + w_clause + (g_cand if w_post else 0) + w_post
        font_use, pad_x, gap = f_cand, px_cand, g_cand
        if total_m <= W - 64:
            break

    def chip_w(t):
        return (text_size(draw, t, font_use)[0] + pad_x * 2) if t else 0

    w_pre, w_ant, w_post, w_clause = chip_w(s1_pre), chip_w(s1_ant), chip_w(s1_post), chip_w(clause_text)
    row1_init_w = w_pre + (gap if w_pre else 0) + w_ant + (gap if w_post else 0) + w_post
    row1_merged_w = w_pre + (gap if w_pre else 0) + w_ant + gap + w_clause + (gap if w_post else 0) + w_post

    p_enter = ease_out_back(seg_p(p, 0.03, 0.18))
    p_arrow = ease_in_out_cubic(seg_p(p, 0.20, 0.38))
    p_morph = ease_out_cubic(seg_p(p, 0.40, 0.60))
    p_merge = ease_in_out_cubic(seg_p(p, 0.62, 0.82))
    p_done = ease_out_cubic(seg_p(p, 0.82, 0.94))

    x1_start = lerp((W - row1_init_w) / 2, max(32, (W - row1_merged_w) / 2), p_merge)
    y1 = 158 + int((1 - p_enter) * 26)

    # Row 1 Label
    draw.text((36, 118), "Sentence 1 -> Main Clause (主句)" if p_merge < 0.5 else "Combined Sentence (定语从句已紧贴先行词!)",
              font=F_XS_B, fill="#93c5fd" if p_merge < 0.5 else "#34d399")

    cur_x = x1_start
    if s1_pre:
        draw_chip(draw, cur_x, y1, s1_pre, font_use, "#1e293b", "#475569", pad_x=pad_x)
        cur_x += w_pre + gap

    ant_x = cur_x
    ant_border = "#38bdf8" if p_arrow > 0.1 else "#64748b"
    ant_bg = "#1e3a8a" if p_arrow > 0.1 else "#1e293b"
    ant_w, ant_h = draw_chip(draw, ant_x, y1, s1_ant, font_use, ant_bg, ant_border, "#ffffff", pad_x=pad_x, border_w=3 if p_arrow > 0.1 else 2)
    # Antecedent tag above
    if p_arrow > 0.2:
        draw.text((ant_x + 2, y1 - 21), "Antecedent (先行词)", font=F_XS, fill="#38bdf8")

    # Show subtle insertion slot outline while opening
    slot_x = ant_x + ant_w + gap
    if 0.05 < p_merge < 0.92:
        slot_w = max(8, int(w_clause * p_merge))
        draw.rounded_rectangle([slot_x, y1, slot_x + slot_w, y1 + ant_h], radius=10, fill="#091d17", outline="#059669", width=1)

    # Suffix slides right to open slot!
    post_x_init = ant_x + ant_w + gap
    post_x_merged = ant_x + ant_w + gap + w_clause + gap
    if s1_post:
        post_x = lerp(post_x_init, post_x_merged, p_merge)
        draw_chip(draw, post_x, y1, s1_post, font_use, "#1e293b", "#475569", pad_x=pad_x)

    # Row 2 (Sentence 2 -> morphs -> flies into Row 1 slot!)
    y2_base = 290
    if p_merge < 0.65:
        draw.text((36, 260), "Sentence 2 (找出重复词并替换为关系词)", font=F_XS_B, fill="#c4b5fd")

    w_s2pre = chip_w(s2_pre)
    w_s2rep = chip_w(s2_rep)
    w_s2post = chip_w(s2_post)
    w_rel = chip_w(rel_word)
    row2_w = w_s2pre + (gap if w_s2pre else 0) + (w_s2rep if p_morph < 0.55 else w_rel) + (gap if w_s2post else 0) + w_s2post
    x2_start = max(32, (W - row2_w) / 2)

    if p_merge < 0.05:
        # Draw Sentence 2 in pieces so repeated word can get struck through & morphed
        cx2 = x2_start
        if s2_pre:
            draw_chip(draw, cx2, y2_base, s2_pre, font_use, "#1e293b", "#6d28d9", pad_x=pad_x)
            cx2 += w_s2pre + gap

        rep_x = cx2
        shake = int(math.sin(p_morph * 22) * 5 * (1 - p_morph)) if 0 < p_morph < 0.55 else 0
        if p_morph < 0.55:
            rw, rh = draw_chip(draw, rep_x + shake, y2_base, s2_rep, font_use, "#450a0a" if p_morph > 0.1 else "#1e293b", "#ef4444" if p_morph > 0.1 else "#8b5cf6", pad_x=pad_x)
            if p_morph > 0.1:
                draw_animated_x(draw, rep_x + 4, y2_base + 4, rep_x + rw - 4, y2_base + rh - 4, seg_p(p_morph, 0.1, 0.5))
        else:
            rw, rh = draw_chip(draw, rep_x, y2_base, rel_word, font_use, "#064e3b", "#10b981", "#a7f3d0", pad_x=pad_x, border_w=3)
            draw.text((rep_x + 2, y2_base + rh + 6), "替换为关系词!", font=F_XS, fill="#34d399")

        if s2_post:
            draw_chip(draw, rep_x + rw + gap, y2_base, s2_post, font_use, "#1e293b", "#6d28d9", pad_x=pad_x)

        # Curved Bezier arrow from repeated word -> Antecedent
        if p_arrow > 0.02 and p_morph < 0.65:
            p0 = (rep_x + w_s2rep / 2, y2_base - 4)
            p2 = (ant_x + ant_w / 2, y1 + ant_h + 6)
            p1 = ((p0[0] + p2[0]) / 2 - 55, (p0[1] + p2[1]) / 2)
            draw_bezier_arrow(draw, p0, p1, p2, p_arrow, color="#38bdf8", width=3)
    else:
        # Fly the newly formed clause chip smoothly into the opened gap on Row 1!
        clause_x = lerp((W - w_clause) / 2, slot_x, p_merge)
        clause_y = lerp(y2_base, y1, p_merge)
        draw_chip(draw, clause_x, clause_y, clause_text, font_use, "#064e3b", "#10b981", "#d1fae5", pad_x=pad_x, border_w=3)
        if p_done > 0.05:
            # Highlight final explanation card below with animated checkmark inside!
            card_y = int(lerp(340, 278, p_done))
            draw.rounded_rectangle([48, card_y, W - 48, card_y + 126], radius=14, fill="#0f291e", outline="#10b981", width=2)
            draw.text((70, card_y + 14), "合并完成 · 满分句式", font=F_SM_B, fill="#34d399")
            full_lines = wrap_text(draw, scene["final_sentence"], F_MD_B, W - 210)
            f_final = F_MD_B if len(full_lines) <= 2 else F_SM_B
            full_lines = wrap_text(draw, scene["final_sentence"], f_final, W - 210)
            fy = card_y + 44
            for ln in full_lines[:3]:
                draw.text((70, fy), ln, font=f_final, fill="#ffffff")
                fy += 28 if f_final == F_MD_B else 23
            draw_animated_check(draw, W - 92, card_y + 62, 40, p_done, color="#10b981", width=5)


def render_trap_smash(draw, scene, p):
    p_in = ease_out_cubic(seg_p(p, 0.0, 0.16))
    hf = fit_font(draw, scene["heading"], [F_LG_B, F_MD_B, F_SM_B], W - 72)
    draw.text((36, int(lerp(94, 72, p_in))), scene["heading"], font=hf, fill="#f8fafc")

    p_shake = seg_p(p, 0.24, 0.52)
    p_x = seg_p(p, 0.30, 0.50)
    p_fix = ease_out_back(seg_p(p, 0.54, 0.78))
    p_chk = seg_p(p, 0.76, 0.92)

    # Wrong box (top)
    shake_x = int(math.sin(p_shake * 28) * 9 * (1 - p_shake)) if 0 < p_shake < 1 else 0
    bx0, by0, bx1, by1 = 48 + shake_x, 128, W - 48 + shake_x, 244
    draw.rounded_rectangle([bx0, by0, bx1, by1], radius=14, fill="#2b0c12", outline="#ef4444", width=3)
    draw.text((bx0 + 22, by0 + 14), "COMMON TRAP (常见失分错句)", font=F_SM_B, fill="#fca5a5")
    w_lines = wrap_text(draw, scene["wrong_sentence"], F_MD_B, W - 190)
    wy = by0 + 46
    for ln in w_lines[:2]:
        draw.text((bx0 + 22, wy), ln, font=F_MD_B, fill="#fee2e2")
        wy += 30
    if p_x > 0:
        draw_animated_x(draw, bx1 - 68, by0 + 34, bx1 - 24, by0 + 78, p_x, color="#ef4444", width=5)

    # Fix box (bottom) slides in
    if p_fix > 0.01:
        fy0 = int(lerp(360, 266, p_fix))
        fy1 = fy0 + 152
        draw.rounded_rectangle([48, fy0, W - 48, fy1], radius=14, fill="#063729", outline="#10b981", width=3)
        draw.text((70, fy0 + 14), "CORRECT FIX (满分正解)", font=F_SM_B, fill="#6ee7b7")
        r_lines = wrap_text(draw, scene["right_sentence"], F_MD_B, W - 190)
        ry = fy0 + 44
        for ln in r_lines[:2]:
            draw.text((70, ry), ln, font=F_MD_B, fill="#ffffff")
            ry += 28
        why_lines = wrap_text(draw, scene["why"], F_XS, W - 200)
        wy2 = fy0 + 104
        for ln in why_lines[:2]:
            draw.text((70, wy2), ln, font=F_XS, fill="#a7f3d0")
            wy2 += 20
        if p_chk > 0:
            draw_animated_check(draw, W - 92, fy0 + 66, 42, p_chk, color="#10b981", width=5)


def render_multi_scanner(draw, scene, p):
    p_in = ease_out_cubic(seg_p(p, 0.0, 0.14))
    hf = fit_font(draw, scene["heading"], [F_LG_B, F_MD_B, F_SM_B], W - 72)
    draw.text((36, int(lerp(90, 70, p_in))), scene["heading"], font=hf, fill="#f8fafc")

    # Sentence box
    draw.rounded_rectangle([40, 114, W - 40, 206], radius=12, fill="#1e293b", outline="#38bdf8", width=2)
    sent_lines = wrap_text(draw, scene["sentence"], F_MD_B, W - 120)
    sy = 128 if len(sent_lines) > 1 else 146
    for ln in sent_lines[:2]:
        draw.text((62, sy), ln, font=F_MD_B, fill="#ffffff")
        sy += 32

    # Antecedent + Role hint strip
    p_ant = ease_out_cubic(seg_p(p, 0.12, 0.26))
    if p_ant > 0:
        hint_str = f"先行词: {scene['antecedent']}   |   成分: {scene['role']}"
        ahf = fit_font(draw, hint_str, [F_SM_B, F_XS_B], W - 96)
        draw.text((48, 220), hint_str, font=ahf, fill="#93c5fd")

    # Animated option scanning cards
    opts = scene["options"]  # list of (label, is_correct, short_reason)
    n = len(opts)
    gap = 16
    card_w = (W - 80 - gap * (n - 1)) // n
    card_y = 260
    card_h = 154

    for i, (lbl, ok, reason) in enumerate(opts):
        scan_start = 0.22 + i * (0.48 / max(1, n))
        scan_end = scan_start + 0.14
        sp = ease_out_back(seg_p(p, scan_start, scan_end))
        cx = 40 + i * (card_w + gap)
        lift = int(-8 * sp) if (ok and sp > 0.2) else 0
        shake = int(math.sin(sp * 20) * 5 * (1 - sp)) if (not ok and 0 < sp < 0.8) else 0

        if sp <= 0.02:
            bg, border, fg = "#1e293b", "#475569", "#cbd5e1"
        elif ok:
            bg, border, fg = "#064e3b", "#10b981", "#d1fae5"
        else:
            bg, border, fg = "#3b0d14", "#ef4444", "#fecaca"

        draw.rounded_rectangle([cx + shake, card_y + lift, cx + card_w + shake, card_y + card_h + lift],
                               radius=12, fill=bg, outline=border, width=3 if sp > 0.02 else 2)
        lf = fit_font(draw, lbl, [F_LG_B, F_MD_B, F_SM_B, F_XS_B], card_w - 20)
        lw, lh = text_size(draw, lbl, lf)
        draw.text((cx + shake + (card_w - lw) // 2, card_y + lift + 26 - lh // 2 + 10), lbl, font=lf, fill=fg)

        if sp > 0.15:
            status_txt = "CORRECT" if ok else "WRONG"
            sw, _ = text_size(draw, status_txt, F_XS_B)
            draw.text((cx + shake + (card_w - sw) // 2, card_y + lift + 60), status_txt,
                      font=F_XS_B, fill="#34d399" if ok else "#f87171")
            rlines = wrap_text(draw, reason, F_XS, card_w - 20)
            ry = card_y + lift + 86
            for rl in rlines[:2]:
                rw, _ = text_size(draw, rl, F_XS)
                draw.text((cx + shake + (card_w - rw) // 2, ry), rl, font=F_XS, fill="#e2e8f0")
                ry += 20


def render_mindmap_grow(draw, scene, p):
    p_in = ease_out_cubic(seg_p(p, 0.0, 0.14))
    hf = fit_font(draw, scene["heading"], [F_LG_B, F_MD_B, F_SM_B], W - 72)
    draw.text((36, int(lerp(90, 70, p_in))), scene["heading"], font=hf, fill="#f8fafc")

    # Root node on left
    p_root = ease_out_back(seg_p(p, 0.06, 0.22))
    rx0, ry0, rx1, ry1 = 44, 210, 274, 330
    scale_off = int((1 - p_root) * 20)
    draw.rounded_rectangle([rx0 - scale_off, ry0, rx1, ry1], radius=16, fill="#1e3a8a", outline="#38bdf8", width=3)
    rlines = wrap_text(draw, scene["root"], F_MD_B, 200)
    ry = ry0 + 28
    for ln in rlines[:3]:
        draw.text((rx0 + 18, ry), ln, font=F_MD_B, fill="#ffffff")
        ry += 28

    branches = scene["branches"]  # list of (title, body, accent)
    nb = len(branches)
    total_h = 304
    bh = (total_h - 14 * (nb - 1)) // nb
    start_y = 120

    for i, (b_title, b_body, accent) in enumerate(branches):
        bp = ease_out_cubic(seg_p(p, 0.18 + i * 0.18, 0.42 + i * 0.18))
        by0 = start_y + i * (bh + 14)
        by1 = by0 + bh
        # Curved connector from root right edge -> branch left edge
        p0 = (rx1 + 2, (ry0 + ry1) / 2)
        p2 = (368, (by0 + by1) / 2)
        p1 = ((p0[0] + p2[0]) / 2, p2[1])
        draw_bezier_arrow(draw, p0, p1, p2, bp, color=accent, width=3)

        if bp > 0.1:
            bx0 = int(lerp(420, 376, bp))
            draw.rounded_rectangle([bx0, by0, W - 40, by1], radius=12, fill="#1e293b", outline=accent, width=2)
            draw.text((bx0 + 18, by0 + 10), b_title, font=F_SM_B, fill=accent)
            blines = wrap_text(draw, b_body, F_SM, W - 40 - bx0 - 34)
            bf = F_SM if len(blines) <= 2 else F_XS
            blines = wrap_text(draw, b_body, bf, W - 40 - bx0 - 34)
            ty = by0 + 36
            for ln in blines[:2]:
                draw.text((bx0 + 18, ty), ln, font=bf, fill="#f1f5f9")
                ty += 22


# ----------------- Video Specifications (6 KP + 34 Questions) -----------------
KP_VIDEOS = [
    {
        "id": "kp1_placement",
        "kp_label": "KP 01 · 位置与基本结构",
        "scenes": [
            {
                "kind": "combine_slide",
                "heading": "核心动画：定语从句紧跟在先行词后面",
                "s1_pre": "", "s1_ant": "The professor", "s1_post": "emailed me.",
                "s2_pre": "", "s2_rep": "He", "s2_post": "teaches Russian.",
                "rel_word": "who", "commas": False,
                "final_sentence": "The professor who teaches Russian emailed me.",
                "rule": "修饰谁，就把定语从句紧贴在谁的后面！",
                "caption": "He 指代 The professor → 替换为 who，滑入主语与 emailed me 之间。",
                "narration": "欢迎来到知识点一，定语从句的位置。看这两句话：The professor emailed me，和 He teaches Russian。He 指代主语 The professor，所以我们划掉 He 换成 who，把整个从句滑进 The professor 后面，组成 The professor who teaches Russian emailed me。",
            },
            {
                "kind": "mindmap_grow",
                "heading": "两种常见位置 & 独立/从属句辨析",
                "root": "Adjective Clause\n定语从句位置",
                "branches": [
                    ("1. 修饰宾语 (句末)", "They met a woman [who teaches psychology].", "#38bdf8"),
                    ("2. 修饰主语 (句中插入)", "The woman [who teaches psychology] is a writer.", "#10b981"),
                    ("3. Dependent Clause 不可独立", "X that we bought  ->  OK The house [that we bought] is big.", "#f59e0b"),
                ],
                "rule": "主句必须有完整主谓，从句紧随被修饰名词之后",
                "caption": "修饰宾语在句末，修饰主语插在主语和主句动词之间。",
                "narration": "定语从句有两种常见位置：修饰宾语时跟在句末；修饰主语时插在主语和主句动词中间。同时记住，定语从句是从属分句，绝不能单独成句。",
            },
        ],
    },
    {
        "id": "kp2_subjects",
        "kp_label": "KP 02 · 作主语的关系代词",
        "scenes": [
            {
                "kind": "mindmap_grow",
                "heading": "空格后直接跟动词 → 关系代词作【主语】",
                "root": "Subject Pronouns\n作主语的关系词",
                "branches": [
                    ("指代人 (People)", "who / that   (例: Anyone who enjoyed the movie...)", "#38bdf8"),
                    ("指代物 (Things)", "which / that   (例: The package which was lying...)", "#a78bfa"),
                    ("两大禁令", "作主语绝不可省略 (NO Ø)！且绝不可用 which 指人！", "#ef4444"),
                ],
                "rule": "人用 who/that | 物用 which/that | 主语不可省",
                "caption": "看到空格后紧跟动词，关系词作主语，不能省略也不能用 which 指人。",
                "narration": "知识点二，作主语的关系代词。当空格后面直接跟动词时，指人用 who 或 that，指物用 which 或 that。切记作主语绝对不能省略，也绝不能用 which 指代人。",
            },
            {
                "kind": "trap_smash",
                "heading": "高频雷区：禁止双主语 (Double Subject)",
                "wrong_sentence": "Chuy is a person who he prefers to be alone.",
                "right_sentence": "Chuy is a person who prefers to be alone.",
                "why": "who 已经占据了从句主语位置，原句里的 he / she / it / they 必须彻底删除！",
                "rule": "有了 who / which / that，千万别留 he / it / they",
                "caption": "删掉多余主语 he！动词单复数跟着从句真正主语变化。",
                "narration": "高频失分雷区：双主语错误。不能写成 who he prefers，因为 who 已经代替了 he，必须把多余的 he 删掉，变成 Chuy is a person who prefers to be alone。",
            },
        ],
    },
    {
        "id": "kp3_objects",
        "kp_label": "KP 03 · 作宾语与省略",
        "scenes": [
            {
                "kind": "combine_slide",
                "heading": "作宾语时：替换并删除句末代词，且可省略 (Ø)",
                "s1_pre": "", "s1_ant": "The dress", "s1_post": "was long and black.",
                "s2_pre": "Mary wore", "s2_rep": "it", "s2_post": "",
                "rel_word": "(that/which/Ø)", "commas": False,
                "final_sentence": "The dress (that / which / Ø) Mary wore was long and black.",
                "rule": "限定性作宾语：可省略 Ø，但句末 it / him 必须删！",
                "caption": "Mary wore 缺宾语 → 删掉 it，用 that / which / Ø 提前连接。",
                "narration": "知识点三，作宾语与省略。在 Mary wore it 中，it 作宾语。我们把 it 划掉，用 that、which 或直接省略引导从句，滑到 The dress 后面，变成 The dress Mary wore was long and black。",
            },
            {
                "kind": "trap_smash",
                "heading": "高频雷区：介词前置 (to whom / in which)",
                "wrong_sentence": "I didn't see the face of the man who I gave the money.",
                "right_sentence": "I didn't see the face of the man to whom I gave the money.",
                "why": "give money TO the man：句末没有 to，必须把 to 提前写成 to whom（介词后禁用 that / Ø）！",
                "rule": "介词前置后只用 whom (人) / which (物)，禁用 that / Ø",
                "caption": "先检查句末有没有介词！缺少 to 时必须选 to whom。",
                "narration": "特别小心介词陷阱！如果句末没有 to，比如 I gave the money 缺少给的对象介词，就必须把 to 提前写成 to whom。记住，介词后面绝对不能用 that 或省略。",
            },
        ],
    },
    {
        "id": "kp4_whose",
        "kp_label": "KP 04 · 所有格关系词 whose",
        "scenes": [
            {
                "kind": "combine_slide",
                "heading": "whose 替代 his / her / its / their + 名词",
                "s1_pre": "", "s1_ant": "The man", "s1_post": "is my father's boss.",
                "s2_pre": "we borrowed", "s2_rep": "his car", "s2_post": "",
                "rel_word": "whose car", "commas": False,
                "final_sentence": "The man whose car we borrowed is my father's boss.",
                "rule": "看到空格后紧跟【光杆名词】→ 立刻选 whose（永不可省）！",
                "caption": "his car 变为 whose car 提前，人、物均可用 whose。",
                "narration": "知识点四，所有格关系词 whose。看这句：we borrowed his car，把 his car 替换成 whose car 提前到 The man 后面，变成 The man whose car we borrowed is my father's boss。whose 既可修饰人也可修饰物，且永远不能省略。",
            },
            {
                "kind": "trap_smash",
                "heading": "BE CAREFUL! whose 永远不可省略，也不可换成 which",
                "wrong_sentence": "Harvey, house we're renting, is a lawyer.",
                "right_sentence": "Harvey, whose house we're renting, is a lawyer.",
                "why": "哪怕 whose house 作宾语也绝不能省略 whose！指物同理：a theory whose origins...",
                "rule": "whose + 名词 = 不可省略 (NO Ø)",
                "caption": "Harvey 是专有名词加逗号，且必须保留 whose。",
                "narration": "避坑提示：千万不能把 whose 省掉，Harvey, whose house we're renting 里的 whose 必须保留。",
            },
        ],
    },
    {
        "id": "kp5_where_when",
        "kp_label": "KP 05 · 地点与时间 (where / when)",
        "scenes": [
            {
                "kind": "trap_smash",
                "heading": "最易踩坑：假地点陷阱 (where 绝不能作主语！)",
                "wrong_sentence": "Stockholm is a city where has beautiful scenery.",
                "right_sentence": "Stockholm is a city that / which has beautiful scenery.",
                "why": "空格后直接跟动词 has，说明缺【主语】！只有能还原成 'there' 作地点状语时才用 where。",
                "rule": "能换成 there -> where | 作主语 -> that / which",
                "caption": "先检验能不能说 there has？不通！所以作主语必须用 that / which。",
                "narration": "知识点五，where 和 when。这是最容易踩的坑：看到 city 别直接选 where！Stockholm is a city 后面直接是动词 has，缺少主语，不能说 there has，所以必须用 that 或 which。",
            },
            {
                "kind": "multi_scanner",
                "heading": "真地点 vs 时间名词：能否省略 Ø？",
                "sentence": "I was surprised to see the log house ( ______ ) my father grew up.",
                "antecedent": "the log house (地点)",
                "role": "grew up there (地点状语)",
                "options": [
                    ("where", True, "自带地点状语含义"),
                    ("which", False, "句末缺介词 in，不能单独用"),
                    ("Ø", False, "句末缺 in，不可省略"),
                ],
                "rule": "地点缺介词只用 where | 时间名词 the day 可用 when / that / Ø",
                "caption": "grew up 后面没有 in，所以唯一选 where，不能用 which 或 Ø。",
                "narration": "看 B8 真题：the log house 后面 grew up 没有介词 in，所以唯一正确答案是 where，不能单独用 which 或省略。而时间名词 the day 后，when、that 和省略三者都可以。",
            },
        ],
    },
    {
        "id": "kp6_commas",
        "kp_label": "KP 06 · 限定 vs 非限定从句",
        "scenes": [
            {
                "kind": "mindmap_grow",
                "heading": "是否加逗号？一看先行词是否已经“特指/唯一”",
                "root": "Commas 逗号规则\n限定 vs 非限定",
                "branches": [
                    ("无逗号 · 限定性", "泛指名词需限定 (The woman who created...) -> 可用 that / Ø", "#38bdf8"),
                    ("有逗号 · 非限定性", "专有名词/唯一事物 (Sara Gomez, who...) -> 额外补充信息", "#10b981"),
                    ("逗号后两大禁区", "一旦出现逗号：严禁使用 that！严禁省略 Ø！", "#ef4444"),
                ],
                "rule": "见逗号 = NO that + NO Ø（仅用 who/whom/which/whose/where/when）",
                "caption": "专有名词（人名/地名/公司名）通常用逗号隔开，且禁用 that 和 Ø。",
                "narration": "知识点六，限定与非限定从句。专有名词如 Sara Gomez 或 British Petroleum 已经明确指向唯一对象，定语从句前后必须加逗号。一旦有逗号，立刻禁用 that 和省略。",
            },
            {
                "kind": "trap_smash",
                "heading": "逗号后禁区实战 & 指代整句话用 , which",
                "wrong_sentence": "Elena, that I met at the conference, has a Type A personality.",
                "right_sentence": "Elena, whom I met at the conference, has a Type A personality.",
                "why": "虽然作宾语，但逗号后禁用 that 和 Ø！另外修饰整句话也必须用 ', which'。",
                "rule": "逗号后指人用 who/whom；指物或整句话只用 which",
                "caption": "看到逗号直接拉黑 that 和 Ø，稳稳拿满分！",
                "narration": "看真题：Elena 后面有逗号，虽然作 met 的宾语，但逗号后面绝对不能用 that 或省略，只能选 whom。",
            },
        ],
    },
]

# Per-question kinetic video specs (34 questions using combine_slide or multi_scanner!)
QUESTION_SPECS = [
    {"id": "kp1_q1", "kp_label": "错题精讲 · B6 #2", "scene": {"kind": "combine_slide", "heading": "错题拆解：修饰主语时，从句紧跟主语", "s1_pre": "", "s1_ant": "The professor", "s1_post": "emailed me.", "s2_pre": "", "s2_rep": "He", "s2_post": "teaches Russian.", "rel_word": "who", "commas": False, "final_sentence": "The professor who teaches Russian emailed me.", "rule": "不要把从句放到 emailed me 后面！", "caption": "He 替换为 who，紧插在 The professor 和 emailed me 中间。", "narration": "这道题考查从句位置。He 指代 The professor，把 He 换成 who，将 who teaches Russian 紧插在 The professor 后面，构成 The professor who teaches Russian emailed me。"}},
    {"id": "kp1_q2", "kp_label": "错题精讲 · B6 #5", "scene": {"kind": "combine_slide", "heading": "错题拆解：主语定语从句合并", "s1_pre": "", "s1_ant": "The little girl", "s1_post": "was crying.", "s2_pre": "", "s2_rep": "She", "s2_post": "hurt her knee.", "rel_word": "who", "commas": False, "final_sentence": "The little girl who hurt her knee was crying.", "rule": "删掉 She 换成 who/that，紧跟 The little girl", "caption": "The little girl [who hurt her knee] was crying.", "narration": "She 指代 The little girl，删掉 She 换成 who 或 that，紧跟在 The little girl 后面，得到 The little girl who hurt her knee was crying。"}},
    {"id": "kp1_q3", "kp_label": "错题精讲 · Page 10 #1", "scene": {"kind": "combine_slide", "heading": "错题拆解：Page 10 #1 合并写句", "s1_pre": "", "s1_ant": "Students", "s1_post": "do well on tests if prepared.", "s2_pre": "", "s2_rep": "Some students", "s2_post": "are anxious.", "rel_word": "who", "commas": False, "final_sentence": "Students who are anxious do well on tests if they are prepared beforehand.", "rule": "把 are anxious 变成 who/that are anxious 紧跟 Students", "caption": "Students 复数配 are，从句紧贴主语之后。", "narration": "把 Some students are anxious 合并到主语 Students 后面，变成 Students who are anxious do well on tests if they are prepared beforehand。"}},
    {"id": "kp1_q4", "kp_label": "错题精讲 · B6 #8", "scene": {"kind": "combine_slide", "heading": "错题拆解：切勿放错先行词位置", "s1_pre": "", "s1_ant": "The child", "s1_post": "went home.", "s2_pre": "", "s2_rep": "He", "s2_post": "was sick.", "rel_word": "who", "commas": False, "final_sentence": "The child who was sick went home.", "rule": "不能写成 went home who was sick（否则修饰 home）", "caption": "He 换 who，紧贴 The child。", "narration": "He 指代 The child，所以 who was sick 要插在 The child 和 went home 之间，得到 The child who was sick went home。"}},
    {"id": "kp1_q5", "kp_label": "错题精讲 · Note 1", "scene": {"kind": "multi_scanner", "heading": "逐项扫描：语序与双主语检验", "sentence": "合并 'The car is outside.' + 'It belongs to my uncle.'", "antecedent": "The car (物)", "role": "从句主语 (which / that)", "options": [("that belongs...", True, "语序与指物均正确"), ("which belongs...", True, "语序与指物均正确"), ("...outside that...", False, "从句远离先行词"), ("which it belongs", False, "双主语错误")], "rule": "从句紧贴先行词，且删除多余的 it", "caption": "前两项完全正确，后两项分别犯了位置错位与双主语错误。", "narration": "修饰物 The car 可用 that 或 which，且必须紧跟 The car 后面，同时不能保留多余的 it。"}},
    {"id": "kp2_q1", "kp_label": "错题精讲 · B8 #10", "scene": {"kind": "multi_scanner", "heading": "B8 #10 逐项扫描：人作主语", "sentence": "Anyone ( ______ ) enjoyed Pirates of the Caribbean will love this movie.", "antecedent": "Anyone (人)", "role": "作 enjoyed 的主语", "options": [("who", True, "指人作主语"), ("whom", False, "只作宾语"), ("that", True, "限定从句指人可用"), ("Ø", False, "主语不可省")], "rule": "空格后直接跟动词 = 作主语，禁用 whom 和 Ø", "caption": "Anyone 指人且缺主语 → 选 who 和 that。", "narration": "空格后面直接是动词 enjoyed，说明缺少主语。指人作主语选 who 或 that，不能选 whom，也不能省略。"}},
    {"id": "kp2_q2", "kp_label": "错题精讲 · Review A #1", "scene": {"kind": "multi_scanner", "heading": "Review A #1 逐项扫描", "sentence": "The lady ( ______ ) is my teacher is the third from the right.", "antecedent": "The lady (人)", "role": "作系动词 is 的主语", "options": [("who", True, "指人作主语"), ("which", False, "不能指人"), ("that", True, "限定从句可用"), ("whom", False, "不能作主语")], "rule": "which 绝不能指代人！", "caption": "The lady 指人作主语 → 选 who 和 that。", "narration": "The lady 指人且后接动词 is，只能用 who 或 that，绝对不能用 which 指人。"}},
    {"id": "kp2_q3", "kp_label": "错题精讲 · Review A #8", "scene": {"kind": "trap_smash", "heading": "Review A #8：双主语雷区", "wrong_sentence": "Chuy is a person who he prefers to be alone.", "right_sentence": "Chuy is a person who prefers to be alone.", "why": "who 本身已经作 prefers 的主语，绝不能再加 he！", "rule": "禁止双主语：who he -> who", "caption": "划掉多余的 he，只选 who。", "narration": "who 已经作主语了，不能写成 who he。正确答案只有 who。"}},
    {"id": "kp2_q4", "kp_label": "错题精讲 · Review A #7", "scene": {"kind": "multi_scanner", "heading": "Review A #7：主谓一致陷阱", "sentence": "Lions are the animals that Lea ( ______ ) the best.", "antecedent": "the animals (作宾语)", "role": "从句真正主语是单数 Lea", "options": [("like", False, "误看了复数 animals"), ("likes", True, "主语 Lea 是第三人称单数")], "rule": "主谓一致看【从句自身的主语 Lea】！", "caption": "Lea 是单数，所以选 likes。", "narration": "不要被复数 Lions 和 animals 迷惑，从句真正的主语是单数 Lea，所以动词要用 likes。"}},
    {"id": "kp2_q5", "kp_label": "错题精讲 · B6 #1", "scene": {"kind": "combine_slide", "heading": "B6 #1：指物作主语合并", "s1_pre": "I picked up", "s1_ant": "the package", "s1_post": "", "s2_pre": "", "s2_rep": "It", "s2_post": "was lying on the step.", "rel_word": "that/which", "commas": False, "final_sentence": "I picked up the package that / which was lying on the front step.", "rule": "物作主语用 that / which，不可省略", "caption": "删掉 It 换 that/which，紧接 the package。", "narration": "package 是物，把 It 替换成 that 或 which，直接接在 the package 后面即可。"}},
    {"id": "kp2_q6", "kp_label": "错题精讲 · Page 10 #5", "scene": {"kind": "combine_slide", "heading": "Page 10 #5：主语后插入指物从句", "s1_pre": "Recently,", "s1_ant": "a large airplane", "s1_post": "had a serious accident.", "s2_pre": "", "s2_rep": "It", "s2_post": "was carrying too many passengers.", "rel_word": "that/which", "commas": False, "final_sentence": "Recently, a large airplane that / which was carrying too many passengers had a serious accident.", "rule": "紧跟 a large airplane，删除 It", "caption": "It 换成 that/which 插在 airplane 和 had 之间。", "narration": "It 指代 a large airplane，把 that was carrying too many passengers 插在 airplane 和 had 之间。"}},
    {"id": "kp3_q1", "kp_label": "错题精讲 · B8 #1", "scene": {"kind": "multi_scanner", "heading": "B8 #1 逐项扫描：人作介词宾语", "sentence": "The girl ( ______ ) I sat next to in math class always knew the answers.", "antecedent": "The girl (人)", "role": "作 next to 的宾语", "options": [("that", True, "限定从句作宾语"), ("who", True, "指人作宾语"), ("which", False, "不能指人"), ("Ø", True, "限定作宾语可省")], "rule": "介词 to 在后面，人作宾语 that / who / Ø 全对", "caption": "排除 which，其余三项全选！", "narration": "The girl 指人，在 I sat next to 中作宾语且无逗号，所以 that、who 和省略都正确，只有 which 不能指人。"}},
    {"id": "kp3_q2", "kp_label": "错题精讲 · B8 #4", "scene": {"kind": "multi_scanner", "heading": "B8 #4 逐项扫描：句末已有介词 about", "sentence": "It's a situation ( ______ ) I'd rather not think about.", "antecedent": "a situation (物)", "role": "作 think about 的宾语", "options": [("that", True, "指物作宾语"), ("which", True, "指物作宾语"), ("to which", False, "句末已有 about，搭配错误")], "rule": "看到句末已有 about，绝不再选多余的 to which！", "caption": "选 that 和 which。", "narration": "动词搭配是 think about，句末已经有 about 了，所以选 that 或 which，不能选多余且错误搭配的 to which。"}},
    {"id": "kp3_q3", "kp_label": "错题精讲 · B8 #7", "scene": {"kind": "multi_scanner", "heading": "B8 #7 逐项扫描：人作动词宾语", "sentence": "Nelson Mandela is a politician ( ______ ) I respect a lot.", "antecedent": "a politician (人)", "role": "作 respect 的宾语", "options": [("who", True, "通用宾语"), ("whom", True, "正式宾语"), ("Ø", True, "口语可省略")], "rule": "无逗号限定性从句人作宾语：who / whom / Ø 全对", "caption": "三个选项全部正确！", "narration": "politician 指人，在 I respect 中作宾语且没有逗号，因此 who、whom 和省略三个选项全部正确。"}},
    {"id": "kp3_q4", "kp_label": "错题精讲 · B8 #11", "scene": {"kind": "multi_scanner", "heading": "B8 #11 逐项扫描：缺少介词 to！", "sentence": "I didn't see the face of the man ( ______ ) I gave the money.", "antecedent": "the man (人)", "role": "give the money TO the man", "options": [("who", False, "缺少介词 to"), ("whom", False, "缺少介词 to"), ("to whom", True, "自带介词 to + whom")], "rule": "句末没有 to 时，必须把 to 带在 whom 前面！", "caption": "唯一正确答案：to whom。", "narration": "仔细看 money 后面没有 to！原意是 give the money to the man，所以必须把 to 带在前面，选 to whom。"}},
    {"id": "kp3_q5", "kp_label": "错题精讲 · Page 10 #7", "scene": {"kind": "combine_slide", "heading": "Page 10 #7：删掉句末宾语 it", "s1_pre": "", "s1_ant": "The dress", "s1_post": "was long, black, and beautiful.", "s2_pre": "Mary wore", "s2_rep": "it", "s2_post": "", "rel_word": "that/which", "commas": False, "final_sentence": "The dress (that / which) Mary wore was long, black, and beautiful.", "rule": "切勿保留句末的 it！", "caption": "删掉 it，把 that Mary wore 滑到 The dress 后面。", "narration": "it 指代 The dress 作宾语。划掉 it，用 that、which 或省略引导从句插在 The dress 后面。"}},
    {"id": "kp3_q6", "kp_label": "错题精讲 · Page 10 #8", "scene": {"kind": "combine_slide", "heading": "Page 10 #8：删掉句末宾语 him", "s1_pre": "On my vacation, I met", "s1_ant": "a boy", "s1_post": "", "s2_pre": "my father disliked", "s2_rep": "him", "s2_post": "", "rel_word": "whom/who/that", "commas": False, "final_sentence": "On my vacation, I met a boy (whom / who / that) my father disliked.", "rule": "必须删掉句末的 him！", "caption": "删掉 him，紧接在 a boy 之后。", "narration": "him 指代 a boy 作 disliked 的宾语。删掉 him，用 whom、who、that 或省略直接接在 a boy 后面。"}},
    {"id": "kp4_q1", "kp_label": "错题精讲 · B8 #3", "scene": {"kind": "multi_scanner", "heading": "B8 #3 逐项扫描：所属关系 whose", "sentence": "My grandmother, ( ______ ) maiden name was Faust, grew up in Germany.", "antecedent": "My grandmother (人)", "role": "her maiden name -> whose maiden name", "options": [("who", False, "不能修饰名词"), ("which", False, "不能指人/所有格"), ("whose", True, "替代 her + 名词")], "rule": "空格后紧跟名词 maiden name → 必选 whose", "caption": "唯一正确答案：whose。", "narration": "maiden name 是属于 grandmother 的，替代 her 必须用所有格 whose。"}},
    {"id": "kp4_q2", "kp_label": "错题精讲 · B8 #5", "scene": {"kind": "multi_scanner", "heading": "B8 #5 逐项扫描：whose name", "sentence": "I saw a former professor of mine ( ______ ) name I can never remember.", "antecedent": "a former professor (人)", "role": "his/her name -> whose name", "options": [("that", False, "不能表所属"), ("whose", True, "his/her name"), ("whom", False, "不能直接加名词")], "rule": "空格后紧跟光杆名词 name → 选 whose", "caption": "唯一正确答案：whose。", "narration": "空格后紧跟名词 name，表示教授的名字，唯一正确选项是 whose。"}},
    {"id": "kp4_q3", "kp_label": "错题精讲 · Review A #4", "scene": {"kind": "multi_scanner", "heading": "Review A #4：whose 永不可省略", "sentence": "The man ( ______ ) car we borrowed is my father's boss.", "antecedent": "The man (人)", "role": "his car -> whose car", "options": [("whose", True, "替代 his car"), ("which", False, "不能表所属"), ("who", False, "不能修饰 car"), ("Ø", False, "whose 不可省")], "rule": "whose 绝不能省略 Ø！", "caption": "we borrowed his car → 选 whose。", "narration": "we borrowed his car 变为 whose car we borrowed，whose 永远不能省略。"}},
    {"id": "kp4_q4", "kp_label": "错题精讲 · Note 4", "scene": {"kind": "multi_scanner", "heading": "Note 4：whose 修饰事物 & 不可省略", "sentence": "判断以下哪些句子正确使用了 whose：", "antecedent": "a theory / the book (物)", "role": "its origins / its reviews -> whose", "options": [("theory whose origins", True, "whose 可修饰物"), ("book whose reviews", True, "whose 可修饰物"), ("Harvey, house we...", False, "漏掉 whose"), ("theory which origins", False, "which 不能表所属")], "rule": "whose 人、物通用，且永不可省", "caption": "前两句正确，后两句漏了 whose 或误用 which。", "narration": "whose 既能修饰人也能修饰物，替代 its，并且永远不能省略。"}},
    {"id": "kp4_q5", "kp_label": "错题精讲 · Page 10 #9", "scene": {"kind": "combine_slide", "heading": "Page 10 #9：专有名词 Jacob + whose", "s1_pre": "", "s1_ant": "Jacob", "s1_post": "is in my biology class, which meets twice a week.", "s2_pre": "", "s2_rep": "His father", "s2_post": "is the ambassador from Kenya.", "rel_word": "whose father", "commas": True, "final_sentence": "Jacob, whose father is the ambassador from Kenya, is a student in my biology class, which meets twice a week.", "rule": "人名 Jacob 是专有名词，whose 从句前后加逗号", "caption": "两处合并：Jacob 后加 , whose father..., 句末加 , which meets...", "narration": "Jacob 是专有名词，把 His father 换成 whose father 并加上逗号插在 Jacob 后面，最后用 which meets twice a week 修饰 biology class。"}},
    {"id": "kp5_q1", "kp_label": "错题精讲 · B8 #2", "scene": {"kind": "multi_scanner", "heading": "B8 #2 逐项扫描：where vs which vs Ø", "sentence": "I was surprised to see the log house ( ______ ) my father grew up.", "antecedent": "the log house (地点)", "role": "grew up there (地点状语)", "options": [("where", True, "自带地点状语含义"), ("which", False, "句末缺介词 in"), ("Ø", False, "句末缺 in 不可省")], "rule": "句末没有 in 时，唯一正确答案是 where", "caption": "唯一正确答案：where。", "narration": "grew up 后面没有介词 in，所以不能单独用 which，也不能省略，唯一正确答案是 where。"}},
    {"id": "kp5_q2", "kp_label": "错题精讲 · B8 #8", "scene": {"kind": "multi_scanner", "heading": "B8 #8 逐项扫描：地点状语 where", "sentence": "It's ten miles from the town ( ______ ) I grew up.", "antecedent": "the town (地点)", "role": "grew up THERE", "options": [("when", False, "when 用于时间"), ("where", True, "替代 there"), ("Ø", False, "缺介词 in")], "rule": "地点状语且句末无介词 → 选 where", "caption": "唯一正确答案：where。", "narration": "the town 是地点，I grew up there 需要地点状语，所以选 where。"}},
    {"id": "kp5_q3", "kp_label": "错题精讲 · B8 #12", "scene": {"kind": "multi_scanner", "heading": "B8 #12 逐项扫描：时间名词 the day", "sentence": "I have fond memories of the day ( ______ ) I met my wife.", "antecedent": "the day (时间)", "role": "on that day (时间状语)", "options": [("that", True, "时间限定可用"), ("when", True, "标准时间状语"), ("Ø", True, "时间限定可省"), ("which", False, "不能单独表时间")], "rule": "限定性时间从句：when / that / Ø 全对（单独 which 不行）", "caption": "选 that、when 和 Ø！", "narration": "时间名词 the day 在限定性从句中可以用 when、that 或省略，但不能单独用 which。"}},
    {"id": "kp5_q4", "kp_label": "错题精讲 · Review A #2", "scene": {"kind": "multi_scanner", "heading": "Review A #2：地点状语 where", "sentence": "Hong Kong is the city ( ______ ) I was born.", "antecedent": "the city (地点)", "role": "was born THERE (地点状语)", "options": [("that", False, "不能单独作地点状语"), ("where", True, "替代 there 地点状语"), ("which", False, "不能单独作地点状语")], "rule": "I was born THERE → 必选 where", "caption": "唯一正确答案：where。", "narration": "I was born in Hong Kong 可还原成 there，句末没有 in，所以必须选 where。"}},
    {"id": "kp5_q5", "kp_label": "错题精讲 · Note 5", "scene": {"kind": "multi_scanner", "heading": "Note 5：警惕“假地点”主语陷阱！", "sentence": "Stockholm is a city ( ______ ) has beautiful scenery.", "antecedent": "a city (在此作主语！)", "role": "It has... (主语位置)", "options": [("where", False, "不能在 has 前作主语"), ("that", True, "指物作主语"), ("which", True, "指物作主语")], "rule": "空格后直接跟动词 has → 选 that / which，绝不选 where！", "caption": "不能说 there has！选 that 和 which。", "narration": "空格后面直接是动词 has，说明需要主语，where 不能作主语，必须选 that 或 which。"}},
    {"id": "kp5_q6", "kp_label": "错题精讲 · Page 10 #3", "scene": {"kind": "combine_slide", "heading": "Page 10 #3：where 替代并删除 there", "s1_pre": "", "s1_ant": "My driveway", "s1_post": "is in front of my house.", "s2_pre": "I park four cars", "s2_rep": "there", "s2_post": "", "rel_word": "where", "commas": True, "final_sentence": "My driveway, where I park four cars, is in front of my house.", "rule": "用 where 替换 there 后必须删掉句末的 there！", "caption": "My driveway, [where I park four cars], is in front of my house.", "narration": "用 where 替换句末的 there，把 where I park four cars 插在 My driveway 后面，一定要删掉多余的 there。"}},
    {"id": "kp6_q1", "kp_label": "错题精讲 · B8 #6", "scene": {"kind": "multi_scanner", "heading": "B8 #6：逗号后禁用 that 与 Ø", "sentence": "I was not expecting the present, ( ______ ) was much too expensive.", "antecedent": "the present (物 · 有逗号)", "role": "非限定性从句作主语", "options": [("that", False, "逗号后禁用 that"), ("which", True, "非限定指物主语"), ("Ø", False, "主语/逗号后均禁用")], "rule": "有逗号 = NO that + NO Ø", "caption": "唯一正确答案：which。", "narration": "看到 present 后面的逗号，立刻排除 that 和省略，指代物只能选 which。"}},
    {"id": "kp6_q2", "kp_label": "错题精讲 · B8 #9", "scene": {"kind": "multi_scanner", "heading": "B8 #9：逗号后指人作主语", "sentence": "My twin brother, ( ______ ) lives next door, calls me every day.", "antecedent": "My twin brother (人 · 逗号)", "role": "非限定性从句作主语", "options": [("that", False, "逗号后禁用 that"), ("who", True, "非限定指人主语"), ("Ø", False, "逗号后与主语均禁用")], "rule": "逗号后指人作主语 → 唯一选 who", "caption": "唯一正确答案：who。", "narration": "brother 后面有逗号，属于非限定性从句，指人作主语只能选 who，绝不能用 that 或省略。"}},
    {"id": "kp6_q3", "kp_label": "错题精讲 · Review A #3", "scene": {"kind": "multi_scanner", "heading": "Review A #3：逗号后宾语也禁用 that/Ø", "sentence": "Elena, ( ______ ) I met at the conference, has a Type A personality.", "antecedent": "Elena (人名 · 有逗号)", "role": "非限定性从句作宾语", "options": [("that", False, "逗号后禁用 that"), ("whom", True, "非限定指人宾语"), ("Ø", False, "逗号后禁止省略")], "rule": "平时作宾语可用 that/Ø，但一旦有逗号全部禁用！", "caption": "唯一正确答案：whom。", "narration": "Elena 是人名且有逗号，虽然作宾语，但逗号后禁用 that 和省略，只能选 whom。"}},
    {"id": "kp6_q4", "kp_label": "错题精讲 · Review A #5", "scene": {"kind": "multi_scanner", "heading": "Review A #5：逗号后指代整句话", "sentence": "Boris Popov is very detail-oriented, ( ______ ) is why we should hire him.", "antecedent": "前面整个分句", "role": "指代前文整件事作主语", "options": [("that", False, "逗号后禁用 that"), ("which", True, "指代整句话唯一选 which"), ("what", False, "不引导定语从句")], "rule": "指代前面整件事且在逗号后 → 只能用 , which", "caption": "唯一正确答案：which。", "narration": "逗号后面指代前面整件事，英语中只能用 which，绝不能用 that 或 what。"}},
    {"id": "kp6_q5", "kp_label": "错题精讲 · Page 10 #4", "scene": {"kind": "combine_slide", "heading": "Page 10 #4：专有名词 + 逗号 which", "s1_pre": "", "s1_ant": "The Industrial Revolution", "s1_post": "changed how people make things.", "s2_pre": "", "s2_rep": "It", "s2_post": "began in England.", "rel_word": "which", "commas": True, "final_sentence": "The Industrial Revolution, which began in England, changed the way people make things.", "rule": "独一无二的专有名词 → 加逗号并用 which（禁用 that）", "caption": "The Industrial Revolution, [which began in England], changed...", "narration": "工业革命是独一无二的专有名词，用逗号加 which began in England 插在主语后面。"}},
    {"id": "kp6_q6", "kp_label": "错题精讲 · Page 10 #6", "scene": {"kind": "combine_slide", "heading": "Page 10 #6：专有公司名 + 逗号 which", "s1_pre": "", "s1_ant": "British Petroleum", "s1_post": "received criticism...", "s2_pre": "", "s2_rep": "It", "s2_post": "is known as BP.", "rel_word": "which", "commas": True, "final_sentence": "British Petroleum, which is known as BP, received criticism because of the oil spill in the Gulf.", "rule": "专有公司名加逗号后只用 which，禁用 that", "caption": "British Petroleum, [which is known as BP], received criticism...", "narration": "British Petroleum 是公司专有名词，把 which is known as BP 用逗号隔开插在主语后面。"}},
]


def render_kinetic_video(spec, force=False, preview_dir=None):
    os.makedirs(STATIC_VIDEOS_DIR, exist_ok=True)
    os.makedirs(DOCS_VIDEOS_DIR, exist_ok=True)

    static_out = os.path.join(STATIC_VIDEOS_DIR, f"{spec['id']}.mp4")
    docs_out = os.path.join(DOCS_VIDEOS_DIR, f"{spec['id']}.mp4")
    if not force and not preview_dir and os.path.exists(static_out) and os.path.exists(docs_out):
        print(f"[skip] {spec['id']}.mp4 already exists.")
        return

    ffmpeg_bin = shutil.which("ffmpeg")
    if not ffmpeg_bin:
        raise RuntimeError("ffmpeg not found in PATH")

    scenes = spec["scenes"]
    with tempfile.TemporaryDirectory() as tmpdir:
        # 1. Generate neural voiceover WAV per scene & gather durations/envelopes
        scene_audio = []
        total_frames_all = 0
        for idx, sc in enumerate(scenes):
            wav_p = os.path.join(tmpdir, f"s_{idx}.wav")
            dur, env = synthesize_audio_wav(sc["narration"], wav_p)
            sc_frames = max(int(3.5 * FPS), int(math.ceil((dur + 0.45) * FPS)))
            # Pad WAV with silence to exact sc_frames duration
            padded_wav = os.path.join(tmpdir, f"sp_{idx}.wav")
            target_sec = sc_frames / float(FPS)
            subprocess.run([
                ffmpeg_bin, "-y", "-i", wav_p,
                "-af", f"apad=whole_dur={target_sec:.4f}",
                "-ar", "24000", "-ac", "1", "-c:a", "pcm_s16le",
                padded_wav
            ], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, check=True)
            scene_audio.append((padded_wav, sc_frames, env))
            total_frames_all += sc_frames

        # 2. Concatenate audio track
        full_wav = os.path.join(tmpdir, "full.wav")
        if len(scene_audio) == 1:
            shutil.copy2(scene_audio[0][0], full_wav)
        else:
            cl = os.path.join(tmpdir, "aud.txt")
            with open(cl, "w", encoding="utf-8") as f:
                for pw, _, _ in scene_audio:
                    f.write(f"file '{pw.replace(chr(92), '/')}'\n")
            subprocess.run([ffmpeg_bin, "-y", "-f", "concat", "-safe", "0", "-i", cl, "-c", "copy", full_wav],
                           stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, check=True)

        # 3. Pipe 24fps raw RGB frames directly into FFmpeg (log stderr to file -> never deadlocks!)
        ffmpeg_log = os.path.join(tmpdir, "ffmpeg.log")
        cmd = [
            ffmpeg_bin, "-y", "-loglevel", "error",
            "-f", "rawvideo", "-vcodec", "rawvideo", "-pix_fmt", "rgb24",
            "-s", f"{W}x{H}", "-r", str(FPS), "-i", "-",
            "-i", full_wav,
            "-c:v", "libx264", "-preset", "fast", "-crf", "24", "-pix_fmt", "yuv420p",
            "-c:a", "aac", "-b:a", "96k", "-ar", "44100",
            "-shortest", "-movflags", "+faststart",
            static_out
        ]
        with open(ffmpeg_log, "wb") as err_f:
            proc = subprocess.Popen(cmd, stdin=subprocess.PIPE, stdout=subprocess.DEVNULL, stderr=err_f)

            global_f = 0
            saved_previews = set()
            for s_idx, sc in enumerate(scenes):
                _, sc_frames, env = scene_audio[s_idx]
                kind = sc["kind"]
                for f in range(sc_frames):
                    p = f / float(max(1, sc_frames - 1))
                    gp = global_f / float(max(1, total_frames_all - 1))
                    rms = env[f] if f < len(env) else 0.0

                    img = BASE_BG.copy()
                    draw_ambient_bg(img, gp)
                    draw = ImageDraw.Draw(img)

                    if kind == "combine_slide":
                        render_combine_slide(draw, sc, p)
                    elif kind == "trap_smash":
                        render_trap_smash(draw, sc, p)
                    elif kind == "multi_scanner":
                        render_multi_scanner(draw, sc, p)
                    elif kind == "mindmap_grow":
                        render_mindmap_grow(draw, sc, p)

                    rule_alpha = seg_p(p, 0.72, 0.88)
                    draw_chrome(draw, spec["kp_label"], s_idx, len(scenes), gp, rms, sc.get("caption", ""), sc.get("rule", ""), rule_alpha)

                    if preview_dir:
                        for frac in (0.34, 0.54, 0.90):
                            key = (s_idx, frac)
                            if key not in saved_previews and p >= frac:
                                os.makedirs(preview_dir, exist_ok=True)
                                img.save(os.path.join(preview_dir, f"{spec['id']}_s{s_idx}_{int(frac*100)}.png"))
                                saved_previews.add(key)

                    try:
                        proc.stdin.write(img.tobytes())
                    except BrokenPipeError:
                        break
                    global_f += 1

            try:
                proc.stdin.close()
            except BrokenPipeError:
                pass
            ret = proc.wait()

        if ret != 0:
            with open(ffmpeg_log, "r", encoding="utf-8", errors="ignore") as lf:
                stderr_out = lf.read()
            raise RuntimeError(f"ffmpeg failed ({ret}): {stderr_out[-300:]}")

    shutil.copy2(static_out, docs_out)
    size_kb = os.path.getsize(static_out) / 1024
    print(f"[done] {spec['id']}.mp4 ({size_kb:.1f} KB, {total_frames_all/FPS:.1f}s @ {FPS}fps)", flush=True)


def _worker_render(args_tuple):
    sp, force, preview_dir = args_tuple
    render_kinetic_video(sp, force=force, preview_dir=preview_dir)
    return sp["id"]


def main():
    from concurrent.futures import ProcessPoolExecutor, as_completed
    parser = argparse.ArgumentParser(description="Render 24fps kinetic motion-graphics MP4 videos with neural voiceover")
    parser.add_argument("--mode", choices=["kp", "all"], default="all")
    parser.add_argument("--ids", nargs="*")
    parser.add_argument("--force", action="store_true")
    parser.add_argument("--preview-dir", default=None)
    parser.add_argument("--workers", type=int, default=4)
    args = parser.parse_args()

    q_specs = [{"id": q["id"], "kp_label": q["kp_label"], "scenes": [q["scene"]]} for q in QUESTION_SPECS]
    all_specs = list(KP_VIDEOS) + q_specs
    if args.ids:
        wanted = set(args.ids)
        specs = [s for s in all_specs if s["id"] in wanted]
    elif args.mode == "kp":
        specs = list(KP_VIDEOS)
    else:
        specs = all_specs

    workers = max(1, min(args.workers, len(specs)))
    print(f"Rendering {len(specs)} kinetic 24fps videos with {workers} parallel worker(s)...", flush=True)
    if workers == 1:
        for i, sp in enumerate(specs, 1):
            print(f"[{i}/{len(specs)}] Rendering kinetic {sp['id']}...", flush=True)
            render_kinetic_video(sp, force=args.force, preview_dir=args.preview_dir)
    else:
        os.makedirs(STATIC_VIDEOS_DIR, exist_ok=True)
        os.makedirs(DOCS_VIDEOS_DIR, exist_ok=True)
        done = 0
        with ProcessPoolExecutor(max_workers=workers) as ex:
            futs = [ex.submit(_worker_render, (sp, args.force, args.preview_dir)) for sp in specs]
            for fut in as_completed(futs):
                vid_id = fut.result()
                done += 1
                print(f"  => Progress: {done}/{len(specs)} ({vid_id})", flush=True)


if __name__ == "__main__":
    main()
