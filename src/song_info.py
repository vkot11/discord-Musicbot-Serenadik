from dataclasses import dataclass, field


@dataclass
class SongInfo:
    url: str = field(default="")
    title: str = field(default="")
    duration: str = field(default="")
    thumbnail: str = field(default="")
    link: str = field(default="")
    artist: str = field(default="")
    flag: str = field(default="default")