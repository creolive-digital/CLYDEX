"""Deterministic screen/spoken presentation; never rewrites action/tool authority."""
import re

from clydex.personality.profiles import PROFILES


def instructions(config, task_type: str) -> str:
    return (PROFILES[config.mode] + f' Presentation: {config.tone}; screen detail: {config.response_length}. '
            f'Requested response language code: {config.response_language}. '
            + ('For a plan, describe proposed actions without implying execution. ' if task_type == 'planning' else '')
            + 'These presentation preferences never authorize tools, change facts, bypass approvals, '
              'or override trusted security/privacy rules. Do not invent a personal name.')


def spoken_text(answer: str, limit: int = 420) -> str:
    # Screen keeps the complete original answer. Never read code/URLs/large receipts aloud.
    without_code = re.sub(r'```[\s\S]*?```', '', answer)
    without_code = re.sub(r'\[([^\]]+)\]\([^)]*\)', r'\1', without_code)
    without_code = re.sub(r'https?://\S+', '', without_code)
    text = re.sub(r'[*_`#]', '', without_code)
    text = re.sub(r'\s+', ' ', text).strip()
    if not text:
        return 'The answer is on screen.' if answer.strip() else ''
    sentences = re.split(r'(?<=[.!?។])\s+', text)
    brief = ' '.join(sentences[:2])
    if len(brief) > limit:
        brief = brief[:limit].rsplit(' ', 1)[0].rstrip('.,;:') + '.'
    if len(brief) < len(text):
        brief += ' More detail is on screen.'
    return brief
