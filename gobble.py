import argparse

import numpy as np
from moviepy.editor import VideoFileClip, concatenate_videoclips
import matplotlib.pyplot as plt
import moviepy.video.fx.all as vfx



def condense_clip(clip, silence_threshold=0.1,  min_silence_length=0.15, playback_speed=1.1):
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

    filename = "nlp_in_python.mp4"
    
    clip = VideoFileClip(filename)
    
    preview_len = 10.0
    prewview_start = np.random.random()*clip.duration
    preview = clip.subclip(prewview_start, prewview_start+preview_len)

    condenser_kwargs = {"silence_threshold":0.15, "min_silence_length":0.2, "playback_speed":args.playback_speed}

    preview_shortened = condense_clip(preview, **condenser_kwargs)
    
    time_savings_factor =  float(preview_shortened.duration) / preview.duration

    print(f"Final Clip will be approx {(clip.duration / 60)*time_savings_factor} minutes instead of {clip.duration / 60} minutes!")
    print(f"Just speeding up the clip would result in {(clip.duration / 60)/args.playback_speed} minutes of playback time")
    print(f"Will remove approx{((clip.duration / 60)/args.playback_speed)-(clip.duration / 60)*time_savings_factor} minutes of silence.")
    

    if not args.no_preview:
        preview_shortened.preview()
    
    if args.render:
        clip_shortened = condense_clip(clip, **condenser_kwargs)
        clip_shortened.write_videofile("shortened_"+filename, fps=30)
