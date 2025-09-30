use std::{env, fs, io::Write, path::PathBuf};
use anyhow::Result;
use ide::{Analysis, AnalysisHost, NavigationTarget, Query, SymbolKind, TextRange};
use ide_db::FileId;
use load_cargo::{LoadCargoConfig, ProcMacroServerChoice, load_workspace};
use project_model::{CargoConfig, ProjectManifest, ProjectWorkspace, RustLibSource};
use vfs::{AbsPathBuf, Vfs};
use serde_json;

use crate::cli::flags;

/// 符号查找结果
#[derive(Debug, Clone, serde::Serialize)]
pub(super) struct SymbolResult {
    /// 符号名称
    pub name: String,
    /// 符号类型
    pub kind: String,
    /// 文件路径
    pub file_path: String,
    /// 符号在文件中的完整范围
    pub full_range: (u32, u32),
    /// 符号的焦点范围（通常是标识符）
    pub focus_range: Option<(u32, u32)>,
    /// 容器名称（如模块、结构体等）
    pub container_name: Option<String>,
    /// 符号描述
    pub description: Option<String>,
}

/// 提取的符号内容
#[derive(Debug, Clone, serde::Serialize)]
pub(super) struct SymbolContent {
    /// 符号信息
    pub symbol: SymbolResult,
    /// 符号的完整源代码
    pub source_code: String,
    /// 符号的文档注释
    pub documentation: Option<String>,
}

/// 函数内容
#[derive(Debug, Clone, serde::Serialize)]
pub(super) struct FunctionContent {
    /// 基础符号内容
    pub base: SymbolContent,
    /// 函数签名
    pub signature: String,
    /// 参数列表
    pub parameters: Vec<String>,
    /// 返回类型
    pub return_type: Option<String>,
}

/// 结构体内容
#[derive(Debug, Clone, serde::Serialize)]
pub(super) struct StructContent {
    /// 基础符号内容
    pub base: SymbolContent,
    /// 字段列表
    pub fields: Vec<StructField>,
    /// 是否是元组结构体
    pub is_tuple_struct: bool,
}

/// 结构体字段
#[derive(Debug, Clone, serde::Serialize)]
pub(super) struct StructField {
    /// 字段名称
    pub name: Option<String>,
    /// 字段类型
    pub field_type: String,
    /// 可见性
    pub visibility: String,
}

/// 符号查找器
pub(super) struct InternalSymbolFinder {
    analysis: Analysis,
    vfs: Vfs,
}

impl InternalSymbolFinder {
    /// 创建新的符号查找器
    pub(super) fn new(analysis: Analysis, vfs: Vfs) -> Self {
        Self { analysis, vfs }
    }

    /// 查找函数符号
    pub(super) fn find_functions(&self, function_name: &str) -> Result<Vec<SymbolResult>, String> {
        let query = Query::new(function_name.to_string());
        
        let navigation_targets = self.analysis
            .symbol_search(query, 50)
            .map_err(|e| format!("符号搜索失败: {:?}", e))?;

        let functions: Vec<SymbolResult> = navigation_targets
            .into_iter()
            .filter(|target| target.kind.unwrap_or(SymbolKind::Module) == SymbolKind::Function)
            .filter(|target| target.name.as_str() == function_name)
            .map(|target| self.convert_navigation_target(target))
            .collect();

        Ok(functions)
    }

    /// 查找结构体符号
    pub(super) fn find_structs(&self, struct_name: &str) -> Result<Vec<SymbolResult>, String> {
        let query = Query::new(struct_name.to_string());
        
        let navigation_targets = self.analysis
            .symbol_search(query, 50)
            .map_err(|e| format!("符号搜索失败: {:?}", e))?;

        let structs: Vec<SymbolResult> = navigation_targets
            .into_iter()
            .filter(|target| target.kind.unwrap_or(SymbolKind::Module) == SymbolKind::Struct)
            .filter(|target| target.name.as_str() == struct_name)
            .map(|target| self.convert_navigation_target(target))
            .collect();

        Ok(structs)
    }

    /// 转换导航目标为符号结果
    fn convert_navigation_target(&self, target: NavigationTarget) -> SymbolResult {
        let file_path = self.vfs.file_path(target.file_id).to_string();
        let kind_str = match target.kind {
            Some(SymbolKind::Function) => "function".to_string(),
            Some(SymbolKind::Struct) => "struct".to_string(),
            Some(kind) => format!("{:?}", kind).to_lowercase(),
            None => "unknown".to_string(),
        };

        SymbolResult {
            name: target.name.to_string(),
            kind: kind_str,
            file_path,
            full_range: (target.full_range.start().into(), target.full_range.end().into()),
            focus_range: target.focus_range.map(|r| (r.start().into(), r.end().into())),
            container_name: target.container_name.map(|n| n.to_string()),
            description: target.description.clone(),
        }
    }

    /// 提取符号内容
    pub(super) fn extract_symbol_content(&self, symbol: &SymbolResult) -> Result<SymbolContent, String> {
        // 查找文件ID
        let file_id = self.find_file_id_by_path(&symbol.file_path)
            .ok_or_else(|| format!("无法找到文件: {}", symbol.file_path))?;

        // 获取文件内容
        let file_text = self.analysis
            .file_text(file_id)
            .map_err(|e| format!("无法读取文件内容: {:?}", e))?;

        let start_offset = symbol.full_range.0 as usize;
        let end_offset = symbol.full_range.1 as usize;
        
        if start_offset >= file_text.len() || end_offset > file_text.len() || start_offset > end_offset {
            return Err(format!("无效的文本范围: {}..{}", start_offset, end_offset));
        }

        let source_code = file_text[start_offset..end_offset].to_string();
        
        // 提取文档注释
        let documentation = self.extract_simple_docs(&file_text, TextRange::new((start_offset as u32).into(), (end_offset as u32).into()));

        Ok(SymbolContent {
            symbol: symbol.clone(),
            source_code,
            documentation,
        })
    }

    /// 查找文件ID
    fn find_file_id_by_path(&self, file_path: &str) -> Option<FileId> {
        for (file_id, path) in self.vfs.iter() {
            let path_str = path.to_string();
            if path_str == file_path {
                return Some(file_id);
            }
        }
        None
    }

    /// 提取简单的文档注释
    fn extract_simple_docs(&self, file_text: &str, range: TextRange) -> Option<String> {
        let lines: Vec<&str> = file_text.lines().collect();
        let start_line = file_text[..range.start().into()].matches('\n').count();
        
        let mut docs = Vec::new();
        
        // 向前查找文档注释
        for i in (0..start_line).rev() {
            if let Some(line) = lines.get(i) {
                let trimmed = line.trim();
                if trimmed.starts_with("///") {
                    docs.insert(0, trimmed.trim_start_matches("///").trim().to_string());
                } else if trimmed.starts_with("//!") {
                    docs.insert(0, trimmed.trim_start_matches("//!").trim().to_string());
                } else if !trimmed.is_empty() {
                    break;
                }
            }
        }
        
        if docs.is_empty() {
            None
        } else {
            Some(docs.join("\n"))
        }
    }

    /// 解析函数内容
    pub(super) fn parse_function_content(&self, content: SymbolContent) -> Result<FunctionContent, String> {
        let signature = self.extract_function_signature(&content.source_code);
        let parameters = self.extract_simple_parameters(&content.source_code);
        let return_type = self.extract_simple_return_type(&content.source_code);

        Ok(FunctionContent {
            base: content,
            signature,
            parameters,
            return_type,
        })
    }

    /// 解析结构体内容
    pub(super) fn parse_struct_content(&self, content: SymbolContent) -> Result<StructContent, String> {
        let fields = self.extract_simple_fields(&content.source_code);
        let is_tuple_struct = content.source_code.contains('(') && !content.source_code.contains('{');

        Ok(StructContent {
            base: content,
            fields,
            is_tuple_struct,
        })
    }

    /// 提取函数签名
    fn extract_function_signature(&self, source: &str) -> String {
        // 简单提取：找到第一个 '{' 或 ';' 之前的部分
        if let Some(body_start) = source.find('{') {
            source[..body_start].trim().to_string()
        } else if let Some(semicolon) = source.find(';') {
            source[..semicolon].trim().to_string()
        } else {
            source.trim().to_string()
        }
    }

    /// 提取简单的参数列表
    fn extract_simple_parameters(&self, source: &str) -> Vec<String> {
        if let Some(start) = source.find('(') {
            if let Some(end) = source[start..].find(')') {
                let params_str = &source[start + 1..start + end];
                return params_str
                    .split(',')
                    .map(|p| p.trim().to_string())
                    .filter(|p| !p.is_empty())
                    .collect();
            }
        }
        Vec::new()
    }

    /// 提取简单的返回类型
    fn extract_simple_return_type(&self, source: &str) -> Option<String> {
        if let Some(arrow_pos) = source.find("->") {
            let after_arrow = &source[arrow_pos + 2..];
            if let Some(brace_pos) = after_arrow.find('{') {
                Some(after_arrow[..brace_pos].trim().to_string())
            } else if let Some(semicolon_pos) = after_arrow.find(';') {
                Some(after_arrow[..semicolon_pos].trim().to_string())
            } else {
                Some(after_arrow.trim().to_string())
            }
        } else {
            None
        }
    }

    /// 提取简单的字段列表
    fn extract_simple_fields(&self, source: &str) -> Vec<StructField> {
        let mut fields = Vec::new();
        
        if let Some(start) = source.find('{') {
            if let Some(end) = source.rfind('}') {
                let fields_str = &source[start + 1..end];
                
                for line in fields_str.lines() {
                    let trimmed = line.trim();
                    if trimmed.is_empty() || trimmed.starts_with("//") {
                        continue;
                    }
                    
                    // 简单解析字段：pub field_name: Type,
                    let parts: Vec<&str> = trimmed.split(':').collect();
                    if parts.len() == 2 {
                        let name_part = parts[0].trim();
                        let type_part = parts[1].trim().trim_end_matches(',');
                        
                        let (visibility, name) = if name_part.starts_with("pub") {
                            let name = name_part.strip_prefix("pub").unwrap().trim();
                            ("pub".to_string(), if name.is_empty() { None } else { Some(name.to_string()) })
                        } else {
                            ("private".to_string(), Some(name_part.to_string()))
                        };
                        
                        fields.push(StructField {
                            name,
                            field_type: type_part.to_string(),
                            visibility,
                        });
                    }
                }
            }
        }
        
        fields
    }
}

impl flags::SymbolFinder {
    pub fn run(self) -> Result<()> {
        eprintln!("正在加载工作空间...");
        
        // 确定项目路径
        let project_path = self.project_path.clone().unwrap_or_else(|| {
            env::current_dir().unwrap_or_else(|_| PathBuf::from("."))
        });
        
        let path = AbsPathBuf::assert_utf8(project_path);
        
        // 检查是否是单个文件
        if path.as_str().ends_with(".rs") {
            return self.run_single_file(&path);
        }
        
        // 项目模式
        self.run_project(&path)
    }
    
    fn run_single_file(&self, file_path: &AbsPathBuf) -> Result<()> {
        let source_code = fs::read_to_string(file_path)?;
        let (analysis, _file_id) = Analysis::from_single_file(source_code);
        let vfs = Vfs::default(); // 单文件模式下的简化VFS
        
        let finder = InternalSymbolFinder::new(analysis, vfs);
        self.process_symbols(&finder)
    }
    
    fn run_project(&self, path: &AbsPathBuf) -> Result<()> {
        let manifest = ProjectManifest::discover_single(path)?;
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
        
        let host = AnalysisHost::with_database(db);
        let analysis = host.analysis();
        
        let finder = InternalSymbolFinder::new(analysis, vfs);
        self.process_symbols(&finder)
    }
    
    fn process_symbols(&self, finder: &InternalSymbolFinder) -> Result<()> {
        match self.symbol_type.as_str() {
            "function" | "func" | "fn" => {
                let functions = finder.find_functions(&self.symbol_name)
                    .map_err(|e| anyhow::anyhow!("查找函数失败: {}", e))?;
                
                if functions.is_empty() {
                    eprintln!("未找到函数: {}", self.symbol_name);
                    return Ok(());
                }
                
                for func_symbol in functions {
                    let content = finder.extract_symbol_content(&func_symbol)
                        .map_err(|e| anyhow::anyhow!("提取符号内容失败: {}", e))?;
                    
                    let func_content = finder.parse_function_content(content)
                        .map_err(|e| anyhow::anyhow!("解析函数内容失败: {}", e))?;
                    
                    self.output_result(&func_content)?;
                }
            }
            "struct" | "structure" => {
                let structs = finder.find_structs(&self.symbol_name)
                    .map_err(|e| anyhow::anyhow!("查找结构体失败: {}", e))?;
                
                if structs.is_empty() {
                    eprintln!("未找到结构体: {}", self.symbol_name);
                    return Ok(());
                }
                
                for struct_symbol in structs {
                    let content = finder.extract_symbol_content(&struct_symbol)
                        .map_err(|e| anyhow::anyhow!("提取符号内容失败: {}", e))?;
                    
                    let struct_content = finder.parse_struct_content(content)
                        .map_err(|e| anyhow::anyhow!("解析结构体内容失败: {}", e))?;
                    
                    self.output_result(&struct_content)?;
                }
            }
            _ => {
                return Err(anyhow::anyhow!("不支持的符号类型: {}。支持的类型: function, struct", self.symbol_type));
            }
        }
        
        Ok(())
    }
    
    fn output_result<T: serde::Serialize>(&self, content: &T) -> Result<()> {
        let output: Box<dyn Write> = match &self.output_path {
            Some(path) => {
                let file = fs::File::create(path)?;
                Box::new(file)
            }
            None => Box::new(std::io::stdout()),
        };
        
        let mut writer = output;
        
        // Only output source code
        match serde_json::to_value(content)? {
            serde_json::Value::Object(map) => {
                if let Some(base) = map.get("base") {
                    if let Some(source_code) = base.get("source_code") {
                        if let Some(code_str) = source_code.as_str() {
                            writeln!(writer, "{}", code_str)?;
                        }
                    }
                } else if let Some(source_code) = map.get("source_code") {
                    if let Some(code_str) = source_code.as_str() {
                        writeln!(writer, "{}", code_str)?;
                    }
                }
            }
            _ => {}
        }
        
        Ok(())
    }
}