# encoding: utf-8
from __future__ import unicode_literals

from .brightcove import BrightcoveLegacyIE
from .common import InfoExtractor
from ..utils import ExtractorError
from ..compat import (
    compat_str,
    compat_urllib_request,
)


class NownessBaseIE(InfoExtractor):
    def _extract_url_result(self, post):
        if post['type'] == 'video':
            for media in post['media']:
                if media['type'] == 'video':
                    video_id = media['content']
                    source = media['source']
                    if source == 'brightcove':
                        player_code = self._download_webpage(
                            'http://www.nowness.com/iframe?id=%s' % video_id, video_id,
                            note='Downloading player JavaScript',
                            errnote='Unable to download player JavaScript')
                        bc_url = BrightcoveLegacyIE._extract_brightcove_url(player_code)
                        if bc_url is None:
                            raise ExtractorError('Could not find player definition')
                        return self.url_result(bc_url, 'BrightcoveLegacy')
                    elif source == 'vimeo':
                        return self.url_result('http://vimeo.com/%s' % video_id, 'Vimeo')
                    elif source == 'youtube':
                        return self.url_result(video_id, 'Youtube')
                    elif source == 'cinematique':
                        # youtube-dl currently doesn't support cinematique
                        # return self.url_result('http://cinematique.com/embed/%s' % video_id, 'Cinematique')
                        pass

    def _api_request(self, url, request_path):
        display_id = self._match_id(url)
        request = compat_urllib_request.Request(
            'http://api.nowness.com/api/' + request_path % display_id,
            headers={
                'X-Nowness-Language': 'zh-cn' if 'cn.nowness.com' in url else 'en-us',
            })
        return display_id, self._download_json(request, display_id)


class NownessIE(NownessBaseIE):
    IE_NAME = 'nowness'
    _VALID_URL = r'https?://(?:(?:www|cn)\.)?nowness\.com/(?:story|(?:series|category)/[^/]+)/(?P<id>[^/]+?)(?:$|[?#])'
    _TESTS = [{
        'url': 'https://www.nowness.com/story/candor-the-art-of-gesticulation',
        'md5': '068bc0202558c2e391924cb8cc470676',
        'info_dict': {
            'id': '2520295746001',
            'ext': 'mp4',
            'title': 'Candor: The Art of Gesticulation',
            'description': 'Candor: The Art of Gesticulation',
            'thumbnail': 're:^https?://.*\.jpg',
            'uploader': 'Nowness',
        },
    }, {
        'url': 'https://cn.nowness.com/story/kasper-bjorke-ft-jaakko-eino-kalevi-tnr',
        'md5': 'e79cf125e387216f86b2e0a5b5c63aa3',
        'info_dict': {
            'id': '3716354522001',
            'ext': 'mp4',
            'title': 'Kasper Bjørke ft. Jaakko Eino Kalevi: TNR',
            'description': 'Kasper Bjørke ft. Jaakko Eino Kalevi: TNR',
            'thumbnail': 're:^https?://.*\.jpg',
            'uploader': 'Nowness',
        },
    }, {
        # vimeo
        'url': 'https://www.nowness.com/series/nowness-picks/jean-luc-godard-supercut',
        'md5': '9a5a6a8edf806407e411296ab6bc2a49',
        'info_dict': {
            'id': '130020913',
            'ext': 'mp4',
            'title': 'Bleu, Blanc, Rouge - A Godard Supercut',
            'description': 'md5:f0ea5f1857dffca02dbd37875d742cec',
            'thumbnail': 're:^https?://.*\.jpg',
            'upload_date': '20150607',
            'uploader': 'Cinema Sem Lei',
            'uploader_id': 'cinemasemlei',
        },
    }]

    def _real_extract(self, url):
        _, post = self._api_request(url, 'post/getBySlug/%s')
        return self._extract_url_result(post)


class NownessPlaylistIE(NownessBaseIE):
    IE_NAME = 'nowness:playlist'
    _VALID_URL = r'https?://(?:(?:www|cn)\.)?nowness\.com/playlist/(?P<id>\d+)'
    _TEST = {
        'url': 'https://www.nowness.com/playlist/3286/i-guess-thats-why-they-call-it-the-blues',
        'info_dict': {
            'id': '3286',
        },
        'playlist_mincount': 8,
    }

    def _real_extract(self, url):
        playlist_id, playlist = self._api_request(url, 'post?PlaylistId=%s')
        entries = [self._extract_url_result(item) for item in playlist['items']]
        return self.playlist_result(entries, playlist_id)


class NownessSeriesIE(NownessBaseIE):
    IE_NAME = 'nowness:series'
    _VALID_URL = r'https?://(?:(?:www|cn)\.)?nowness\.com/series/(?P<id>[^/]+?)(?:$|[?#])'
    _TEST = {
        'url': 'https://www.nowness.com/series/60-seconds',
        'info_dict': {
            'id': '60',
            'title': '60 Seconds',
            'description': 'One-minute wisdom in a new NOWNESS series',
        },
        'playlist_mincount': 4,
    }

    def _real_extract(self, url):
        display_id, series = self._api_request(url, 'series/getBySlug/%s')
        entries = [self._extract_url_result(post) for post in series['posts']]
        series_title = None
        series_description = None
        translations = series.get('translations', [])
        if translations:
            series_title = translations[0].get('title') or translations[0]['seoTitle']
            series_description = translations[0].get('seoDescription')
        return self.playlist_result(
            entries, compat_str(series['id']), series_title, series_description)
