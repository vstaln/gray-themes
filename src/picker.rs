//! `/theme` bare — arrow-key picker in the terminal handoff. The plugin owns
//! the whole surface now: rows are the built-in, user files in
//! ~/.gray/themes, and the embedded pack (not-installed entries install on
//! select). Enter applies: installs if needed, writes `"theme"` to
//! config.json, prints the restart hint.

use std::io::Write;

use serde_json::Value;

use crate::{THEMES, themes_dir};

pub struct Row {
    pub name: String,
    pub json: Option<&'static str>,
    pub builtin: bool,
    pub installed: bool,
}

fn dir_themes() -> Vec<String> {
    let Ok(read) = std::fs::read_dir(themes_dir()) else {
        return Vec::new();
    };
    let mut out: Vec<String> = read
        .filter_map(|e| e.ok())
        .filter_map(|e| {
            let p = e.path();
            if p.extension().and_then(|x| x.to_str()) != Some("json") {
                return None;
            }
            p.file_stem()?.to_str().map(str::to_string)
        })
        .collect();
    out.sort();
    out.dedup();
    out
}

pub fn rows() -> Vec<Row> {
    let mut out = vec![Row {
        name: "gray".into(),
        json: None,
        builtin: true,
        installed: true,
    }];
    let dir = dir_themes();
    for name in &dir {
        if name.as_str() != "gray" {
            out.push(Row {
                name: name.clone(),
                json: None,
                builtin: false,
                installed: true,
            });
        }
    }
    for (name, json) in THEMES {
        if !dir.iter().any(|d| d == name) {
            out.push(Row {
                name: (*name).to_string(),
                json: Some(json),
                builtin: false,
                installed: false,
            });
        }
    }
    out
}

fn swatch(json: &str) -> String {
    let m: Value = serde_json::from_str(json).unwrap_or(Value::Null);
    let v = &m["vars"];
    let hex = |k: &str| v[k].as_str().unwrap_or("000000");
    let rgb = |h: &str| -> (u8, u8, u8) {
        let h = h.trim_start_matches('#');
        let p = |s: &str| u8::from_str_radix(s, 16).unwrap_or(0);
        (
            p(h.get(0..2).unwrap_or("00")),
            p(h.get(2..4).unwrap_or("00")),
            p(h.get(4..6).unwrap_or("00")),
        )
    };
    let (br, bg_, bb) = rgb(hex("bg"));
    let (fr, fg, fb) = rgb(hex("fg"));
    let (ar, ag, ab) = rgb(hex("accent"));
    format!(
        "\x1b[48;2;{br};{bg_};{bb}m \x1b[48;2;{fr};{fg};{fb}m \x1b[48;2;{ar};{ag};{ab}m \x1b[0m"
    )
}

fn row_swatch(row: &Row) -> String {
    if row.builtin {
        return "   ".to_string();
    }
    let json = match &row.json {
        Some(j) => Some((*j).to_string()),
        None => std::fs::read_to_string(themes_dir().join(format!("{}.json", row.name))).ok(),
    };
    json.map(|j| swatch(&j)).unwrap_or_else(|| "   ".into())
}

/// Interactive picker. Returns the applied theme name (`"gray"` = built-in)
/// or None when cancelled / no tty.
pub fn pick() -> Option<String> {
    use crossterm::{cursor, event, execute, terminal};

    let rows = rows();
    let mut sel = crate::saved_theme()
        .and_then(|a| rows.iter().position(|r| r.name == a))
        .unwrap_or(0);
    let mut out = std::io::stdout();
    terminal::enable_raw_mode().ok()?;
    let _ = execute!(out, terminal::EnterAlternateScreen, cursor::Hide);

    let mut applied: Option<String> = None;
    loop {
        let mut buf = String::from("\x1b[H");
        buf.push_str("theme — up/down select · enter apply · esc cancel\r\n\r\n");
        for (i, r) in rows.iter().enumerate() {
            let mark = if i == sel { ">" } else { " " };
            let tag = if r.builtin {
                "built-in"
            } else if r.installed {
                ""
            } else {
                "pack — installs on apply"
            };
            buf.push_str(&format!(
                "{mark} {:<16} {} {tag}\r\n",
                r.name,
                row_swatch(r)
            ));
        }
        let _ = write!(out, "{buf}");
        let _ = out.flush();
        if let event::Event::Key(k) = event::read().unwrap_or(event::Event::Resize(0, 0)) {
            match k.code {
                event::KeyCode::Up | event::KeyCode::Char('k') => sel = sel.saturating_sub(1),
                event::KeyCode::Down | event::KeyCode::Char('j') => {
                    sel = (sel + 1).min(rows.len().saturating_sub(1));
                }
                event::KeyCode::Enter => {
                    applied = Some(rows[sel].name.clone());
                    break;
                }
                event::KeyCode::Esc | event::KeyCode::Char('q') => break,
                _ => {}
            }
        }
    }
    let _ = execute!(out, cursor::Show, terminal::LeaveAlternateScreen);
    let _ = terminal::disable_raw_mode();
    applied
}

/// Apply a chosen row: install pack file when needed, write config, report.
pub fn apply(name: &str) -> String {
    if name == "gray" || name.eq_ignore_ascii_case("default") {
        return match crate::persist_theme(None) {
            Ok(()) => "theme gray (built-in) — restart gray to apply".into(),
            Err(e) => format!("built-in set but not saved: {e}"),
        };
    }
    if let Some(entry) = crate::find(name) {
        if let Err(e) = crate::install(entry) {
            return format!("install skipped: {e}");
        }
    } else if !themes_dir().join(format!("{name}.json")).is_file() {
        return format!("no such theme `{name}` — /theme lists them");
    }
    match crate::persist_theme(Some(name)) {
        Ok(()) => format!("theme {name} — restart gray to apply"),
        Err(e) => format!("theme {name} not saved: {e}"),
    }
}
