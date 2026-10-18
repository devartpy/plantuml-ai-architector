[← Configuration](configuration.md) · [Back to README](../README.md) · [Using Skills →](skills-usage.md)

# Agent Setup

`init` creates `.ai-architect/mcp-config-example.json`; agents do not load this file automatically. It defines an `mcpServers.plantuml` entry that launches the pinned `plantuml-mcp-server@0.2.4` through `npx -y`. Install Node.js 18+ and npm where the agent runs. The first launch may download the npm package.

The `PLANTUML_SERVER_URL` value is the renderer from `config.json`, not an MCP URL. The [PlantUML MCP server](https://github.com/infobip/plantuml-mcp-server) provides rendering and encode/decode tools; the renderer alone does not expose MCP tools. When asked to save rendered files, that server limits output to its working directory by default.

---

## Make the Skills Available

Run `ai-architect init` **in the project where you want to draw diagrams**. It places the four skills in `.ai-architect/skills/`, but that package-managed directory is not a standard skill-discovery location. Expose the **skill folders** in your agent's discovery directory based on the table below:

| Agent | Destination in the target project |
| --- | --- |
| [Claude Code](https://code.claude.com/docs/en/skills) | `.claude/skills/<skill-name>/SKILL.md` |
| [Codex](https://learn.chatgpt.com/docs/build-skills) | `.agents/skills/<skill-name>/SKILL.md` |
| [Cursor](https://prod.cursor.com/help/customization/skills) | `.agents/skills/<skill-name>/SKILL.md` |

### Step-by-Step Installation

Select the setup command matching your operating system. Run these commands from your **target project root**.

> 💡 **Note:** The examples below target `.agents/skills` (for Codex/Cursor). If you are using Claude Code, change the destination path variable to `.claude/skills`.

#### 🌐 macOS & Linux (Symbolic Links)
Creating symlinks allows the agent to automatically receive skill updates whenever you run `ai-architect init` in the future.
```bash
SKILLS_ROOT=".agents/skills" # Use ".claude/skills" for Claude Code
mkdir -p "$SKILLS_ROOT"
for name in plantuml-create plantuml-modify plantuml-verify self-correct; do
    ln -s "$(pwd)/.ai-architect/skills/$name" "$SKILLS_ROOT/$name"
done
```

#### 🪟 Windows (File Copying)
Creating a symbolic link on Windows may require Administrator privileges or Developer Mode. Copy the folders when you want a straightforward installation:
```powershell
$skillsRoot = ".agents/skills" # Use ".claude/skills" for Claude Code
New-Item -ItemType Directory -Force -Path $skillsRoot | Out-Null
foreach ($name in @("plantuml-create", "plantuml-modify", "plantuml-verify", "self-correct")) {
    $source = Join-Path ".ai-architect/skills" $name
    $target = Join-Path $skillsRoot $name
    if (Test-Path -LiteralPath $target) { throw "Skill already exists: $target" }
    Copy-Item -LiteralPath $source -Destination $target -Recurse
}
```

Copies do not update when you rerun `ai-architect init`. After a package upgrade, review and replace the four copied skill folders to pick up changes. The command above stops if a destination already exists, so it cannot silently overwrite a skill you edited.

For a Windows installation that follows updates without copying, use directory junctions instead. On this workstation, `New-Item -ItemType Junction` works without elevation and exposes `SKILL.md` at the discovery path:

```powershell
$skillsRoot = ".agents/skills" # Use ".claude/skills" for Claude Code
New-Item -ItemType Directory -Force -Path $skillsRoot | Out-Null
foreach ($name in @("plantuml-create", "plantuml-modify", "plantuml-verify", "self-correct")) {
    $source = (Resolve-Path ".ai-architect/skills/$name").Path
    $target = Join-Path $skillsRoot $name
    if (Test-Path -LiteralPath $target) { throw "Skill already exists: $target" }
    New-Item -ItemType Junction -Path $target -Target $source | Out-Null
}
```

Check discovery in your agent after creating junctions; its documentation does not explicitly guarantee support for Windows junctions. If it does not discover them, use copies. Recreate junctions if you move the project.

### Verify Skill Installation

Check that all four `SKILL.md` files exist under your agent's discovery directory. Reopen the agent if they do not appear. In Codex CLI, `/skills` lists discovered skills. Then follow [Using the Diagram Skills](skills-usage.md) for invocation examples and expected behavior.

Registering skills does not connect PlantUML MCP. Configure the server separately below.

---

## Connect PlantUML MCP

Open the generated `.ai-architect/mcp-config-example.json` file and merge its `plantuml` entry into your agent's configuration file:

| Client | Configuration File Location | Format |
| --- | --- | --- |
| [Claude Code](https://code.claude.com/docs/en/mcp) | `.mcp.json` at the project root, under `mcpServers` | JSON |
| [Cursor](https://prod.cursor.com/help/customization/mcp) | `.cursor/mcp.json`, under `mcpServers` | JSON |
| [Codex](https://developers.openai.com/codex/mcp) | `.codex/config.toml`, under `mcp_servers` | TOML |

### Configuration Templates

> ⚠️ **Important:** Replace the `PLANTUML_SERVER_URL` value below with the actual `plantuml_server_url` from your project's `.ai-architect/config.json`. Preserve any other configured MCP servers in your file.

#### 🌐 Configuration for macOS & Linux (POSIX)

**JSON-based clients (Claude Code, Cursor):**
```json
{
  "mcpServers": {
    "plantuml": {
      "command": "npx",
      "args": ["-y", "plantuml-mcp-server@0.2.4"],
      "env": {
        "PLANTUML_SERVER_URL": "https://www.plantuml.com/plantuml"
      }
    }
  }
}
```

**TOML-based clients (Codex):**
```toml
[mcp_servers.plantuml]
command = "npx"
args = ["-y", "plantuml-mcp-server@0.2.4"]

[mcp_servers.plantuml.env]
PLANTUML_SERVER_URL = "https://www.plantuml.com/plantuml"
```

#### 🪟 Configuration for Windows

**JSON-based clients (Claude Code, Cursor):**
```json
{
  "mcpServers": {
    "plantuml": {
      "command": "cmd.exe",
      "args": ["/d", "/c", "npx.cmd", "-y", "plantuml-mcp-server@0.2.4"],
      "env": {
        "PLANTUML_SERVER_URL": "https://www.plantuml.com/plantuml"
      }
    }
  }
}
```

**TOML-based clients (Codex):**
```toml
[mcp_servers.plantuml]
command = "cmd.exe"
args = ["/d", "/c", "npx", "-y", "plantuml-mcp-server@0.2.4"]

[mcp_servers.plantuml.env]
PLANTUML_SERVER_URL = "https://www.plantuml.com/plantuml"
```

### Verification

After updating the configuration file, restart or reload your client workspace. Approve or trust the new project configuration when prompted by your agent.

To verify that the PlantUML MCP tools are active, run the check command for your specific client:
* **Claude Code:** Run `claude mcp get plantuml` in the terminal.
* **Codex:** Run `codex mcp list` or use the `/mcp` command in its CLI.
* **Cursor:** Open **Customize → MCPs** to inspect the server; check **MCP Logs** in the Output panel if it fails to connect.

---

## See Also

* [Getting Started](getting-started.md) — create the workspace first
* [Using the Diagram Skills](skills-usage.md) — invoke and choose a diagram type
* [Configuration](configuration.md) — choose a local or internal renderer
