"""Fixed trusted presentation profiles, never model-generated permission policy."""
PROFILES = {
    'personal': 'Use a calm, warm and respectful conversational tone.',
    'professional': 'Use precise, courteous professional language and clear next steps.',
    'developer': 'Prefer concrete technical explanations and usable code on screen.',
    'technical_support': 'Diagnose step by step; distinguish observations from assumptions.',
    'study': 'Explain progressively, using examples appropriate to the question.',
    'focus': 'Keep answers brief and avoid unnecessary interruptions.',
    'gaming': 'Keep answers very brief and minimize interruptions.',
    'privacy': 'Use restrained wording. Local privacy policy blocks cloud requests.',
    'custom': 'Use the explicitly configured presentation preferences.',
}
TONES = {'calm', 'warm', 'direct', 'formal'}
LENGTHS = {'brief', 'balanced', 'detailed'}
