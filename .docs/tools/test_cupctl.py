#!/usr/bin/env python3
"""cupctl: every verb/action maps to a script that exists, and bad input is refused."""
import os
import subprocess
import sys
import unittest

TOOLS = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, TOOLS)
import cupctl  # noqa: E402


def cupctl_run(*args):
    return subprocess.run([sys.executable, os.path.join(TOOLS, "cupctl.py"), *args], capture_output=True, text=True)


class Plans(unittest.TestCase):
    def test_every_script_a_command_runs_exists(self):
        for verb, (_, actions) in cupctl.COMMANDS.items():
            for action, (_, build) in actions.items():
                plan = build(["PAGE"])
                steps = plan if isinstance(plan[0], (list, dict)) else [plan]
                for step in steps:
                    cmd = step["cmd"] if isinstance(step, dict) else step
                    for part in cmd:
                        if part.endswith(".py") and os.path.isabs(part):
                            self.assertTrue(os.path.exists(part), f"{verb} {action}: {part}")

    def test_extra_arguments_are_passed_on(self):
        plan = cupctl.COMMANDS["page"][1]["new"][1](["--dry-run"])
        self.assertEqual(plan[-1], "--dry-run")

    def test_navigation_is_generated_from_the_docs_folder(self):
        steps = cupctl.nav_regen([])
        self.assertTrue(all(s["cwd"].endswith(".docs") for s in steps if isinstance(s, dict)))


class Cli(unittest.TestCase):
    def test_help_lists_every_verb(self):
        out = cupctl_run("--help").stdout
        for verb in cupctl.COMMANDS:
            self.assertIn(verb, out)

    def test_unknown_verb_and_action_fail(self):
        self.assertEqual(cupctl_run("nope").returncode, 2)
        self.assertEqual(cupctl_run("page", "nope").returncode, 2)

    def test_a_missing_page_argument_is_refused(self):
        r = cupctl_run("page", "adopt")
        self.assertNotEqual(r.returncode, 0)
        self.assertIn("PAGE", r.stderr)


if __name__ == "__main__":
    unittest.main()
