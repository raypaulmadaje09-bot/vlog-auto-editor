import os
import glob
from moviepy.editor import (
    VideoFileClip,
    AudioFileClip,
    CompositeAudioClip,
    concatenate_videoclips,
    vfx
)

def cinematic_color_grade(clip):
    graded = clip.fx(vfx.lum_contrast, lum=0, contrast=0.15, contrast_thr=127)
    graded = graded.fx(vfx.colorx, 1.12)
    return graded

def process_clip(file_path, target_duration=None):
    clip = VideoFileClip(file_path)
    if target_duration and clip.duration > target_duration:
        start_t = max(0, (clip.duration - target_duration) / 2)
        end_t = start_t + target_duration
        clip = clip.subclip(start_t, end_t)
    clip = clip.fx(vfx.fadein, 0.4).fx(vfx.fadeout, 0.4)
    return cinematic_color_grade(clip)

def build_vlog():
    footage_dir = "footage"
    audio_dir = "audio"
    output_dir = "output"
    os.makedirs(output_dir, exist_ok=True)

    extensions = ('*.mp4', '*.MP4', '*.mov', '*.MOV')
    raw_files = []
    for ext in extensions:
        raw_files.extend(glob.glob(os.path.join(footage_dir, ext)))
    raw_files.sort()

    if not raw_files:
        print(f"Walang nakitang video files sa /{footage_dir}! Maglagay ng clips.")
        return

    print(f"Found {len(raw_files)} raw footage clips. Sequencing timeline...")

    processed_clips = []
    for idx, path in enumerate(raw_files):
        target_dur = 4.5 if idx == 0 else 8.0
        print(f"Processing ({idx+1}/{len(raw_files)}): {path}")
        processed_clips.append(process_clip(path, target_duration=target_dur))

    final_video = concatenate_videoclips(processed_clips, method="compose")
    print(f"Total video duration: {final_video.duration:.1f} seconds")

    bgm_files = glob.glob(os.path.join(audio_dir, "*.mp3")) + glob.glob(os.path.join(audio_dir, "*.wav"))
    audio_tracks = []
    if final_video.audio is not None:
        audio_tracks.append(final_video.audio.volumex(1.1))

    if bgm_files:
        bgm_path = bgm_files[0]
        print(f"Applying BGM track: {bgm_path}")
        bgm = AudioFileClip(bgm_path)
        if bgm.duration < final_video.duration:
            bgm = bgm.fx(vfx.audio_loop, duration=final_video.duration)
        else:
            bgm = bgm.subclip(0, final_video.duration)
        bgm = bgm.volumex(0.16).audio_fadeout(2.0)
        audio_tracks.append(bgm)

    if audio_tracks:
        final_video.audio = CompositeAudioClip(audio_tracks)

    output_path = os.path.join(output_dir, "cinematic_long_vlog.mp4")
    print(f"Rendering final export to {output_path}...")
    final_video.write_videofile(
        output_path,
        codec="libx264",
        audio_codec="aac",
        fps=30,
        preset="fast",
        threads=4
    )
    print("Export complete!")

if __name__ == "__main__":
    build_vlog()
