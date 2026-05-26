"""Plugin manager slash command for Hermes Agent gateway (/pm).

Lets you install, list, remove, update, enable, and disable plugins
directly from Discord, Telegram, or any messaging platform —
no terminal needed.

Usage:
  /pm install owner/repo   — install & enable a plugin from GitHub
  /pm list                  — list installed plugins
  /pm remove <name>        — uninstall a plugin
  /pm update <name>        — pull latest version
  /pm enable <name>        — enable a disabled plugin
  /pm disable <name>       — disable without removing
"""

import asyncio
import logging
import shlex
import os

logger = logging.getLogger(__name__)

PLUGIN_HELP = """**Plugin Manager (/pm)**

```
/pm install <owner/repo>   Install & enable from GitHub
/pm list                   List installed plugins
/pm remove <name>          Uninstall a plugin
/pm update <name>          Pull latest version
/pm enable <name>          Enable a disabled plugin
/pm disable <name>         Disable without removing
```

*Tip: Add a quick command alias to use /plugins instead:*
```yaml
quick_commands:
  plugins:
    type: alias
    target: /pm
```"""


def _hermes_bin() -> str:
    """Resolve the hermes binary path."""
    # Check common locations
    candidates = [
        os.path.expanduser("~/.local/bin/hermes"),
        os.path.expanduser("~/.local/bin/coder"),
        "/usr/local/bin/hermes",
    ]
    for path in candidates:
        if os.path.isfile(path):
            return path
    # Try PATH
    return "hermes"


def _run_sync(cmd: str) -> str:
    """Run a shell command and return stripped stdout+stderr."""
    import subprocess
    try:
        result = subprocess.run(
            cmd,
            shell=True,
            capture_output=True,
            text=True,
            timeout=30,
        )
        output = (result.stdout or result.stderr or "").strip()
        return output or "OK (no output)"
    except subprocess.TimeoutExpired:
        return "Command timed out after 30s."
    except Exception as e:
        return f"Error: {e}"


async def _handle_pm(raw_args: str) -> str:
    """Handle /pm slash command."""
    args = raw_args.strip()
    if not args:
        return PLUGIN_HELP

    parts = shlex.split(args)
    subcmd = parts[0].lower()
    rest = parts[1:]

    hermes = _hermes_bin()

    if subcmd == "install":
        if not rest:
            return "Usage: `/pm install <owner/repo>`\nExample: `/pm install evanyudis/cjk_sanitizer`"
        repo = rest[0]
        cmd = f"{hermes} plugins install {shlex.quote(repo)} --enable"
        output = _run_sync(cmd)
        return f"Installing `{repo}`...\n```\n{output}\n```\nRestart gateway with `hermes gateway restart` to activate."

    elif subcmd in ("remove", "rm", "uninstall"):
        if not rest:
            return "Usage: `/pm remove <name>`"
        name = rest[0]
        cmd = f"{hermes} plugins remove {shlex.quote(name)}"
        output = _run_sync(cmd)
        return f"Removing `{name}`...\n```\n{output}\n```"

    elif subcmd in ("list", "ls"):
        cmd = f"{hermes} plugins list"
        output = _run_sync(cmd)
        return f"**Installed plugins:**\n```\n{output or '(none)'}\n```"

    elif subcmd == "update":
        if not rest:
            return "Usage: `/pm update <name>`"
        name = rest[0]
        cmd = f"{hermes} plugins update {shlex.quote(name)}"
        output = _run_sync(cmd)
        return f"Updating `{name}`...\n```\n{output}\n```"

    elif subcmd == "enable":
        if not rest:
            return "Usage: `/pm enable <name>`"
        name = rest[0]
        cmd = f"{hermes} plugins enable {shlex.quote(name)}"
        output = _run_sync(cmd)
        return f"Enabled `{name}`.\n```\n{output}\n```\nRestart gateway to apply."

    elif subcmd == "disable":
        if not rest:
            return "Usage: `/pm disable <name>`"
        name = rest[0]
        cmd = f"{hermes} plugins disable {shlex.quote(name)}"
        output = _run_sync(cmd)
        return f"Disabled `{name}`.\n```\n{output}\n```"

    else:
        return f"Unknown subcommand `{subcmd}`.\n\n{PLUGIN_HELP}"


def register(ctx):
    ctx.register_command(
        name="pm",
        handler=_handle_pm,
        description="Plugin manager: install, list, remove, update Hermes plugins",
        args_hint="<install|list|remove|update|enable|disable> [name]",
    )
