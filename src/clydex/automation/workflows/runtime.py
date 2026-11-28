"""Single-run interpreter. All effects are injected trusted executor calls."""
from dataclasses import dataclass
import time

from clydex.automation.tasks import CancellationToken
from clydex.core.contracts import canonical_json
from clydex.security.schema import detached
from clydex.automation.workflows.schema import validate_inputs, validate_workflow


class LinkedCancellation(CancellationToken):
    def __init__(self, parent, timeout):
        super().__init__(timeout)
        self.parent = parent

    def is_set(self):
        return self.parent.is_set() or super().is_set()


def resolve(value, outputs, depth=0):
    if depth > 12:
        raise ValueError('Reference nesting exceeded.')
    if type(value) is dict:
        if '$ref' in value:
            result = outputs
            for part in value['$ref'].split('.'):
                if type(result) is not dict or part not in result:
                    raise ValueError('Output unavailable on the selected branch.')
                result = result[part]
            return detached(result)
        return {k: resolve(v, outputs, depth + 1) for k, v in value.items()}
    if type(value) is list:
        return [resolve(v, outputs, depth + 1) for v in value]
    return value


def condition(left, operator, right):
    if operator == 'exists':
        return left is not None
    if operator in ('eq', 'ne'):
        equal = type(left) is type(right) and left == right
        return equal if operator == 'eq' else not equal
    if operator == 'contains':
        if type(left) not in (str, list, dict):
            raise ValueError('Contains requires a string, array or object.')
        return right in left
    if type(left) not in (int, float) or type(right) not in (int, float):
        raise ValueError('Ordering comparisons require numbers.')
    return {'gt': left > right, 'gte': left >= right, 'lt': left < right, 'lte': left <= right}[operator]


@dataclass
class WorkflowRuntime:
    specs: dict
    invoke: object
    approve: object
    guard: object
    event: object = lambda *args: None

    def preview(self, definition):
        value = validate_workflow(definition, self.specs)
        return dict(valid=True, nodes=len(value['nodes']), timeout=value['timeout'],
                    actions=[self.specs[n['config']['tool']].inventory() for n in value['nodes']
                             if n['kind'] in ('tool', 'loop')], effects_executed=0)

    def run(self, definition, inputs, parent):
        value = validate_workflow(definition, self.specs)
        validate_inputs(value, inputs)
        token = LinkedCancellation(parent, value['timeout'])
        outputs, status, decisions = {'inputs': detached(inputs)}, {}, {}
        pending = {n['id']: n for n in value['nodes']}
        edges = value['edges']
        while pending:
            for key, node in list(pending.items()):
                incoming = [e for e in edges if e['to'] == key]
                if any(e['from'] not in status for e in incoming):
                    continue
                token.check()
                self.guard()
                active = not incoming or any(status[e['from']] == 'complete' and
                    (e['port'] == 'next' or decisions.get(e['from']) == (e['port'] == 'true')) for e in incoming)
                if not active:
                    status[key] = 'skipped'
                    self.event(key, 'skipped')
                    del pending[key]
                    continue
                self.event(key, 'running')
                config, kind = node['config'], node['kind']
                if kind in ('tool', 'loop'):
                    results = []
                    for index in range(config.get('count', 1)):
                        token.check()
                        self.guard()
                        outputs['iteration'] = {'index': index}
                        args = resolve(config['arguments'], outputs)
                        self.specs[config['tool']].validate(args)
                        result = self.invoke(config['tool'], args, token)
                        token.check()
                        results.append(result)
                        if len(canonical_json(results).encode('utf-8')) > 65536:
                            raise ValueError('Loop output exceeds its bound; completed effects remain.')
                    result = results if kind == 'loop' else results[0]
                elif kind == 'condition':
                    result = condition(resolve(config['left'], outputs), config['operator'], resolve(config['right'], outputs))
                    decisions[key] = result
                elif kind == 'delay':
                    deadline = time.monotonic() + config['seconds']
                    while time.monotonic() < deadline:
                        token.check()
                        self.guard()
                        time.sleep(min(.05, max(0, deadline - time.monotonic())))
                    result = None
                elif kind == 'approval':
                    self.approve(key, config['message'], token)
                    result = {'approved': True}
                elif kind == 'input':
                    result = detached(inputs)
                elif kind == 'note':
                    result = config['text']
                else:
                    result = resolve(config['value'], outputs)
                token.check()
                outputs[key] = detached(result)
                if len(canonical_json(outputs).encode('utf-8')) > 262144:
                    raise ValueError('Workflow output memory budget exceeded.')
                status[key] = 'complete'
                self.event(key, 'complete')
                del pending[key]
        return dict(status='complete', nodes=status,
                    outputs={n['id']: outputs[n['id']] for n in value['nodes'] if n['kind'] == 'output' and n['id'] in outputs})
