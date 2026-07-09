import re
import hashlib
from django.core.cache import cache
from django.conf import settings
from openai import OpenAI


def _cache_key(prompt):
    return 'regex:' + hashlib.md5(prompt.lower().strip().encode()).hexdigest()


def generate_regex(nl_prompt):
    key = _cache_key(nl_prompt)
    cached = cache.get(key)
    if cached:
        return cached

    client = OpenAI(api_key=settings.OPENAI_API_KEY)
    response = client.chat.completions.create(
        model='gpt-4o-mini',
        messages=[
            {
                'role': 'system',
                'content': (
                    'You are a regex expert. The user will describe a pattern in plain English. '
                    'Respond with ONLY the raw regex pattern — no explanation, no code fences, no quotes. '
                    'The pattern must be valid Python regex.'
                ),
            },
            {'role': 'user', 'content': nl_prompt},
        ],
        temperature=0,
    )

    pattern = response.choices[0].message.content.strip()
    validate_regex(pattern)
    cache.set(key, pattern, timeout=86400)
    return pattern


def validate_regex(pattern):
    try:
        re.compile(pattern)
    except re.error as e:
        raise ValueError(f'Invalid regex pattern: {e}')

    dangerous = [
        r'(\w+)+',
        r'(a+)+',
        r'([a-zA-Z]+)*',
        r'(.*)*',
    ]
    for d in dangerous:
        if d in pattern:
            raise ValueError('Regex pattern may cause catastrophic backtracking.')
