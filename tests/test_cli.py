from __future__ import annotations

from pathlib import Path

from dbweakcheck import cli


def test_read_word_file_skips_comments_and_blank_lines(tmp_path: Path) -> None:
    word_file = tmp_path / "words.txt"
    word_file.write_text("\n# comment\nadmin\n\nroot\n", encoding="utf-8")

    assert cli.read_word_file(word_file) == ["admin", "root"]


def test_collect_attempts_supports_single_and_dictionary_values(tmp_path: Path) -> None:
    password_file = tmp_path / "passwords.txt"
    password_file.write_text("admin123\nadmin123\nroot\n", encoding="utf-8")
    parser = cli.build_parser()
    args = parser.parse_args(
        [
            "--authorize",
            "--db",
            "mysql",
            "--host",
            "127.0.0.1",
            "--user",
            "root",
            "--password",
            "toor",
            "--password-file",
            str(password_file),
            "--empty-password",
        ]
    )

    attempts = cli.collect_attempts(args)

    assert attempts == [
        cli.CredentialAttempt("root", ""),
        cli.CredentialAttempt("root", "toor"),
        cli.CredentialAttempt("root", "admin123"),
        cli.CredentialAttempt("root", "root"),
    ]


def test_main_requires_authorization(capsys) -> None:
    code = cli.main(["--db", "mysql", "--host", "127.0.0.1", "--user", "root", "--password", "root"])

    captured = capsys.readouterr()
    assert code == 2
    assert "--authorize is required" in captured.err


def test_dry_run_does_not_call_checker(capsys) -> None:
    def checker(target: cli.TargetConfig, username: str, password: str) -> tuple[bool, str]:
        raise AssertionError("checker should not be called during dry run")

    code = cli.main(
        [
            "--authorize",
            "--db",
            "redis",
            "--host",
            "127.0.0.1",
            "--user",
            "default",
            "--password",
            "redis",
            "--dry-run",
        ],
        checkers={"redis": checker},
    )

    captured = capsys.readouterr()
    assert code == 0
    assert "Planned 1 attempt(s)" in captured.out


def test_found_password_is_masked_by_default(capsys) -> None:
    def checker(target: cli.TargetConfig, username: str, password: str) -> tuple[bool, str]:
        return password == "secret", "login accepted"

    code = cli.main(
        [
            "--authorize",
            "--db",
            "postgresql",
            "--host",
            "db.internal",
            "--user",
            "postgres",
            "--password",
            "secret",
            "--fail-on-found",
        ],
        checkers={"postgresql": checker},
    )

    captured = capsys.readouterr()
    assert code == 3
    assert "s****t" in captured.out
    assert "password='secret'" not in captured.out


def test_reveal_password_prints_raw_password(capsys) -> None:
    def checker(target: cli.TargetConfig, username: str, password: str) -> tuple[bool, str]:
        return True, "login accepted"

    code = cli.main(
        [
            "--authorize",
            "--db",
            "mysql",
            "--host",
            "localhost",
            "--user",
            "root",
            "--password",
            "root",
            "--reveal-password",
        ],
        checkers={"mysql": checker},
    )

    captured = capsys.readouterr()
    assert code == 0
    assert "password='root'" in captured.out

def test_password_templates_expand_per_user_and_target() -> None:
    parser = cli.build_parser()
    args = parser.parse_args(
        [
            "--authorize",
            "--db",
            "postgresql",
            "--host",
            "db01.internal",
            "--database",
            "appdb",
            "--user",
            "postgres",
            "--user",
            "app",
            "--password",
            "static",
            "--password-template",
            "{user}@{database}",
            "--password-template",
            "{host_label}{port}",
        ]
    )

    attempts = cli.collect_attempts(args)

    assert attempts == [
        cli.CredentialAttempt("postgres", "static"),
        cli.CredentialAttempt("postgres", "postgres@appdb"),
        cli.CredentialAttempt("postgres", "db015432"),
        cli.CredentialAttempt("postgres", "app@appdb"),
        cli.CredentialAttempt("app", "static"),
        cli.CredentialAttempt("app", "postgres@appdb"),
        cli.CredentialAttempt("app", "db015432"),
        cli.CredentialAttempt("app", "app@appdb"),
    ]


def test_password_template_rejects_unknown_placeholder() -> None:
    parser = cli.build_parser()
    args = parser.parse_args(
        [
            "--authorize",
            "--db",
            "mysql",
            "--host",
            "127.0.0.1",
            "--user",
            "root",
            "--password-template",
            "{unknown}",
        ]
    )

    try:
        cli.collect_attempts(args)
    except ValueError as exc:
        assert "Unknown password template placeholder: unknown" in str(exc)
    else:
        raise AssertionError("expected ValueError")


def test_max_attempts_limits_generated_combinations() -> None:
    parser = cli.build_parser()
    args = parser.parse_args(
        [
            "--authorize",
            "--db",
            "redis",
            "--host",
            "127.0.0.1",
            "--user",
            "default",
            "--user",
            "admin",
            "--password",
            "redis",
            "--password",
            "admin",
            "--max-attempts",
            "3",
        ]
    )

    try:
        cli.collect_attempts(args)
    except ValueError as exc:
        assert "exceeds --max-attempts 3" in str(exc)
    else:
        raise AssertionError("expected ValueError")


def test_summary_includes_status_counts(capsys) -> None:
    def checker(target: cli.TargetConfig, username: str, password: str) -> tuple[bool, str]:
        return password == "secret", "login accepted" if password == "secret" else "denied"

    code = cli.main(
        [
            "--authorize",
            "--db",
            "mysql",
            "--host",
            "localhost",
            "--user",
            "root",
            "--password",
            "bad",
            "--password",
            "secret",
            "--continue-after-success",
        ],
        checkers={"mysql": checker},
    )

    captured = capsys.readouterr()
    assert code == 0
    assert "found=1" in captured.out
    assert "failed=1" in captured.out

def test_delay_wait_stops_before_calling_checker_after_success() -> None:
    target = cli.TargetConfig(
        db_type="mysql",
        host="localhost",
        port=3306,
        database=None,
        service_name=None,
        sid=None,
        timeout=1.0,
    )
    attempts = [
        cli.CredentialAttempt("root", "secret"),
        cli.CredentialAttempt("root", "later"),
    ]
    seen: list[str] = []

    def checker(target: cli.TargetConfig, username: str, password: str) -> tuple[bool, str]:
        seen.append(password)
        return password == "secret", "login accepted"

    results = cli.run_checks(
        target,
        attempts,
        checker,
        max_workers=1,
        delay=0.01,
        stop_on_success=True,
    )

    assert seen == ["secret"]
    assert any(result.status == "found" for result in results)

