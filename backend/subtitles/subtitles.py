#! /usr/bin/python
# -*- coding: UTF-8 -*-
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program.  If not, see <http://www.gnu.org/licenses/>
#

import os
import subprocess
import requests
import md5
import pycountry # https://bitbucket.org/flyingcircus/pycountry
from converter import Converter # https://github.com/senko/python-video-converter
import chardet # https://github.com/chardet/chardet

class SubtitlesUploader(object):
    def __init__(self, subtitles, wikifilename, auth1,
            statuscallback = None, errorcallback = None):
        self.subtitles = subtitles
        self.wikifilename = wikifilename
        self.auth1 = auth1
        self.statuscallback = statuscallback or (lambda text, percent: None)
        self.errorcallback = errorcallback or (lambda text: None)

    def run(self):
        for lang, filename in subtitles.items():
            percent = 0
            try:
                langname = self.lang(lang)
                if langname:
                    self.statuscallback('Loading subtitle in ' + langname, int(percent))
                    subtitletext = ''
                    format = self.format(filename)
                    if format.lower() != 'srt':
                        filename = self.transcode(filename, format)

                    f = open(filename)
                    subtitletext = f.read()
                    f.close()
                    subtitletext = subtitletext.decode(chardet.detect(subtitletext)['encoding'])

                    percent += 50.0 / len(subtitles)
                    self.statuscallback('Uploading subtitle in ' + langname, int(percent))

                    self.edit(u'TimedText:' + wikifilename.decode('utf-8') + u'.' + lang.lower() + u'.srt', subtitletext,\
                        u'Import ' + langname + u' subtitles for [[:File:' + wikifilename.decode('utf-8') + ']]')

                    percent += 50.0 / len(subtitles)
                    self.statuscallback('Finished processing subtitle in ' + langname, int(percent))

            except Exception, e:
                print e
                pass

    @staticmethod
    def lang(langcode):
        lang = pycountry.languages.get(iso639_1_code=langcode) # For now
        return lang and lang.name

    @staticmethod
    def format(filename):
        c = Converter(ffmpeg_path='/usr/bin/avconv', ffprobe_path='/usr/bin/avprobe')
        info = c.probe(filename)
        if not info: return None
        if len(info.streams) != 1: return None
        if info.streams[0].type != 'subtitle': return None
        return info.streams[0].codec

    @staticmethod
    def transcode(filename, format):
        target = filename + '.srt'
        # https://github.com/JDaren/subtitleConverter
        cmd = ['/usr/bin/java', '-jar', 'subtitleConvert.jar', format, target, 'srt']
        self.statuscallback("Running cmd: %s" % cmd, None)
        subprocess.check_output(cmd, stderr=subprocess.STDOUT)

        return target

    def edit(title, text, summary):
        text = text.encode("utf-8")
        md5hash = md5.new(text).digest()
        response = requests.get(
            "https://commons.wikimedia.org/w/api.php",
            params={
                'action': "query",
                'meta': "tokens",
                'format': "json"
            },
            auth=auth1
        )
        token = response.json()['query']['tokens']['csrftoken']
        response = requests.get(
            "https://commons.wikimedia.org/w/api.php",
            params={
                'action': "edit",
                'title': title.encode("utf-8"),
                'text': text,
                'md5': md5hash,
                'createonly': '1',
                'token': token,
                'text': "json"
            },
            auth=auth1
        )

def subtitles(subtitles, wikifilename, auth1, statuscallback = None, errorcallback = None):
    job = SubtitlesUploader(subtitles, wikifilename, auth1, statuscallback, errorcallback)
    job.run()