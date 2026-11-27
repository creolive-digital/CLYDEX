"""Voice lifecycle only. It delegates intelligence and tools to the existing Core."""
import threading
import time
from dataclasses import replace

from clydex.core.errors import Cancelled, SpeechInputError
from clydex.voice.events import VoiceState
from clydex.voice.privacy import require_active


class VoiceLifecycle:
    transitions = {
        VoiceState.STANDBY: {VoiceState.LISTENING, VoiceState.WAKE_DETECTED, VoiceState.THINKING, VoiceState.SPEAKING, VoiceState.WAITING_FOR_APPROVAL},
        VoiceState.WAKE_DETECTED: {VoiceState.LISTENING},
        VoiceState.LISTENING: {VoiceState.TRANSCRIBING, VoiceState.STANDBY},
        VoiceState.TRANSCRIBING: {VoiceState.THINKING, VoiceState.STANDBY},
        VoiceState.THINKING: {VoiceState.WAITING_FOR_APPROVAL, VoiceState.SPEAKING, VoiceState.LISTENING, VoiceState.STANDBY},
        VoiceState.WAITING_FOR_APPROVAL: {VoiceState.THINKING, VoiceState.SPEAKING, VoiceState.STANDBY},
        VoiceState.SPEAKING: {VoiceState.LISTENING, VoiceState.STANDBY, VoiceState.THINKING},
        VoiceState.INTERRUPTED: {VoiceState.STANDBY, VoiceState.WAKE_DETECTED, VoiceState.LISTENING, VoiceState.THINKING, VoiceState.SPEAKING, VoiceState.WAITING_FOR_APPROVAL},
        VoiceState.SLEEPING: {VoiceState.STANDBY, VoiceState.WAKE_DETECTED, VoiceState.LISTENING, VoiceState.THINKING, VoiceState.SPEAKING, VoiceState.WAITING_FOR_APPROVAL},
        VoiceState.ERROR: {VoiceState.STANDBY, VoiceState.WAKE_DETECTED, VoiceState.LISTENING, VoiceState.THINKING, VoiceState.SPEAKING, VoiceState.WAITING_FOR_APPROVAL},
    }

    def __init__(self, events, clock=time.monotonic):
        self.events, self.clock = events, clock
        self.state = VoiceState.STANDBY
        self.last_activity = self.clock()
        self._lock = threading.RLock()

    def transition(self, state: VoiceState):
        with self._lock:
            if state == self.state:
                return
            if state not in (VoiceState.INTERRUPTED, VoiceState.SLEEPING, VoiceState.ERROR) and state not in self.transitions[self.state]:
                raise RuntimeError('Invalid voice lifecycle transition.')
            previous, self.state = self.state, state
            self.last_activity = self.clock()
        self.events.emit('state_changed', state, previous=previous.value)
        if previous == VoiceState.THINKING:
            self.events.emit('thinking_stopped', state)
        if state == VoiceState.THINKING:
            self.events.emit('thinking_started', state)
        elif state == VoiceState.WAITING_FOR_APPROVAL:
            self.events.emit('approval_waiting', state)
        elif state == VoiceState.WAKE_DETECTED:
            self.events.emit('wake_detected', state)
        elif state == VoiceState.SLEEPING:
            self.events.emit('sleeping', state)
        elif state == VoiceState.INTERRUPTED:
            self.events.emit('speech_interrupted', state)


class VoiceConversation:
    def __init__(self, capture, recognizer, lifecycle, events, clock=time.monotonic):
        self.capture, self.recognizer = capture, recognizer
        self.lifecycle, self.events, self.clock = lifecycle, events, clock

    def run(self, config, cancel, finish, guard, dispatch, *, check_only=False, wake=False):
        require_active(cancel, guard)
        last_user, followup = self.clock(), False
        if wake:
            self.lifecycle.transition(VoiceState.WAKE_DETECTED)
        try:
            while True:
                require_active(cancel, guard)
                self.lifecycle.transition(VoiceState.LISTENING)
                try:
                    remaining = min(config.followup_seconds, max(0, config.inactivity_seconds - (self.clock() - last_user)))
                    if followup and remaining <= 0:
                        self.lifecycle.transition(VoiceState.SLEEPING)
                        return
                    capture_config = replace(config, initial_silence_seconds=config.followup_seconds) if followup else config
                    audio = self.capture.capture(capture_config, cancel, finish, guard, check_only=check_only,
                                                 listen_seconds=remaining if followup else None)
                except SpeechInputError:
                    if followup:
                        self.lifecycle.transition(VoiceState.SLEEPING)
                        return
                    raise
                if check_only:
                    self.lifecycle.transition(VoiceState.STANDBY)
                    return
                require_active(cancel, guard)
                self.lifecycle.transition(VoiceState.TRANSCRIBING)
                try:
                    result = self.recognizer.recognize(audio, config, cancel, guard)
                finally:
                    # Capture has closed; discard the consumed transient buffer
                    # even on uncertain/canceled recognition. No raw persistence.
                    if hasattr(audio.samples, 'fill'):
                        audio.samples.fill(0)
                    del audio
                require_active(cancel, guard)
                if result.text.strip().casefold().rstrip('.!?') in ('stop listening', 'go to sleep', 'sleep clydex'):
                    self.lifecycle.transition(VoiceState.SLEEPING)
                    return
                if result.text.strip().casefold().rstrip('.!?') in ('stop', 'cancel'):
                    self.lifecycle.transition(VoiceState.INTERRUPTED)
                    return
                self.lifecycle.transition(VoiceState.THINKING)
                last_user = self.clock()
                dispatch(result.text)
                require_active(cancel, guard)
                if not config.continuous or self.clock() - last_user >= config.inactivity_seconds:
                    self.lifecycle.transition(VoiceState.STANDBY)
                    return
                followup = True
                finish.clear()
        except Cancelled:
            self.lifecycle.transition(VoiceState.INTERRUPTED)
            raise
        except Exception:
            self.lifecycle.transition(VoiceState.ERROR)
            raise
