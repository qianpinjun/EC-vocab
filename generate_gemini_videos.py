#!/usr/bin/env python3
"""
Pre-generate real MP4 explainer videos using Gemini Omni 1.2 Flash (gemini-omni-1.2-flash)
via the official google-genai SDK + Interactions API, then burn crisp grammar
subtitles with ffmpeg and save to both static/videos/ and docs/videos/.

Usage:
  pip install -U google-genai
  $env:GEMINI_API_KEY="your-gemini-api-key"
  python generate_gemini_videos.py --mode kp         # 6 Knowledge Point videos (recommended first)
  python generate_gemini_videos.py --mode all        # All KP + per-question explanation videos
  python generate_gemini_videos.py --ids kp1_q1      # Specific video ID(s)
  python generate_gemini_videos.py --dry-run         # Preview jobs without calling API
"""

import argparse
import base64
import os
import shutil
import subprocess
import sys
import tempfile
import time

DEFAULT_MODEL = "gemini-omni-1.1-flash"
ALT_MODEL = "gemini-omni-1.2-flash"
STATIC_VIDEOS_DIR = os.path.join("static", "videos")
DOCS_VIDEOS_DIR = os.path.join("docs", "videos")

# 6 Knowledge Point Quick Reminder video specifications
KP_VIDEO_JOBS = [
    {
        "id": "kp1_placement",
        "title": "KP 01 · Placement & Clauses",
        "prompt": (
            "Clean modern animated educational whiteboard video, bright minimalist studio style. "
            "An engaging English teacher illustrates combining two sentences on a sleek digital board: "
            "'The professor emailed me.' + 'He teaches Russian.' sliding together to highlight "
            "'The professor who teaches Russian emailed me.' Smooth motion arrows pointing to the noun 'professor', "
            "friendly spoken English explanation of adjective clause placement directly after the noun, clear upbeat tone."
        ),
        "subtitles": [
            (0.3, 3.5, "KP 01: Adjective Clause Placement (定语从句位置)"),
            (3.6, 7.0, "Rule: Put the clause directly AFTER the noun it modifies."),
            (7.1, 9.8, "The professor [who teaches Russian] emailed me."),
        ],
    },
    {
        "id": "kp2_subjects",
        "title": "KP 02 · Subject Relative Pronouns",
        "prompt": (
            "Clean modern animated educational whiteboard video, bright minimalist studio style. "
            "Animated grammar lesson showing 'WHO / THAT' for people and 'WHICH / THAT' for things as subjects, "
            "with a red X crossing out a duplicate subject pronoun 'who he' and green checkmark on 'who'. "
            "Friendly spoken English narration explaining subject relative pronouns and verb agreement."
        ),
        "subtitles": [
            (0.3, 3.5, "KP 02: Subjects: WHO / THAT (People), WHICH / THAT (Things)"),
            (3.6, 7.0, "Never repeat the subject! (NO 'who he' or 'which it')"),
            (7.1, 9.8, "Subject pronouns can NEVER be omitted (No Ø)."),
        ],
    },
    {
        "id": "kp3_objects",
        "title": "KP 03 · Objects, Omission & Prepositions",
        "prompt": (
            "Clean modern animated educational whiteboard video, bright minimalist studio style. "
            "Animated grammar demonstration showing an object relative pronoun disappearing into an empty circle (Ø) "
            "in 'The dress (that/which/Ø) Mary wore', followed by moving 'to' before 'whom' in 'the man to whom I gave the money'. "
            "Clear spoken English explanation."
        ),
        "subtitles": [
            (0.3, 3.5, "KP 03: Object Pronouns: who(m) / which / that / Ø"),
            (3.6, 7.0, "Identifying object pronouns can be omitted (Ø)."),
            (7.1, 9.8, "After a preposition, ONLY use whom or which (to whom)."),
        ],
    },
    {
        "id": "kp4_whose",
        "title": "KP 04 · Possession with WHOSE",
        "prompt": (
            "Clean modern animated educational whiteboard video, bright minimalist studio style. "
            "Visual grammar card transforming 'his / her / its / their + noun' into 'whose + noun', "
            "showing 'the man whose car we borrowed' and 'a theory whose origins go back'. "
            "Friendly spoken English explanation emphasizing whose can never be omitted."
        ),
        "subtitles": [
            (0.3, 3.5, "KP 04: WHOSE + Noun = his / her / its / their + noun"),
            (3.6, 7.0, "Works for BOTH people and things (whose origins)."),
            (7.1, 9.8, "BE CAREFUL: 'whose' can NEVER be omitted!"),
        ],
    },
    {
        "id": "kp5_where_when",
        "title": "KP 05 · WHERE & WHEN Clauses",
        "prompt": (
            "Clean modern animated educational whiteboard video, bright minimalist studio style. "
            "Animated grammar test showing 'where' equals 'there / in which', contrasting "
            "'the town where I was born' (checkmark) against 'a city that has scenery' (not 'where has'). "
            "Clear spoken English explanation of where and when."
        ),
        "subtitles": [
            (0.3, 3.5, "KP 05: WHERE = there / in which (Place Adverbial)"),
            (3.6, 7.0, "Trap: NEVER use 'where' as subject (use that/which has)."),
            (7.1, 9.8, "Time nouns allow: when / that / Ø (the day I met you)."),
        ],
    },
    {
        "id": "kp6_commas",
        "title": "KP 06 · Identifying vs. Nonidentifying (Commas)",
        "prompt": (
            "Clean modern animated educational whiteboard video, bright minimalist studio style. "
            "Visual grammar split screen comparing no commas vs. commas around extra information for proper nouns "
            "like 'Sara Gomez, who created the test, ...' with bold warning badges banning 'that' and omission after a comma. "
            "Friendly spoken English narration."
        ),
        "subtitles": [
            (0.3, 3.5, "KP 06: Commas = Extra Info (Nonidentifying Clause)"),
            (3.6, 7.0, "After a comma: NEVER use 'that' and NEVER omit (Ø)!"),
            (7.1, 9.8, "Use ', which' to refer to an entire preceding clause."),
        ],
    },
]

# Per-question explanation video specs (short targeted explanations)
QUESTION_VIDEO_SPECS = [
    ("kp1_q1", "The professor who teaches Russian emailed me.", "Put 'who teaches Russian' right after 'The professor'."),
    ("kp1_q2", "The little girl who hurt her knee was crying.", "Place the clause right after 'The little girl'."),
    ("kp1_q3", "Students who are anxious do well on tests...", "Insert 'who/that are anxious' right after 'Students'."),
    ("kp1_q4", "The child who was sick went home.", "Place 'who was sick' right after 'The child'."),
    ("kp1_q5", "The car that/which belongs to my uncle is outside.", "Keep clause next to 'The car'; no duplicate 'it'."),
    ("kp2_q1", "Anyone who/that enjoyed the movie...", "Subject for people: use who or that (never whom or Ø)."),
    ("kp2_q2", "The lady who/that is my teacher...", "Subject for people: use who or that (never which)."),
    ("kp2_q3", "Chuy is a person who prefers to be alone.", "No double subject! Never write 'who he'."),
    ("kp2_q4", "Lions are the animals that Lea likes the best.", "Verb agrees with clause subject 'Lea' (likes)."),
    ("kp2_q5", "I picked up the package that/which was lying...", "Subject for thing: replace 'It' with that/which."),
    ("kp2_q6", "Recently, a large airplane that/which was carrying...", "Replace 'It' with that/which after 'airplane'."),
    ("kp3_q1", "The girl (that/who/Ø) I sat next to...", "Object for person with 'to' at end: that, who, or Ø."),
    ("kp3_q2", "It's a situation (that/which) I'd rather not think about.", "'about' is already at the end; do NOT use 'to which'."),
    ("kp3_q3", "Nelson Mandela is a politician (who/whom/Ø) I respect.", "Object for person: who, whom, or Ø are all valid."),
    ("kp3_q4", "I didn't see the face of the man to whom I gave the money.", "No 'to' at the end -> must use 'to whom'."),
    ("kp3_q5", "The dress (that/which) Mary wore was long...", "Object pronoun replaces and deletes 'it'."),
    ("kp3_q6", "On my vacation, I met a boy (who/whom/that) my father disliked.", "Object pronoun replaces and deletes 'him'."),
    ("kp4_q1", "My grandmother, whose maiden name was Faust...", "Possession + noun ('maiden name') -> use 'whose'."),
    ("kp4_q2", "I saw a former professor whose name I forget.", "Possession ('his name') -> use 'whose name'."),
    ("kp4_q3", "The man whose car we borrowed...", "Possession ('his car') -> 'whose' can never be omitted."),
    ("kp4_q4", "It's a theory whose origins go back many years.", "'whose' works for things too, and cannot be omitted."),
    ("kp4_q5", "Jacob, whose father is ambassador, ... class, which meets...", "Proper noun Jacob needs commas + whose."),
    ("kp5_q1", "the log house (where / in which) my father grew up", "No 'in' at end -> use 'where' or 'in which' (not Ø)."),
    ("kp5_q2", "the town where I grew up", "Place adverbial ('there') without preposition -> 'where'."),
    ("kp5_q3", "the day (that / when / Ø) I met my wife", "Time noun 'the day' allows when, that, or Ø."),
    ("kp5_q4", "Hong Kong is the city where I was born.", "'I was born there' -> use 'where'."),
    ("kp5_q5", "Stockholm is a city that/which has beautiful scenery.", "Before verb 'has', use subject 'that/which' (NOT where!)."),
    ("kp5_q6", "My driveway, where I park four cars, is in front...", "Replace 'there' with 'where' and delete 'there'."),
    ("kp6_q1", "the present, which was much too expensive...", "After comma: NEVER use 'that' or Ø -> use 'which'."),
    ("kp6_q2", "My twin brother, who lives next door...", "After comma for person subject -> use 'who' only."),
    ("kp6_q3", "Elena, whom I met at the conference...", "After comma, even objects CANNOT use 'that' or Ø."),
    ("kp6_q4", "Boris is detail-oriented, which is why...", "Referring to whole clause after comma -> ', which'."),
    ("kp6_q5", "The Industrial Revolution, which began in England...", "Proper noun takes commas + 'which' (never 'that')."),
    ("kp6_q6", "British Petroleum, which is known as BP...", "Company proper name takes commas + 'which'."),
]


def build_question_job(qid, answer, rule):
    return {
        "id": qid,
        "title": f"Mistake Review · {qid}",
        "prompt": (
            "Clean modern animated educational whiteboard video, bright minimalist studio style. "
            f"An English grammar instructor explains a sentence correction on a sleek board showing '{answer}' "
            f"with a glowing highlight on the relative clause connector. Friendly clear English voiceover."
        ),
        "subtitles": [
            (0.3, 4.5, f"Rule: {rule}"),
            (4.6, 9.5, f"Correct: {answer}"),
        ],
    }


def write_srt(subtitles, srt_path):
    def fmt_ts(sec):
        ms = int(round((sec % 1) * 1000))
        s = int(sec) % 60
        m = (int(sec) // 60) % 60
        h = int(sec) // 3600
        return f"{h:02d}:{m:02d}:{s:02d},{ms:03d}"

    with open(srt_path, "w", encoding="utf-8") as f:
        for i, (start, end, text) in enumerate(subtitles, 1):
            f.write(f"{i}\n{fmt_ts(start)} --> {fmt_ts(end)}\n{text}\n\n")


def burn_subtitles_ffmpeg(raw_mp4, out_mp4, subtitles):
    ffmpeg_bin = shutil.which("ffmpeg")
    if not ffmpeg_bin or not subtitles:
        shutil.copy2(raw_mp4, out_mp4)
        return

    with tempfile.TemporaryDirectory() as tmpdir:
        srt_path = os.path.join(tmpdir, "subs.srt")
        write_srt(subtitles, srt_path)
        abs_raw = os.path.abspath(raw_mp4)
        abs_out = os.path.abspath(out_mp4)
        cmd = [
            ffmpeg_bin, "-y", "-i", abs_raw,
            "-vf", "subtitles=subs.srt:force_style='Fontsize=18,PrimaryColour=&H00FFFFFF,OutlineColour=&H00000000,BackColour=&H80000000,BorderStyle=3,Outline=1,MarginV=22'",
            "-c:a", "copy",
            abs_out
        ]
        proc = subprocess.run(cmd, cwd=tmpdir, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
        if proc.returncode != 0:
            print(f"  [warn] ffmpeg subtitle burn failed, keeping raw video: {proc.stderr[-200:]}")
            shutil.copy2(raw_mp4, out_mp4)


def _extract_video_bytes(client, output_video):
    if not output_video:
        return None
    if getattr(output_video, "data", None):
        data = output_video.data
        return base64.b64decode(data) if isinstance(data, str) else data
    if getattr(output_video, "uri", None):
        return client.files.download(file=output_video.uri)
    return None


def _run_interaction(client, m_name, job, resolution, duration):
    response_fmt = {
        "type": "video",
        "aspect_ratio": "16:9",
        "resolution": resolution,
    }
    if duration:
        response_fmt["duration"] = duration

    req_kwargs = {
        "model": m_name,
        "input": job["prompt"],
        "response_format": response_fmt,
    }

    try:
        interaction = client.interactions.create(**req_kwargs, background=True)
        print(f"  [async] Started job {interaction.id}, polling every 5s...", flush=True)
        elapsed = 0
        while True:
            status = getattr(interaction, "status", None)
            if status in (None, "completed"):
                break
            if status in ("failed", "cancelled", "incomplete"):
                details = interaction.model_dump(exclude_none=True) if hasattr(interaction, "model_dump") else repr(interaction)
                raise RuntimeError(f"Interaction {interaction.id} ended with status={status} | details={details}")
            if elapsed >= 300:
                raise TimeoutError(f"Video generation timed out after {elapsed}s for {job['id']}")
            time.sleep(5)
            elapsed += 5
            interaction = client.interactions.get(interaction.id)
            print(f"  [poll {elapsed}s] status={getattr(interaction, 'status', '?')}", flush=True)
        return interaction
    except Exception as e:
        if "background" in str(e).lower() and ("400" in str(e) or "invalid" in str(e).lower() or "unsupported" in str(e).lower()):
            print("  [sync] background=True unsupported, running synchronous request (max 240s)...", flush=True)
            return client.interactions.create(**req_kwargs)
        raise


def _create_with_fallback(genai, types, job, model, api_version, resolution, duration):
    attempts = [(model, api_version)]
    if api_version != "v1":
        attempts.append((model, "v1"))
    if model != ALT_MODEL:
        attempts.append((ALT_MODEL, "v1beta"))

    last_err = None
    for m_name, ver in attempts:
        opts = types.HttpOptions(timeout=240 * 1000, api_version=ver)
        client = genai.Client(http_options=opts)
        for net_try in range(1, 4):
            try:
                print(f"[gen] {job['id']} ({job['title']}) via {m_name} ({ver}, {resolution}, {duration})...", flush=True)
                interaction = _run_interaction(client, m_name, job, resolution, duration)
                video_bytes = _extract_video_bytes(client, interaction.output_video)
                if not video_bytes:
                    raise RuntimeError(f"No output_video returned for {job['id']}")
                return video_bytes
            except Exception as e:
                last_err = e
                msg = str(e)
                lower_msg = msg.lower()
                if "404" in msg or "not_found" in lower_msg or "not found" in lower_msg:
                    print(f"  [fallback] {m_name} ({ver}) not found, trying next...", flush=True)
                    break
                if ("eof" in lower_msg or "connect" in lower_msg or "ssl" in lower_msg or "timeout" in lower_msg) and net_try < 3:
                    print(f"  [retry {net_try}/3] Network/SSL drop, retrying in 3s...", flush=True)
                    time.sleep(3)
                    continue
                raise
    raise last_err


def generate_one(genai, types, job, model=DEFAULT_MODEL, api_version="v1", resolution="360p", duration="10s", force=False):
    os.makedirs(STATIC_VIDEOS_DIR, exist_ok=True)
    os.makedirs(DOCS_VIDEOS_DIR, exist_ok=True)

    static_out = os.path.join(STATIC_VIDEOS_DIR, f"{job['id']}.mp4")
    docs_out = os.path.join(DOCS_VIDEOS_DIR, f"{job['id']}.mp4")

    if not force and os.path.exists(static_out) and os.path.exists(docs_out):
        print(f"[skip] {job['id']}.mp4 already exists.")
        return

    video_bytes = _create_with_fallback(genai, types, job, model, api_version, resolution, duration)
    with tempfile.TemporaryDirectory() as tmpdir:
        raw_mp4 = os.path.join(tmpdir, "raw.mp4")
        with open(raw_mp4, "wb") as f:
            f.write(video_bytes)
        burn_subtitles_ffmpeg(raw_mp4, static_out, job.get("subtitles"))

    shutil.copy2(static_out, docs_out)
    size_kb = os.path.getsize(static_out) / 1024
    print(f"[done] Saved {static_out} & {docs_out} ({size_kb:.1f} KB)")


def main():
    parser = argparse.ArgumentParser(description="Pre-generate Gemini Omni MP4 videos for EC Grammar Studio")
    parser.add_argument("--mode", choices=["kp", "all"], default="kp", help="kp = 6 Knowledge Point videos; all = KP + per-question videos")
    parser.add_argument("--ids", nargs="*", help="Generate only specific video IDs (e.g. kp1_placement kp1_q1)")
    parser.add_argument("--model", default=DEFAULT_MODEL, help="Video model ID (default: gemini-omni-1.1-flash)")
    parser.add_argument("--api-version", default="v1beta", choices=["v1", "v1beta"], help="Gemini API version")
    parser.add_argument("--resolution", choices=["360p", "720p", "1080p"], default="360p", help="360p keeps GitHub Pages repo light")
    parser.add_argument("--duration", default=None, help="Optional clip duration (e.g. 5s, 10s); omit for model default")
    parser.add_argument("--inspect", default=None, help="Inspect an existing interaction ID to see full status/error details")
    parser.add_argument("--force", action="store_true", help="Overwrite existing MP4 files")
    parser.add_argument("--check", action="store_true", help="Quickly test API key & list available video models")
    parser.add_argument("--dry-run", action="store_true", help="List planned jobs without calling Gemini API")
    args = parser.parse_args()

    all_jobs = list(KP_VIDEO_JOBS) + [build_question_job(qid, ans, rule) for qid, ans, rule in QUESTION_VIDEO_SPECS]
    if args.ids:
        wanted = set(args.ids)
        jobs = [j for j in all_jobs if j["id"] in wanted]
    elif args.mode == "kp":
        jobs = list(KP_VIDEO_JOBS)
    else:
        jobs = all_jobs

    if not jobs:
        print("No matching video jobs found.")
        sys.exit(1)

    if args.dry_run:
        print(f"Dry run: {len(jobs)} video job(s) planned ({args.resolution}, {args.duration}):")
        for j in jobs:
            print(f"  - {j['id']}.mp4 : {j['title']}")
        return

    api_key = os.environ.get("GEMINI_API_KEY")
    if not api_key:
        print("Error: GEMINI_API_KEY environment variable is not set.", file=sys.stderr)
        print("Run: $env:GEMINI_API_KEY=\"your-api-key\"", file=sys.stderr)
        sys.exit(2)

    try:
        from google import genai
        from google.genai import types
    except ImportError:
        print("Error: google-genai SDK is not installed. Run: pip install -U google-genai", file=sys.stderr)
        sys.exit(2)

    if args.inspect:
        c = genai.Client(http_options=types.HttpOptions(timeout=30 * 1000, api_version=args.api_version))
        it = c.interactions.get(args.inspect)
        print(it.model_dump(exclude_none=True) if hasattr(it, "model_dump") else repr(it))
        return

    if args.check:
        for ver in ["v1", "v1beta"]:
            print(f"Checking {ver} models (15s timeout)...", flush=True)
            c = genai.Client(http_options=types.HttpOptions(timeout=15 * 1000, api_version=ver))
            names = [m.name for m in c.models.list() if any(k in m.name.lower() for k in ("omni", "veo", "video", "gemini-4", "gemini-3"))]
            print(f"  {ver} matches ({len(names)}):", names[:20], flush=True)
        return

    for i, job in enumerate(jobs, 1):
        print(f"--- [{i}/{len(jobs)}] ---")
        generate_one(
            genai, types, job,
            model=args.model,
            api_version=args.api_version,
            resolution=args.resolution,
            duration=args.duration,
            force=args.force,
        )
        if i < len(jobs):
            time.sleep(1)


if __name__ == "__main__":
    main()
