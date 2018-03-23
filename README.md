## Downloader for YouTube comments


### Prerequirties
* YouTube API key


### Installation

Get the repo and install dependencies
```
git clone https://github.com/gasabr/yt-comments.git
cd yt-comments
pip install -r requirements.txt
```

I use YamJam to manage secret keys, to set up it on you machine, please, create
file ~/.yamjam/config.yaml with following content:
```
yt_comments:
	YOUTUBE_KEY: <your API key>
```

Alternatively, you can just change the way variable YOUTUBE\_KEY is set in the
source code 


### Usage

```
python3 main.py --videoId=videoId > videoId.json
```

videoId is the part in the video URL after "https://www.youtube.com/watch?v="

Comments will be outputed in json to the stdout once after they all were
downloaded
