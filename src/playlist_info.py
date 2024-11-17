from dataclasses import dataclass, field


@dataclass
class PlaylistInfo:
    title: str = field(default="")
    total_songs: int = field(default=0)
    songs: any = field(default_factory=[])