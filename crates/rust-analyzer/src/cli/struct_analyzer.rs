use std::{env, fs, path::PathBuf, collections::HashMap, panic};
use anyhow::Result;
use hir::{Crate, ModuleDef, Semantics, Struct, HasAttrs, HirDisplay};
use ide::AnalysisHost;
use ide_db::LineIndexDatabase;
use load_cargo::{LoadCargoConfig, ProcMacroServerChoice, load_workspace};
use project_model::{CargoConfig, ProjectManifest, ProjectWorkspace, RustLibSource};
use rustc_hash::FxHashSet;
use vfs::{AbsPathBuf, Vfs};
use syntax::AstNode;
use serde::{Serialize, Deserialize};
use chrono::{DateTime, Utc};
use hir_ty::display::DisplayTarget;

use crate::cli::flags;

/// Information about a Solana Anchor account structure
#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct AccountStructInfo {
    pub name: String,
    pub module_path: String,
    pub file_path: String,
    pub line_number: u32,
    pub column_number: u32,
    pub instruction_params: Vec<InstructionParam>,
    pub fields: Vec<AccountField>,
    pub derives: Vec<String>,
    pub visibility: String,
    pub documentation: Option<String>,
    pub is_anchor_accounts: bool,
}

/// Information about instruction parameters
#[derive(Debug, Clone, Serialize, Deserialize)]
pub(super) struct InstructionParam {
    pub name: String,
    pub param_type: String,
}

/// Information about an account field
#[derive(Debug, Clone, Serialize, Deserialize)]
pub(super) struct AccountField {
    pub name: String,
    pub field_type: String,
    pub constraints: Vec<ConstraintInfo>,
    pub is_pda: bool,
    pub pda_info: Option<PdaInfo>,
    pub documentation: Option<String>,
    pub span_info: SpanInfo,
}

/// Information about field constraints
#[derive(Debug, Clone, Serialize, Deserialize)]
pub(super) struct ConstraintInfo {
    pub constraint_type: ConstraintType,
    pub parameters: HashMap<String, String>,
    pub error_code: Option<String>,
}

/// Types of constraints in Anchor
#[derive(Debug, Clone, Serialize, Deserialize)]
pub(super) enum ConstraintType {
    Init {
        payer: String,
        space: Option<String>,
        owner: Option<String>,
    },
    Mut,
    Signer,
    HasOne {
        field: String,
        error: Option<String>,
    },
    AssociatedToken {
        mint: String,
        authority: String,
        token_program: Option<String>,
    },
    Seeds {
        seeds: Vec<SeedComponent>,
        bump: Option<BumpInfo>,
    },
    Constraint {
        expression: String,
        error: Option<String>,
    },
    Address(String),
    Owner(String),
    Close(String),
    Realloc {
        payer: String,
        zero: bool,
    },
}

/// Information about PDA (Program Derived Address)
#[derive(Debug, Clone, Serialize, Deserialize)]
pub(super) struct PdaInfo {
    pub seeds: Vec<SeedComponent>,
    pub bump: BumpInfo,
    pub program_id: Option<String>,
    pub canonical_bump: Option<u8>,
    pub derived_address: Option<String>,
}

/// Components that make up PDA seeds
#[derive(Debug, Clone, Serialize, Deserialize)]
pub(super) enum SeedComponent {
    Literal(Vec<u8>),
    StringLiteral(String),
    Variable {
        name: String,
        transformation: Option<String>,
    },
    AccountKey(String),
    Expression(String),
}

/// Information about bump seeds
#[derive(Debug, Clone, Serialize, Deserialize)]
pub(super) enum BumpInfo {
    Auto,
    Explicit(String),
    Field(String),
}

/// Span information for source code location
#[derive(Debug, Clone, Serialize, Deserialize)]
pub(super) struct SpanInfo {
    pub start_line: u32,
    pub start_column: u32,
    pub end_line: u32,
    pub end_column: u32,
}

/// Project analysis information
#[derive(Debug, Clone, Serialize, Deserialize)]
pub(super) struct ProjectInfo {
    pub name: String,
    pub anchor_version: Option<String>,
    pub program_id: Option<String>,
    pub analysis_timestamp: DateTime<Utc>,
    pub rust_version: Option<String>,
}

/// Complete analysis result
#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct AnalysisResult {
    pub project_info: ProjectInfo,
    pub account_structs: Vec<AccountStructInfo>,
    pub pda_relationships: Vec<PdaRelationship>,
    pub constraint_summary: ConstraintSummary,
    pub statistics: AnalysisStatistics,
}

/// Relationship between PDAs
#[derive(Debug, Clone, Serialize, Deserialize)]
pub(super) struct PdaRelationship {
    pub parent: String,
    pub child: String,
    pub relationship_type: String,
    pub shared_seeds: Vec<String>,
}

/// Summary of constraints found
#[derive(Debug, Clone, Serialize, Deserialize)]
pub(super) struct ConstraintSummary {
    pub total_constraints: usize,
    pub constraint_types: HashMap<String, usize>,
    pub pda_count: usize,
    pub init_accounts: usize,
    pub mutable_accounts: usize,
}

/// Analysis statistics
#[derive(Debug, Clone, Serialize, Deserialize)]
pub(super) struct AnalysisStatistics {
    pub total_structs: usize,
    pub anchor_structs: usize,
    pub total_fields: usize,
    pub pda_fields: usize,
    pub files_analyzed: usize,
    pub analysis_duration_ms: u64,
}

/// Main struct analyzer
pub(super) struct StructAnalyzer {
    db: ide::RootDatabase,
    vfs: Vfs,
    project_root: AbsPathBuf,
}

impl StructAnalyzer {
    /// Analyze the project and return results
    pub(super) fn analyze(&self) -> Result<AnalysisResult> {
        let start_time = std::time::Instant::now();
        
        // Detect if this is an Anchor project
        let anchor_detector = AnchorDetector::new(&self.project_root);
        let is_anchor_project = anchor_detector.is_anchor_project()?;
        
        if !is_anchor_project {
            eprintln!("Warning: This doesn't appear to be an Anchor project");
        }

        // Extract all structs
        let structs = self.extract_all_structs()?;
        eprintln!("Found {} structs", structs.len());

        // Filter and analyze Anchor account structs
        let account_structs = self.analyze_account_structs(&structs)?;
        eprintln!("Found {} Anchor account structs", account_structs.len());

        // Analyze PDA relationships
        let pda_relationships = self.analyze_pda_relationships(&account_structs)?;

        // Generate constraint summary
        let constraint_summary = self.generate_constraint_summary(&account_structs);

        // Generate statistics
        let statistics = AnalysisStatistics {
            total_structs: structs.len(),
            anchor_structs: account_structs.len(),
            total_fields: account_structs.iter().map(|s| s.fields.len()).sum(),
            pda_fields: account_structs.iter()
                .flat_map(|s| &s.fields)
                .filter(|f| f.is_pda)
                .count(),
            files_analyzed: self.count_analyzed_files(),
            analysis_duration_ms: start_time.elapsed().as_millis() as u64,
        };

        // Get project info
        let project_info = self.get_project_info(&anchor_detector)?;

        Ok(AnalysisResult {
            project_info,
            account_structs,
            pda_relationships,
            constraint_summary,
            statistics,
        })
    }

    /// Extract all structs from the project
    fn extract_all_structs(&self) -> Result<Vec<Struct>> {
        let mut structs = Vec::new();
        let mut visited_modules = FxHashSet::default();
        let mut visit_queue = Vec::new();

        // Get all crates in the workspace
        let crates = Crate::all(&self.db);

        // Initialize the queue with root modules from all crates
        for krate in crates {
            let root_module = krate.root_module();
            visit_queue.push(root_module);
        }

        // Process all modules
        while let Some(module) = visit_queue.pop() {
            if visited_modules.insert(module) {
                visit_queue.extend(module.children(&self.db));

                // Extract structs from this module
                for decl in module.declarations(&self.db) {
                    if let ModuleDef::Adt(hir::Adt::Struct(struct_def)) = decl {
                        // Filter out external library structs
                        if !self.is_external_struct(&struct_def)? {
                            structs.push(struct_def);
                        }
                    }
                }
            }
        }

        Ok(structs)
    }

    /// Check if a struct is from external libraries
    fn is_external_struct(&self, struct_def: &Struct) -> Result<bool> {
        let sema = Semantics::new(&self.db);
        
        if let Some(source) = sema.source(*struct_def) {
            let file_id = source.file_id.file_id();
            if let Some(editioned_file_id) = file_id {
                let vfs_file_id = editioned_file_id.file_id(&self.db);
                let path = self.vfs.file_path(vfs_file_id);
                let file_path = path.to_string();
                
                // Check if the file is outside the project root
                let project_root_str = self.project_root.to_string();
                if !file_path.starts_with(&project_root_str) {
                    return Ok(true);
                }
                
                // Check for external dependencies
                if file_path.contains(".cargo/registry/") ||
                   file_path.contains(".cargo/git/") ||
                   file_path.contains("/target/") {
                    return Ok(true);
                }
            }
        }
        
        Ok(false)
    }

    /// Analyze account structs and extract Anchor-specific information
    fn analyze_account_structs(&self, structs: &[Struct]) -> Result<Vec<AccountStructInfo>> {
        let mut account_structs = Vec::new();
        
        for struct_def in structs {
            if let Some(account_struct) = self.analyze_single_struct(struct_def)? {
                account_structs.push(account_struct);
            }
        }
        
        Ok(account_structs)
    }

    /// Analyze a single struct to determine if it's an Anchor account struct
    fn analyze_single_struct(&self, struct_def: &Struct) -> Result<Option<AccountStructInfo>> {
        // Use catch_unwind to handle panics during struct analysis
        let result = panic::catch_unwind(panic::AssertUnwindSafe(|| {
            self.analyze_single_struct_inner(struct_def)
        }));
        
        match result {
            Ok(analysis_result) => analysis_result,
            Err(panic_info) => {
                let struct_name = struct_def.name(&self.db).display(&self.db, syntax::Edition::CURRENT).to_string();
                eprintln!("Warning: Panic occurred while analyzing struct '{}': {:?}", struct_name, panic_info);
                eprintln!("Skipping this struct and continuing with analysis...");
                Ok(None)
            }
        }
    }

    /// Inner implementation of struct analysis (can panic)
    fn analyze_single_struct_inner(&self, struct_def: &Struct) -> Result<Option<AccountStructInfo>> {
        let sema = Semantics::new(&self.db);
        
        // Get struct attributes
        let attrs = struct_def.attrs(&self.db);
        
        // Check if this struct has #[derive(Accounts)]
        let is_anchor_accounts = self.has_accounts_derive(&attrs);
        
        if !is_anchor_accounts {
            return Ok(None);
        }

        // Extract basic struct information
        let name = struct_def.name(&self.db).display(&self.db, syntax::Edition::CURRENT).to_string();
        
        let (file_path, line_number, column_number, module_path) = if let Some(source) = sema.source(*struct_def) {
            let syntax_node = source.value.syntax();
            let original_range = sema.original_range(syntax_node);
            let file_id = original_range.file_id.file_id(&self.db);
            let path = self.vfs.file_path(file_id);
            let file_path = self.convert_to_relative_path(&path.to_string());
            
            let line_index = self.db.line_index(file_id);
            let line_col = line_index.line_col(original_range.range.start());
            
            // Get module path
            let module = struct_def.module(&self.db);
            let module_path = module.path_to_root(&self.db)
                .into_iter()
                .rev()
                .map(|m| m.name(&self.db).map(|n| n.display(&self.db, syntax::Edition::CURRENT).to_string()).unwrap_or_default())
                .filter(|s| !s.is_empty())
                .collect::<Vec<_>>()
                .join("::");
            
            (file_path, line_col.line + 1, line_col.col + 1, module_path)
        } else {
            return Ok(None);
        };

        // Extract instruction parameters
        let instruction_params = self.extract_instruction_params(&attrs)?;

        // Extract struct fields
        let fields = self.extract_struct_fields(struct_def)?;

        // Extract derives
        let derives = self.extract_derives(&attrs);

        // Extract documentation
        let documentation = self.extract_documentation(&attrs);

        Ok(Some(AccountStructInfo {
            name,
            module_path,
            file_path,
            line_number,
            column_number,
            instruction_params,
            fields,
            derives,
            visibility: "pub".to_string(), // Anchor structs are typically public
            documentation,
            is_anchor_accounts: true,
        }))
    }

    /// Check if attributes contain #[derive(Accounts)]
    fn has_accounts_derive(&self, attrs: &hir::Attrs) -> bool {
        // This is a simplified check - in a real implementation,
        // we would need to parse the derive attributes more carefully
        for attr in attrs.iter() {
            let path = attr.path();
            if path.segments().len() == 1 && path.segments()[0].display(&self.db, syntax::Edition::CURRENT).to_string() == "derive" {
                // Check if the derive contains "Accounts"
                if let Some(tt) = attr.token_tree_value() {
                    let token_text = format!("{:?}", tt);
                    if token_text.contains("Accounts") {
                        return true;
                    }
                }
            }
        }
        false
    }

    /// Extract instruction parameters from #[instruction(...)] attribute
    fn extract_instruction_params(&self, attrs: &hir::Attrs) -> Result<Vec<InstructionParam>> {
        let mut params = Vec::new();
        
        for attr in attrs.iter() {
            let path = attr.path();
            if path.segments().len() == 1 && path.segments()[0].display(&self.db, syntax::Edition::CURRENT).to_string() == "instruction" {
                if let Some(tt) = attr.token_tree_value() {
                    // Parse the token tree to extract parameters
                    // This is a simplified implementation
                    let token_text = format!("{:?}", tt);
                    // Extract parameter information from token text
                    // In a real implementation, we would parse this more carefully
                    if token_text.contains("offer_id") {
                        params.push(InstructionParam {
                            name: "offer_id".to_string(),
                            param_type: "u64".to_string(),
                        });
                    }
                }
            }
        }
        
        Ok(params)
    }

    /// Extract struct fields and their constraints
    fn extract_struct_fields(&self, struct_def: &Struct) -> Result<Vec<AccountField>> {
        let mut fields = Vec::new();
        let sema = Semantics::new(&self.db);
        
        for field in struct_def.fields(&self.db) {
            let field_name = field.name(&self.db).display(&self.db, syntax::Edition::CURRENT).to_string();
            let display_target = DisplayTarget::from_crate(&self.db, struct_def.module(&self.db).krate().into());
            let field_type = field.ty(&self.db).display(&self.db, display_target).to_string();
            
            // Get field attributes
            let field_attrs = field.attrs(&self.db);
            
            // Parse constraints from #[account(...)] attributes
            let constraints = self.parse_field_constraints(&field_attrs)?;
            
            // Determine if this is a PDA field
            let is_pda = constraints.iter().any(|c| matches!(c.constraint_type, ConstraintType::Seeds { .. }));
            
            // Extract PDA information if applicable
            let pda_info = if is_pda {
                self.extract_pda_info(&constraints)?
            } else {
                None
            };
            
            // Get field documentation
            let documentation = self.extract_field_documentation(&field_attrs);
            
            // Get span information
            let span_info = if let Some(source) = sema.source(field) {
                let syntax_node = source.value.syntax();
                let original_range = sema.original_range(syntax_node);
                let file_id = original_range.file_id.file_id(&self.db);
                let line_index = self.db.line_index(file_id);
                let start_line_col = line_index.line_col(original_range.range.start());
                let end_line_col = line_index.line_col(original_range.range.end());
                
                SpanInfo {
                    start_line: start_line_col.line + 1,
                    start_column: start_line_col.col + 1,
                    end_line: end_line_col.line + 1,
                    end_column: end_line_col.col + 1,
                }
            } else {
                SpanInfo {
                    start_line: 0,
                    start_column: 0,
                    end_line: 0,
                    end_column: 0,
                }
            };
            
            fields.push(AccountField {
                name: field_name,
                field_type,
                constraints,
                is_pda,
                pda_info,
                documentation,
                span_info,
            });
        }
        
        Ok(fields)
    }

    /// Parse field constraints from attributes
    fn parse_field_constraints(&self, attrs: &hir::Attrs) -> Result<Vec<ConstraintInfo>> {
        let constraint_parser = ConstraintParser::new();
        constraint_parser.parse_constraints(attrs, &self.db)
    }

    /// Extract PDA information from constraints
    fn extract_pda_info(&self, constraints: &[ConstraintInfo]) -> Result<Option<PdaInfo>> {
        let pda_analyzer = PdaAnalyzer::new();
        pda_analyzer.extract_pda_info(constraints)
    }

    /// Extract documentation from attributes
    fn extract_documentation(&self, attrs: &hir::Attrs) -> Option<String> {
        // Extract doc comments
        let mut doc_parts = Vec::new();
        
        for attr in attrs.iter() {
            let path = attr.path();
            if path.segments().len() == 1 && path.segments()[0].display(&self.db, syntax::Edition::CURRENT).to_string() == "doc" {
                if let Some(tt) = attr.token_tree_value() {
                    let token_text = format!("{:?}", tt);
                    // Extract the actual documentation text
                    // This is simplified - real implementation would parse more carefully
                    if let Some(start) = token_text.find('"') {
                        if let Some(end) = token_text.rfind('"') {
                            if start < end {
                                let doc_text = &token_text[start + 1..end];
                                doc_parts.push(doc_text.trim().to_string());
                            }
                        }
                    }
                }
            }
        }
        
        if doc_parts.is_empty() {
            None
        } else {
            Some(doc_parts.join("\n"))
        }
    }

    /// Extract field documentation
    fn extract_field_documentation(&self, attrs: &hir::Attrs) -> Option<String> {
        self.extract_documentation(attrs)
    }

    /// Extract derive attributes
    fn extract_derives(&self, attrs: &hir::Attrs) -> Vec<String> {
        let mut derives = Vec::new();
        
        for attr in attrs.iter() {
            let path = attr.path();
            if path.segments().len() == 1 && path.segments()[0].display(&self.db, syntax::Edition::CURRENT).to_string() == "derive" {
                if let Some(tt) = attr.token_tree_value() {
                    let token_text = format!("{:?}", tt);
                    // Extract derive names - simplified implementation
                    if token_text.contains("Accounts") {
                        derives.push("Accounts".to_string());
                    }
                    if token_text.contains("Clone") {
                        derives.push("Clone".to_string());
                    }
                    if token_text.contains("Debug") {
                        derives.push("Debug".to_string());
                    }
                }
            }
        }
        
        derives
    }

    /// Analyze PDA relationships between structs
    fn analyze_pda_relationships(&self, account_structs: &[AccountStructInfo]) -> Result<Vec<PdaRelationship>> {
        let pda_analyzer = PdaAnalyzer::new();
        pda_analyzer.analyze_relationships(account_structs)
    }

    /// Generate constraint summary
    fn generate_constraint_summary(&self, account_structs: &[AccountStructInfo]) -> ConstraintSummary {
        let mut constraint_types = HashMap::new();
        let mut total_constraints = 0;
        let mut pda_count = 0;
        let mut init_accounts = 0;
        let mut mutable_accounts = 0;

        for struct_info in account_structs {
            for field in &struct_info.fields {
                total_constraints += field.constraints.len();
                
                if field.is_pda {
                    pda_count += 1;
                }
                
                for constraint in &field.constraints {
                    let constraint_name = match &constraint.constraint_type {
                        ConstraintType::Init { .. } => {
                            init_accounts += 1;
                            "init"
                        },
                        ConstraintType::Mut => {
                            mutable_accounts += 1;
                            "mut"
                        },
                        ConstraintType::Signer => "signer",
                        ConstraintType::HasOne { .. } => "has_one",
                        ConstraintType::AssociatedToken { .. } => "associated_token",
                        ConstraintType::Seeds { .. } => "seeds",
                        ConstraintType::Constraint { .. } => "constraint",
                        ConstraintType::Address(_) => "address",
                        ConstraintType::Owner(_) => "owner",
                        ConstraintType::Close(_) => "close",
                        ConstraintType::Realloc { .. } => "realloc",
                    };
                    
                    *constraint_types.entry(constraint_name.to_string()).or_insert(0) += 1;
                }
            }
        }

        ConstraintSummary {
            total_constraints,
            constraint_types,
            pda_count,
            init_accounts,
            mutable_accounts,
        }
    }

    /// Count analyzed files
    fn count_analyzed_files(&self) -> usize {
        let mut file_count = 0;
        let project_root_str = self.project_root.to_string();
        
        for (_file_id, path) in self.vfs.iter() {
            let file_path = path.to_string();
            if file_path.starts_with(&project_root_str) && 
               file_path.ends_with(".rs") &&
               !file_path.contains("/target/") {
                file_count += 1;
            }
        }
        
        file_count
    }

    /// Get project information
    fn get_project_info(&self, anchor_detector: &AnchorDetector) -> Result<ProjectInfo> {
        let project_name = self.project_root
            .file_name()
            .map(|name| name.to_string())
            .unwrap_or_else(|| "unknown_project".to_string());
            
        let anchor_version = anchor_detector.get_anchor_version()?;
        let program_id = anchor_detector.get_program_id()?;
        
        Ok(ProjectInfo {
            name: project_name,
            anchor_version,
            program_id,
            analysis_timestamp: Utc::now(),
            rust_version: Some("1.88".to_string()),
        })
    }

    /// Convert absolute path to relative path
    fn convert_to_relative_path(&self, file_path: &str) -> String {
        let abs_path = std::path::Path::new(file_path);
        let project_root_path = std::path::Path::new(self.project_root.as_str());
        
        if let Ok(relative_path) = abs_path.strip_prefix(project_root_path) {
            relative_path.to_string_lossy().to_string()
        } else {
            file_path.to_string()
        }
    }
}

/// Anchor project detector
pub struct AnchorDetector {
    project_root: AbsPathBuf,
}

impl AnchorDetector {
    pub fn new(project_root: &AbsPathBuf) -> Self {
        Self {
            project_root: project_root.clone(),
        }
    }

    /// Check if this is an Anchor project
    pub fn is_anchor_project(&self) -> Result<bool> {
        // Method 1: Check for Anchor.toml file (most definitive)
        let anchor_toml = self.project_root.join("Anchor.toml");
        if std::fs::metadata(&anchor_toml).is_ok() {
            return Ok(true);
        }

        // Method 2: Check for anchor-lang dependency in workspace Cargo.toml
        let workspace_cargo_toml = self.project_root.join("Cargo.toml");
        if std::fs::metadata(&workspace_cargo_toml).is_ok() {
            let content = fs::read_to_string(&workspace_cargo_toml)?;
            if content.contains("anchor-lang") || content.contains("anchor_lang") {
                return Ok(true);
            }
        }

        // Method 3: Check for programs directory with Anchor-style structure
        let programs_dir = self.project_root.join("programs");
        if std::fs::metadata(&programs_dir).is_ok() {
            if let Ok(metadata) = std::fs::metadata(&programs_dir) {
                if metadata.is_dir() {
                    // Check if any program in programs directory has anchor-lang dependency
                    if let Ok(entries) = std::fs::read_dir(&programs_dir) {
                        for entry in entries.flatten() {
                            if entry.file_type().map(|ft| ft.is_dir()).unwrap_or(false) {
                                let program_cargo = entry.path().join("Cargo.toml");
                                if let Ok(cargo_content) = fs::read_to_string(&program_cargo) {
                                    if cargo_content.contains("anchor-lang") {
                                        return Ok(true);
                                    }
                                }
                            }
                        }
                    }
                }
            }
        }

        // Method 4: Check for program directory (single program structure like mango-v3)
        let program_dir = self.project_root.join("program");
        if std::fs::metadata(&program_dir).is_ok() {
            let program_cargo = program_dir.join("Cargo.toml");
            if let Ok(cargo_content) = fs::read_to_string(&program_cargo) {
                if cargo_content.contains("anchor-lang") || 
                   cargo_content.contains("solana-program") ||
                   cargo_content.contains("spl-token") {
                    return Ok(true);
                }
            }
        }

        // Method 5: Check workspace members for Solana/Anchor patterns
        if std::fs::metadata(&workspace_cargo_toml).is_ok() {
            let content = fs::read_to_string(&workspace_cargo_toml)?;
            if content.contains("[workspace]") {
                // Look for common Anchor workspace member patterns
                if content.contains("program") || 
                   content.contains("programs/") ||
                   content.contains("mango-") || // Common in Solana projects like mango-v3
                   content.contains("anchor") {
                    // Double check by looking at member directories for Solana dependencies
                    if let Ok(entries) = std::fs::read_dir(&self.project_root) {
                        for entry in entries.flatten() {
                            if entry.file_type().map(|ft| ft.is_dir()).unwrap_or(false) {
                                let member_cargo = entry.path().join("Cargo.toml");
                                if let Ok(cargo_content) = fs::read_to_string(&member_cargo) {
                                    if cargo_content.contains("solana-program") ||
                                       cargo_content.contains("anchor-lang") ||
                                       cargo_content.contains("spl-token") ||
                                       cargo_content.contains("serum_dex") {
                                        return Ok(true);
                                    }
                                }
                            }
                        }
                    }
                }
            }
        }

        // Method 6: Check for common Solana program files
        let src_dir = self.project_root.join("src");
        if std::fs::metadata(&src_dir).is_ok() {
            if let Ok(entries) = std::fs::read_dir(&src_dir) {
                for entry in entries.flatten() {
                    if let Some(file_name) = entry.file_name().to_str() {
                        // Common Solana program files
                        if file_name == "lib.rs" || file_name == "processor.rs" || 
                           file_name == "instruction.rs" || file_name == "state.rs" {
                            if let Ok(file_content) = fs::read_to_string(entry.path()) {
                                if file_content.contains("solana_program") ||
                                   file_content.contains("anchor_lang") ||
                                   file_content.contains("Program") ||
                                   file_content.contains("#[program]") {
                                    return Ok(true);
                                }
                            }
                        }
                    }
                }
            }
        }

        Ok(false)
    }

    /// Get Anchor version from Anchor.toml
    pub fn get_anchor_version(&self) -> Result<Option<String>> {
        let anchor_toml = self.project_root.join("Anchor.toml");
        if std::fs::metadata(&anchor_toml).is_ok() {
            let content = fs::read_to_string(&anchor_toml)?;
            // Simple parsing - in real implementation, use a TOML parser
            for line in content.lines() {
                if line.starts_with("anchor_version") {
                    if let Some(version) = line.split('=').nth(1) {
                        let version = version.trim().trim_matches('"');
                        return Ok(Some(version.to_string()));
                    }
                }
            }
        }
        Ok(None)
    }

    /// Get program ID from Anchor.toml
    pub fn get_program_id(&self) -> Result<Option<String>> {
        let anchor_toml = self.project_root.join("Anchor.toml");
        if std::fs::metadata(&anchor_toml).is_ok() {
            let content = fs::read_to_string(&anchor_toml)?;
            // Simple parsing - look for program ID in [programs.localnet] section
            let mut in_programs_section = false;
            for line in content.lines() {
                if line.starts_with("[programs.") {
                    in_programs_section = true;
                    continue;
                }
                if line.starts_with('[') && in_programs_section {
                    in_programs_section = false;
                    continue;
                }
                if in_programs_section && line.contains('=') {
                    if let Some(program_id) = line.split('=').nth(1) {
                        let program_id = program_id.trim().trim_matches('"');
                        return Ok(Some(program_id.to_string()));
                    }
                }
            }
        }
        Ok(None)
    }
}

/// Constraint parser for #[account(...)] attributes
pub struct ConstraintParser;

impl ConstraintParser {
    pub fn new() -> Self {
        Self
    }

    /// Parse constraints from field attributes
    pub fn parse_constraints(&self, attrs: &hir::Attrs, db: &ide::RootDatabase) -> Result<Vec<ConstraintInfo>> {
        let mut constraints = Vec::new();
        
        for attr in attrs.iter() {
            let path = attr.path();
            if path.segments().len() == 1 && path.segments()[0].display(db, syntax::Edition::CURRENT).to_string() == "account" {
                if let Some(tt) = attr.token_tree_value() {
                    let token_text = format!("{:?}", tt);
                    constraints.extend(self.parse_constraint_tokens(&token_text)?);
                }
            }
        }
        
        Ok(constraints)
    }

    /// Parse individual constraint tokens
    fn parse_constraint_tokens(&self, token_text: &str) -> Result<Vec<ConstraintInfo>> {
        let mut constraints = Vec::new();
        
        // This is a simplified parser - in a real implementation,
        // we would need a proper token tree parser
        
        if token_text.contains("init") {
            let mut parameters = HashMap::new();
            
            // Extract payer
            if let Some(payer_start) = token_text.find("payer = ") {
                let payer_part = &token_text[payer_start + 8..];
                if let Some(payer_end) = payer_part.find(',').or_else(|| payer_part.find(')')) {
                    let payer = payer_part[..payer_end].trim();
                    parameters.insert("payer".to_string(), payer.to_string());
                }
            }
            
            // Extract space
            if let Some(space_start) = token_text.find("space = ") {
                let space_part = &token_text[space_start + 8..];
                if let Some(space_end) = space_part.find(',').or_else(|| space_part.find(')')) {
                    let space = space_part[..space_end].trim();
                    parameters.insert("space".to_string(), space.to_string());
                }
            }
            
            constraints.push(ConstraintInfo {
                constraint_type: ConstraintType::Init {
                    payer: parameters.get("payer").cloned().unwrap_or_default(),
                    space: parameters.get("space").cloned(),
                    owner: None,
                },
                parameters,
                error_code: None,
            });
        }
        
        if token_text.contains("mut") && !token_text.contains("mut,") {
            constraints.push(ConstraintInfo {
                constraint_type: ConstraintType::Mut,
                parameters: HashMap::new(),
                error_code: None,
            });
        }
        
        if token_text.contains("seeds = ") {
            let seeds = self.parse_seeds(&token_text)?;
            let bump = self.parse_bump(&token_text)?;
            
            constraints.push(ConstraintInfo {
                constraint_type: ConstraintType::Seeds { seeds, bump },
                parameters: HashMap::new(),
                error_code: None,
            });
        }
        
        if token_text.contains("associated_token") {
            let mut mint = String::new();
            let mut authority = String::new();
            
            if let Some(mint_start) = token_text.find("mint = ") {
                let mint_part = &token_text[mint_start + 7..];
                if let Some(mint_end) = mint_part.find(',').or_else(|| mint_part.find(')')) {
                    mint = mint_part[..mint_end].trim().to_string();
                }
            }
            
            if let Some(auth_start) = token_text.find("authority = ") {
                let auth_part = &token_text[auth_start + 12..];
                if let Some(auth_end) = auth_part.find(',').or_else(|| auth_part.find(')')) {
                    authority = auth_part[..auth_end].trim().to_string();
                }
            }
            
            constraints.push(ConstraintInfo {
                constraint_type: ConstraintType::AssociatedToken {
                    mint,
                    authority,
                    token_program: None,
                },
                parameters: HashMap::new(),
                error_code: None,
            });
        }
        
        Ok(constraints)
    }

    /// Parse seeds from constraint tokens
    fn parse_seeds(&self, token_text: &str) -> Result<Vec<SeedComponent>> {
        let mut seeds = Vec::new();
        
        // Look for seeds = [...]
        if let Some(seeds_start) = token_text.find("seeds = [") {
            let seeds_part = &token_text[seeds_start + 9..];
            if let Some(seeds_end) = seeds_part.find(']') {
                let seeds_content = &seeds_part[..seeds_end];
                
                // Parse individual seed components
                for seed_part in seeds_content.split(',') {
                    let seed_part = seed_part.trim();
                    
                    if seed_part.starts_with("b\"") && seed_part.ends_with('"') {
                        // String literal seed
                        let literal = &seed_part[2..seed_part.len() - 1];
                        seeds.push(SeedComponent::StringLiteral(literal.to_string()));
                    } else if seed_part.contains(".to_le_bytes()") {
                        // Variable with transformation
                        let var_name = seed_part.split('.').next().unwrap_or(seed_part);
                        seeds.push(SeedComponent::Variable {
                            name: var_name.to_string(),
                            transformation: Some(".to_le_bytes().as_ref()".to_string()),
                        });
                    } else {
                        // Simple variable or expression
                        seeds.push(SeedComponent::Variable {
                            name: seed_part.to_string(),
                            transformation: None,
                        });
                    }
                }
            }
        }
        
        Ok(seeds)
    }

    /// Parse bump information
    fn parse_bump(&self, token_text: &str) -> Result<Option<BumpInfo>> {
        if token_text.contains("bump") {
            if token_text.contains("bump = ") {
                // Explicit bump value
                if let Some(bump_start) = token_text.find("bump = ") {
                    let bump_part = &token_text[bump_start + 7..];
                    if let Some(bump_end) = bump_part.find(',').or_else(|| bump_part.find(')')) {
                        let bump_value = bump_part[..bump_end].trim();
                        return Ok(Some(BumpInfo::Explicit(bump_value.to_string())));
                    }
                }
            } else {
                // Auto bump
                return Ok(Some(BumpInfo::Auto));
            }
        }
        Ok(None)
    }
}

/// PDA analyzer for analyzing Program Derived Addresses
pub struct PdaAnalyzer;

impl PdaAnalyzer {
    pub fn new() -> Self {
        Self
    }

    /// Extract PDA information from constraints
    pub fn extract_pda_info(&self, constraints: &[ConstraintInfo]) -> Result<Option<PdaInfo>> {
        for constraint in constraints {
            if let ConstraintType::Seeds { seeds, bump } = &constraint.constraint_type {
                return Ok(Some(PdaInfo {
                    seeds: seeds.clone(),
                    bump: bump.clone().unwrap_or(BumpInfo::Auto),
                    program_id: None,
                    canonical_bump: None,
                    derived_address: None,
                }));
            }
        }
        Ok(None)
    }

    /// Analyze relationships between PDAs
    pub fn analyze_relationships(&self, account_structs: &[AccountStructInfo]) -> Result<Vec<PdaRelationship>> {
        let mut relationships = Vec::new();
        
        // Find PDAs and analyze their relationships
        let pda_fields: Vec<_> = account_structs
            .iter()
            .flat_map(|s| s.fields.iter().filter(|f| f.is_pda))
            .collect();
        
        // Compare PDAs to find relationships
        for (i, pda1) in pda_fields.iter().enumerate() {
            for pda2 in pda_fields.iter().skip(i + 1) {
                if let (Some(pda_info1), Some(pda_info2)) = (&pda1.pda_info, &pda2.pda_info) {
                    let shared_seeds = self.find_shared_seeds(&pda_info1.seeds, &pda_info2.seeds);
                    
                    if !shared_seeds.is_empty() {
                        relationships.push(PdaRelationship {
                            parent: pda1.name.clone(),
                            child: pda2.name.clone(),
                            relationship_type: "shared_seeds".to_string(),
                            shared_seeds,
                        });
                    }
                }
            }
        }
        
        Ok(relationships)
    }

    /// Find shared seeds between two PDA seed lists
    fn find_shared_seeds(&self, seeds1: &[SeedComponent], seeds2: &[SeedComponent]) -> Vec<String> {
        let mut shared = Vec::new();
        
        for seed1 in seeds1 {
            for seed2 in seeds2 {
                match (seed1, seed2) {
                    (SeedComponent::StringLiteral(s1), SeedComponent::StringLiteral(s2)) => {
                        if s1 == s2 {
                            shared.push(s1.clone());
                        }
                    },
                    (SeedComponent::Variable { name: n1, .. }, SeedComponent::Variable { name: n2, .. }) => {
                        if n1 == n2 {
                            shared.push(n1.clone());
                        }
                    },
                    _ => {}
                }
            }
        }
        
        shared
    }
}

/// JSON exporter for analysis results
pub struct JsonExporter;

impl JsonExporter {
    pub fn new() -> Self {
        Self
    }

    /// Export analysis results to JSON
    pub fn export(&self, result: &AnalysisResult, output_path: &Option<PathBuf>) -> Result<()> {
        let json_output = serde_json::to_string_pretty(result)?;
        
        match output_path {
            Some(path) => {
                fs::write(path, json_output)?;
                eprintln!("Analysis results written to: {}", path.display());
            },
            None => {
                println!("{}", json_output);
            }
        }
        
        Ok(())
    }
}

impl flags::StructAnalyzer {
    pub fn run(self) -> Result<()> {
        eprintln!("Starting Solana Anchor struct analysis...");
        
        // Create analyzer with full configuration (all features enabled)
        let path = AbsPathBuf::assert_utf8(env::current_dir()?.join(&self.path));
        let manifest = ProjectManifest::discover_single(&path)?;
        let mut cargo_config = CargoConfig::default();
        cargo_config.sysroot = Some(RustLibSource::Discover);

        let load_cargo_config = LoadCargoConfig {
            load_out_dirs_from_check: true, // Enable build scripts for complete analysis
            with_proc_macro_server: ProcMacroServerChoice::Sysroot, // Enable proc macros
            prefill_caches: false,
        };

        let ws = ProjectWorkspace::load(manifest, &cargo_config, &|_| {})?;
        let (db, vfs, _proc_macro) = load_workspace(
            ws,
            &cargo_config.extra_env,
            &load_cargo_config,
        )?;

        let host = AnalysisHost::with_database(db.clone());
        let _analysis = host.analysis();
        let project_root = path;

        let analyzer = StructAnalyzer {
            db,
            vfs,
            project_root,
        };
        
        // Check if this is an Anchor project
        let anchor_detector = AnchorDetector::new(&analyzer.project_root);
        if !anchor_detector.is_anchor_project()? {
            eprintln!("Warning: This doesn't appear to be an Anchor project. Continuing analysis anyway...");
        }
        
        // Perform comprehensive analysis
        let result = analyzer.analyze()?;
        
        // Determine project name from path
        let project_name = analyzer.project_root
            .file_name()
            .unwrap_or("unknown")
            .to_string();

        // Export results
        let exporter = JsonExporter::new();
        exporter.export(&result, &None)?;
        
        eprintln!("Analysis completed successfully!");
        eprintln!("Found {} Anchor account structs", result.account_structs.len());
        eprintln!("Total structs analyzed: {}", result.statistics.total_structs);
        eprintln!("Files processed: {}", result.statistics.files_analyzed);
        eprintln!("Analysis duration: {}ms", result.statistics.analysis_duration_ms);
        
        Ok(())
    }
}