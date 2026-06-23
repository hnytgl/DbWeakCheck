# dbweakcheck

`dbweakcheck` 是一个用于授权安全自查的数据库弱口令检查命令行工具。它支持单个口令测试，也支持从字典文件批量测试常见数据库服务。

支持的数据库类型：

- MySQL
- Microsoft SQL Server
- Oracle
- PostgreSQL
- Redis

这个工具一次检查一个目标主机，并且每次运行都必须显式添加 `--authorize`。请只在你拥有或已经获得明确授权的系统上使用。

## 安装

只安装命令行工具，不安装数据库驱动：

```powershell
python -m pip install -e .
```

安装全部可选数据库驱动：

```powershell
python -m pip install -e ".[all]"
```

只安装某一类数据库驱动：

```powershell
python -m pip install -e ".[mysql]"
python -m pip install -e ".[mssql]"
python -m pip install -e ".[oracle]"
python -m pip install -e ".[postgresql]"
python -m pip install -e ".[redis]"
```

## 使用示例

测试单个口令：

```powershell
dbweakcheck --authorize --db mysql --host 127.0.0.1 --user root --password root
```

使用密码字典：

```powershell
dbweakcheck --authorize `
  --db postgresql `
  --host 127.0.0.1 `
  --database postgres `
  --user postgres `
  --password-file .\passwords.txt
```

同时指定多个用户名和多个口令：

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


使用模板派生本地审计常见口令，减少手工维护字典：

```powershell
dbweakcheck --authorize `
  --db postgresql `
  --host db01.internal `
  --database appdb `
  --user postgres `
  --user app `
  --password-file .\passwords.txt `
  --password-template "{user}@{database}" `
  --password-template "{host_label}{port}" `
  --max-attempts 5000
```

检查 MSSQL：

```powershell
dbweakcheck --authorize `
  --db mssql `
  --host 127.0.0.1 `
  --database master `
  --user sa `
  --password-file .\passwords.txt
```

使用 Oracle Service Name：

```powershell
dbweakcheck --authorize `
  --db oracle `
  --host 127.0.0.1 `
  --service-name ORCLPDB1 `
  --user system `
  --password-file .\passwords.txt
```

使用 Oracle SID：

```powershell
dbweakcheck --authorize `
  --db oracle `
  --host 127.0.0.1 `
  --sid ORCLCDB `
  --user system `
  --password manager
```

## 常用参数

- `--authorize`：确认你正在检查自己拥有或已获授权的目标，必填。
- `--db`：数据库类型，可选 `mysql`、`mssql`、`oracle`、`postgresql`、`redis`。
- `--host`：目标主机或 IP 地址。
- `--port`：目标端口，不传时使用对应数据库默认端口。
- `--database`：数据库名，PostgreSQL 的 dbname，或 Oracle service fallback。
- `--service-name`：Oracle Service Name。
- `--sid`：Oracle SID，优先级高于 `--service-name`。
- `--user`：要测试的用户名，可重复传入。
- `--user-file`：用户名字典文件，每行一个用户名。
- `--password`：要测试的口令，可重复传入。
- `--password-file`：口令字典文件，每行一个口令。
- `--empty-password`：额外测试空口令。
- `--password-template`：按用户和目标信息派生口令，支持 `{user}`、`{username}`、`{db}`、`{database}`、`{host}`、`{host_label}`、`{port}`，可重复传入。
- `--max-attempts 10000`：限制最终生成的用户名和口令组合数量，避免误把超大字典打到目标服务上。
- `--dry-run`：只显示计划尝试次数，不发起连接。
- `--max-workers 4`：设置并发数量。
- `--delay 0.5`：每次尝试前等待的秒数。
- `--continue-after-success`：发现有效口令后继续测试后续组合。
- `--json-output results.json`：输出 JSON 结果。
- `--csv-output results.csv`：输出 CSV 结果。
- `--fail-on-found`：发现有效口令时以退出码 `3` 结束，适合 CI 或巡检脚本。
- `--reveal-password`：显示明文口令。默认会对口令做脱敏。
- `--verbose`：输出失败尝试，默认只输出发现项和错误信息。

## 输出说明

默认情况下，工具会隐藏口令，例如把 `secret` 显示为 `s****t`。如果需要在本地审计报告中保留明文口令，可以显式添加 `--reveal-password`。

使用 `--json-output` 或 `--csv-output` 导出结果时，同样默认脱敏；只有添加 `--reveal-password` 后才会写入明文口令。

结束摘要会按状态统计结果，例如 `found=1, failed=20, skipped=3`，方便快速区分有效口令、认证失败、缺少驱动或网络错误。默认发现有效口令后会停止提交后续组合；添加 `--continue-after-success` 后会继续完整测试。

## 开发

```powershell
python -m pip install -e ".[dev]"
python -m pytest
$env:PYTHONPATH='src'; python -m dbweakcheck --help
```
