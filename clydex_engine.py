"""Voice recording, local transcription, Codex requests, and Windows speech."""
import json
import os
from pathlib import Path
import queue
import shutil
import subprocess
import tempfile
import threading
from clydex_spectrum import SpectrumStream


class VoiceEngine:
    def __init__(self):
        self.events = queue.Queue()
        self.history = []
        self.stop_event = threading.Event()
        self.whisper = None
        self.speak_preference = True
        self.closed = False

    def record_worker(self, device, check_only):
        try:
            import numpy as np
            import sounddevice as sd
            info = sd.query_devices(device, 'input')
            rate = int(info['default_samplerate'])
            spectrum = SpectrumStream(rate)
            chunks=[]
            peak = 0.0
            def callback(indata,frames,time_info,status):
                nonlocal peak
                peak = max(peak, float(np.max(np.abs(indata))))
                if not check_only:
                    chunks.append(indata.copy())
                spectrum.push(indata[:,0])
            with sd.InputStream(device=device, samplerate=rate, channels=1, dtype='float32',
                                blocksize=0, callback=callback):
                self.events.put(('audio_stream', spectrum))
                self.events.put(('status', 'CHECKING MIC' if check_only else 'RECORDING'))
                self.stop_event.wait(timeout=5 if check_only else 30)
            if check_only:
                result = (f'Signal detected ({20*math.log10(peak):.0f} dBFS peak).'
                          if peak >= .00015 else 'No usable signal. Select another input or check mute and input volume.')
                self.events.put(('mic_info', f"{info['name']} · {result}"))
                return
            self.events.put(('record_done',None))
            if not chunks:raise RuntimeError('No microphone audio. Check Windows mic permissions.')
            self.events.put(('status','TRANSCRIBING'))
            import wave
            with tempfile.NamedTemporaryFile(suffix='.wav',delete=False) as tmp: wav_path=tmp.name
            try:
                samples=np.concatenate(chunks).flatten()
                peak=float(np.max(np.abs(samples)))
                if peak < 0.00015:
                    raise RuntimeError(
                        'The microphone is capturing silence. In Windows Settings > System > Sound > Input, '
                        'select and unmute your microphone, then check that the input meter moves while you speak.'
                    )
                with wave.open(wav_path,'wb') as wav:
                    wav.setnchannels(1);wav.setsampwidth(2);wav.setframerate(rate)
                    wav.writeframes((np.clip(samples,-1,1)*32767).astype('<i2').tobytes())
                if self.whisper is None:
                    self.events.put(('status','LOADING SPEECH MODEL · FIRST USE DOWNLOAD'))
                    from faster_whisper import WhisperModel
                    self.whisper=WhisperModel('base',device='cpu',compute_type='int8')
                self.events.put(('status','TRANSCRIBING'))
                segments,_=self.whisper.transcribe(wav_path,beam_size=3,vad_filter=True)
                question=' '.join(s.text.strip() for s in segments).strip()
                if not question:
                    # A second pass without VAD helps with short or quiet utterances.
                    segments,_=self.whisper.transcribe(wav_path,beam_size=3,vad_filter=False)
                    question=' '.join(s.text.strip() for s in segments).strip()
            finally:
                try:os.unlink(wav_path)
                except OSError:pass
            if not question:raise RuntimeError('No speech recognized. Please try again.')
            self.ask(question)
        except Exception as exc:self.events.put(('error',str(exc)))
        finally:self.events.put(('done',None))

    def text_worker(self,question):
        try:self.ask(question)
        except Exception as exc:self.events.put(('error',str(exc)))
        finally:self.events.put(('done',None))

    def ask(self,question):
        self.events.put(('user',question))
        self.events.put(('status','THINKING'))
        answer = self.chat_reply(question)
        self.history.extend([('User',question),('CLYDEX',answer)])
        self.history=self.history[-12:]
        self.events.put(('bot',answer))
        if self.speak_preference:
            try:
                self.speak_with_audio_meter(answer)
            except Exception as exc:
                self.events.put(('error','Speech output: '+str(exc)))

    @staticmethod
    def launch_installed_app(name):
        # Resolve the model's display name against the local Start menu.
        if not isinstance(name, str) or not name.strip():
            return 'Which app would you like to open?'
        catalog = subprocess.run(
            ['powershell.exe', '-NoProfile', '-NonInteractive', '-Command',
             '[Console]::OutputEncoding=[Text.UTF8Encoding]::new($false); '
             'ConvertTo-Json -Compress -InputObject @(Get-StartApps | Select-Object Name,AppID)'],
            capture_output=True, text=True, encoding='utf-8', check=True, timeout=20,
            creationflags=subprocess.CREATE_NO_WINDOW,
        )
        apps = json.loads(catalog.stdout)
        key = name.strip().casefold()
        matches = [app for app in apps if app['Name'].casefold() == key]
        if not matches:
            matches = [app for app in apps if key in app['Name'].casefold()]
        if not matches:
            return f'I couldn’t find {name} in the Windows Start menu.'
        if len(matches) > 1:
            choices = ', '.join(app['Name'] for app in matches[:6])
            return f'Which app did you mean? I found {choices}.'
        app = matches[0]
        os.startfile("shell:AppsFolder\\" + app['AppID'])
        return f"Opening {app['Name']}."

    def chat_reply(self,question):
        codex=shutil.which('codex') or shutil.which('codex.cmd')
        if not codex:raise RuntimeError('Codex not found. Check codex --version in Command Prompt.')
        prompt = (
            'You are Clydex, a conversational desktop assistant. Interpret the latest user message '
            'in context, in any language. You can request the desktop tool open_app by giving '
            'the Windows app display name. Use it when the user wants an app opened now. '
            'For questions, negations, unclear targets, or unsupported tasks choose reply and '
            'answer or ask for clarification. Never claim an action has already happened. '
            'Use only this response interface. Return a short spoken answer in the user’s language '
            'for reply. Leave unused string fields empty. Conversation and current message follow.\n'
            + json.dumps({'history': self.history[-6:], 'message': question}, ensure_ascii=False)
        )
        schema = {
            'type': 'object', 'additionalProperties': False,
            'properties': {'action': {'type': 'string', 'enum': ['reply', 'open_app']},
                           'app': {'type': 'string'}, 'message': {'type': 'string'}},
            'required': ['action', 'app', 'message'],
        }
        with tempfile.TemporaryDirectory(prefix='clydex_') as folder:
            output = Path(folder) / 'answer.json'
            schema_path = Path(folder) / 'response.schema.json'
            schema_path.write_text(json.dumps(schema), encoding='utf-8')
            cmd = [codex, 'exec', '--sandbox', 'read-only', '--skip-git-repo-check',
                   '--output-schema', str(schema_path), '--output-last-message', str(output), '-']
            if os.name=='nt' and str(codex).lower().endswith(('.cmd','.bat')):
                cmd=['cmd.exe','/d','/c']+cmd
            try:
                proc=subprocess.run(cmd,cwd=folder,input=prompt,capture_output=True,text=True,
                                    encoding='utf-8',errors='replace',timeout=180)
            except subprocess.TimeoutExpired:raise RuntimeError('Codex timed out. Try again.')
            if proc.returncode:
                raise RuntimeError('Codex failed; check codex login status. '+(proc.stderr or proc.stdout)[-500:])
            answer=output.read_text(encoding='utf-8').strip() if output.exists() else ''
        if not answer:raise RuntimeError('Codex returned no answer.')
        response = json.loads(answer)
        if response.get('action') == 'open_app':
            return self.launch_installed_app(response.get('app'))
        if response.get('action') == 'reply' and response.get('message', '').strip():
            return response['message'].strip()
        raise RuntimeError('Codex returned an incomplete response. Please try again.')

    def speak_with_audio_meter(self, answer):
        """Synthesize Windows SAPI speech to WAV and meter PCM during actual playback.
        Speech and visualization use the exact same sample stream; no fake speaking waveform.
        """
        import numpy as np
        import sounddevice as sd
        import wave
        if os.name != 'nt':
            raise RuntimeError('Real-audio TTS requires Windows System.Speech.')
        if not shutil.which('powershell.exe'):
            raise RuntimeError('Windows PowerShell is required for system speech synthesis.')
        text_to_speak = answer[:1300].strip()
        if not text_to_speak:
            return
        with tempfile.TemporaryDirectory(prefix='clydex_tts_') as folder:
            folder = Path(folder)
            message = folder / 'message.txt'
            output = folder / 'speech.wav'
            script = folder / 'synthesize.ps1'
            message.write_text(text_to_speak, encoding='utf-8-sig')
            script.write_text(
                'Add-Type -AssemblyName System.Speech\n'
                '$s = New-Object System.Speech.Synthesis.SpeechSynthesizer\n'
                'try {\n'
                '  $content = [System.IO.File]::ReadAllText($args[0], [System.Text.Encoding]::UTF8)\n'
                '  $s.SetOutputToWaveFile($args[1])\n'
                '  $s.Speak($content)\n'
                '  $s.SetOutputToNull()\n'
                '} finally { $s.Dispose() }\n', encoding='utf-8')
            proc = subprocess.run(
                ['powershell.exe','-NoProfile','-NonInteractive','-ExecutionPolicy','Bypass',
                 '-File',str(script),str(message),str(output)],
                capture_output=True,text=True,timeout=120,
                creationflags=getattr(subprocess,'CREATE_NO_WINDOW',0))
            if proc.returncode or not output.is_file():
                raise RuntimeError('Windows Speech synthesis failed: '+(proc.stderr or proc.stdout)[-400:])
            with wave.open(str(output),'rb') as wav:
                nch=wav.getnchannels()
                rate=wav.getframerate()
                width=wav.getsampwidth()
                if width != 2 or nch not in (1,2):
                    raise RuntimeError('Unsupported TTS WAV format. Expected 16-bit PCM.')
                spectrum = SpectrumStream(rate)
                self.events.put(('audio_stream', spectrum))
                self.events.put(('status','SPEAKING'))
                with sd.OutputStream(samplerate=rate,channels=nch,dtype='int16',blocksize=1024) as stream:
                    while not self.closed:
                        raw=wav.readframes(1024)
                        if not raw:break
                        pcm=np.frombuffer(raw,dtype='<i2').reshape(-1,nch)
                        stream.write(pcm)
                        spectrum.push(pcm.astype(np.float32).mean(axis=1)/32768.)
                self.events.put(('audio_stream',None))

