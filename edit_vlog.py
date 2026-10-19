"""
Zero-Upload Pro Vlog Editor
- Self-Generating Whoosh SFX: Synthesizes acoustic whooshes directly via NumPy/SciPy
- Auto-BGM Support: Plays bundled/auto-fetched royalty-free ambient track
- 5-8 Minute Dynamic Pacing & Geo Ong Tropical Grading
"""

import os
import glob
import numpy as np
import cv2
from moviepy.editor import (
    VideoFileClip,
    AudioFileClip,
    CompositeAudioClip,
    concatenate_videoclips,
    vfx
)
from moviepy.audio.AudioClip import AudioArrayClip

def generate_synthetic_whoosh(duration=0.5, fps=44100):
    """Generates an organic cinematic whoosh using noise modulation without any audio files."""
    t = np.linspace(0, 1, int(fps * duration))
    # Gaussian envelope para sa smooth whoosh sweep
    envelope = np.exp(-((t - 0.5) ** 2) / (2 * (0.12 ** 2)))
    # Frequency modulation sweep
    freq = 150 + 600 * envelope
    noise = np.random.uniform(-1, 1, len(t))
    # Sound shaping
    signal = noise * envelope * np.sin(2 * np.pi * freq * t)
    signal = signal / (np.max(np.abs(signal)) + 1e-6) # Normalize
    stereo = np.column_stack((signal, signal))
    return AudioArrayClip(stereo, fps=fps).volumex(0.35)

def geo_ong_color_grade(clip):
    """Warm, saturated adventure colors."""
    graded = clip.fx(vfx.lum_contrast, lum=3, contrast=0.18, contrast_thr=128)
    graded = graded.fx(vfx.colorx, 1.15)
    return graded

def add_smooth_motion(clip, zoom_speed=0.03):
    def effect(get_frame, t):
        img = get_frame(t)
        h, w = img.shape[:2]
        scale = 1.0 + (zoom_speed * (t / max(clip.duration, 0.1)))
        nh, nw = int(h / scale), int(w / scale)
        top = (h - nh) // 2
        left = (w - nw) // 2
        cropped = img[top:top + nh, left:left + nw]
        return cv2.resize(cropped, (w, h))
    try:
        return clip.fl(effect)
    except Exception:
        return clip

def process_clip(file_path, duration=7.5):
    clip = VideoFileClip(file_path)
    if clip.duration > duration:
        start_t = (clip.duration - duration) / 2
        clip = clip.subclip(start_t, start_t + duration)
    clip = geo_ong_color_grade(clip)
    clip = add_smooth_motion(clip)
    return clip

def build_vlog():
    footage_dir = "footage"
    output_dir = "output"
    os.makedirs(output_dir, exist_ok=True)

    extensions = ('*.mp4', '*.MP4', '*.mov', '*.MOV')
    files = []
    for ext in extensions:
        files.extend(glob.glob(os.path.join(footage_dir, ext)))
    files.sort()

    if not files:
        print("Walang video clips sa loob ng footage/ folder!")
        return

    TARGET_TOTAL_SECONDS = 330.0  # 5.5 minutes target
    timeline_clips = []
    cut_timestamps = []
    current_time = 0.0

    print("Building sequence to 5-8 minutes...")
    while current_time < TARGET_TOTAL_SECONDS:
        for f in files:
            processed = process_clip(f, duration=7.5)
            timeline_clips.append(processed)
            current_time += processed.duration
            cut_timestamps.append(current_time)
            if current_time >= TARGET_TOTAL_SECONDS:
                break

    base_video = concatenate_videoclips(timeline_clips, method="compose")
    print(f"Total Video Length: {base_video.duration / 60:.2f} mins")

    audio_layers = []

    # 1. Natural Audio
    if base_video.audio is not None:
        audio_layers.append(base_video.audio.volumex(1.15))

    # 2. Self-Generated Whoosh on every transition (No files needed!)
    print(f"Synthesizing {len(cut_timestamps)-1} transition whoosh effects on the fly...")
    whoosh_sound = generate_synthetic_whoosh(duration=0.45)
    for cut_t in cut_timestamps[:-1]:
        start_at = max(0.0, cut_t - 0.22)
        audio_layers.append(whoosh_sound.set_start(start_at))

    # 3. Auto-downloaded BGM
    auto_bgm = "bgm.mp3"
    if os.path.exists(auto_bgm):
        print("Attaching auto-downloaded background music...")
        bgm = AudioFileClip(auto_bgm)
        if bgm.duration < base_video.duration:
            bgm = bgm.fx(vfx.audio_loop, duration=base_video.duration)
        else:
            bgm = bgm.subclip(0, base_video.duration)
        audio_layers.append(bgm.volumex(0.18).audio_fadein(1.5).audio_fadeout(3.0))

    if audio_layers:
        base_video.audio = CompositeAudioClip(audio_layers)

    out_path = os.path.join(output_dir, "cinematic_long_vlog.mp4")
    print(f"Rendering full automated vlog to {out_path}...")
    base_video.write_videofile(
        out_path,
        codec="libx264",
        audio_codec="aac",
        fps=30,
        preset="fast",
        threads=4
    )
    print("All done!")

if __name__ == "__main__":
    build_vlog()