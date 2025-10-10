//! Source code finder based on symbol search.
//! 
//! This module provides functionality to search for symbols (functions, structs, etc.)
//! in a Rust project and return their source code.

use std::env;

use anyhow::{Context, Result};
use ide::{Analysis, AnalysisHost};
use ide_db::{
    base_db::FileId,
    symbol_index::Query,
};
use load_cargo::{load_workspace, LoadCargoConfig, ProcMacroServerChoice};
use project_model::{CargoConfig, ProjectManifest, ProjectWorkspace, RustLibSource};
use vfs::{AbsPathBuf, Vfs};

use crate::cli::flags;

impl flags::SourceFinder {
    pub fn run(self) -> Result<()> {
        let path = AbsPathBuf::assert_utf8(env::current_dir()?.join(&self.project_path));
        
        // Load the project
        let manifest = ProjectManifest::discover_single(&path)
            .context("Failed to discover project manifest")?;
        
        let mut cargo_config = CargoConfig::default();
        cargo_config.sysroot = Some(RustLibSource::Discover);
        
        let load_cargo_config = LoadCargoConfig {
            load_out_dirs_from_check: true,
            with_proc_macro_server: ProcMacroServerChoice::Sysroot,
            prefill_caches: false,
        };
        let ws = ProjectWorkspace::load(manifest, &cargo_config, &|_: String| {})?;
        let (db, vfs, _proc_macro) = load_workspace(
            ws,
            &cargo_config.extra_env,
            &load_cargo_config,
        )?;
        
        let host = AnalysisHost::with_database(db);
        let analysis = host.analysis();
        
        // Get project root path
        let project_root = AbsPathBuf::assert_utf8(env::current_dir()?.join(&self.project_path));
        
        // Search for symbols
        let results = self.search_symbols(&analysis, &vfs, &project_root)?;
        
        if results.is_empty() {
            eprintln!("No symbols found matching '{}'", self.symbol_name);
            return Ok(());
        }
        
        // Print simplified output: only File Path and Source Code
        for (_, file_path, source_code) in &results {
            println!("File Path: {}", file_path);
            println!("Source Code:");
            println!("{}", source_code);
            println!();
        }
        
        Ok(())
    }
    
    fn search_symbols(&self, analysis: &Analysis, vfs: &Vfs, project_root: &AbsPathBuf) -> Result<Vec<(String, String, String)>> {
        let mut query = Query::new(self.symbol_name.clone());
        query.fuzzy(); // Enable fuzzy matching
        
        let search_results = analysis.symbol_search(query, 50)
            .map_err(|_| anyhow::anyhow!("Symbol search was cancelled"))?;
        
        let mut results = Vec::new();
        
        for nav_target in search_results {
            // Get the source code for this symbol
            if let Ok(source_text) = analysis.file_text(nav_target.file_id) {
                let source_code = self.extract_symbol_source(&source_text, &nav_target);
                let file_path = self.get_file_path(vfs, nav_target.file_id, project_root);
                results.push((
                    nav_target.name.to_string(),
                    file_path,
                    source_code,
                ));
            }
        }
        
        Ok(results)
    }
    
    fn extract_symbol_source(&self, source_text: &str, nav_target: &ide::NavigationTarget) -> String {
        let full_range = nav_target.full_range;
        let start_offset: usize = full_range.start().into();
        let end_offset: usize = full_range.end().into();
        
        // Ensure we don't go out of bounds
        let start_offset = start_offset.min(source_text.len());
        let end_offset = end_offset.min(source_text.len());
        
        if start_offset >= end_offset {
            return String::new();
        }
        
        // Extract the exact range of the symbol
        let symbol_text = &source_text[start_offset..end_offset];
        
        // Try to include complete lines for better readability
        let lines: Vec<&str> = source_text.lines().collect();
        
        // Find which lines contain our symbol
        let mut current_offset = 0;
        let mut start_line = 0;
        let mut end_line = 0;
        
        for (line_idx, line) in lines.iter().enumerate() {
            let line_end = current_offset + line.len();
            
            if current_offset <= start_offset && start_offset <= line_end {
                start_line = line_idx;
            }
            
            if current_offset <= end_offset && end_offset <= line_end {
                end_line = line_idx + 1; // Include the line containing the end
                break;
            }
            
            current_offset = line_end + 1; // +1 for the newline character
        }
        
        // Extract complete lines for better formatting
        if start_line < lines.len() && end_line <= lines.len() {
            let symbol_lines = &lines[start_line..end_line];
            symbol_lines.join("\n")
        } else {
            // Fallback to exact byte range if line calculation fails
            symbol_text.to_string()
        }
    }
    
    fn get_file_path(&self, vfs: &Vfs, file_id: FileId, project_root: &AbsPathBuf) -> String {
        let vfs_path = vfs.file_path(file_id);
        
        // Convert to absolute path and then to relative path from project root
        if let Some(abs_path) = vfs_path.as_path() {
            if let Some(relative_path) = abs_path.strip_prefix(project_root) {
                return relative_path.as_str().to_string();
            }
            return abs_path.as_str().to_string();
        }
        
        // Fallback to VFS path string representation
        vfs_path.to_string()
    }
}