# dbweakcheck

`dbweakcheck` is a command-line weak-password checker for authorized database
security audits. It supports single-password tests and dictionary-based checks
against common database services.

Supported targets:

- MySQL
- Microsoft SQL Server
- Oracle
- PostgreSQL
- Redis

The tool checks one host at a time and requires `--authorize` on every run.
Use it only on systems you own or have explicit permission to assess.

## Install

Install the CLI without database drivers:

```powershell
python -m pip install -e .
```

Install all optional database drivers:

```powershell
python -m pip install -e ".[all]"
```

Install only one driver family:

```powershell
python -m pip install -e ".[mysql]"
python -m pip install -e ".[mssql]"
python -m pip install -e ".[oracle]"
python -m pip install -e ".[postgresql]"
python -m pip install -e ".[redis]"
```

## Examples

Single password:

```powershell
dbweakcheck --authorize --db mysql --host 127.0.0.1 --user root --password root
```

Password dictionary:

```powershell
dbweakcheck --authorize `
  --db postgresql `
  --host 127.0.0.1 `
  --database postgres `
  --user postgres `
  --password-file .\passwords.txt
```

Multiple users and passwords:

```powershell
dbweakcheck --authorize `
  --db redis `
  --host 127.0.0.1 `
  --user default `
  --user-file .\users.txt `
  --password redis `
  --password-file .\passwords.txt `
  --empty-password
```

MSSQL:

```powershell
dbweakcheck --authorize `
  --db mssql `
  --host 127.0.0.1 `
  --database master `
  --user sa `
  --password-file .\passwords.txt
```

Oracle service name:

```powershell
dbweakcheck --authorize `
  --db oracle `
  --host 127.0.0.1 `
  --service-name ORCLPDB1 `
  --user system `
  --password-file .\passwords.txt
```

Oracle SID:

```powershell
dbweakcheck --authorize `
  --db oracle `
  --host 127.0.0.1 `
  --sid ORCLCDB `
  --user system `
  --password manager
```

## Options

- `--dry-run`: print the planned attempt count without connecting.
- `--max-workers 4`: set the concurrency limit.
- `--delay 0.5`: wait before each attempt.
- `--continue-after-success`: keep testing after a valid credential is found.
- `--json-output results.json`: write JSON results.
- `--csv-output results.csv`: write CSV results.
- `--fail-on-found`: exit with code `3` when a valid credential is found.
- `--reveal-password`: show raw passwords. Passwords are masked by default.
- `--verbose`: print failed attempts as well as findings and errors.

## Development

```powershell
python -m pip install -e ".[dev]"
python -m pytest
python -m dbweakcheck --help
```
