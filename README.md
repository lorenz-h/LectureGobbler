# Lecture Gobbler
This repo contains a script gobble.py that speeds up video files and removes silences from these files. It is particulary useful for lengthy computer science lectures. It uses [MoviePy](https://github.com/Zulko/moviepy) under the hood to process the video. By default the script will only show a preview of the changes to the file. To render the result to a file the --render flag must be set. The rendering process can take a while depending on the size of your video.