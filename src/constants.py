import re


FFMPEG_OPTIONS = {
    'options': '-vn', 
    'before_options': '-reconnect 1 -reconnect_streamed 1 -reconnect_delay_max 5'
}

FFMPEG_NIGHTCORE_OPTIONS = {
    'options': '-vn -c:a libopus -b:a 96k -af "asetrate=48000*1.25,atempo=1.15"',
    'before_options': '-reconnect 1 -reconnect_streamed 1 -reconnect_delay_max 5'
}

FFMPEG_BASSBOOST_OPTIONS = {
    'options': '-vn -c:a libopus -b:a 96k -af "bass=g=20"',
    'before_options': '-reconnect 1 -reconnect_streamed 1 -reconnect_delay_max 5'
}

URL_REGEX = re.compile(
    r'(https?://)?(www\.)?((youtube|youtu|youtube-nocookie|music.youtube)\.(com|be)/.+|(open\.spotify\.com)/(track|album|playlist|artist)/[a-zA-Z0-9]+)'
)