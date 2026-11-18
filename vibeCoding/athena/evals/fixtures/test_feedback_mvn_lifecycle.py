# quantum-backend G-005: `mvn clean test` (lifecycle with leading clean/options) was kind=other.
import json
import subprocess
import unittest
from gate_harness import GATE, ENV


def classify(commands):
    code = "const e=require(process.argv[1]);console.log(JSON.stringify(JSON.parse(process.argv[2]).map(c=>e.classify(c))))"
    run = subprocess.run(['node', '-e', code, str(GATE / 'lib/evidence.cjs'), json.dumps(commands)],
                         capture_output=True, text=True, env=ENV)
    assert run.returncode == 0, run.stderr
    return json.loads(run.stdout)


class MavenGradleLifecycle(unittest.TestCase):
    def assertKinds(self, expected):
        cmds = list(expected)
        for cmd, kind in zip(cmds, classify(cmds)):
            with self.subTest(cmd=cmd):
                self.assertEqual(kind, expected[cmd])

    def test_clean_and_options_before_test_phase_are_tests(self):
        self.assertKinds({
            'mvn test': 'test',
            'mvn clean test': 'test',
            'mvn -q clean test': 'test',
            'mvn -B -q clean verify': 'test',
            './mvnw clean test': 'test',
            'mvn -pl quantum-server -am clean test': 'test',
            'mvn -o -P ci clean install': 'test',
            'mvn clean package': 'test',
            'mvn -Dtest=FooTest test': 'test',
            './gradlew clean test': 'test',
        })

    def test_compile_phases_are_builds(self):
        self.assertKinds({
            'mvn compile': 'build',
            'mvn clean compile': 'build',
            'mvn -q clean test-compile': 'build',
        })

    def test_skipped_tests_never_prove_test(self):
        self.assertKinds({
            'mvn clean test -DskipTests': 'build',
            'mvn -DskipTests=true verify': 'build',
            'mvn test -Dmaven.test.skip=true': 'build',
            'mvn clean package -DskipTests': 'build',
            './gradlew clean test -x test': 'build',
        })

    def test_non_lifecycle_maven_is_not_evidence(self):
        self.assertKinds({
            'mvn clean': None,
            'mvn dependency:tree': None,
            'echo mvn clean test': None,
        })


if __name__ == '__main__':
    unittest.main()
