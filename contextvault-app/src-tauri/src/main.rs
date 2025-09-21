// Prevents additional console window on Windows in release, DO NOT REMOVE!!
#![cfg_attr(not(debug_assertions), windows_subsystem = "windows")]

use std::process::{Command, Stdio};
use std::thread;
use std::time::Duration;
use std::path::Path;
use std::fs;
use tauri::{Manager, SystemTray, SystemTrayEvent, SystemTrayMenu, CustomMenuItem, State, Window};
use serde::{Deserialize, Serialize};
use anyhow::Result;

#[derive(Debug, Clone, Serialize, Deserialize)]
struct ContextVaultStatus {
    running: bool,
    port: Option<u16>,
    ollama_detected: bool,
    ollama_port: Option<u16>,
    context_entries: u32,
    last_error: Option<String>,
}

struct AppState {
    server_process: Option<std::process::Child>,
    status: ContextVaultStatus,
}

impl Default for AppState {
    fn default() -> Self {
        Self {
            server_process: None,
            status: ContextVaultStatus {
                running: false,
                port: None,
                ollama_detected: false,
                ollama_port: None,
                context_entries: 0,
                last_error: None,
            },
        }
    }
}

fn main() {
    let quit = CustomMenuItem::new("quit".to_string(), "Quit");
    let show = CustomMenuItem::new("show".to_string(), "Show");
    let hide = CustomMenuItem::new("hide".to_string(), "Hide");
    let tray_menu = SystemTrayMenu::new()
        .add_item(show)
        .add_item(hide)
        .add_native_item(tauri::SystemTrayMenuItem::Separator)
        .add_item(quit);

    let system_tray = SystemTray::new().with_menu(tray_menu);

    tauri::Builder::default()
        .manage(AppState::default())
        .system_tray(system_tray)
        .on_system_tray_event(|app, event| match event {
            SystemTrayEvent::LeftClick {
                position: _,
                size: _,
                ..
            } => {
                let window = app.get_window("main").unwrap();
                window.show().unwrap();
                window.set_focus().unwrap();
            }
            SystemTrayEvent::MenuItemClick { id, .. } => {
                match id.as_str() {
                    "quit" => {
                        std::process::exit(0);
                    }
                    "show" => {
                        let window = app.get_window("main").unwrap();
                        window.show().unwrap();
                        window.set_focus().unwrap();
                    }
                    "hide" => {
                        let window = app.get_window("main").unwrap();
                        window.hide().unwrap();
                    }
                    _ => {}
                }
            }
            _ => {}
        })
        .invoke_handler(tauri::generate_handler![
            start_contextvault_server,
            stop_contextvault_server,
            get_server_status,
            check_ollama_status,
            get_context_entries,
            add_context_entry,
            delete_context_entry,
            get_system_info
        ])
        .setup(|app| {
            // Start ContextVault server automatically
            let app_handle = app.handle();
            thread::spawn(move || {
                thread::sleep(Duration::from_secs(2)); // Wait for app to initialize
                if let Ok(window) = app_handle.get_window("main") {
                    let _ = window.emit("server-starting", ());
                }
                
                // Try to start the server
                let _ = start_contextvault_server_internal(&app_handle);
            });
            
            Ok(())
        })
        .on_window_event(|event| match event.event() {
            tauri::WindowEvent::CloseRequested { api, .. } => {
                // Hide to tray instead of closing
                event.window().hide().unwrap();
                api.prevent_close();
            }
            _ => {}
        })
        .run(tauri::generate_context!())
        .expect("error while running tauri application");
}

#[tauri::command]
async fn start_contextvault_server(window: Window, state: State<'_, AppState>) -> Result<ContextVaultStatus, String> {
    let result = start_contextvault_server_internal(&window.app_handle());
    match result {
        Ok(status) => {
            let _ = window.emit("server-started", &status);
            Ok(status)
        }
        Err(e) => {
            let error_msg = format!("Failed to start ContextVault server: {}", e);
            let _ = window.emit("server-error", &error_msg);
            Err(error_msg)
        }
    }
}

#[tauri::command]
async fn stop_contextvault_server(state: State<'_, AppState>) -> Result<ContextVaultStatus, String> {
    let mut app_state = state.inner();
    
    if let Some(mut process) = app_state.server_process.take() {
        if let Err(e) = process.kill() {
            return Err(format!("Failed to stop server: {}", e));
        }
    }
    
    app_state.status.running = false;
    app_state.status.port = None;
    app_state.status.last_error = Some("Server stopped".to_string());
    
    Ok(app_state.status.clone())
}

#[tauri::command]
async fn get_server_status(state: State<'_, AppState>) -> ContextVaultStatus {
    let app_state = state.inner();
    
    // Check if server is actually running by making a request
    if app_state.status.running {
        if let Some(port) = app_state.status.port {
            match reqwest::get(&format!("http://localhost:{}/api/health", port)).await {
                Ok(response) => {
                    if response.status().is_success() {
                        return app_state.status.clone();
                    }
                }
                Err(_) => {}
            }
        }
        
        // Server is not responding, update status
        let mut status = app_state.status.clone();
        status.running = false;
        status.last_error = Some("Server not responding".to_string());
        return status;
    }
    
    app_state.status.clone()
}

#[tauri::command]
async fn check_ollama_status() -> Result<bool, String> {
    // Check if Ollama is running
    match reqwest::get("http://localhost:11434/api/tags").await {
        Ok(response) => Ok(response.status().is_success()),
        Err(_) => Ok(false),
    }
}

#[tauri::command]
async fn get_context_entries() -> Result<Vec<serde_json::Value>, String> {
    // Make request to ContextVault API
    match reqwest::get("http://localhost:8000/api/context").await {
        Ok(response) => {
            if response.status().is_success() {
                match response.json::<serde_json::Value>().await {
                    Ok(data) => {
                        if let Some(entries) = data.get("entries").and_then(|e| e.as_array()) {
                            Ok(entries.clone())
                        } else {
                            Ok(vec![])
                        }
                    }
                    Err(e) => Err(format!("Failed to parse response: {}", e))
                }
            } else {
                Err(format!("Server returned status: {}", response.status()))
            }
        }
        Err(e) => Err(format!("Failed to connect to ContextVault server: {}", e))
    }
}

#[tauri::command]
async fn add_context_entry(content: String, context_type: String, tags: Vec<String>) -> Result<String, String> {
    let client = reqwest::Client::new();
    let payload = serde_json::json!({
        "content": content,
        "context_type": context_type,
        "tags": tags
    });
    
    match client.post("http://localhost:8000/api/context")
        .json(&payload)
        .send()
        .await
    {
        Ok(response) => {
            if response.status().is_success() {
                match response.text().await {
                    Ok(body) => Ok(body),
                    Err(e) => Err(format!("Failed to read response: {}", e))
                }
            } else {
                Err(format!("Server returned status: {}", response.status()))
            }
        }
        Err(e) => Err(format!("Failed to add context entry: {}", e))
    }
}

#[tauri::command]
async fn delete_context_entry(entry_id: String) -> Result<String, String> {
    let client = reqwest::Client::new();
    
    match client.delete(&format!("http://localhost:8000/api/context/{}", entry_id))
        .send()
        .await
    {
        Ok(response) => {
            if response.status().is_success() {
                match response.text().await {
                    Ok(body) => Ok(body),
                    Err(e) => Err(format!("Failed to read response: {}", e))
                }
            } else {
                Err(format!("Server returned status: {}", response.status()))
            }
        }
        Err(e) => Err(format!("Failed to delete context entry: {}", e))
    }
}

#[tauri::command]
async fn get_system_info() -> Result<serde_json::Value, String> {
    let mut info = serde_json::json!({
        "os": std::env::consts::OS,
        "arch": std::env::consts::ARCH,
        "app_version": env!("CARGO_PKG_VERSION")
    });
    
    // Add Ollama detection
    match check_ollama_status().await {
        Ok(ollama_running) => {
            info["ollama_running"] = serde_json::Value::Bool(ollama_running);
        }
        Err(_) => {
            info["ollama_running"] = serde_json::Value::Bool(false);
        }
    }
    
    Ok(info)
}

fn start_contextvault_server_internal(app_handle: &tauri::AppHandle) -> Result<ContextVaultStatus> {
    let contextvault_path = get_contextvault_server_path()?;
    
    // Check if ContextVault server binary exists
    if !Path::new(&contextvault_path).exists() {
        return Err(anyhow::anyhow!("ContextVault server not found at: {}", contextvault_path));
    }
    
    // Start the server process
    let mut process = Command::new(&contextvault_path)
        .arg("server")
        .arg("--host")
        .arg("127.0.0.1")
        .arg("--port")
        .arg("8000")
        .stdout(Stdio::piped())
        .stderr(Stdio::piped())
        .spawn()?;
    
    // Wait a bit for server to start
    thread::sleep(Duration::from_secs(3));
    
    // Check if process is still running
    match process.try_wait() {
        Ok(Some(status)) => {
            return Err(anyhow::anyhow!("Server process exited with status: {}", status));
        }
        Ok(None) => {
            // Process is still running
        }
        Err(e) => {
            return Err(anyhow::anyhow!("Error checking process status: {}", e));
        }
    }
    
    // Update app state
    let mut app_state = app_handle.state::<AppState>();
    app_state.server_process = Some(process);
    app_state.status.running = true;
    app_state.status.port = Some(8000);
    app_state.status.last_error = None;
    
    Ok(app_state.status.clone())
}

fn get_contextvault_server_path() -> Result<String> {
    let exe_path = std::env::current_exe()?;
    let app_dir = exe_path.parent()
        .ok_or_else(|| anyhow::anyhow!("Could not get app directory"))?;
    
    let server_path = app_dir.join("contextvault-server").join("contextvault-server");
    
    if cfg!(windows) {
        Ok(format!("{}.exe", server_path.display()))
    } else {
        Ok(server_path.to_string_lossy().to_string())
    }
}
