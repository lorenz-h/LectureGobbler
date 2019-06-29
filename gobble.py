import argparse
import shutil
import subprocess

import numpy as np
import moviepy
from moviepy.editor import VideoFileClip, concatenate_videoclips
import matplotlib.pyplot as plt
import moviepy.video.fx.all as vfx
from moviepy.config import get_setting

from utils import make_path_absolute, create_dir


def get_silent_segments(clip, silence_threshold, min_silence_length):
    vols = []
    for i, audio_frame in enumerate(clip.audio.iter_frames(fps=clip.fps)):
        vol = np.mean(np.abs(audio_frame))
        vols.append(vol)
        if i / clip.fps % 10 == 0 and int(i / clip.fps) != 0:
            print(f"Parsed {i / clip.fps} seconds")
    
    
    avg_vol = np.mean(np.array(vols))

    seg_start = None
    silence_segments = []
    
    for i in range(len(vols)):
        if vols[i] < silence_threshold * avg_vol:
            if seg_start is None:
                seg_start  = i / float(clip.fps)
        else:
            if seg_start is not None:
                if i / float(clip.fps) - seg_start > min_silence_length:
                    segment_bounds = (seg_start, i / float(clip.fps))
                    silence_segments.append(segment_bounds)
                seg_start = None

    
    print(f"Found {len(silence_segments)} silences in video.")

    assert len(silence_segments) != 0, "No silences to remove"
    return silence_segments


def condense_clip_ffmpeg(orig_vid, silence_threshold=0.1,  min_silence_length=0.15, playback_speed=1.1):
    try:
        shutil.rmtree('_temp')
    except FileNotFoundError:
        pass
    tempdir = create_dir("_temp")
    
    
    silence_segments = get_silent_segments(clip, silence_threshold, min_silence_length)
    
    print("Extracting subclips")
    clip_start = 0.0
    for i, seg in enumerate(silence_segments):
        fname = f"clipd_{i}.mp4"
        moviepy.video.io.ffmpeg_tools.ffmpeg_extract_subclip(orig_vid, clip_start, seg[0], str(tempdir / fname))
        with open(tempdir / "render.txt", "a") as myfile:
            myfile.write("file '"+ fname + "'"+ "\n")
        clip_start = seg[1]
        if i % 50 == 0:
            print(f"extracted subclip {i}")

    cmd_string = get_setting("FFMPEG_BINARY") + " -f concat -safe 0 -i _temp/render.txt -c copy _temp/concated.mp4"
    subprocess.run(cmd_string, shell=True) 

    cmd_string = f"{get_setting('FFMPEG_BINARY')} -i _temp/concated.mp4 -filter_complex [0:v]setpts={1.0/playback_speed}*PTS[v];[0:a]atempo={playback_speed}[a] -map [v] -map [a] output.mp4"
    #cmd_string = f"{get_setting('FFMPEG_BINARY')} -i _temp/concated.mp4 -filter:v setpts={1.0/playback_speed}*PTS output.mp4"
    subprocess.run(cmd_string, shell=True) 




def condense_clip(clip, silence_threshold=0.1,  min_silence_length=0.15, playback_speed=1.1):
    
    silence_segments = get_silent_segments(clip, silence_threshold, min_silence_length)

    spoken_clips = []
    print("Extracting subclips")
    clip_start = 0.0
    for i, seg in enumerate(silence_segments):
        not_silences = clip.subclip(clip_start, seg[0])
        clip_start = seg[1]
        spoken_clips.append(not_silences)
        if i % 50 == 0:
            print(f"extracted subclip {i}")
    print("Concatenating subclips...")
    final_clip = concatenate_videoclips(spoken_clips)
    print("Finished ConcatOp")
    final_clip.fps = 30
    final_clip.audio.fps = 30
    print("Speeding up clip")
    final_clip = vfx.speedx(final_clip, playback_speed)
    print(f"Length of Shortened Clip: {final_clip.duration}")
    return final_clip



if __name__ == "__main__":
    
    parser = argparse.ArgumentParser(description='Condense boring lectures by speeding up the video and removing sections where the lecturer is not speaking.')
    parser.add_argument('--no_preview', action='store_true')
    parser.add_argument('--render', action='store_true')
    parser.add_argument('--playback_speed', default=1.15, type=float)
    
    args = parser.parse_args()

    filename = "emilio.mp4"
    
    clip = VideoFileClip(filename)
    
    preview_len = 80.0
    prewview_start = np.random.random()*clip.duration
    preview = clip.subclip(prewview_start, prewview_start+preview_len)

    condenser_kwargs = {"silence_threshold":0.15, "min_silence_length":0.7, "playback_speed":args.playback_speed}

    preview_shortened = condense_clip(preview, **condenser_kwargs)
    
    time_savings_factor =  float(preview_shortened.duration) / preview.duration

    print(f"Final Clip will be approx {(clip.duration / 60)*time_savings_factor} minutes instead of {clip.duration / 60} minutes!")
    print(f"Just speeding up the clip would result in {(clip.duration / 60)/args.playback_speed} minutes of playback time")
    print(f"Will remove approx {((clip.duration / 60)/args.playback_speed)-(clip.duration / 60)*time_savings_factor} minutes of silence.")
    
    
    if not args.no_preview:
        preview_shortened.preview()
    
    if args.render:
        condense_clip_ffmpeg(filename, **condenser_kwargs)
