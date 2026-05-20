# Windows tooling

## Principle

In PowerShell 5.1 native (Windows corporate-restricted; no WSL
available), `Out-File -Encoding utf8` emits UTF-8 with BOM. For
commit messages, file content, and any text intended to be
interpreted as pure UTF-8, use
`[System.IO.File]::WriteAllText` with an explicit
`UTF8Encoding($false)`.

## Justification

Materialized in session #25 during commit message authoring.
`Out-File -Encoding utf8` injected a BOM, which propagated to
commit subjects and broke conventions. Fix: explicit no-BOM
encoder. Behavior is corrected in PS 7+ (where `utf8NoBOM` is
available), but the operating environment is PS 5.1.

## When to apply

- Writing commit messages from a file (multi-line commits or
  templated subjects).
- Writing any file whose downstream consumer is sensitive to
  BOM (git, parsers, CI tooling).
- Generally in this environment, prefer the explicit pattern
  rather than relying on `Out-File` defaults.

## How to apply

    $msg = "feat(scope): subject line`n`nBody paragraph here."
    [System.IO.File]::WriteAllText(
      "$PSScriptRoot\commit-msg.txt",
      $msg,
      [System.Text.UTF8Encoding]::new($false)
    )
    git commit -F .\commit-msg.txt
    Remove-Item .\commit-msg.txt

For single-line subjects, `git commit -m "..."` with the subject
inline avoids the temp file entirely and is preferred when the
subject fits.

## Reference

No direct Anthropic guidance — environment-specific to Windows
PowerShell 5.1 native.
