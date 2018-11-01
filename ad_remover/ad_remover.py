def remove(audio_haystack, audio_needle, destination_directory):
	file_segments = []
	pos_start = 0
	pos_next = find_audio(audio_haystack, audio_needle)
	while pos_next != -1:
		new_file = split_and_save_audio(audio_haystack, pos_start, pos_next, destination_directory)
		file_segments.append(new_file)
		pos_start = pos_next + len(pos_start) # TODO: skip the splice sound
		pos_next = find_audio(audio_haystack, audio_needle, pos_next+1)
	results = {"files": file_segments}
	return results

def find_audio(audio_haystack, audio_needle, offset=0):
	# TODO: implement
	return position

def split_and_save_audio(audio_haystack, pos_start, pos_next, destination_directory):
	# TODO: implement

def join(file1, file2):
	# TODO: implementation of concatenating file1 and file2
results2 = ad_remover.
final_output = results2['output_filename']


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
