use std::{env, fs, io::Write, path::PathBuf};
use anyhow::Result;
use hir::{Crate, ModuleDef, Semantics};
use ide::{Analysis, AnalysisHost, CallHierarchyConfig, CallItem, FilePosition, LineCol};
use ide_db::{EditionedFileId, LineIndexDatabase};
use load_cargo::{LoadCargoConfig, ProcMacroServerChoice, load_workspace};
use project_model::{CargoConfig, ProjectManifest, ProjectWorkspace, RustLibSource};
use rustc_hash::FxHashSet;
use vfs::{AbsPathBuf, Vfs};
use syntax::AstNode;
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
    caller: FunctionInfo,
    callee: FunctionInfo,
    call_site_line: u32,
    call_site_column: u32,
}

impl flags::CallHierarchy {
    pub fn run(self) -> Result<()> {
        eprintln!("Loading workspace...");
        
        let path = AbsPathBuf::assert_utf8(env::current_dir()?.join(&self.path));
        let manifest = ProjectManifest::discover_single(&path)?;
        let mut cargo_config = CargoConfig::default();
        cargo_config.sysroot = Some(RustLibSource::Discover);
        
        let load_cargo_config = LoadCargoConfig {
            load_out_dirs_from_check: !self.disable_build_scripts,
            with_proc_macro_server: if self.disable_proc_macros {
                ProcMacroServerChoice::None
            } else {
                match self.proc_macro_srv {
                    Some(ref path) => {
                        let path = vfs::AbsPathBuf::assert_utf8(path.to_owned());
                        ProcMacroServerChoice::Explicit(path)
                    }
                    None => ProcMacroServerChoice::Sysroot,
                }
            },
            prefill_caches: false,
        };
        
        let ws = ProjectWorkspace::load(manifest, &cargo_config, &|_| {})?;
        let (db, vfs, _proc_macro) = load_workspace(
            ws,
            &cargo_config.extra_env,
            &load_cargo_config,
        )?;
        
        let host = AnalysisHost::with_database(db.clone());
        let analysis = host.analysis();
        
        eprintln!("Extracting functions...");
        let functions = extract_all_functions(&db, &vfs)?;
        eprintln!("Found {} functions", functions.len());
        
        eprintln!("Analyzing call relationships...");
        let call_relations = analyze_call_relationships(&analysis, &functions, &vfs, &db)?;
        eprintln!("Found {} call relationships", call_relations.len());
        
        eprintln!("Writing output...");
        write_output(&call_relations, &self.output)?;
        
        eprintln!("Call hierarchy analysis completed!");
        Ok(())
    }
}

fn extract_all_functions(db: &ide::RootDatabase, vfs: &Vfs) -> Result<Vec<FunctionInfo>> {
    let mut functions = Vec::new();
    let mut visited_modules = FxHashSet::default();
    let mut visit_queue = Vec::new();
    
    // Get all crates in the workspace
    let crates = Crate::all(db);
    
    // Initialize the queue with root modules from all crates
    for krate in crates {
        let root_module = krate.root_module();
        visit_queue.push(root_module);
    }
    
    // Process all modules
    while let Some(module) = visit_queue.pop() {
        if visited_modules.insert(module) {
            visit_queue.extend(module.children(db));
            
            // Extract functions from this module
            for decl in module.declarations(db) {
                if let ModuleDef::Function(func) = decl {
                    if let Some(func_info) = extract_function_info(db, func, vfs)? {
                        functions.push(func_info);
                    }
                }
            }
            
            // Also check for associated functions in impls
            for impl_def in module.impl_defs(db) {
                for item in impl_def.items(db) {
                    if let hir::AssocItem::Function(func) = item {
                        if let Some(func_info) = extract_function_info(db, func, vfs)? {
                            functions.push(func_info);
                        }
                    }
                }
            }
        }
    }
    
    Ok(functions)
}

fn extract_function_info(
    db: &ide::RootDatabase,
    func: hir::Function,
    vfs: &Vfs,
) -> Result<Option<FunctionInfo>> {
    // Create Semantics instance to handle proper text range mapping
    let sema = Semantics::new(db);
    
    if let Some(source) = sema.source(func) {
        let syntax_node = source.value.syntax();
        
        // Use original_range to map syntax node to its original file range
        // This ensures text_range and line_index correspond to the same file
        let original_range = sema.original_range(syntax_node);
        let original_file_id = original_range.file_id;
        let text_range = original_range.range;
        
        let file_id = original_file_id.file_id(db);
        let path = vfs.file_path(file_id);
        let file_path = path.to_string();
        
        // Now line_index and text_range are guaranteed to be from the same file
        let line_index = db.line_index(original_file_id.file_id(db));
        let line_col = line_index.line_col(text_range.start());
        
        let function_info = FunctionInfo {
            name: func.name(db).display(db, syntax::Edition::CURRENT).to_string(),
            file_path,
            line: line_col.line + 1, // Convert to 1-based
            column: line_col.col + 1, // Convert to 1-based
        };
        
        return Ok(Some(function_info));
    }
    
    Ok(None)
}

fn analyze_call_relationships(
    analysis: &Analysis,
    functions: &[FunctionInfo],
    vfs: &Vfs,
    db: &ide::RootDatabase,
) -> Result<Vec<CallRelation>> {
    let mut call_relations = Vec::new();
    
    for func in functions {
        // Find the file_id for this function
        if let Some(file_id) = find_file_id_by_path(vfs, &func.file_path) {
            // Use EditionedFileId for consistent file handling
            let editioned_file_id = EditionedFileId::current_edition(db, file_id);
            let line_index = db.line_index(editioned_file_id.file_id(db));
            
            // Ensure line and column are within valid range before creating offset
            let line_col = LineCol {
                line: func.line.saturating_sub(1), // Convert to 0-based with bounds check
                col: func.column.saturating_sub(1), // Convert to 0-based with bounds check
            };
            
            // Validate that the line_col is within the file bounds
             if line_col.line < line_index.len().into() {
                 let offset = line_index.offset(line_col);
                 
                 if let Some(offset) = offset {
                     let position = FilePosition { file_id: file_id, offset };
                     
                     let config = CallHierarchyConfig {
                         exclude_tests: false,
                     };
                     
                     // Get outgoing calls (functions this function calls)
                     if let Ok(Some(outgoing_calls)) = analysis.outgoing_calls(config, position) {
                         for call_item in outgoing_calls {
                             if let Some(call_relation) = create_call_relation_from_item(
                                 func,
                                 &call_item,
                                 vfs,
                                 db,
                             )? {
                                 call_relations.push(call_relation);
                             }
                         }
                     }
                 }
             }
         }
     }
    
    Ok(call_relations)
}

fn find_file_id_by_path(vfs: &Vfs, file_path: &str) -> Option<vfs::FileId> {
    // Search through all files in VFS to find matching path
    for (file_id, path) in vfs.iter() {
        let path_str = path.to_string();
        if path_str == file_path {
            return Some(file_id);
        }
    }
    None
}

fn create_call_relation_from_item(
    caller_func: &FunctionInfo,
    call_item: &CallItem,
    vfs: &Vfs,
    db: &ide::RootDatabase,
) -> Result<Option<CallRelation>> {
    let target = &call_item.target;
    
    // Get callee information
    let file_id = target.file_id;
    let path = vfs.file_path(file_id);
    let file_path = path.to_string();
    
    // Convert vfs::FileId to EditionedFileId for line_index
    let editioned_file_id = EditionedFileId::current_edition(db, file_id);
    let line_index = db.line_index(editioned_file_id.file_id(db));
    let target_range = target.focus_or_full_range();
    
    // Validate target_range is within file bounds
    if target_range.start() > line_index.len().into() {
        return Ok(None); // Skip this item if range is invalid
    }
    
    let line_col = line_index.line_col(target_range.start());
    
    let callee_info = FunctionInfo {
        name: target.name.to_string(),
        file_path,
        line: line_col.line + 1,
        column: line_col.col + 1,
    };
    
    // Get call site information
    let (_call_line_col, call_site_line, call_site_column) = if let Some(range_info) = call_item.ranges.first() {
        let call_file_id = range_info.file_id;
        let call_range = range_info.range;
        
        // Use the correct line_index for the call site file
        let call_editioned_file_id = EditionedFileId::current_edition(db, call_file_id);
        let call_line_index = db.line_index(call_editioned_file_id.file_id(db));
        
        // Validate call_range is within file bounds
        if call_range.start() > call_line_index.len().into() {
            return Ok(None); // Skip this item if range is invalid
        }
        
        let call_line_col = call_line_index.line_col(call_range.start());
        
        (call_line_col, call_line_col.line + 1, call_line_col.col + 1)
    } else {
        // Fallback to target range if no call ranges available
        let call_line_col = line_index.line_col(target_range.start());
        (call_line_col, call_line_col.line + 1, call_line_col.col + 1)
    };
    
    let call_relation = CallRelation {
        caller: caller_func.clone(),
        callee: callee_info,
        call_site_line,
        call_site_column,
    };
    
    Ok(Some(call_relation))
}

fn write_output(call_relations: &[CallRelation], output_path: &Option<PathBuf>) -> Result<()> {
    let output = match output_path {
        Some(path) => {
            let file = fs::File::create(path)?;
            Box::new(file) as Box<dyn Write>
        }
        None => Box::new(std::io::stdout()) as Box<dyn Write>,
    };
    
    let mut writer = output;
    
    // Write header
    writeln!(writer, "# Function Call Hierarchy Analysis")?;
    writeln!(writer, "# Format: caller_function -> callee_function (call_site)")?;
    writeln!(writer)?;
    
    // Write call relations
    for relation in call_relations {
        writeln!(
            writer,
            "{}:{}:{} -> {}:{}:{} (call at {}:{})",
            relation.caller.file_path,
            relation.caller.line,
            relation.caller.name,
            relation.callee.file_path,
            relation.callee.line,
            relation.callee.name,
            relation.call_site_line,
            relation.call_site_column
        )?;
    }
    
    Ok(())
}