#!/usr/bin/env python3
"""
Solana Contract Structure Extractor - Simplified & Accurate Version

专注于完整提取结构体定义，为AI漏洞扫描提供准确的上下文信息。
核心思路：匹配到#[account]等前缀后，使用健壮的括号匹配算法提取完整结构体。
"""

import os
import re
from pathlib import Path
from typing import Dict, List, Optional, Tuple
from dataclasses import dataclass, field

@dataclass
class StructField:
    """结构体字段"""
    name: str
    field_type: str
    constraints: List[str] = field(default_factory=list)

@dataclass
class StructDefinition:
    """完整的结构体定义"""
    name: str
    file_path: str
    line_number: int
    fields: List[StructField] = field(default_factory=list)
    derives: List[str] = field(default_factory=list)
    attributes: List[str] = field(default_factory=list)
    is_account_struct: bool = False

@dataclass
class ConstantDef:
    """常量定义"""
    name: str
    const_type: str
    value: str
    file_path: str
    line_number: int

@dataclass
class ProgramIdDef:
    """程序ID定义"""
    program_id: str
    file_path: str
    line_number: int

@dataclass
class OracleInfo:
    """预言机/价格馈送信息"""
    oracle_type: str  # "switchboard", "pyth", "chainlink", etc.
    feed_address: Optional[str] = None
    price_account: Optional[str] = None
    staleness_threshold: Optional[int] = None
    confidence_threshold: Optional[str] = None
    file_path: str = ""
    line_number: int = 0

@dataclass
class LiquidityPoolInfo:
    """流动性池配置"""
    pool_type: str  # "constant_product", "stable_swap", "concentrated", etc.
    token_a_mint: Optional[str] = None
    token_b_mint: Optional[str] = None
    fee_rate: Optional[str] = None
    admin_fee_rate: Optional[str] = None
    min_liquidity: Optional[str] = None
    max_liquidity: Optional[str] = None
    slippage_tolerance: Optional[str] = None
    file_path: str = ""
    line_number: int = 0

@dataclass
class LendingPoolInfo:
    """借贷池配置"""
    pool_name: str
    collateral_mint: Optional[str] = None
    borrow_mint: Optional[str] = None
    collateral_ratio: Optional[str] = None
    liquidation_threshold: Optional[str] = None
    borrow_limit: Optional[str] = None
    interest_rate_model: Optional[str] = None
    reserve_factor: Optional[str] = None
    file_path: str = ""
    line_number: int = 0

@dataclass
class VaultInfo:
    """金库/策略配置"""
    vault_type: str  # "yield_farming", "lending", "staking", etc.
    underlying_mint: Optional[str] = None
    strategy_type: Optional[str] = None
    performance_fee: Optional[str] = None
    management_fee: Optional[str] = None
    withdrawal_fee: Optional[str] = None
    max_deposit: Optional[str] = None
    min_deposit: Optional[str] = None
    emergency_pause: bool = False
    time_lock: Optional[str] = None
    file_path: str = ""
    line_number: int = 0

@dataclass
class GovernanceInfo:
    """治理和管理控制"""
    governance_type: str  # "multisig", "dao", "timelock", etc.
    admin_authority: Optional[str] = None
    emergency_authority: Optional[str] = None
    upgrade_authority: Optional[str] = None
    proposal_threshold: Optional[str] = None
    voting_delay: Optional[str] = None
    voting_period: Optional[str] = None
    execution_delay: Optional[str] = None
    file_path: str = ""
    line_number: int = 0

class SolanaStructExtractor:
    """简化的Solana结构体提取器"""
    
    def __init__(self, project_root: str):
        self.project_root = Path(project_root)
        self.structs: List[StructDefinition] = []
        self.constants: List[ConstantDef] = []
        self.program_ids: List[ProgramIdDef] = []
        
        # DeFi特定数据结构
        self.oracle_infos: List[OracleInfo] = []
        self.liquidity_pools: List[LiquidityPoolInfo] = []
        self.lending_pools: List[LendingPoolInfo] = []
        self.vaults: List[VaultInfo] = []
        self.governance_infos: List[GovernanceInfo] = []
        
        # 核心模式匹配
        self.struct_pattern = re.compile(r'pub struct (\w+)')
        self.const_pattern = re.compile(r'pub const (\w+):\s*([^=]+?)\s*=\s*([^;]+);')
        self.derive_pattern = re.compile(r'#\[derive\((.*?)\)\]')
        self.declare_id_pattern = re.compile(r'declare_id!\s*\(\s*["\']([^"\']+)["\']\s*\)')
        
        # DeFi特定模式
        self.oracle_pattern = re.compile(r'(switchboard|pyth|chainlink).*?(feed|oracle|price)', re.IGNORECASE)
        self.pool_pattern = re.compile(r'(pool|liquidity|amm|swap)', re.IGNORECASE)
        self.vault_pattern = re.compile(r'(vault|strategy|farm)', re.IGNORECASE)
        self.lending_pattern = re.compile(r'(lending|borrow|collateral|liquidat)', re.IGNORECASE)
        
    def extract_from_project(self) -> None:
        """从项目中提取数据"""
        programs_dirs = list(self.project_root.glob("**/programs/*/src"))
        
        if not programs_dirs:
            print(f"No programs/src directories found in {self.project_root}")
            return
            
        for programs_dir in programs_dirs:
            print(f"Processing: {programs_dir}")
            self._process_directory(programs_dir)
    
    def _process_directory(self, directory: Path) -> None:
        """递归处理目录中的所有Rust文件"""
        for rust_file in directory.rglob("*.rs"):
            try:
                self._process_file(rust_file)
            except Exception as e:
                print(f"Error processing {rust_file}: {e}")
    
    def _process_file(self, file_path: Path) -> None:
        """处理单个Rust文件"""
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()
        except Exception as e:
            print(f"Error reading file {file_path}: {e}")
            return
        
        lines = content.split('\n')
        
        # 提取结构体
        self._extract_structs_with_robust_matching(lines, file_path)
        
        # 提取常量
        self._extract_constants(lines, file_path)
        
        # 提取程序ID
        self._extract_program_ids(lines, file_path)
        
        # 提取DeFi特定结构
        self._extract_oracle_infos(lines, file_path)
        self._extract_liquidity_pools(lines, file_path)
        self._extract_lending_pools(lines, file_path)
        self._extract_vaults(lines, file_path)
        self._extract_governance_infos(lines, file_path)
    
    def _extract_structs_with_robust_matching(self, lines: List[str], file_path: Path) -> None:
        """使用健壮的括号匹配算法提取结构体"""
        i = 0
        while i < len(lines):
            line = lines[i].strip()
            
            # 查找结构体定义
            struct_match = self.struct_pattern.search(line)
            if struct_match:
                struct_name = struct_match.group(1)
                
                # 收集结构体前的属性和derives
                attributes, derives, is_account = self._collect_struct_metadata(lines, i)
                
                # 使用健壮的括号匹配提取完整结构体
                fields = self._extract_complete_struct_with_robust_parsing(lines, i)
                
                if fields is not None:  # 只有成功解析才添加
                    struct_def = StructDefinition(
                        name=struct_name,
                        file_path=str(file_path),
                        line_number=i + 1,
                        fields=fields,
                        derives=derives,
                        attributes=attributes,
                        is_account_struct=is_account
                    )
                    
                    self.structs.append(struct_def)
                    print(f"✓ Extracted struct: {struct_name} with {len(fields)} fields")
            
            i += 1
    
    def _collect_struct_metadata(self, lines: List[str], struct_line: int) -> Tuple[List[str], List[str], bool]:
        """收集结构体前的属性和derives"""
        attributes = []
        derives = []
        is_account = False
        
        # 向前查找属性
        i = struct_line - 1
        while i >= 0:
            line = lines[i].strip()
            if not line or line.startswith('//'):
                i -= 1
                continue
            elif line.startswith('#['):
                attributes.append(line)
                if '#[account' in line:
                    is_account = True
                elif line.startswith('#[derive'):
                    derive_match = self.derive_pattern.search(line)
                    if derive_match:
                        derives.extend([d.strip() for d in derive_match.group(1).split(',')])
                i -= 1
            else:
                break
        
        return attributes, derives, is_account
    
    def _extract_complete_struct_with_robust_parsing(self, lines: List[str], start_line: int) -> Optional[List[StructField]]:
        """使用健壮的状态机解析完整结构体"""
        fields = []
        i = start_line
        
        # 找到结构体开始的大括号
        while i < len(lines) and '{' not in lines[i]:
            i += 1
        
        if i >= len(lines):
            return None
        
        # 使用状态机进行精确的括号匹配
        brace_stack = []
        in_string = False
        in_char = False
        in_line_comment = False
        in_block_comment = False
        escape_next = False
        current_constraints = []
        
        # 从包含开括号的行开始
        start_brace_line = i
        
        for line_idx in range(start_brace_line, len(lines)):
            line = lines[line_idx]
            char_idx = 0
            
            while char_idx < len(line):
                char = line[char_idx]
                
                # 处理转义字符
                if escape_next:
                    escape_next = False
                    char_idx += 1
                    continue
                
                if char == '\\' and (in_string or in_char):
                    escape_next = True
                    char_idx += 1
                    continue
                
                # 处理注释状态
                if not in_string and not in_char:
                    # 行注释
                    if char == '/' and char_idx + 1 < len(line) and line[char_idx + 1] == '/':
                        in_line_comment = True
                        break  # 跳过本行剩余部分
                    
                    # 块注释开始
                    if char == '/' and char_idx + 1 < len(line) and line[char_idx + 1] == '*':
                        in_block_comment = True
                        char_idx += 2
                        continue
                    
                    # 块注释结束
                    if in_block_comment and char == '*' and char_idx + 1 < len(line) and line[char_idx + 1] == '/':
                        in_block_comment = False
                        char_idx += 2
                        continue
                
                # 如果在注释中，跳过
                if in_line_comment or in_block_comment:
                    char_idx += 1
                    continue
                
                # 处理字符串状态
                if char == '"' and not in_char:
                    in_string = not in_string
                elif char == "'" and not in_string:
                    in_char = not in_char
                
                # 处理括号匹配（只在非字符串状态下）
                if not in_string and not in_char:
                    if char == '{':
                        brace_stack.append((line_idx, char_idx))
                    elif char == '}':
                        if brace_stack:
                            brace_stack.pop()
                            if not brace_stack:  # 找到匹配的结束括号
                                # 提取结构体内容
                                struct_content = self._extract_struct_content(lines, start_brace_line, line_idx)
                                return self._parse_struct_fields(struct_content)
                
                char_idx += 1
            
            # 重置行注释状态
            in_line_comment = False
        
        return None  # 没有找到匹配的括号
    
    def _extract_struct_content(self, lines: List[str], start_line: int, end_line: int) -> List[str]:
        """提取结构体内容（去除开始和结束的大括号行）"""
        content_lines = []
        
        for i in range(start_line, end_line + 1):
            line = lines[i]
            if i == start_line:
                # 移除开始行的大括号前的内容
                brace_pos = line.find('{')
                if brace_pos != -1:
                    line = line[brace_pos + 1:]
            if i == end_line:
                # 移除结束行的大括号后的内容
                brace_pos = line.find('}')
                if brace_pos != -1:
                    line = line[:brace_pos]
            
            if line.strip():  # 只添加非空行
                content_lines.append(line)
        
        return content_lines
    
    def _parse_struct_fields(self, content_lines: List[str]) -> List[StructField]:
        """解析结构体字段"""
        fields = []
        current_constraints = []
        
        for line in content_lines:
            line = line.strip()
            
            # 跳过空行和注释
            if not line or line.startswith('//') or line.startswith('///'):
                continue
            
            # 收集约束
            if line.startswith('#[account('):
                constraint_content = self._extract_single_constraint(line)
                if constraint_content:
                    current_constraints.append(constraint_content)
                continue
            
            # 解析字段定义
            if ':' in line and not line.startswith('#'):
                field_match = re.match(r'^\s*(?:pub\s+)?(\w+)\s*:\s*([^,\n]+?)(?:,\s*)?(?://.*)?$', line)
                if field_match:
                    field_name = field_match.group(1)
                    field_type = field_match.group(2).strip().rstrip(',')
                    
                    field = StructField(
                        name=field_name,
                        field_type=field_type,
                        constraints=current_constraints.copy()
                    )
                    fields.append(field)
                    current_constraints = []  # 重置约束
        
        return fields
    
    def _extract_single_constraint(self, line: str) -> Optional[str]:
        """提取单行约束内容"""
        match = re.search(r'#\[account\((.*?)\)\]', line)
        return match.group(1).strip() if match else None
    
    def _extract_constants(self, lines: List[str], file_path: Path) -> None:
        """提取常量定义"""
        for i, line in enumerate(lines):
            const_match = self.const_pattern.search(line)
            if const_match:
                const_def = ConstantDef(
                    name=const_match.group(1),
                    const_type=const_match.group(2).strip(),
                    value=const_match.group(3).strip(),
                    file_path=str(file_path),
                    line_number=i + 1
                )
                self.constants.append(const_def)
    
    def _extract_program_ids(self, lines: List[str], file_path: Path) -> None:
        """提取程序ID声明"""
        for i, line in enumerate(lines):
            declare_match = self.declare_id_pattern.search(line)
            if declare_match:
                program_id = ProgramIdDef(
                    program_id=declare_match.group(1),
                    file_path=str(file_path),
                    line_number=i + 1
                )
                self.program_ids.append(program_id)
    
    def _extract_oracle_infos(self, lines: List[str], file_path: Path) -> None:
        """提取预言机和价格馈送相关信息"""
        for i, line in enumerate(lines):
            line_stripped = line.strip()
            line_lower = line_stripped.lower()
            
            # 跳过注释行和空行
            if (not line_stripped or 
                line_stripped.startswith('//') or 
                line_stripped.startswith('///')):
                continue
            
            # 只匹配有意义的Oracle相关代码
            if self.oracle_pattern.search(line_stripped):
                # 必须是结构体字段、函数调用或常量定义
                if not ((':' in line_stripped and 'pub ' in line_stripped) or 
                       '(' in line_stripped or 
                       'const ' in line_stripped):
                    continue
                
                oracle_type = "unknown"
                if "switchboard" in line_lower:
                    oracle_type = "switchboard"
                elif "pyth" in line_lower:
                    oracle_type = "pyth"
                elif "chainlink" in line_lower:
                    oracle_type = "chainlink"
                
                # 提取相关参数
                feed_address = self._extract_address_from_line(line_stripped)
                staleness_threshold = self._extract_numeric_value(line_stripped, ["staleness", "stale_after"])
                confidence_threshold = self._extract_numeric_value(line_stripped, ["confidence", "conf_interval"])
                
                # 只有提取到实际参数值时才记录
                if feed_address or staleness_threshold or confidence_threshold:
                    oracle_info = OracleInfo(
                        oracle_type=oracle_type,
                        feed_address=feed_address,
                        staleness_threshold=staleness_threshold,
                        confidence_threshold=confidence_threshold,
                        file_path=str(file_path),
                        line_number=i + 1
                    )
                    self.oracle_infos.append(oracle_info)
    
    def _extract_liquidity_pools(self, lines: List[str], file_path: Path) -> None:
        """提取流动性池配置"""
        for i, line in enumerate(lines):
            line_stripped = line.strip()
            line_lower = line_stripped.lower()
            
            # 跳过注释行和空行
            if (not line_stripped or 
                line_stripped.startswith('//') or 
                line_stripped.startswith('///')):
                continue
            
            # 使用更精确的池模式匹配
            pool_keywords = ['pool', 'liquidity', 'amm', 'swap']
            if not any(keyword in line_lower for keyword in pool_keywords):
                continue
            
            # 只匹配结构体字段、函数调用或常量定义
            if not ((':' in line_stripped and 'pub ' in line_stripped) or 
                   '(' in line_stripped or 
                   'const ' in line_stripped or
                   'struct ' in line_stripped):
                continue
            
            pool_type = "unknown"
            if "constant_product" in line_lower or "xy=k" in line_lower:
                pool_type = "constant_product"
            elif "stable" in line_lower and ("swap" in line_lower or "pool" in line_lower):
                pool_type = "stable_swap"
            elif "concentrated" in line_lower or "clmm" in line_lower:
                pool_type = "concentrated"
            
            # 提取池参数
            fee_rate = self._extract_numeric_value(line_stripped, ["fee", "fee_rate"])
            min_liquidity = self._extract_numeric_value(line_stripped, ["min_liquidity", "min_lp"])
            max_liquidity = self._extract_numeric_value(line_stripped, ["max_liquidity", "max_lp"])
            slippage_tolerance = self._extract_numeric_value(line_stripped, ["slippage", "max_slippage"])
            
            # 只有提取到实际参数值时才记录
            if fee_rate or min_liquidity or max_liquidity or slippage_tolerance:
                pool_info = LiquidityPoolInfo(
                    pool_type=pool_type,
                    fee_rate=fee_rate,
                    min_liquidity=min_liquidity,
                    max_liquidity=max_liquidity,
                    slippage_tolerance=slippage_tolerance,
                    file_path=str(file_path),
                    line_number=i + 1
                )
                self.liquidity_pools.append(pool_info)
    
    def _extract_lending_pools(self, lines: List[str], file_path: Path) -> None:
        """提取借贷池配置"""
        for i, line in enumerate(lines):
            line_stripped = line.strip()
            line_lower = line_stripped.lower()
            
            # 跳过注释行和空行
            if (not line_stripped or 
                line_stripped.startswith('//') or 
                line_stripped.startswith('///')):
                continue
            
            # 使用更精确的借贷模式匹配
            lending_keywords = ['lending', 'borrow', 'collateral', 'liquidat']
            if not any(keyword in line_lower for keyword in lending_keywords):
                continue
            
            # 只匹配结构体字段、函数调用或常量定义
            if not ((':' in line_stripped and 'pub ' in line_stripped) or 
                   '(' in line_stripped or 
                   'const ' in line_stripped):
                continue
            
            # 提取借贷参数
            collateral_ratio = self._extract_numeric_value(line_stripped, ["collateral_ratio", "ltv"])
            liquidation_threshold = self._extract_numeric_value(line_stripped, ["liquidation", "liquidate_threshold"])
            borrow_limit = self._extract_numeric_value(line_stripped, ["borrow_limit", "max_borrow"])
            interest_rate = self._extract_numeric_value(line_stripped, ["interest", "rate", "apr", "apy"])
            
            # 只有提取到实际参数值时才记录
            if any([collateral_ratio, liquidation_threshold, borrow_limit, interest_rate]):
                lending_info = LendingPoolInfo(
                    pool_name=f"lending_pool_{i}",
                    collateral_ratio=collateral_ratio,
                    liquidation_threshold=liquidation_threshold,
                    borrow_limit=borrow_limit,
                    interest_rate_model=interest_rate,
                    file_path=str(file_path),
                    line_number=i + 1
                )
                self.lending_pools.append(lending_info)
    
    def _extract_vaults(self, lines: List[str], file_path: Path) -> None:
        """提取金库/策略配置"""
        for i, line in enumerate(lines):
            line_stripped = line.strip()
            line_lower = line_stripped.lower()
            
            # 跳过注释行和空行
            if (not line_stripped or 
                line_stripped.startswith('//') or 
                line_stripped.startswith('///')):
                continue
            
            # 使用更精确的金库模式匹配
            vault_keywords = ['vault', 'strategy', 'farm']
            if not any(keyword in line_lower for keyword in vault_keywords):
                continue
            
            # 只匹配结构体字段、函数调用或常量定义
            if not ((':' in line_stripped and 'pub ' in line_stripped) or 
                   '(' in line_stripped or 
                   'const ' in line_stripped or
                   'struct ' in line_stripped):
                continue
            
            vault_type = "unknown"
            if "yield" in line_lower or "farm" in line_lower:
                vault_type = "yield_farming"
            elif "lending" in line_lower:
                vault_type = "lending"
            elif "staking" in line_lower:
                vault_type = "staking"
            
            # 提取费用参数
            performance_fee = self._extract_numeric_value(line_stripped, ["performance_fee", "perf_fee"])
            management_fee = self._extract_numeric_value(line_stripped, ["management_fee", "mgmt_fee"])
            withdrawal_fee = self._extract_numeric_value(line_stripped, ["withdrawal_fee", "exit_fee"])
            max_deposit = self._extract_numeric_value(line_stripped, ["max_deposit", "deposit_cap"])
            min_deposit = self._extract_numeric_value(line_stripped, ["min_deposit", "min_amount"])
            
            # 只有提取到实际参数值时才记录
            if any([performance_fee, management_fee, withdrawal_fee, max_deposit, min_deposit]):
                vault_info = VaultInfo(
                    vault_type=vault_type,
                    performance_fee=performance_fee,
                    management_fee=management_fee,
                    withdrawal_fee=withdrawal_fee,
                    max_deposit=max_deposit,
                    min_deposit=min_deposit,
                    file_path=str(file_path),
                    line_number=i + 1
                )
                self.vaults.append(vault_info)
    
    def _extract_governance_infos(self, lines: List[str], file_path: Path) -> None:
        """提取治理和管理控制信息"""
        for i, line in enumerate(lines):
            line_stripped = line.strip()
            line_lower = line_stripped.lower()
            
            # 跳过注释行和空行
            if (not line_stripped or 
                line_stripped.startswith('//') or 
                line_stripped.startswith('///')):
                continue
            
            # 使用更精确的治理模式匹配
            governance_found = False
            governance_type = "unknown"
            
            # 检查结构体字段中的治理字段
            if ':' in line_stripped and 'pub ' in line_stripped:
                if 'global_authority' in line_lower or 'admin_authority' in line_lower:
                    governance_type = "admin"
                    governance_found = True
                elif 'migration_authority' in line_lower:
                    governance_type = "migration"
                    governance_found = True
                elif 'upgrade_authority' in line_lower:
                    governance_type = "upgrade"
                    governance_found = True
                elif 'emergency_authority' in line_lower:
                    governance_type = "emergency"
                    governance_found = True
            
            # 检查函数调用中的权限检查
            elif 'require!' in line_stripped and ('authority' in line_lower or 'admin' in line_lower):
                governance_type = "access_control"
                governance_found = True
            
            # 检查多签相关
            elif 'multisig' in line_lower and ('struct ' in line_stripped or 'pub ' in line_stripped):
                governance_type = "multisig"
                governance_found = True
            
            # 检查DAO相关
            elif 'dao' in line_lower and ('vote' in line_lower or 'proposal' in line_lower):
                governance_type = "dao"
                governance_found = True
            
            # 检查时间锁相关
            elif ('timelock' in line_lower or 'time_lock' in line_lower) and 'pub ' in line_stripped:
                governance_type = "timelock"
                governance_found = True
            
            if governance_found:
                # 提取治理参数
                proposal_threshold = self._extract_numeric_value(line_stripped, ["proposal_threshold", "min_proposal"])
                voting_delay = self._extract_numeric_value(line_stripped, ["voting_delay", "delay"])
                voting_period = self._extract_numeric_value(line_stripped, ["voting_period", "vote_duration"])
                execution_delay = self._extract_numeric_value(line_stripped, ["execution_delay", "timelock_delay"])
                
                # 只有提取到实际参数值或者是明确的权限字段时才记录
                if (proposal_threshold or voting_delay or voting_period or execution_delay or 
                    governance_type in ["admin", "migration", "upgrade", "emergency", "access_control"]):
                    governance_info = GovernanceInfo(
                        governance_type=governance_type,
                        proposal_threshold=proposal_threshold,
                        voting_delay=voting_delay,
                        voting_period=voting_period,
                        execution_delay=execution_delay,
                        file_path=str(file_path),
                        line_number=i + 1
                    )
                    self.governance_infos.append(governance_info)
    
    def _extract_address_from_line(self, line: str) -> Optional[str]:
        """从行中提取Solana地址"""
        # Solana地址通常是44个字符的base58编码
        address_pattern = re.compile(r'[1-9A-HJ-NP-Za-km-z]{32,44}')
        match = address_pattern.search(line)
        return match.group(0) if match else None
    
    def _extract_numeric_value(self, line: str, keywords: List[str]) -> Optional[str]:
        """提取与关键词相关的数值"""
        for keyword in keywords:
            pattern = rf'{keyword}[:\s=]+([0-9]+(?:\.[0-9]+)?)'
            match = re.search(pattern, line, re.IGNORECASE)
            if match:
                return match.group(1)
        return None
    
    def export_to_rust_file(self, output_path: str) -> None:
        """导出为Rust文件"""
        output_file = Path(output_path)
        output_file.parent.mkdir(parents=True, exist_ok=True)
        
        with open(output_file, 'w', encoding='utf-8') as f:
            f.write("// Extracted Solana Contract Structures for AI Vulnerability Analysis\n")
            f.write("// Complete context to prevent cross-file misanalysis\n\n")
            f.write("use anchor_lang::prelude::*;\n\n")
            
            # 导出程序ID
            if self.program_ids:
                f.write("// ===== PROGRAM IDs =====\n\n")
                for program_id in self.program_ids:
                    f.write(f"// {program_id.file_path}:{program_id.line_number}\n")
                    f.write(f'declare_id!("{program_id.program_id}");\n\n')
            
            # 导出常量
            if self.constants:
                f.write("// ===== CONSTANTS =====\n\n")
                for constant in self.constants:
                    f.write(f"// {constant.file_path}:{constant.line_number}\n")
                    f.write(f"pub const {constant.name}: {constant.const_type} = {constant.value};\n\n")
            
            # 导出完整结构体定义
            if self.structs:
                f.write("// ===== COMPLETE STRUCT DEFINITIONS =====\n\n")
                for struct in self.structs:
                    self._write_complete_struct(f, struct)
            
            # 导出DeFi特定结构 - 只有在有数据时才显示
            if self.oracle_infos:
                f.write("// ===== ORACLE INFORMATION =====\n\n")
                for oracle_info in self.oracle_infos:
                    self._write_oracle_info_as_code(f, oracle_info)
            
            if self.liquidity_pools:
                f.write("// ===== LIQUIDITY POOLS =====\n\n")
                for pool_info in self.liquidity_pools:
                    self._write_liquidity_pool_as_code(f, pool_info)
            
            if self.lending_pools:
                f.write("// ===== LENDING POOLS =====\n\n")
                for lending_info in self.lending_pools:
                    self._write_lending_pool_as_code(f, lending_info)
            
            if self.vaults:
                f.write("// ===== VAULTS =====\n\n")
                for vault_info in self.vaults:
                    self._write_vault_as_code(f, vault_info)
            
            if self.governance_infos:
                f.write("// ===== GOVERNANCE =====\n\n")
                for governance_info in self.governance_infos:
                    self._write_governance_as_code(f, governance_info)
        
        print(f"\n✓ Complete structures exported to: {output_path}")
        print(f"✓ Extracted {len(self.structs)} structs, {len(self.constants)} constants, {len(self.program_ids)} program IDs")
        
        # 统计信息
        account_structs = [s for s in self.structs if s.is_account_struct]
        total_fields = sum(len(s.fields) for s in self.structs)
        defi_info_count = (len(self.oracle_infos) + len(self.liquidity_pools) + 
                          len(self.lending_pools) + len(self.vaults) + len(self.governance_infos))
        print(f"✓ Account structs: {len(account_structs)}, Total fields: {total_fields}")
        print(f"✓ DeFi info extracted: {defi_info_count} (Oracle: {len(self.oracle_infos)}, Pool: {len(self.liquidity_pools)}, Lending: {len(self.lending_pools)}, Vault: {len(self.vaults)}, Governance: {len(self.governance_infos)})")
    
    def _write_oracle_info_as_code(self, f, oracle_info: OracleInfo) -> None:
        """写入预言机信息作为代码注释"""
        f.write(f"// {oracle_info.file_path}:{oracle_info.line_number}\n")
        f.write(f"// Oracle Type: {oracle_info.oracle_type}\n")
        if oracle_info.feed_address:
            f.write(f"// Feed Address: {oracle_info.feed_address}\n")
        if oracle_info.staleness_threshold:
            f.write(f"// Staleness Threshold: {oracle_info.staleness_threshold}\n")
        if oracle_info.confidence_threshold:
            f.write(f"// Confidence Threshold: {oracle_info.confidence_threshold}\n")
        f.write("\n")
    
    def _write_liquidity_pool_as_code(self, f, pool_info: LiquidityPoolInfo) -> None:
        """写入流动性池信息作为代码注释"""
        f.write(f"// {pool_info.file_path}:{pool_info.line_number}\n")
        f.write(f"// Pool Type: {pool_info.pool_type}\n")
        if pool_info.fee_rate:
            f.write(f"// Fee Rate: {pool_info.fee_rate}\n")
        if pool_info.min_liquidity:
            f.write(f"// Min Liquidity: {pool_info.min_liquidity}\n")
        if pool_info.max_liquidity:
            f.write(f"// Max Liquidity: {pool_info.max_liquidity}\n")
        if pool_info.slippage_tolerance:
            f.write(f"// Slippage Tolerance: {pool_info.slippage_tolerance}\n")
        f.write("\n")
    
    def _write_lending_pool_as_code(self, f, lending_info: LendingPoolInfo) -> None:
        """写入借贷池信息作为代码注释"""
        f.write(f"// {lending_info.file_path}:{lending_info.line_number}\n")
        f.write(f"// Pool Name: {lending_info.pool_name}\n")
        if lending_info.collateral_ratio:
            f.write(f"// Collateral Ratio: {lending_info.collateral_ratio}\n")
        if lending_info.liquidation_threshold:
            f.write(f"// Liquidation Threshold: {lending_info.liquidation_threshold}\n")
        if lending_info.borrow_limit:
            f.write(f"// Borrow Limit: {lending_info.borrow_limit}\n")
        if lending_info.interest_rate_model:
            f.write(f"// Interest Rate: {lending_info.interest_rate_model}\n")
        f.write("\n")
    
    def _write_vault_as_code(self, f, vault_info: VaultInfo) -> None:
        """写入金库信息作为代码注释"""
        f.write(f"// {vault_info.file_path}:{vault_info.line_number}\n")
        f.write(f"// Vault Type: {vault_info.vault_type}\n")
        if vault_info.performance_fee:
            f.write(f"// Performance Fee: {vault_info.performance_fee}\n")
        if vault_info.management_fee:
            f.write(f"// Management Fee: {vault_info.management_fee}\n")
        if vault_info.withdrawal_fee:
            f.write(f"// Withdrawal Fee: {vault_info.withdrawal_fee}\n")
        if vault_info.max_deposit:
            f.write(f"// Max Deposit: {vault_info.max_deposit}\n")
        if vault_info.min_deposit:
            f.write(f"// Min Deposit: {vault_info.min_deposit}\n")
        f.write("\n")
    
    def _write_governance_as_code(self, f, governance_info: GovernanceInfo) -> None:
        """写入治理信息作为代码注释"""
        f.write(f"// {governance_info.file_path}:{governance_info.line_number}\n")
        f.write(f"// Governance Type: {governance_info.governance_type}\n")
        if governance_info.proposal_threshold:
            f.write(f"// Proposal Threshold: {governance_info.proposal_threshold}\n")
        if governance_info.voting_delay:
            f.write(f"// Voting Delay: {governance_info.voting_delay}\n")
        if governance_info.voting_period:
            f.write(f"// Voting Period: {governance_info.voting_period}\n")
        if governance_info.execution_delay:
            f.write(f"// Execution Delay: {governance_info.execution_delay}\n")
        f.write("\n")
    
    def _write_complete_struct(self, f, struct: StructDefinition) -> None:
        """写入完整的结构体定义"""
        f.write(f"// {struct.file_path}:{struct.line_number}\n")
        
        # 写入derives
        if struct.derives:
            f.write(f"#[derive({', '.join(struct.derives)})]\n")
        
        # 写入属性
        for attr in struct.attributes:
            f.write(f"{attr}\n")
        
        # 写入结构体定义
        f.write(f"pub struct {struct.name} {{\n")
        
        # 写入所有字段和约束
        for field in struct.fields:
            if field.constraints:
                for constraint in field.constraints:
                    f.write(f"    #[account({constraint})]\n")
            
            f.write(f"    pub {field.name}: {field.field_type},\n")
        
        f.write("}\n\n")

def main():
    """主函数"""
    import argparse
    
    parser = argparse.ArgumentParser(description='Extract complete Solana structures for AI analysis')
    parser.add_argument('project_path', help='Path to the Solana project root')
    parser.add_argument('--output', '-o', default='output/complete_structures.rs',
                       help='Output file path (default: output/complete_structures.rs)')
    
    args = parser.parse_args()
    
    extractor = SolanaStructExtractor(args.project_path)
    print(f"Extracting complete structures from: {args.project_path}")
    
    extractor.extract_from_project()
    extractor.export_to_rust_file(args.output)

if __name__ == '__main__':
    main()