"""Tests for rollout-db, the plan-rollout SQLite ledger script.

Runner: python3 -m unittest discover -s skills/plan-rollout/scripts -p 'test_*.py' -t .
"""
import json
import subprocess
import sqlite3
import sys
import tempfile
import threading
import unittest
from pathlib import Path

SCRIPT = Path(__file__).parent / "rollout-db"


def run_cli(args, db_path, cwd=None):
    """Invoke the rollout-db CLI as a subprocess against a temp db path.

    Returns (returncode, stdout, stderr).
    """
    cmd = [sys.executable, str(SCRIPT), "--db", str(db_path)] + args
    proc = subprocess.run(cmd, cwd=cwd, capture_output=True, text=True)
    return proc.returncode, proc.stdout, proc.stderr


class TempDbTestCase(unittest.TestCase):
    def setUp(self):
        self._tmpdir = tempfile.TemporaryDirectory()
        self.db_path = Path(self._tmpdir.name) / "rollout.db"

    def tearDown(self):
        self._tmpdir.cleanup()


class InitCommandTests(TempDbTestCase):
    def test_init_creates_runs_row(self):
        rc, out, err = run_cli(
            ["init", "BOOK-1022", "--plan", "/tmp/plan.md", "--base", "main", "--sha", "abc123"],
            self.db_path,
        )
        self.assertEqual(rc, 0, msg=f"stderr={err}")
        data = json.loads(out)
        self.assertEqual(data["ticket"], "BOOK-1022")

        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        row = conn.execute("SELECT * FROM runs WHERE ticket = ?", ("BOOK-1022",)).fetchone()
        conn.close()
        self.assertIsNotNone(row)
        self.assertEqual(row["ticket"], "BOOK-1022")
        self.assertEqual(row["plan_path"], "/tmp/plan.md")
        self.assertEqual(row["base_branch"], "main")
        self.assertEqual(row["base_sha"], "abc123")
        self.assertEqual(row["written_by"], "coordinator")
        self.assertIsNotNone(row["created_at"])


class AgentUpsertTests(TempDbTestCase):
    def _init_run(self):
        run_cli(["init", "BOOK-1022", "--plan", "/tmp/p.md", "--base", "main", "--sha", "abc"], self.db_path)

    def test_agent_upsert_inserts_row(self):
        self._init_run()
        rc, out, err = run_cli(
            [
                "agent", "upsert", "coder-1",
                "--run", "BOOK-1022",
                "--role", "coder",
                "--parent", "slc-1",
                "--aspect", "api",
                "--pr", "42",
                "--branch", "feat/x",
                "--base-sha", "aaa",
                "--head-sha", "bbb",
                "--worktree", "/tmp/wt",
                "--status", "dispatched",
                "--blocked-on", "",
                "--report-path", "/tmp/reports/coder-1.md",
                "--brief-path", "/tmp/briefs/coder-1.md",
            ],
            self.db_path,
        )
        self.assertEqual(rc, 0, msg=f"stderr={err}")
        printed = json.loads(out)
        self.assertEqual(printed["name"], "coder-1")
        self.assertEqual(printed["status"], "dispatched")
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        row = conn.execute(
            "SELECT * FROM agents WHERE run = ? AND name = ?", ("BOOK-1022", "coder-1")
        ).fetchone()
        conn.close()
        self.assertIsNotNone(row)
        assert row is not None
        self.assertEqual(row["role"], "coder")
        self.assertEqual(row["parent"], "slc-1")
        self.assertEqual(row["aspect"], "api")
        self.assertEqual(row["pr"], 42)
        self.assertEqual(row["branch"], "feat/x")
        self.assertEqual(row["base_sha"], "aaa")
        self.assertEqual(row["head_sha"], "bbb")
        self.assertEqual(row["worktree"], "/tmp/wt")
        self.assertEqual(row["status"], "dispatched")
        self.assertEqual(row["report_path"], "/tmp/reports/coder-1.md")
        self.assertEqual(row["brief_path"], "/tmp/briefs/coder-1.md")
        self.assertEqual(row["written_by"], "coder-1")

    def test_agent_upsert_partial_update_preserves_other_fields(self):
        self._init_run()
        run_cli(
            ["agent", "upsert", "coder-1", "--run", "BOOK-1022", "--role", "coder", "--branch", "feat/x"],
            self.db_path,
        )
        rc, out, err = run_cli(
            ["agent", "upsert", "coder-1", "--run", "BOOK-1022", "--status", "done", "--head-sha", "ccc"],
            self.db_path,
        )
        self.assertEqual(rc, 0, msg=f"stderr={err}")
        printed = json.loads(out)
        self.assertEqual(printed["status"], "done")
        self.assertEqual(printed["head_sha"], "ccc")
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        row = conn.execute(
            "SELECT * FROM agents WHERE run = ? AND name = ?", ("BOOK-1022", "coder-1")
        ).fetchone()
        conn.close()
        assert row is not None
        # fields from the first call survive the second, partial call
        self.assertEqual(row["role"], "coder")
        self.assertEqual(row["branch"], "feat/x")
        # fields from the second call took effect
        self.assertEqual(row["status"], "done")
        self.assertEqual(row["head_sha"], "ccc")


class NoteTrapTicketDecisionAuditTests(TempDbTestCase):
    def _init_run(self):
        run_cli(["init", "BOOK-1022", "--plan", "/tmp/p.md", "--base", "main", "--sha", "abc"], self.db_path)

    def _rows(self, table):
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        rows = [dict(r) for r in conn.execute(f"SELECT * FROM {table}").fetchall()]
        conn.close()
        return rows

    def test_note_add_inserts_row_with_valid_kind(self):
        self._init_run()
        rc, out, err = run_cli(
            ["note", "add", "--run", "BOOK-1022", "--agent", "coder-1", "--kind", "left_undone", "--text", "did not add X"],
            self.db_path,
        )
        self.assertEqual(rc, 0, msg=f"stderr={err}")
        printed = json.loads(out)
        self.assertEqual(printed["kind"], "left_undone")
        rows = self._rows("notes")
        self.assertEqual(len(rows), 1)
        self.assertEqual(rows[0]["kind"], "left_undone")
        self.assertEqual(rows[0]["text"], "did not add X")
        self.assertEqual(rows[0]["written_by"], "coder-1")

    def test_note_add_accepts_brief_error_plan_error_incident_kinds(self):
        self._init_run()
        for kind in ("brief_error", "plan_error", "incident"):
            rc, out, err = run_cli(
                ["note", "add", "--run", "BOOK-1022", "--agent", "coder-1", "--kind", kind, "--text", "x"],
                self.db_path,
            )
            self.assertEqual(rc, 0, msg=f"kind={kind} stderr={err}")
            printed = json.loads(out)
            self.assertEqual(printed["kind"], kind)
        rows = self._rows("notes")
        self.assertEqual({r["kind"] for r in rows}, {"brief_error", "plan_error", "incident"})

    def test_note_add_rejects_invalid_kind(self):
        self._init_run()
        rc, out, err = run_cli(
            ["note", "add", "--run", "BOOK-1022", "--agent", "coder-1", "--kind", "bogus_kind", "--text", "x"],
            self.db_path,
        )
        self.assertNotEqual(rc, 0)
        self.assertEqual(out, "", msg="nothing should print to stdout on a rejected note add")
        self.assertIn("bogus_kind", err)
        self.assertEqual(self._rows("notes"), [])

    def test_trap_add_inserts_row(self):
        self._init_run()
        rc, out, err = run_cli(
            ["trap", "add", "--run", "BOOK-1022", "--agent", "coder-1", "--repo", "fhir-works",
             "--path", "packages/prior-auth/**", "--text", "watch for X"],
            self.db_path,
        )
        self.assertEqual(rc, 0, msg=f"stderr={err}")
        printed = json.loads(out)
        self.assertEqual(printed["repo"], "fhir-works")
        rows = self._rows("traps")
        self.assertEqual(len(rows), 1)
        self.assertEqual(rows[0]["repo"], "fhir-works")
        self.assertEqual(rows[0]["path"], "packages/prior-auth/**")
        self.assertEqual(rows[0]["text"], "watch for X")

    def _trap_rows(self):
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        rows = [dict(r) for r in conn.execute("SELECT rowid, * FROM traps ORDER BY created_at").fetchall()]
        conn.close()
        return rows

    def test_trap_resolve_supersedes_by_rowid(self):
        self._init_run()
        run_cli(
            ["trap", "add", "--run", "BOOK-1022", "--agent", "coder-1", "--repo", "fhir-works",
             "--path", "packages/prior-auth/**", "--text", "watch for X"],
            self.db_path,
        )
        run_cli(
            ["trap", "add", "--run", "BOOK-1022", "--agent", "coder-2", "--repo", "fhir-works",
             "--path", "packages/prior-auth/**", "--text", "actually watch for Y"],
            self.db_path,
        )
        rows = self._trap_rows()
        false_rowid = rows[0]["rowid"]
        correction_rowid = rows[1]["rowid"]

        rc, out, err = run_cli(
            ["trap", "resolve", "--run", "BOOK-1022", "--rowid", str(false_rowid),
             "--by-rowid", str(correction_rowid), "--reason", "X was wrong, see Y"],
            self.db_path,
        )
        self.assertEqual(rc, 0, msg=f"stderr={err}")
        printed = json.loads(out)
        self.assertEqual(printed["superseded_by"], correction_rowid)
        self.assertEqual(printed["superseded_reason"], "X was wrong, see Y")

        rows = self._trap_rows()
        false_row = next(r for r in rows if r["rowid"] == false_rowid)
        correction_row = next(r for r in rows if r["rowid"] == correction_rowid)
        self.assertEqual(false_row["superseded_by"], correction_rowid)
        self.assertEqual(false_row["superseded_reason"], "X was wrong, see Y")
        self.assertIsNone(correction_row["superseded_by"])

    def test_trap_resolve_rejects_unknown_rowid(self):
        self._init_run()
        run_cli(
            ["trap", "add", "--run", "BOOK-1022", "--agent", "coder-1", "--repo", "fhir-works",
             "--path", "packages/prior-auth/**", "--text", "correction row"],
            self.db_path,
        )
        correction_rowid = self._trap_rows()[0]["rowid"]
        rc, out, err = run_cli(
            ["trap", "resolve", "--run", "BOOK-1022", "--rowid", "999999",
             "--by-rowid", str(correction_rowid), "--reason", "nope"],
            self.db_path,
        )
        self.assertNotEqual(rc, 0)
        self.assertEqual(out, "", msg="a rejected trap resolve must print nothing to stdout")
        self.assertIn("999999", err)

    def test_trap_resolve_rejects_already_superseded(self):
        self._init_run()
        run_cli(
            ["trap", "add", "--run", "BOOK-1022", "--agent", "coder-1", "--repo", "fhir-works",
             "--path", "packages/prior-auth/**", "--text", "watch for X"],
            self.db_path,
        )
        run_cli(
            ["trap", "add", "--run", "BOOK-1022", "--agent", "coder-2", "--repo", "fhir-works",
             "--path", "packages/prior-auth/**", "--text", "actually watch for Y"],
            self.db_path,
        )
        run_cli(
            ["trap", "add", "--run", "BOOK-1022", "--agent", "coder-3", "--repo", "fhir-works",
             "--path", "packages/prior-auth/**", "--text", "actually watch for Z"],
            self.db_path,
        )
        rows = self._trap_rows()
        false_rowid, correction_rowid, other_rowid = (rows[0]["rowid"], rows[1]["rowid"], rows[2]["rowid"])
        rc, out, err = run_cli(
            ["trap", "resolve", "--run", "BOOK-1022", "--rowid", str(false_rowid),
             "--by-rowid", str(correction_rowid), "--reason", "first resolve"],
            self.db_path,
        )
        self.assertEqual(rc, 0, msg=f"stderr={err}")

        rc, out, err = run_cli(
            ["trap", "resolve", "--run", "BOOK-1022", "--rowid", str(false_rowid),
             "--by-rowid", str(other_rowid), "--reason", "second resolve"],
            self.db_path,
        )
        self.assertNotEqual(rc, 0)
        self.assertEqual(out, "", msg="a rejected trap resolve must print nothing to stdout")
        self.assertIn(str(false_rowid), err)

    def test_ticket_add_inserts_row(self):
        self._init_run()
        rc, out, err = run_cli(
            ["ticket", "add", "--run", "BOOK-1022", "--key", "BOOK-999", "--title", "fix Y",
             "--in-epic", "no", "--reason", "pre-existing", "--agent", "coder-1"],
            self.db_path,
        )
        self.assertEqual(rc, 0, msg=f"stderr={err}")
        printed = json.loads(out)
        self.assertEqual(printed["key"], "BOOK-999")
        rows = self._rows("tickets")
        self.assertEqual(len(rows), 1)
        self.assertEqual(rows[0]["key"], "BOOK-999")
        self.assertEqual(rows[0]["in_epic"], "no")

    def test_ticket_add_stores_labels(self):
        self._init_run()
        rc, out, err = run_cli(
            ["ticket", "add", "--run", "BOOK-1022", "--key", "BOOK-998", "--title", "fix Z",
             "--in-epic", "no", "--reason", "pre-existing", "--agent", "coder-1",
             "--labels", "ready-for-agent,alloydb"],
            self.db_path,
        )
        self.assertEqual(rc, 0, msg=f"stderr={err}")
        printed = json.loads(out)
        self.assertEqual(printed["labels"], "ready-for-agent,alloydb")
        rows = self._rows("tickets")
        self.assertEqual(rows[0]["labels"], "ready-for-agent,alloydb")

    def test_ticket_add_migrates_db_missing_labels_column(self):
        conn = sqlite3.connect(str(self.db_path))
        conn.execute(
            "CREATE TABLE tickets (run TEXT, created_at TEXT, written_by TEXT, key TEXT, "
            "title TEXT, in_epic TEXT, reason TEXT, agent TEXT)"
        )
        conn.commit()
        conn.close()
        self._init_run()
        rc, out, err = run_cli(
            ["ticket", "add", "--run", "BOOK-1022", "--key", "BOOK-997", "--title", "fix W",
             "--in-epic", "yes", "--reason", "related", "--agent", "coder-1",
             "--labels", "ready-for-human"],
            self.db_path,
        )
        self.assertEqual(rc, 0, msg=f"stderr={err}")
        rows = self._rows("tickets")
        self.assertEqual(
            [r["labels"] for r in rows if r["key"] == "BOOK-997"], ["ready-for-human"]
        )

    def test_decision_add_inserts_row_with_json_options(self):
        self._init_run()
        rc, out, err = run_cli(
            ["decision", "add", "--run", "BOOK-1022", "--reason", "which db path",
             "--options", '["a", "b"]', "--decided-by", "darren"],
            self.db_path,
        )
        self.assertEqual(rc, 0, msg=f"stderr={err}")
        printed = json.loads(out)
        self.assertEqual(printed["decided_by"], "darren")
        rows = self._rows("decisions")
        self.assertEqual(len(rows), 1)
        self.assertEqual(json.loads(rows[0]["options"]), ["a", "b"])
        self.assertEqual(rows[0]["answer"], "")
        self.assertEqual(rows[0]["written_by"], "darren")

    def test_decision_resolve_clears_it_from_state_open_decisions(self):
        self._init_run()
        run_cli(
            ["decision", "add", "--run", "BOOK-1022", "--reason", "which db path",
             "--options", '["a", "b"]', "--decided-by", "darren"],
            self.db_path,
        )
        rc, out, err = run_cli(["state", "BOOK-1022"], self.db_path)
        self.assertEqual(rc, 0, msg=f"stderr={err}")
        before = json.loads(out)
        self.assertEqual([d["reason"] for d in before["open_decisions"]], ["which db path"])

        rc, out, err = run_cli(
            ["decision", "resolve", "--run", "BOOK-1022", "--reason", "which db path",
             "--answer", "a", "--decided-by", "darren"],
            self.db_path,
        )
        self.assertEqual(rc, 0, msg=f"stderr={err}")
        printed = json.loads(out)
        self.assertEqual(printed["answer"], "a")
        self.assertEqual(printed["decided_by"], "darren")

        rc, out, err = run_cli(["state", "BOOK-1022"], self.db_path)
        self.assertEqual(rc, 0, msg=f"stderr={err}")
        after = json.loads(out)
        self.assertEqual(
            [d["reason"] for d in after["open_decisions"]], [],
            msg="a resolved decision must no longer appear in open_decisions",
        )

    def test_decision_resolve_no_matching_open_row_is_error(self):
        self._init_run()
        rc, out, err = run_cli(
            ["decision", "resolve", "--run", "BOOK-1022", "--reason", "nonexistent reason",
             "--answer", "a", "--decided-by", "darren"],
            self.db_path,
        )
        self.assertNotEqual(rc, 0)
        self.assertEqual(out, "", msg="a rejected decision resolve must print nothing to stdout")
        self.assertIn("nonexistent reason", err)
        self.assertEqual(self._rows("decisions"), [])

    def test_decision_resolve_only_updates_most_recent_open_row_for_reason(self):
        self._init_run()
        run_cli(
            ["decision", "add", "--run", "BOOK-1022", "--reason", "which db path",
             "--options", "[]", "--decided-by", "darren"],
            self.db_path,
        )
        run_cli(
            ["decision", "add", "--run", "BOOK-1022", "--reason", "which db path",
             "--options", "[]", "--decided-by", "darren"],
            self.db_path,
        )
        rc, out, err = run_cli(
            ["decision", "resolve", "--run", "BOOK-1022", "--reason", "which db path",
             "--answer", "b", "--decided-by", "darren"],
            self.db_path,
        )
        self.assertEqual(rc, 0, msg=f"stderr={err}")
        rows = self._rows("decisions")
        answers = sorted(r["answer"] for r in rows)
        # exactly one of the two open rows for this reason is now resolved
        self.assertEqual(answers, ["", "b"])

    def test_audit_add_inserts_row_with_json_blast_radius(self):
        self._init_run()
        rc, out, err = run_cli(
            ["audit", "add", "--run", "BOOK-1022", "--agent", "auditor-1", "--evidence-status", "clean",
             "--discrepancies", "none", "--blast-radius-sections", '["section-3"]',
             "--audit-path", "/tmp/audits/auditor-1.md"],
            self.db_path,
        )
        self.assertEqual(rc, 0, msg=f"stderr={err}")
        printed = json.loads(out)
        self.assertEqual(printed["evidence_status"], "clean")
        rows = self._rows("audits")
        self.assertEqual(len(rows), 1)
        self.assertEqual(json.loads(rows[0]["blast_radius_sections"]), ["section-3"])
        self.assertEqual(rows[0]["audit_path"], "/tmp/audits/auditor-1.md")


class QueryCommandTests(TempDbTestCase):
    def _init_run(self):
        run_cli(["init", "BOOK-1022", "--plan", "/tmp/p.md", "--base", "main", "--sha", "abc"], self.db_path)

    def test_query_runs_select(self):
        self._init_run()
        rc, out, err = run_cli(["query", "SELECT ticket FROM runs"], self.db_path)
        self.assertEqual(rc, 0, msg=f"stderr={err}")
        data = json.loads(out)
        self.assertEqual(data, [{"ticket": "BOOK-1022"}])

    def test_query_rejects_non_select(self):
        self._init_run()
        rc, out, err = run_cli(["query", "DELETE FROM runs"], self.db_path)
        self.assertNotEqual(rc, 0)
        self.assertEqual(out, "", msg="a rejected query must print nothing to stdout")
        self.assertIn("SELECT", err)
        rows = self._select_all("runs")
        self.assertEqual(len(rows), 1)

    def test_query_rejects_select_with_trailing_statement(self):
        self._init_run()
        rc, out, err = run_cli(["query", "SELECT 1; DROP TABLE runs"], self.db_path)
        self.assertNotEqual(rc, 0)
        self.assertEqual(out, "", msg="a rejected query must print nothing to stdout")
        self.assertIn("SELECT", err)
        rows = self._select_all("runs")
        self.assertEqual(len(rows), 1)

    def _select_all(self, table):
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        rows = [dict(r) for r in conn.execute(f"SELECT * FROM {table}").fetchall()]
        conn.close()
        return rows


REPORT_HEADINGS = [
    "status",
    "agent",
    "branch",
    "head_sha",
    "base_at_dispatch",
    "worktree",
    "blocked_on",
    "shared_contract_changes",
    "changes_inventory",
    "deviations",
    "plan_errors",
    "brief_errors",
    "left_undone",
    "skipped",
    "red_not_on_base",
    "tickets",
    "traps",
    "tdd_mode_and_seam",
    "skills_used",
    "verification",
    "evidence",
    "runtime_only_concerns",
    "deploy_ordering",
    "files_written",
    "review_notes",
]


def default_report_bodies():
    """A fully-populated, non-empty body for every one of the 25 fixed headings."""
    bodies = {h: f"prose for {h}" for h in REPORT_HEADINGS}
    bodies["status"] = "done"
    bodies["agent"] = "coder-1"
    bodies["branch"] = "feat/x"
    bodies["head_sha"] = "bbb"
    bodies["base_at_dispatch"] = "aaa"
    bodies["worktree"] = "/tmp/wt"
    bodies["blocked_on"] = "none"
    bodies["shared_contract_changes"] = "- signature: foo() gained a kw arg"
    bodies["deviations"] = "- used COALESCE instead of overwrite"
    bodies["plan_errors"] = "none"
    bodies["brief_errors"] = "- brief omitted --run on agent upsert"
    bodies["left_undone"] = "none"
    bodies["skipped"] = "none"
    bodies["red_not_on_base"] = "no"
    bodies["tickets"] = "- BOOK-999"
    bodies["traps"] = "- watch for X"
    bodies["files_written"] = "- rollout-db\n- test_rollout_db.py"
    return bodies


def render_report(bodies, omit=None):
    lines = []
    for heading in REPORT_HEADINGS:
        if heading == omit:
            continue
        lines.append(f"## {heading}")
        lines.append(bodies.get(heading, ""))
        lines.append("")
    return "\n".join(lines)


def write_report(tmpdir, bodies, omit=None):
    path = Path(tmpdir) / "report.md"
    path.write_text(render_report(bodies, omit=omit))
    return path


class ReportCommandTests(TempDbTestCase):
    def _init_run_and_agent(self, run="BOOK-1022", agent="coder-1"):
        run_cli(["init", run, "--plan", "/tmp/p.md", "--base", "main", "--sha", "abc"], self.db_path)
        run_cli(
            ["agent", "upsert", agent, "--run", run, "--branch", "feat/x", "--head-sha", "bbb",
             "--base-sha", "aaa", "--worktree", "/tmp/wt", "--report-path", str(self._report_path)],
            self.db_path,
        )

    def setUp(self):
        super().setUp()
        self._tmp_reports = tempfile.TemporaryDirectory()
        self._report_path = Path(self._tmp_reports.name) / "report.md"

    def tearDown(self):
        self._tmp_reports.cleanup()
        super().tearDown()

    def _headers_row(self, run, agent):
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        row = conn.execute(
            "SELECT * FROM headers WHERE run = ? AND agent = ?", (run, agent)
        ).fetchone()
        conn.close()
        return dict(row) if row else None

    def _agent_row(self, run, agent):
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        row = conn.execute(
            "SELECT * FROM agents WHERE run = ? AND name = ?", (run, agent)
        ).fetchone()
        conn.close()
        return dict(row) if row else None

    def test_report_missing_heading_is_fatal_and_writes_no_row(self):
        self._init_run_and_agent()
        bodies = default_report_bodies()
        report_path = write_report(self._tmp_reports.name, bodies, omit="evidence")
        rc, out, err = run_cli(["report", "coder-1", "--file", str(report_path)], self.db_path)
        self.assertNotEqual(rc, 0)
        self.assertEqual(out, "", msg="a rejected report must print nothing to stdout")
        self.assertIn("evidence", err)
        self.assertIsNone(self._headers_row("BOOK-1022", "coder-1"))

    def test_report_missing_multiple_headings_names_all_of_them(self):
        self._init_run_and_agent()
        bodies = default_report_bodies()
        report_path = write_report(self._tmp_reports.name, bodies, omit="evidence")
        # also strip a second heading manually
        text = report_path.read_text().replace("## verification\nprose for verification\n\n", "")
        report_path.write_text(text)
        rc, out, err = run_cli(["report", "coder-1", "--file", str(report_path)], self.db_path)
        self.assertNotEqual(rc, 0)
        self.assertEqual(out, "", msg="a rejected report must print nothing to stdout")
        self.assertIn("evidence", err)
        self.assertIn("verification", err)

    def test_report_missing_new_headings_are_caught(self):
        self._init_run_and_agent()
        bodies = default_report_bodies()
        report_path = write_report(self._tmp_reports.name, bodies, omit="skills_used")
        # also strip deploy_ordering manually
        text = report_path.read_text().replace("## deploy_ordering\nprose for deploy_ordering\n\n", "")
        report_path.write_text(text)
        rc, out, err = run_cli(["report", "coder-1", "--file", str(report_path)], self.db_path)
        self.assertNotEqual(rc, 0)
        self.assertEqual(out, "", msg="a rejected report must print nothing to stdout")
        self.assertIn("skills_used", err)
        self.assertIn("deploy_ordering", err)
        self.assertIsNone(self._headers_row("BOOK-1022", "coder-1"))

    def test_report_happy_path_writes_headers_row_and_prints_header(self):
        self._init_run_and_agent()
        bodies = default_report_bodies()
        report_path = write_report(self._tmp_reports.name, bodies)
        rc, out, err = run_cli(["report", "coder-1", "--file", str(report_path)], self.db_path)
        self.assertEqual(rc, 0, msg=f"stderr={err}")

        row = self._headers_row("BOOK-1022", "coder-1")
        self.assertIsNotNone(row)
        assert row is not None
        self.assertEqual(row["status"], "done")
        self.assertEqual(row["red_not_on_base"], "no")
        self.assertEqual(json.loads(row["deviations"]), ["used COALESCE instead of overwrite"])
        self.assertEqual(json.loads(row["plan_errors"]), [])
        self.assertIn("plan_errors", json.loads(row["empty_sections"]))
        self.assertNotIn("deviations", json.loads(row["empty_sections"]))

        self.assertIn("status: done", out)
        self.assertIn("report_file:", out)
        self.assertIn("ledger_rows:", out)
        self.assertIn("files_written:", out)
        self.assertIn("tickets:", out)
        self.assertIn("empty_sections:", out)

    def test_report_header_is_under_30_lines(self):
        self._init_run_and_agent()
        bodies = default_report_bodies()
        report_path = write_report(self._tmp_reports.name, bodies)
        rc, out, err = run_cli(["report", "coder-1", "--file", str(report_path)], self.db_path)
        self.assertEqual(rc, 0, msg=f"stderr={err}")
        line_count = len(out.strip("\n").split("\n"))
        self.assertLess(line_count, 30, msg=out)

    def test_report_rejects_bad_status(self):
        self._init_run_and_agent()
        bodies = default_report_bodies()
        bodies["status"] = "in_progress"
        report_path = write_report(self._tmp_reports.name, bodies)
        rc, out, err = run_cli(["report", "coder-1", "--file", str(report_path)], self.db_path)
        self.assertNotEqual(rc, 0)
        self.assertEqual(out, "", msg="a rejected report must print nothing to stdout")
        self.assertIn("status", err)
        self.assertIsNone(self._headers_row("BOOK-1022", "coder-1"))

    def test_report_rejects_bad_red_not_on_base(self):
        self._init_run_and_agent()
        bodies = default_report_bodies()
        bodies["red_not_on_base"] = "maybe"
        report_path = write_report(self._tmp_reports.name, bodies)
        rc, out, err = run_cli(["report", "coder-1", "--file", str(report_path)], self.db_path)
        self.assertNotEqual(rc, 0)
        self.assertEqual(out, "", msg="a rejected report must print nothing to stdout")
        self.assertIn("red_not_on_base", err)
        self.assertIsNone(self._headers_row("BOOK-1022", "coder-1"))

    def test_report_ledger_rows_reflects_db_counts(self):
        self._init_run_and_agent()
        run_cli(["note", "add", "--run", "BOOK-1022", "--agent", "coder-1", "--kind", "skipped", "--text", "x"], self.db_path)
        run_cli(["note", "add", "--run", "BOOK-1022", "--agent", "coder-1", "--kind", "skipped", "--text", "y"], self.db_path)
        run_cli(["ticket", "add", "--run", "BOOK-1022", "--key", "BOOK-999", "--title", "t", "--in-epic", "no", "--reason", "r", "--agent", "coder-1"], self.db_path)
        bodies = default_report_bodies()
        report_path = write_report(self._tmp_reports.name, bodies)
        rc, out, err = run_cli(["report", "coder-1", "--file", str(report_path)], self.db_path)
        self.assertEqual(rc, 0, msg=f"stderr={err}")
        self.assertIn("notes +2", out)
        self.assertIn("tickets +1", out)
        self.assertIn("tickets: BOOK-999", out)

    def test_report_updates_agent_status_and_head_sha(self):
        # The agent row starts at its dispatch-time status, with no head_sha yet — the same
        # state `rollout-db state` would show a coordinator that never ran a follow-up
        # `agent upsert`.
        run_cli(["init", "BOOK-1022", "--plan", "/tmp/p.md", "--base", "main", "--sha", "abc"], self.db_path)
        run_cli(
            ["agent", "upsert", "coder-1", "--run", "BOOK-1022", "--branch", "feat/x",
             "--base-sha", "aaa", "--worktree", "/tmp/wt", "--status", "dispatched"],
            self.db_path,
        )
        before = self._agent_row("BOOK-1022", "coder-1")
        assert before is not None
        self.assertEqual(before["status"], "dispatched")
        self.assertIsNone(before["head_sha"])

        bodies = default_report_bodies()
        bodies["status"] = "done"
        bodies["head_sha"] = "deadbee"
        report_path = write_report(self._tmp_reports.name, bodies)
        rc, out, err = run_cli(["report", "coder-1", "--file", str(report_path)], self.db_path)
        self.assertEqual(rc, 0, msg=f"stderr={err}")

        after = self._agent_row("BOOK-1022", "coder-1")
        assert after is not None
        self.assertEqual(after["status"], "done")
        self.assertEqual(after["head_sha"], "deadbee")

    def test_report_blocked_updates_agent_status_and_blocked_on(self):
        self._init_run_and_agent()
        bodies = default_report_bodies()
        bodies["status"] = "blocked"
        bodies["blocked_on"] = "which model for the fix round"
        report_path = write_report(self._tmp_reports.name, bodies)
        rc, out, err = run_cli(["report", "coder-1", "--file", str(report_path)], self.db_path)
        self.assertEqual(rc, 0, msg=f"stderr={err}")

        after = self._agent_row("BOOK-1022", "coder-1")
        assert after is not None
        self.assertEqual(after["status"], "blocked")
        self.assertEqual(after["blocked_on"], "which model for the fix round")


class UnitUpsertTests(TempDbTestCase):
    def _init_run(self):
        run_cli(["init", "BOOK-1022", "--plan", "/tmp/p.md", "--base", "main", "--sha", "abc"], self.db_path)

    def test_unit_upsert_inserts_row(self):
        self._init_run()
        rc, out, err = run_cli(
            ["unit", "upsert", "pr-api", "--run", "BOOK-1022", "--aspect", "api", "--wave", "1",
             "--kind", "pr", "--depends-on", '["pr-schema"]', "--status", "pending", "--ticket", "BOOK-1050"],
            self.db_path,
        )
        self.assertEqual(rc, 0, msg=f"stderr={err}")
        printed = json.loads(out)
        self.assertEqual(printed["unit"], "pr-api")
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        row = conn.execute(
            "SELECT * FROM units WHERE run = ? AND unit = ?", ("BOOK-1022", "pr-api")
        ).fetchone()
        conn.close()
        self.assertIsNotNone(row)
        assert row is not None
        self.assertEqual(row["aspect"], "api")
        self.assertEqual(row["wave"], 1)
        self.assertEqual(row["kind"], "pr")
        self.assertEqual(json.loads(row["depends_on"]), ["pr-schema"])
        self.assertEqual(row["status"], "pending")
        self.assertEqual(row["ticket"], "BOOK-1050")

    def test_unit_upsert_updates_status_on_conflict(self):
        self._init_run()
        run_cli(
            ["unit", "upsert", "pr-api", "--run", "BOOK-1022", "--aspect", "api", "--wave", "1",
             "--kind", "pr", "--depends-on", "[]", "--status", "pending", "--ticket", "BOOK-1050"],
            self.db_path,
        )
        rc, out, err = run_cli(
            ["unit", "upsert", "pr-api", "--run", "BOOK-1022", "--status", "merged"],
            self.db_path,
        )
        self.assertEqual(rc, 0, msg=f"stderr={err}")
        printed = json.loads(out)
        self.assertEqual(printed["status"], "merged")
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        row = conn.execute(
            "SELECT * FROM units WHERE run = ? AND unit = ?", ("BOOK-1022", "pr-api")
        ).fetchone()
        conn.close()
        assert row is not None
        self.assertEqual(row["status"], "merged")
        self.assertEqual(row["aspect"], "api")  # preserved from first call


class StateCommandTests(TempDbTestCase):
    def test_state_shows_agents_wave_and_open_decisions(self):
        run_cli(["init", "BOOK-1022", "--plan", "/tmp/p.md", "--base", "main", "--sha", "abc"], self.db_path)
        run_cli(
            ["agent", "upsert", "coder-1", "--run", "BOOK-1022", "--role", "coder", "--status", "dispatched"],
            self.db_path,
        )
        run_cli(
            ["decision", "add", "--run", "BOOK-1022", "--reason", "db path?", "--options", '["a","b"]', "--decided-by", "darren"],
            self.db_path,
        )
        run_cli(
            ["unit", "upsert", "pr-api", "--run", "BOOK-1022", "--aspect", "api", "--wave", "1",
             "--kind", "pr", "--depends-on", "[]", "--status", "pending", "--ticket", "BOOK-1050"],
            self.db_path,
        )
        rc, out, err = run_cli(["state", "BOOK-1022"], self.db_path)
        self.assertEqual(rc, 0, msg=f"stderr={err}")
        data = json.loads(out)
        self.assertEqual(data["ticket"], "BOOK-1022")
        self.assertEqual(data["current_wave"], 0)
        names = [a["name"] for a in data["agents"]]
        self.assertIn("coder-1", names)
        self.assertEqual(len(data["open_decisions"]), 1)
        self.assertEqual(data["open_decisions"][0]["reason"], "db path?")
        unit_names = [u["unit"] for u in data["units"]]
        self.assertIn("pr-api", unit_names)

    def test_state_decision_with_answer_is_not_open(self):
        run_cli(["init", "BOOK-1022", "--plan", "/tmp/p.md", "--base", "main", "--sha", "abc"], self.db_path)
        run_cli(
            ["decision", "add", "--run", "BOOK-1022", "--reason", "db path?", "--options", '["a"]',
             "--answer", "a", "--decided-by", "darren"],
            self.db_path,
        )
        rc, out, err = run_cli(["state", "BOOK-1022"], self.db_path)
        self.assertEqual(rc, 0, msg=f"stderr={err}")
        data = json.loads(out)
        self.assertEqual(data["open_decisions"], [])


class DumpCommandTests(TempDbTestCase):
    def test_dump_renders_markdown(self):
        run_cli(["init", "BOOK-1022", "--plan", "/tmp/p.md", "--base", "main", "--sha", "abc"], self.db_path)
        run_cli(["agent", "upsert", "coder-1", "--run", "BOOK-1022", "--role", "coder"], self.db_path)
        rc, out, err = run_cli(["dump", "BOOK-1022"], self.db_path)
        self.assertEqual(rc, 0, msg=f"stderr={err}")
        self.assertIn("BOOK-1022", out)
        self.assertIn("coder-1", out)
        self.assertIn("#", out)

    def test_dump_renders_superseded_trap_inline(self):
        run_cli(["init", "BOOK-1022", "--plan", "/tmp/p.md", "--base", "main", "--sha", "abc"], self.db_path)
        run_cli(
            ["trap", "add", "--run", "BOOK-1022", "--agent", "coder-1", "--repo", "fhir-works",
             "--path", "a.py", "--text", "watch for X"],
            self.db_path,
        )
        run_cli(
            ["trap", "add", "--run", "BOOK-1022", "--agent", "coder-2", "--repo", "fhir-works",
             "--path", "b.py", "--text", "actually watch for Y"],
            self.db_path,
        )
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        rows = [dict(r) for r in conn.execute("SELECT rowid, * FROM traps ORDER BY created_at").fetchall()]
        conn.close()
        false_rowid = rows[0]["rowid"]
        correction_rowid = rows[1]["rowid"]
        run_cli(
            ["trap", "resolve", "--run", "BOOK-1022", "--rowid", str(false_rowid),
             "--by-rowid", str(correction_rowid), "--reason", "X was wrong, see Y"],
            self.db_path,
        )
        rc, out, err = run_cli(["dump", "BOOK-1022"], self.db_path)
        self.assertEqual(rc, 0, msg=f"stderr={err}")
        self.assertIn("SUPERSEDED", out)
        self.assertIn(f"rowid {correction_rowid}", out)
        self.assertIn("watch for X", out)
        self.assertIn("actually watch for Y", out)


class TrapsCommandTests(TempDbTestCase):
    def test_traps_filters_by_repo_and_path_glob(self):
        run_cli(["init", "BOOK-1022", "--plan", "/tmp/p.md", "--base", "main", "--sha", "abc"], self.db_path)
        run_cli(
            ["trap", "add", "--run", "BOOK-1022", "--agent", "coder-1", "--repo", "fhir-works",
             "--path", "packages/prior-auth/api/foo.py", "--text", "watch A"],
            self.db_path,
        )
        run_cli(
            ["trap", "add", "--run", "BOOK-1022", "--agent", "coder-1", "--repo", "fhir-works",
             "--path", "packages/fhir-client/bar.py", "--text", "watch B"],
            self.db_path,
        )
        run_cli(
            ["trap", "add", "--run", "BOOK-1022", "--agent", "coder-1", "--repo", "other-repo",
             "--path", "x.py", "--text", "watch C"],
            self.db_path,
        )
        rc, out, err = run_cli(["traps", "--repo", "fhir-works"], self.db_path)
        self.assertEqual(rc, 0, msg=f"stderr={err}")
        data = json.loads(out)
        self.assertEqual(len(data), 2)

        rc, out, err = run_cli(["traps", "--repo", "fhir-works", "--path", "packages/prior-auth/*"], self.db_path)
        self.assertEqual(rc, 0, msg=f"stderr={err}")
        data = json.loads(out)
        self.assertEqual(len(data), 1)
        self.assertEqual(data[0]["text"], "watch A")

    def test_traps_renders_superseded_row_inline_at_its_position(self):
        run_cli(["init", "BOOK-1022", "--plan", "/tmp/p.md", "--base", "main", "--sha", "abc"], self.db_path)
        run_cli(
            ["trap", "add", "--run", "BOOK-1022", "--agent", "coder-1", "--repo", "fhir-works",
             "--path", "a.py", "--text", "watch for X"],
            self.db_path,
        )
        run_cli(
            ["trap", "add", "--run", "BOOK-1022", "--agent", "coder-2", "--repo", "fhir-works",
             "--path", "b.py", "--text", "watch for Y"],
            self.db_path,
        )
        run_cli(
            ["trap", "add", "--run", "BOOK-1022", "--agent", "coder-3", "--repo", "fhir-works",
             "--path", "c.py", "--text", "actually watch for X'"],
            self.db_path,
        )
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        rows = [dict(r) for r in conn.execute("SELECT rowid, * FROM traps ORDER BY created_at").fetchall()]
        conn.close()
        false_rowid = rows[0]["rowid"]
        correction_rowid = rows[2]["rowid"]

        rc, out, err = run_cli(
            ["trap", "resolve", "--run", "BOOK-1022", "--rowid", str(false_rowid),
             "--by-rowid", str(correction_rowid), "--reason", "X was wrong"],
            self.db_path,
        )
        self.assertEqual(rc, 0, msg=f"stderr={err}")

        rc, out, err = run_cli(["traps", "--repo", "fhir-works"], self.db_path)
        self.assertEqual(rc, 0, msg=f"stderr={err}")
        data = json.loads(out)
        self.assertEqual(len(data), 3)
        # The superseded row stays at its own (first) position, with the
        # correction marker inline, rather than being appended after the rest.
        self.assertIn("SUPERSEDED", data[0]["text"])
        self.assertIn(f"rowid {correction_rowid}", data[0]["text"])
        self.assertIn("watch for X", data[0]["text"])
        self.assertEqual(data[1]["text"], "watch for Y")
        self.assertEqual(data[2]["text"], "actually watch for X'")


class HookCheckCommandTests(TempDbTestCase):
    def _init_run(self):
        run_cli(["init", "BOOK-1022", "--plan", "/tmp/p.md", "--base", "main", "--sha", "abc"], self.db_path)

    def _notes(self):
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        rows = [dict(r) for r in conn.execute("SELECT * FROM notes").fetchall()]
        conn.close()
        return rows

    def test_hook_check_exits_0_when_agent_fine(self):
        self._init_run()
        with tempfile.TemporaryDirectory() as d:
            report_path = Path(d) / "report.md"
            report_path.write_text("dummy")
            run_cli(
                ["agent", "upsert", "coder-1", "--run", "BOOK-1022", "--report-path", str(report_path)],
                self.db_path,
            )
            bodies = default_report_bodies()
            full_report = Path(d) / "full-report.md"
            full_report.write_text(render_report(bodies))
            run_cli(["report", "coder-1", "--file", str(full_report)], self.db_path)

            rc, out, err = run_cli(["hook-check", "coder-1"], self.db_path)
            self.assertEqual(rc, 0, msg=f"stderr={err}")
            data = json.loads(out)
            self.assertEqual(data["status"], "ok")
        self.assertEqual([n for n in self._notes() if n["kind"] == "hook_warning"], [])

    def test_hook_check_exits_0_and_skips_when_agent_never_dispatched(self):
        # A name with no `agents` row (and no `audits` row) was never
        # dispatched under that name -- e.g. the hook's `agent_type` field --
        # so there is nothing to check it against, and no note is written.
        self._init_run()
        rc, out, err = run_cli(["hook-check", "nonexistent-agent"], self.db_path)
        self.assertEqual(rc, 0, msg=f"stderr={err}")
        data = json.loads(out)
        self.assertEqual(data["status"], "ok")
        self.assertEqual([n for n in self._notes() if n["kind"] == "hook_warning"], [])

    def test_hook_check_exits_0_and_skips_when_agent_name_empty(self):
        self._init_run()
        rc, out, err = run_cli(["hook-check", ""], self.db_path)
        self.assertEqual(rc, 0, msg=f"stderr={err}")
        data = json.loads(out)
        self.assertEqual(data["status"], "ok")
        self.assertEqual([n for n in self._notes() if n["kind"] == "hook_warning"], [])

    def test_hook_check_warns_when_dispatched_agent_has_no_headers_or_audits(self):
        self._init_run()
        run_cli(
            ["agent", "upsert", "coder-1", "--run", "BOOK-1022", "--report-path", "/tmp/never-written.md"],
            self.db_path,
        )
        rc, out, err = run_cli(["hook-check", "coder-1"], self.db_path)
        self.assertEqual(rc, 0, msg=f"stderr={err}")
        data = json.loads(out)
        self.assertEqual(data["status"], "warning")
        warnings = [n for n in self._notes() if n["kind"] == "hook_warning"]
        self.assertEqual(len(warnings), 1)
        self.assertIn("coder-1", warnings[0]["text"])

    def test_hook_check_auditor_with_audit_row_and_no_headers_is_ok(self):
        # The auditor agent writes an `audits` row and never runs `report`, so it
        # has no `headers` row. That must read as healthy, not a miss: without
        # this, every plan-rollout-auditor* dispatch trips a spurious warning via
        # the SubagentStop hook's plan-rollout-* matcher.
        self._init_run()
        run_cli(
            ["audit", "add", "--run", "BOOK-1022", "--agent", "auditor-1", "--evidence-status", "clean",
             "--discrepancies", "none", "--blast-radius-sections", "[]", "--audit-path", "/tmp/audits/auditor-1.md"],
            self.db_path,
        )
        rc, out, err = run_cli(["hook-check", "auditor-1"], self.db_path)
        self.assertEqual(rc, 0, msg=f"stderr={err}")
        data = json.loads(out)
        self.assertEqual(data["status"], "ok")
        self.assertEqual(
            [n for n in self._notes() if n["kind"] == "hook_warning"], [],
            msg="an auditor with an audits row and no headers row must not get a hook_warning note",
        )


class ConcurrencyTests(TempDbTestCase):
    def test_two_concurrent_note_adds_both_land(self):
        run_cli(["init", "BOOK-1022", "--plan", "/tmp/p.md", "--base", "main", "--sha", "abc"], self.db_path)

        results = {}

        def worker(key, text):
            results[key] = run_cli(
                ["note", "add", "--run", "BOOK-1022", "--agent", "coder-1", "--kind", "other", "--text", text],
                self.db_path,
            )

        t1 = threading.Thread(target=worker, args=("a", "note-a"))
        t2 = threading.Thread(target=worker, args=("b", "note-b"))
        t1.start()
        t2.start()
        t1.join(timeout=30)
        t2.join(timeout=30)

        rc_a, out_a, err_a = results["a"]
        rc_b, out_b, err_b = results["b"]
        self.assertEqual(rc_a, 0, msg=f"stderr={err_a}")
        self.assertEqual(rc_b, 0, msg=f"stderr={err_b}")
        self.assertIn("note-a", json.loads(out_a)["text"])
        self.assertIn("note-b", json.loads(out_b)["text"])

        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        rows = [dict(r) for r in conn.execute("SELECT * FROM notes").fetchall()]
        conn.close()
        self.assertEqual(len(rows), 2)
        texts = {r["text"] for r in rows}
        self.assertEqual(texts, {"note-a", "note-b"})


if __name__ == "__main__":
    unittest.main()
