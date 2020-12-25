import logging

from feeluown.library import AbstractProvider, ProviderV2, ProviderFlags as PF, \
    SongModel
from feeluown.media import Quality
from feeluown.models import ModelType
from .api import API


logger = logging.getLogger(__name__)


class NeteaseProvider(AbstractProvider, ProviderV2):
    class meta:
        identifier = 'netease'
        name = '网易云音乐'
        flags = {
            ModelType.song: PF.model_v2 | PF.similar | PF.multi_quality | PF.get,
        }

    def __init__(self):
        super().__init__()
        self.api = API()

    @property
    def identifier(self):
        return 'netease'

    @property
    def name(self):
        return '网易云音乐'

    def auth(self, user):
        assert user.cookies is not None
        self._user = user
        self.api.load_cookies(user.cookies)

    def song_get(self, identifier):
        data = self.api.song_detail(int(identifier))
        song_v1 = _deserialize(data, NeteaseSongSchema)
        return SongModel.from_orm(song_v1)

    def song_list_similar(self, song):
        songs = self.api.get_similar_song(song.identifier)
        return [_deserialize(song, NeteaseSongSchema) for song in songs]

    def song_list_quality(self, song):
        return list(self._fetch_song_q_media_mapping(song))

    def song_get_media(self, song, quality):
        return self._fetch_song_q_media_mapping(song).get(quality)

    def _fetch_song_q_media_mapping(self, song):
        mapping = song.cache_get('quality_media_mapping')
        if mapping is not None:
            return mapping
        songs = self.api.weapi_songs_url([int(song.identifier)], 999000)
        mapping = {}
        if songs and songs[0]['url']:
            # TODO: parse songs list and get more reasonable mapping
            mapping = {
                Quality.Audio.sq: songs[0]['url']
            }
        ttl = 60 * 20
        song.cache_set('quality_media_mapping', mapping, ttl)
        return mapping


provider = NeteaseProvider()


from .models import search, _deserialize  # noqa
from .schemas import NeteaseSongSchema
provider.search = search
