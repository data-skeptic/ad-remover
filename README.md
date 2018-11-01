# Ad Remover

This library provides some high level functionality for processing audio files.

The `ad_remover` exposes two primary functions that work this way:

```
audio1 = 'audio_examples/full_episode.mp3'
audio2 = 'audio_example/splice_sound.wav'
destination_directory = 'output/'
results = ad_remover.remove(audio1, audio2, destination_directory)
files = resutls['files']
assert(len(files) == 3)
```

You will find at `splice_sound.wav` appears twice in `full_episode.mp3`.  This is why we expect an output of 3 files.

These 3 files will be named:
* `output/full_episode_1.mp3`
* `output/full_episode_2.mp3`
* `output/full_episode_3.mp3`

After the file have been split, the user will want to create the ad-free version of the podcast.  They can use this code:

```
results2 = ad_remover.join(files[0], files[2])
final_output = results2['output_filename']
```
