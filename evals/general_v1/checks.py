"""Predeclared, narrow adherence probes, separate from content fidelity."""
import ast
import io
import re
import tokenize

from ownvoice.checks import check


def paragraphs(text):
    return [part.strip() for part in re.split(r'\n\s*\n', text.strip()) if part.strip()]


def sentences(text):
    text = re.sub(r'\[[A-Za-z]+\d+\]', '', text)
    return [part.strip() for part in re.split(r'[。！？!?]|\.(?!\d)', text) if part.strip()]


def style(task, artifact, profile):
    forced = bool(re.search(r'(?is)(?:please|could you|can you|need you to|must|need to|before I can)'
                            r'.{0,45}(?:provide|share|create|answer|fill).{0,45}(?:profile|sample|preference|questionnaire)|'
                            r'请.{0,15}(?:提供|建立|填写|回答).{0,20}(?:档案|偏好|问卷|样本)|'
                            r'(?:需要先|必须先).{0,25}(?:档案|偏好|问卷|样本)', artifact))
    invented = bool(re.search(r'(?i)your usual style|as you always|你一贯|你平时喜欢|你的习惯是', artifact))
    if profile == 'none':
        return {'passed': not forced and not invented,
                'probes': {'no_forced_calibration': not forced, 'no_explicit_invented_habit': not invented},
                'scope': 'Entry-flow markers only; naturalness and all unsupported inferences are not proven.'}
    if profile == 'conflict':
        return {'passed': None, 'probes': {}, 'scope': 'Invalid preferences must lose to task constraints; see content checks and review.'}
    probes = {}
    metrics = {}
    domain = task['domain']
    if domain == 'code':
        try:
            tree = ast.parse(artifact)
            names = {node.id for node in ast.walk(tree) if isinstance(node, ast.Name)
                     and isinstance(node.ctx, ast.Store)} - set(task['parameters'])
            lengths = [len(re.sub('[^A-Za-z]', '', name)) for name in names]
            comments = sum(token.type == tokenize.COMMENT for token in tokenize.generate_tokens(io.StringIO(artifact).readline))
            metrics = {'short_internal_names': sum(0 < length <= 4 for length in lengths),
                       'descriptive_internal_names': sum(length >= 8 for length in lengths),
                       'assignments': sum(isinstance(node, (ast.Assign, ast.AnnAssign, ast.AugAssign)) for node in ast.walk(tree)),
                       'list_comprehensions': sum(isinstance(node, ast.ListComp) for node in ast.walk(tree)),
                       'comments': comments}
            if profile == 'compact':
                probes = {'short_name': metrics['short_internal_names'] >= 1,
                          'compact_expression': metrics['list_comprehensions'] >= 1,
                          'comment_density': comments <= 1}
            else:
                probes = {'descriptive_names': metrics['descriptive_internal_names'] >= 2,
                          'intermediate_steps': metrics['assignments'] >= 3,
                          'has_comment': comments >= 1}
        except (SyntaxError, tokenize.TokenError, IndentationError):
            probes = {'parsable': False}
    elif domain == 'research':
        anchors = task['style_anchors']
        setup, result = artifact.find(anchors['setup']), artifact.find(anchors['result'])
        parts = sentences(artifact)
        lengths = [len(re.findall(r"[A-Za-z]+(?:'[A-Za-z]+)?|\d+(?:\.\d+)?", part))
                   if task['language'] == 'en' else len(re.sub(r'\s', '', part)) for part in parts]
        metrics = {'sample_position': setup, 'result_position': result,
                   'sentences': len(parts), 'longest_sentence': max(lengths, default=0),
                   'paragraphs': len(paragraphs(artifact))}
        if profile == 'compact':
            probes = {'result_first': 0 <= result < setup, 'short_sentences': 3 <= len(parts) <= 6,
                      'sentence_length': max(lengths, default=0) <= (35 if task['language'] == 'en' else 90)}
        else:
            probes = {'setup_first': 0 <= setup < result, 'connected_sentences': 1 <= len(parts) <= 2}
        probes['single_paragraph'] = len(paragraphs(artifact)) == 1
    else:
        first_line = artifact.strip().splitlines()[0] if artifact.strip() else ''
        name = re.escape(task['protected'][0])
        greeting = bool(re.search(r'(?i)^\s*(?:hi\b|hello\b|dear\b)|你好|您好|早上好|晚上好', first_line)
                        or re.fullmatch(name + r'[,，:：]?\s*', first_line))
        thanks = bool(re.search(r'(?i)\bthanks?\b|\bregards\b|best wishes|谢谢|感谢|祝好', artifact))
        metrics = {'greeting': greeting, 'thanks_or_closing': thanks,
                   'paragraphs': len(paragraphs(artifact))}
        if profile == 'compact':
            probes = {'no_greeting': not greeting, 'no_closing': not thanks,
                      'single_paragraph': len(paragraphs(artifact)) == 1}
        else:
            probes = {'greeting': greeting, 'closing': thanks,
                      'separate_paragraphs': len(paragraphs(artifact)) >= 3}
    return {'passed': bool(probes) and all(probes.values()), 'probes': probes, 'metrics': metrics,
            'scope': 'Observable preference adherence, not naturalness, quality, identity or semantic fidelity.'}


def assess(task, artifact, profile):
    content = check(task, artifact)
    if task['domain'] == 'research':
        content['single_paragraph'] = len(paragraphs(artifact)) == 1
        content['passed'] = content['passed'] and content['single_paragraph']
    return {'passed': content['passed'], 'content': content, 'style': style(task, artifact, profile)}
