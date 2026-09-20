"""Q12#5/#7/#8 合同解析与诊断: CC/CX 同夹具驱动, Pi 同源函数文本相等。"""
import hashlib
import importlib.util
import json
from pathlib import Path
import re
import subprocess
import sys
import tempfile
import unittest
sys.dont_write_bytecode = True

ROOT = Path(__file__).resolve().parents[3]
CX = ROOT / 'codex/9.9.9/.codex/hooks'
CC = ROOT / 'claude/9.9.9/.claude/hooks'
PI = ROOT / 'pi-agent/plugin/extensions/cc-core'
CC_GATE = CC / 'delivery-gate.cjs'
PI_GATE = PI / 'delivery-gate.cjs'
PACKET_TEMPLATES = (
    ROOT / 'claude/9.9.9/.claude/skills/pace/templates/sprints/review-packet.md',
    ROOT / 'codex/9.9.9/.codex/skills/pace/templates/sprints/review-packet.md',
    ROOT / 'pi-agent/plugin/skills/pace/templates/sprints/review-packet.md',
)
# AC7 同源集合: Pi 的这些函数与常量行必须与 CC 逐字相等 (新增同源函数须同步入集)。
SAME_SOURCE_FUNCTIONS = (
    'stripInlineCode', 'extractAcIds', 'acceptanceSections', 'acceptanceCriteria',
    'acceptanceHeadHint', 'validateTddEvidence',
)
SAME_SOURCE_CONSTANTS = ('ACCEPTANCE_HEAD', 'ACCEPTANCE_HEAD_ALIASES', 'TDD_RECORD_FIELDS')
TDD_FIELDS = (
    'red_command', 'red_summary', 'red_observed_at', 'implementation_files',
    'implementation_observed_at', 'green_command', 'green_summary', 'green_observed_at',
)
# CC 内部函数探针: 不改发行导出 (切片 5 的事), 只在加载时追加一个测试专用出口。
CC_HARNESS = r'''
const fs = require('fs'), path = require('path'), Module = require('module');
const gate = process.argv[1], fn = process.argv[2], args = JSON.parse(process.argv[3]);
const names = ['stripInlineCode', 'extractAcIds', 'acceptanceSections', 'acceptanceCriteria',
  'validateTddEvidence', 'validateSpecGate', 'validateReviewPacket', 'validateAcMapping'];
const tail = '\nmodule.exports.__t={' +
  names.map(n => n + ':typeof ' + n + '!=="undefined"?' + n + ':undefined').join(',') + '};\n';
const mod = new Module(gate, null);
mod.filename = gate;
mod.paths = Module._nodeModulePaths(path.dirname(gate));
mod._compile(fs.readFileSync(gate, 'utf8') + tail, gate);
const probe = mod.exports.__t;
if (probe[fn] === undefined) {
  process.stdout.write(JSON.stringify({ok: false, error: 'missing internal ' + fn}));
  process.exit(0);
}
try {
  const value = probe[fn](...args);
  process.stdout.write(JSON.stringify({ok: true, value: value === undefined ? null : value}));
} catch (error) {
  process.stdout.write(JSON.stringify({ok: false, error: String((error && error.message) || error)}));
}
'''


def cx_gate():
    sys.path.insert(0, str(CX))
    spec = importlib.util.spec_from_file_location('delivery_gate', CX / 'delivery-gate.py')
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def cc_probe(fn, *args):
    run = subprocess.run(
        ['node', '-e', CC_HARNESS, str(CC_GATE), fn, json.dumps([str(a) if isinstance(a, Path) else a for a in args])],
        text=True, capture_output=True,
    )
    if run.returncode != 0:
        raise AssertionError('CC harness crashed: ' + run.stderr)
    return json.loads(run.stdout)


def cc_value(fn, *args):
    result = cc_probe(fn, *args)
    if not result['ok']:
        raise AssertionError('CC %s raised: %s' % (fn, result['error']))
    return result['value']


def cc_error(fn, *args):
    result = cc_probe(fn, *args)
    if result['ok']:
        raise AssertionError('CC %s did not fail; value=%r' % (fn, result['value']))
    return result['error']


def cx_error(call):
    try:
        call()
    except Exception as exc:  # gate 的 GateError 即预期失败通道
        return str(exc)
    raise AssertionError('CX call did not fail')


def js_function_text(source, name):
    match = re.search(r'(?m)^function %s\(.*?^\}' % re.escape(name), source, re.S)
    if not match:
        raise AssertionError('function %s not found' % name)
    return match.group(0)


def js_const_line(source, name):
    match = re.search(r'(?m)^const %s = .*$' % re.escape(name), source)
    if not match:
        raise AssertionError('const %s not found' % name)
    return match.group(0)


class AliasBoundary(unittest.TestCase):
    """AC1: AC/验收 别名仅在后随行尾或冒号时识别; 全名别名边界不变。"""

    POSITIVE = (
        '## AC', '## AC:', '## AC：', '## 验收', '## 验收:', '## 验收：',
        '## Done Contract', '## Acceptance Criteria', '## 验收标准', '## 验收标准 (Done Contract)',
    )
    NEGATIVE = (
        '## AC 覆盖表', '## 验收 流程', '## 验收 :', '## **AC**', '## AC-1', '## AC(草案)',
        '## ACL 配置', '## 验收流程说明',
        '### AC 标识一律从合同结构提取（#7）',
        '## AC 标识与围栏',
    )

    def test_alias_headings_are_recognized(self):
        gate = cx_gate()
        for heading in self.POSITIVE:
            doc = heading + '\n- AC1: 锁竞争不丢字节\n'
            with self.subTest(heading=heading, platform='cx'):
                self.assertEqual(gate.acceptance_criteria(doc), ['AC1: 锁竞争不丢字节'])
            with self.subTest(heading=heading, platform='cc'):
                self.assertEqual(cc_value('acceptanceCriteria', doc), ['AC1: 锁竞争不丢字节'])

    def test_near_miss_headings_are_not_acceptance_sections(self):
        gate = cx_gate()
        for heading in self.NEGATIVE:
            doc = heading + '\n- AC1: 锁竞争不丢字节\n'
            with self.subTest(heading=heading, platform='cx'):
                self.assertEqual(gate.acceptance_criteria(doc), [])
                self.assertFalse(gate.acceptance_sections(doc)['found'])
            with self.subTest(heading=heading, platform='cc'):
                self.assertEqual(cc_value('acceptanceCriteria', doc), [])
                self.assertFalse(cc_value('acceptanceSections', doc)['found'])


class ZeroCriteriaDiagnostics(unittest.TestCase):
    """AC2: 无小节 / 有小节零条目 是两条不同且明确的 spec-gate 报错。"""

    ALL_HEADINGS = ('## Done Contract', '## Acceptance Criteria', '## 验收标准', '## AC', '## 验收')

    def spec_gate_messages(self, design_text):
        with tempfile.TemporaryDirectory() as tmp:
            ai_state = Path(tmp) / '.ai_state'
            sprint = ai_state / 'sprints/q12-parser'
            sprint.mkdir(parents=True)
            (sprint / 'design.md').write_text(design_text, encoding='utf-8')
            fm = {'path': 'Feature', 'current_sprint_slug': 'q12-parser'}
            gate = cx_gate()
            cx = cx_error(lambda: gate.validate_spec_gate(sprint, ai_state, fm, 'q12-parser',
                                                          allow_exception=True))
            cc = cc_error('validateSpecGate', str(sprint), str(ai_state), fm, 'q12-parser',
                          {'allowException': True})
            return cc, cx

    def test_missing_section_lists_every_accepted_heading(self):
        cc, cx = self.spec_gate_messages('# design\n\n## HOW\n- 做点什么\n')
        self.assertEqual(cc, cx)
        for heading in self.ALL_HEADINGS:
            self.assertIn(heading, cc)

    def test_empty_section_is_a_distinct_message(self):
        cc, cx = self.spec_gate_messages('## 验收标准\n- TODO: 待补\n')
        self.assertEqual(cc, cx)
        missing_cc, _ = self.spec_gate_messages('# design\n- 无小节\n')
        self.assertNotEqual(cc, missing_cc)
        self.assertNotIn('## Done Contract', cc)
        for marker in ('验收小节', '0 条'):
            self.assertIn(marker, cc)


class PacketAcExtraction(unittest.TestCase):
    """AC3: packet 的 AC 集只来自其验收小节结构。"""

    def write_pair(self, sprint, design_text, packet_body):
        (sprint / 'design.md').write_text(design_text, encoding='utf-8')
        digest = hashlib.sha256(design_text.encode('utf-8')).hexdigest()
        packet = '---\nsource_design_sha256: "%s"\n---\n%s' % (digest, packet_body)
        (sprint / 'review-packet.md').write_text(packet, encoding='utf-8')

    def test_prose_outside_packet_section_is_not_an_ac(self):
        design = '## 验收标准\n- AC1: 锁竞争不丢字节\n- AC2: 过期结果被拒\n'
        packet = ('# Review Packet\n\n对照切片 3 的 AC5 与 AC9, 本次不复用。\n\n'
                  '## 验收标准\n- AC1: 锁竞争不丢字节\n- AC2: 过期结果被拒\n')
        with tempfile.TemporaryDirectory() as tmp:
            sprint = Path(tmp)
            self.write_pair(sprint, design, packet)
            cx_gate().validate_review_packet(sprint)
            self.assertEqual(cc_probe('validateReviewPacket', str(sprint))['ok'], True)

    def test_design_ids_stay_inside_its_acceptance_section(self):
        design = '背景: AC99 已退役。\n## 验收标准\n- AC1: 锁竞争不丢字节\n'
        packet = '# Review Packet\n\n## 验收标准\n- AC1: 锁竞争不丢字节\n'
        with tempfile.TemporaryDirectory() as tmp:
            sprint = Path(tmp)
            self.write_pair(sprint, design, packet)
            cx_gate().validate_review_packet(sprint)
            self.assertEqual(cc_probe('validateReviewPacket', str(sprint))['ok'], True)

    def test_packet_without_acceptance_section_reports_headings_not_mismatch(self):
        design = '## 验收标准\n- AC1: 锁竞争不丢字节\n'
        packet = '# Review Packet\n\n## Acceptance mapping\n- AC1: 锁竞争不丢字节\n'
        with tempfile.TemporaryDirectory() as tmp:
            sprint = Path(tmp)
            self.write_pair(sprint, design, packet)
            gate = cx_gate()
            cx = cx_error(lambda: gate.validate_review_packet(sprint))
            cc = cc_error('validateReviewPacket', str(sprint))
            self.assertEqual(cc, cx)
            self.assertNotIn('AC set mismatch', cc)
            for heading in ZeroCriteriaDiagnostics.ALL_HEADINGS:
                self.assertIn(heading, cc)


class InlineCodeAndFence(unittest.TestCase):
    """AC4: 成对反引号 span 与围栏行不产生 AC 约束; 落单反引号原样保留。"""

    def test_paired_backticks_are_blanked_and_lone_backtick_survives(self):
        text = '删除 `test_x_AC5_y` 断言, 保留 `AC7 的说明'
        gate = cx_gate()
        self.assertEqual(gate.extract_ac_ids(text), ['AC7'])
        self.assertEqual(cc_value('extractAcIds', text), ['AC7'])
        stripped_cx = gate.strip_inline_code(text)
        stripped_cc = cc_value('stripInlineCode', text)
        self.assertEqual(stripped_cc, stripped_cx)
        self.assertEqual(len(stripped_cc), len(text))
        self.assertNotIn('AC5', stripped_cc)
        self.assertIn('`AC7 的说明', stripped_cc)

    def test_fenced_lines_inside_the_section_are_not_criteria(self):
        doc = ('## 验收标准\n- AC1: 锁竞争不丢字节\n\n```yaml\n- AC9: 这是示例不是条目\n```\n'
               '- AC2: 过期结果被拒\n')
        expected = ['AC1: 锁竞争不丢字节', 'AC2: 过期结果被拒']
        gate = cx_gate()
        self.assertEqual(gate.acceptance_criteria(doc), expected)
        self.assertEqual(cc_value('acceptanceCriteria', doc), expected)
        self.assertEqual(gate.extract_ac_ids('\n'.join(gate.acceptance_criteria(doc))), ['AC1', 'AC2'])

    def test_ac_mapping_ignores_labels_quoted_inside_criteria(self):
        criteria = ['AC1 | 删除 `test_review_binding_AC5_pin` 断言 | 见 `AC9` 历史']
        review = '## Evidence Cross-Check\nFinal verdict: PASS\n| AC1 | PASS |\n'
        with tempfile.TemporaryDirectory() as tmp:
            sprint = Path(tmp)
            review_path = sprint / 'reviews/implementation-review.md'
            review_path.parent.mkdir(parents=True)
            review_path.write_text(review, encoding='utf-8')
            gate = cx_gate()
            cx = cx_error(lambda: gate.validate_ac_mapping(sprint, criteria, [], review_path, review, 'deadbeef'))
            cc = cc_error('validateAcMapping', str(sprint), criteria, [], str(review_path), review, 'deadbeef')
        for message in (cc, cx):
            self.assertIn('AC1', message)
            self.assertNotIn('AC5', message)
            self.assertNotIn('AC9', message)


class TddEvidenceDiagnostics(unittest.TestCase):
    """AC5: TDD 证据三类失败各自可区分, CC/CX 消息逐字相同。"""

    RECORD = ('tdd_records:\n  - test_file: tests/test_a.py\n'
              '    red_command: pytest tests/test_a.py\n    red_summary: 1 failed\n'
              '    red_observed_at: %s\n    implementation_files: gate.cjs\n'
              '    implementation_observed_at: %s\n    green_command: pytest tests/test_a.py\n'
              '    green_summary: 1 passed\n    green_observed_at: %s\n')

    def messages(self, content):
        with tempfile.TemporaryDirectory() as tmp:
            evidence = Path(tmp) / 'tdd-evidence.yaml'
            evidence.write_text(content, encoding='utf-8')
            gate = cx_gate()
            cx = cx_error(lambda: gate.validate_tdd_evidence(evidence))
            cc = cc_error('validateTddEvidence', str(evidence))
        self.assertEqual(cc, cx)
        return cc

    def test_four_failures_are_four_distinct_messages(self):
        comments_only = self.messages('# 本切片还没记\n# 待补\n')
        unparsable = self.messages('records:\n  test_file: tests/test_a.py\n  red_command: pytest\n')
        complete = self.RECORD % ('2026-09-20T10:00:00Z', '2026-09-20T11:00:00Z', '2026-09-20T12:00:00Z')
        missing_fields = self.messages(
            complete.replace('    green_summary: 1 passed\n', '')
            .replace('    green_observed_at: 2026-09-20T12:00:00Z\n', ''))
        out_of_order = self.messages(
            self.RECORD % ('2026-09-20T10:00:00Z', '2026-09-20T09:00:00Z', '2026-09-20T11:00:00Z'))
        self.assertEqual(len({comments_only, unparsable, missing_fields, out_of_order}), 4)

        self.assertIn('注释', comments_only)

        self.assertIn('- test_file:', unparsable)
        for field in TDD_FIELDS:
            self.assertIn(field, unparsable)

        self.assertIn('record #1', missing_fields)
        self.assertIn('tests/test_a.py', missing_fields)
        self.assertIn('green_summary', missing_fields)
        self.assertIn('green_observed_at', missing_fields)
        self.assertNotIn('red_command', missing_fields)

        self.assertIn('record #1', out_of_order)
        for value in ('2026-09-20T10:00:00Z', '2026-09-20T09:00:00Z', '2026-09-20T11:00:00Z'):
            self.assertIn(value, out_of_order)

    def test_valid_evidence_still_passes(self):
        content = self.RECORD % ('2026-09-20T10:00:00Z', '2026-09-20T11:00:00Z', '2026-09-20T12:00:00Z')
        with tempfile.TemporaryDirectory() as tmp:
            evidence = Path(tmp) / 'tdd-evidence.yaml'
            evidence.write_text(content, encoding='utf-8')
            cx_gate().validate_tdd_evidence(evidence)
            self.assertEqual(cc_probe('validateTddEvidence', str(evidence))['ok'], True)


class PiSameSourceParity(unittest.TestCase):
    """AC7: Pi 的同源函数与常量行与 CC 逐字相等。"""

    def test_pi_contract_parsers_match_cc_verbatim(self):
        cc_source = CC_GATE.read_text(encoding='utf-8')
        pi_source = PI_GATE.read_text(encoding='utf-8')
        for name in SAME_SOURCE_FUNCTIONS:
            with self.subTest(function=name):
                self.assertEqual(js_function_text(pi_source, name), js_function_text(cc_source, name))
        for name in SAME_SOURCE_CONSTANTS:
            with self.subTest(const=name):
                self.assertEqual(js_const_line(pi_source, name), js_const_line(cc_source, name))


class PacketTemplateContract(unittest.TestCase):
    """AC8: 发行模板自带可识别的验收小节标题。"""

    def test_templates_carry_a_recognized_acceptance_heading(self):
        gate = cx_gate()
        for template in PACKET_TEMPLATES:
            text = template.read_text(encoding='utf-8')
            with self.subTest(template=str(template)):
                self.assertTrue(gate.acceptance_sections(text)['found'])
                self.assertTrue(cc_value('acceptanceSections', text)['found'])

    def test_template_packet_passes_validation(self):
        template = PACKET_TEMPLATES[0].read_text(encoding='utf-8')
        design = '## 验收标准\n- AC1: 锁竞争不丢字节\n'
        digest = hashlib.sha256(design.encode('utf-8')).hexdigest()
        packet = template.replace('source_design_sha256: ""', 'source_design_sha256: "%s"' % digest)
        self.assertIn(digest, packet)
        with tempfile.TemporaryDirectory() as tmp:
            sprint = Path(tmp)
            (sprint / 'design.md').write_text(design, encoding='utf-8')
            (sprint / 'review-packet.md').write_text(packet, encoding='utf-8')
            cx_gate().validate_review_packet(sprint)
            self.assertEqual(cc_probe('validateReviewPacket', str(sprint))['ok'], True)


if __name__ == '__main__':
    unittest.main()
