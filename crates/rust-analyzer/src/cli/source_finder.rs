//! Source code finder based on symbol search.
//! 
//! This module provides functionality to search for symbols (functions, structs, etc.)
//! in a Rust project and return their source code with call graph information.

use std::env;

use anyhow::{Context, Result};
use hir::{Crate, ModuleDef, Semantics};
use ide::{Analysis, AnalysisHost, CallHierarchyConfig, CallItem, FilePosition, LineCol};
use ide_db::{
    base_db::FileId,
    symbol_index::Query,
    EditionedFileId, LineIndexDatabase,
};
use load_cargo::{load_workspace, LoadCargoConfig, ProcMacroServerChoice};
use project_model::{CargoConfig, ProjectManifest, ProjectWorkspace, RustLibSource};

use syntax::AstNode;
use vfs::{AbsPathBuf, Vfs};

use crate::cli::flags;

#[derive(Debug, Clone)]
struct FunctionInfo {
    name: String,
    file_path: String,
    line: u32,
    column: u32,
}

#[derive(Debug, Clone)]
struct CallRelation {
    callee: FunctionInfo,
}

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
        
        let host = AnalysisHost::with_database(db.clone());
        let analysis = host.analysis();
        
        // Get project root path
        let project_root = AbsPathBuf::assert_utf8(env::current_dir()?.join(&self.project_path));
        
        // Search for symbols
        let results = self.search_symbols(&analysis, &vfs, &project_root)?;
        
        if results.is_empty() {
            eprintln!("No symbols found matching '{}'", self.symbol_name);
            return Ok(());
        }
        
        // For each found symbol, get call graph information if it's a function
        for (symbol_name, file_path, source_code, start_line, end_line) in &results {
            println!("File Path: {}", file_path);
            println!("Start Line: {}", start_line);
            println!("End Line: {}", end_line);
            println!("Source Code:");
            println!("{}", source_code);
            
            // Try to get call graph information for functions
            if let Some(calls) = self.get_function_calls(&analysis, symbol_name, file_path, &vfs, &db, &project_root)? {
                if !calls.is_empty() {
                    println!("Function Calls:");
                    for call in calls {
                        println!("  -> {}:{}:{}", 
                            self.convert_to_relative_path(&call.callee.file_path, &project_root),
                            call.callee.line,
                            call.callee.name
                        );
                    }
                } else {
                    println!("Function Calls: None");
                }
            }
            
            println!();
        }
        
        Ok(())
    }
    
    fn search_symbols(&self, analysis: &Analysis, vfs: &Vfs, project_root: &AbsPathBuf) -> Result<Vec<(String, String, String, u32, u32)>> {
        let mut query = Query::new(self.symbol_name.clone());
        query.fuzzy(); // Enable fuzzy matching
        
        let search_results = analysis.symbol_search(query, 50)
            .map_err(|_| anyhow::anyhow!("Symbol search was cancelled"))?;
        
        let mut results = Vec::new();
        
        for nav_target in search_results {
            // Get the source code for this symbol
            if let Ok(source_text) = analysis.file_text(nav_target.file_id) {
                let (source_code, start_line, end_line) = self.extract_symbol_source(&source_text, &nav_target);
                let file_path = self.get_file_path(vfs, nav_target.file_id, project_root);
                results.push((
                    nav_target.name.to_string(),
                    file_path,
                    source_code,
                    start_line,
                    end_line,
                ));
            }
        }
        
        Ok(results)
    }
    
    fn extract_symbol_source(&self, source_text: &str, nav_target: &ide::NavigationTarget) -> (String, u32, u32) {
        let full_range = nav_target.full_range;
        let start_offset: usize = full_range.start().into();
        let end_offset: usize = full_range.end().into();
        
        // Ensure we don't go out of bounds
        let start_offset = start_offset.min(source_text.len());
        let end_offset = end_offset.min(source_text.len());
        
        if start_offset >= end_offset {
            return (String::new(), 0, 0);
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
            let source_code = symbol_lines.join("\n");
            (source_code, (start_line + 1) as u32, end_line as u32)
        } else {
            // Fallback to exact byte range if line calculation fails
            (symbol_text.to_string(), 1, 1)
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
    
    /// Get function calls for a specific function
    fn get_function_calls(
        &self,
        analysis: &Analysis,
        symbol_name: &str,
        file_path: &str,
        vfs: &Vfs,
        db: &ide::RootDatabase,
        project_root: &AbsPathBuf,
    ) -> Result<Option<Vec<CallRelation>>> {
        // Find the file_id for this function
        if let Some(file_id) = self.find_file_id_by_path(vfs, file_path) {
            // Try to find the function in the file
            if let Some(func_info) = self.find_function_in_file(db, vfs, file_id, symbol_name, project_root)? {
                // Get call relationships for this function
                let calls = self.analyze_function_calls(analysis, &func_info, vfs, db, project_root)?;
                return Ok(Some(calls));
            }
        }
        Ok(None)
    }
    
    /// Find file_id by path
    fn find_file_id_by_path(&self, vfs: &Vfs, file_path: &str) -> Option<vfs::FileId> {
        // Convert relative path to absolute path for comparison
        let abs_file_path = if file_path.starts_with('/') {
            file_path.to_string()
        } else {
            // If it's a relative path, make it absolute
            let current_dir = env::current_dir().ok()?;
            let project_path = current_dir.join(&self.project_path);
            project_path.join(file_path).to_string_lossy().to_string()
        };
        
        // Search through all files in VFS to find matching path
        for (file_id, path) in vfs.iter() {
            let path_str = path.to_string();
            if path_str == file_path || path_str == abs_file_path {
                return Some(file_id);
            }
        }
        None
    }
    
    /// Find a specific function in a file
    fn find_function_in_file(
        &self,
        db: &ide::RootDatabase,
        vfs: &Vfs,
        file_id: vfs::FileId,
        function_name: &str,
        project_root: &AbsPathBuf,
    ) -> Result<Option<FunctionInfo>> {
        // Get all crates and search for the function
        let crates = Crate::all(db);
        
        for krate in crates {
            let root_module = krate.root_module();
            if let Some(func_info) = self.search_function_in_module(db, vfs, root_module, function_name, file_id, project_root)? {
                return Ok(Some(func_info));
            }
        }
        
        Ok(None)
    }
    
    /// Search for a function in a module recursively
    fn search_function_in_module(
        &self,
        db: &ide::RootDatabase,
        vfs: &Vfs,
        module: hir::Module,
        function_name: &str,
        target_file_id: vfs::FileId,
        project_root: &AbsPathBuf,
    ) -> Result<Option<FunctionInfo>> {
        // Check functions in this module
        for decl in module.declarations(db) {
            if let ModuleDef::Function(func) = decl {
                if let Some(func_info) = self.extract_function_info(db, func, vfs)? {
                    // Check if this function matches our criteria
                    if func_info.name == function_name {
                        // Check if it's in the target file
                        if let Some(file_id) = self.find_file_id_by_path(vfs, &func_info.file_path) {
                            if file_id == target_file_id {
                                return Ok(Some(func_info));
                            }
                        }
                    }
                }
            }
        }
        
        // Check associated functions in impls
        for impl_def in module.impl_defs(db) {
            for item in impl_def.items(db) {
                if let hir::AssocItem::Function(func) = item {
                    if let Some(func_info) = self.extract_function_info(db, func, vfs)? {
                        if func_info.name == function_name {
                            if let Some(file_id) = self.find_file_id_by_path(vfs, &func_info.file_path) {
                                if file_id == target_file_id {
                                    return Ok(Some(func_info));
                                }
                            }
                        }
                    }
                }
            }
        }
        
        // Recursively search child modules
        for child in module.children(db) {
            if let Some(func_info) = self.search_function_in_module(db, vfs, child, function_name, target_file_id, project_root)? {
                return Ok(Some(func_info));
            }
        }
        
        Ok(None)
    }
    
    /// Extract function information from hir::Function
    fn extract_function_info(
        &self,
        db: &ide::RootDatabase,
        func: hir::Function,
        vfs: &Vfs,
    ) -> Result<Option<FunctionInfo>> {
        let sema = Semantics::new(db);
        
        if let Some(source) = sema.source(func) {
            let syntax_node = source.value.syntax();
            let original_range = sema.original_range(syntax_node);
            let original_file_id = original_range.file_id;
            let text_range = original_range.range;
            
            let file_id = original_file_id.file_id(db);
            let path = vfs.file_path(file_id);
            let file_path = path.to_string();
            
            let line_index = db.line_index(original_file_id.file_id(db));
            let line_col = line_index.line_col(text_range.start());
            
            let function_info = FunctionInfo {
                name: func.name(db).display(db, syntax::Edition::CURRENT).to_string(),
                file_path,
                line: line_col.line + 1,
                column: line_col.col + 1,
            };
            
            return Ok(Some(function_info));
        }
        
        Ok(None)
    }
    
    /// Analyze function calls for a specific function
    fn analyze_function_calls(
        &self,
        analysis: &Analysis,
        func_info: &FunctionInfo,
        vfs: &Vfs,
        db: &ide::RootDatabase,
        project_root: &AbsPathBuf,
    ) -> Result<Vec<CallRelation>> {
        let mut call_relations = Vec::new();
        
        if let Some(file_id) = self.find_file_id_by_path(vfs, &func_info.file_path) {
            let editioned_file_id = EditionedFileId::current_edition(db, file_id);
            let line_index = db.line_index(editioned_file_id.file_id(db));
            
            let line_col = LineCol {
                line: func_info.line.saturating_sub(1),
                col: func_info.column.saturating_sub(1),
            };
            
            if line_col.line < line_index.len().into() {
                if let Some(offset) = line_index.offset(line_col) {
                    let position = FilePosition { file_id, offset };
                    
                    let config = CallHierarchyConfig {
                        exclude_tests: false,
                    };
                    
                    if let Ok(Some(outgoing_calls)) = analysis.outgoing_calls(config, position) {
                        for call_item in outgoing_calls {
                            if let Some(call_relation) = self.create_call_relation_from_item(
                                func_info,
                                &call_item,
                                vfs,
                                db,
                                project_root,
                            )? {
                                call_relations.push(call_relation);
                            }
                        }
                    }
                }
            }
        }
        
        Ok(call_relations)
    }
    
    /// Create call relation from call item
    fn create_call_relation_from_item(
        &self,
        caller_func: &FunctionInfo,
        call_item: &CallItem,
        vfs: &Vfs,
        db: &ide::RootDatabase,
        project_root: &AbsPathBuf,
    ) -> Result<Option<CallRelation>> {
        let target = &call_item.target;
        
        let file_id = target.file_id;
        let path = vfs.file_path(file_id);
        let file_path = path.to_string();
        
        let editioned_file_id = EditionedFileId::current_edition(db, file_id);
        let line_index = db.line_index(editioned_file_id.file_id(db));
        let target_range = target.focus_or_full_range();
        
        if target_range.start() > line_index.len().into() {
            return Ok(None);
        }
        
        let line_col = line_index.line_col(target_range.start());
        
        let callee_info = FunctionInfo {
            name: target.name.to_string(),
            file_path: file_path.clone(),
            line: line_col.line + 1,
            column: line_col.col + 1,
        };
        
        // Filter out external library calls
        if self.is_external_path(&caller_func.file_path, project_root) {
            return Ok(None);
        }
        

        
        let call_relation = CallRelation {
            callee: callee_info,
        };
        
        Ok(Some(call_relation))
    }
    
    /// Check if a file path is external to the project
    fn is_external_path(&self, file_path: &str, project_root: &AbsPathBuf) -> bool {
        let project_root_str = project_root.to_string();
        
        if !file_path.starts_with(&project_root_str) {
            return true;
        }
        
        if file_path.contains(".cargo/registry/") ||
           file_path.contains(".cargo/git/") {
            return true;
        }
        
        if file_path.contains(".cargo/registry/") && 
           (file_path.contains("anchor-") || file_path.contains("/anchor/")) {
            return true;
        }
        
        if file_path.contains("/target/") ||
           file_path.contains("/build/") ||
           file_path.contains("/deps/") {
            return true;
        }
        
        false
    }
    
    /// Convert to relative path
    fn convert_to_relative_path(&self, file_path: &str, project_root: &AbsPathBuf) -> String {
        let abs_path = std::path::Path::new(file_path);
        let project_root_path = std::path::Path::new(project_root.as_str());
        
        if let Ok(relative_path) = abs_path.strip_prefix(project_root_path) {
            relative_path.to_string_lossy().to_string()
        } else {
            file_path.to_string()
        }
    }
}