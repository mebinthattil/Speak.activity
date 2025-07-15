# Copyright (C) 2009, Aleksey Lim
# Copyright (C) 2019, Chihurumnaya Ibiam <ibiamchihurumnaya@sugarlabs.org>
#
# This program is free software; you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation; either version 2 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program; if not, write to the Free Software
# Foundation, Inc., 51 Franklin St, Fifth Floor, Boston, MA  02110-1301  USA

import numpy
from kokoro import KPipeline
import tempfile
import os
from gi.repository import Gst
from gi.repository import GLib
from gi.repository import GObject
import logging
logger = logging.getLogger('speak')
from sugar3.speech import GstSpeechPlayer
import soundfile as sf
from kokoro.pipeline import LANG_CODES


class Speech(GstSpeechPlayer):
    __gsignals__ = {
        'peak': (GObject.SIGNAL_RUN_FIRST, None, [GObject.TYPE_PYOBJECT]),
        'wave': (GObject.SIGNAL_RUN_FIRST, None, [GObject.TYPE_PYOBJECT]),
        'idle': (GObject.SIGNAL_RUN_FIRST, None, []),
    }

    def __init__(self):
        GstSpeechPlayer.__init__(self)
        self.pipeline = None

        self._cb = {}
        for cb in ['peak', 'wave', 'idle']:
            self._cb[cb] = None

    def disconnect_all(self):
        for cb in ['peak', 'wave', 'idle']:
            hid = self._cb[cb]
            if hid is not None:
                self.disconnect(hid)
                self._cb[cb] = None

    def connect_peak(self, cb):
        self._cb['peak'] = self.connect('peak', cb)

    def connect_wave(self, cb):
        self._cb['wave'] = self.connect('wave', cb)

    def connect_idle(self, cb):
        self._cb['idle'] = self.connect('idle', cb)

    def make_pipeline(self):
        self.pipeline = None #temporarily no pipeline needed cause reading from WAV file

    def speak(self, status, text):
        voice = getattr(status.voice, 'name', None)
        pitch = getattr(status, 'pitch', 100)
        rate = getattr(status, 'rate', 100)
        #Need to write better mapping code
        lang_code = 'a'  # default
        if voice:
            v = voice.split('_')[0].lower()
            if v in LANG_CODES:
                lang_code = v
            else:
                for code, name in LANG_CODES.items():
                    if v in name.lower() or v in code:
                        lang_code = code
                        break
        # Fallback to a known working voice if not valid
        valid_voices = ["af_heart", "af_alloy", "af_aoede", "af_bella", "af_jessica", "af_kore", "af_nicole", "af_nova", "af_river", "af_sarah", "af_sky", "am_adam", "am_echo", "am_eric", "am_fenrir", "am_liam", "am_michael", "am_onyx", "am_puck", "am_santa", "bf_alice", "bf_emma", "bf_isabella", "bf_lily", "bm_daniel", "bm_fable", "bm_george", "bm_lewis", "jf_alpha", "jf_gongitsune", "jf_nezumi", "jf_tebukuro", "jm_kumo", "zf_xiaobei", "zf_xiaoni", "zf_xiaoxiao", "zf_xiaoyi", "zm_yunjian", "zm_yunxi", "zm_yunxia", "zm_yunyang", "ef_dora", "em_alex", "em_santa", "ff_siwis", "hf_alpha", "hf_beta", "hm_omega", "hm_psi", "if_sara", "im_nicola", "pf_dora", "pm_alex", "pm_santa"]
        if not voice or voice.lower() not in valid_voices:
            voice = 'af_heart'
        pipeline = KPipeline(lang_code=lang_code)
        speed = max(0.5, min(2.0, rate / 100.0))
        for result in pipeline(text, voice=voice, speed=speed):
            if result.audio is not None:
                audio = result.audio.cpu().numpy() if hasattr(result.audio, 'cpu') else result.audio
                with tempfile.NamedTemporaryFile(suffix='.wav', delete=False) as tmpfile:
                    sf.write(tmpfile.name, audio, 24000)
                    tmpfile.flush()
                    self._play_wav_with_gst(tmpfile.name)
                    os.unlink(tmpfile.name)
                break

    def _play_wav_with_gst(self, wav_path):
        pipeline_str = f'filesrc location="{wav_path}" ! wavparse ! audioconvert ! audioresample ! autoaudiosink'
        pipeline = Gst.parse_launch(pipeline_str)
        pipeline.set_state(Gst.State.PLAYING)
        bus = pipeline.get_bus()
        while True:
            msg = bus.timed_pop_filtered(10 * Gst.SECOND, Gst.MessageType.EOS | Gst.MessageType.ERROR)
            if msg:
                break
        pipeline.set_state(Gst.State.NULL)


_speech = None


def get_speech():
    global _speech

    if _speech is None:
        _speech = Speech()

    return _speech

PITCH_MIN = 0
PITCH_MAX = 200
RATE_MIN = 0
RATE_MAX = 200
