// Extracted Solana Contract Structures for AI Vulnerability Analysis
// Complete context to prevent cross-file misanalysis

use anchor_lang::prelude::*;

// ===== PROGRAM IDs =====

// ../2025-01-pump-science/programs/pump-science/src/lib.rs:14
declare_id!("EtZR9gh25YUM6LkL2o2yYV1KzyuDdftHvYk3wsb2Ypkj");

// ===== CONSTANTS =====

// ../2025-01-pump-science/programs/pump-science/src/util.rs:1
pub const BASIS_POINTS_DIVISOR: u64 = 10_000;

// ../2025-01-pump-science/programs/pump-science/src/constants.rs:1
pub const METEORA_PROGRAM_KEY: &str = "Eo7WjKq67rjJQSZxS6z3YkapzY3eMj6Xy8X5EQVn5UaB";

// ../2025-01-pump-science/programs/pump-science/src/constants.rs:2
pub const METEORA_VAULT_PROGRAM_KEY: &str = "24Uqj9JCLxUeoC3hGfh5W3s9FM9uCHDS2SG3LYwBpyTi";

// ../2025-01-pump-science/programs/pump-science/src/constants.rs:3
pub const QUOTE_MINT: &str = "So11111111111111111111111111111111111111112";

// ../2025-01-pump-science/programs/pump-science/src/constants.rs:5
pub const CREATION_AUTHORITY_PUBKEY: &str = "Hce3sP3t82MZFSt42ZmMQMF34sghycvjiQXsSEp6afui";

// ../2025-01-pump-science/programs/pump-science/src/constants.rs:6
pub const MAX_START_SLOT_DELAY: u64 = 1_512_000;

// ../2025-01-pump-science/programs/pump-science/src/constants.rs:8
pub const TOKEN_VAULT_SEED: &str = "token_vault";

// ../2025-01-pump-science/programs/pump-science/src/state/whitelist.rs:10
pub const SEED_PREFIX: &'static str = "wl-seed";

// ../2025-01-pump-science/programs/pump-science/src/state/global.rs:73
pub const SEED_PREFIX: &'static str = "global";

// ../2025-01-pump-science/programs/pump-science/src/state/bonding_curve/curve.rs:11
pub const SEED_PREFIX: &'static str = "bonding-curve";

// ../2025-01-pump-science/programs/pump-science/src/state/bonding_curve/curve.rs:12
pub const SOL_ESCROW_SEED_PREFIX: &'static str = "sol-escrow";

// ===== COMPLETE STRUCT DEFINITIONS =====

// ../2025-01-pump-science/programs/pump-science/src/events.rs:4
#[event]
pub struct GlobalUpdateEvent {
    pub global_authority: Pubkey,
    pub migration_authority: Pubkey,
    pub initial_virtual_token_reserves: u64,
    pub initial_virtual_sol_reserves: u64,
    pub initial_real_token_reserves: u64,
    pub token_total_supply: u64,
    pub mint_decimals: u8,
}

// ../2025-01-pump-science/programs/pump-science/src/events.rs:15
#[event]
pub struct CreateEvent {
    pub mint: Pubkey,
    pub creator: Pubkey,
    pub name: String,
    pub symbol: String,
    pub uri: String,
    pub start_slot: u64,
    pub virtual_sol_reserves: u64,
    pub virtual_token_reserves: u64,
    pub real_sol_reserves: u64,
    pub real_token_reserves: u64,
    pub token_total_supply: u64,
}

// ../2025-01-pump-science/programs/pump-science/src/events.rs:30
#[event]
pub struct WithdrawEvent {
    pub withdraw_authority: Pubkey,
    pub mint: Pubkey,
    pub fee_vault: Pubkey,
    pub withdrawn: u64,
    pub total_withdrawn: u64,
    pub withdraw_time: i64,
}

// ../2025-01-pump-science/programs/pump-science/src/events.rs:42
#[event]
pub struct TradeEvent {
    pub mint: Pubkey,
    pub sol_amount: u64,
    pub token_amount: u64,
    pub fee_lamports: u64,
    pub is_buy: bool,
    pub user: Pubkey,
    pub timestamp: i64,
    pub virtual_sol_reserves: u64,
    pub virtual_token_reserves: u64,
    pub real_sol_reserves: u64,
    pub real_token_reserves: u64,
}

// ../2025-01-pump-science/programs/pump-science/src/events.rs:57
#[event]
pub struct CompleteEvent {
    pub user: Pubkey,
    pub mint: Pubkey,
    pub virtual_sol_reserves: u64,
    pub virtual_token_reserves: u64,
    pub real_sol_reserves: u64,
    pub real_token_reserves: u64,
    pub timestamp: i64,
}

// ../2025-01-pump-science/programs/pump-science/src/instructions/admin/add_wl.rs:9
#[derive(Accounts)]
#[instruction(new_creator: Pubkey)]
#[derive(Accounts)]
pub struct AddWl {
    pub admin: Signer<'info>,
}

// ../2025-01-pump-science/programs/pump-science/src/instructions/curve/swap.rs:19
#[derive(AnchorSerialize, AnchorDeserialize, Clone)]
#[derive(AnchorSerialize, AnchorDeserialize, Clone)]
pub struct SwapParams {
    pub base_in: bool,
    pub exact_in_amount: u64,
    pub min_out_amount: u64,
}

// ../2025-01-pump-science/programs/pump-science/src/instructions/curve/create_bonding_curve.rs:21
#[derive(Accounts)]
#[instruction(params: CreateBondingCurveParams)]
#[derive(Accounts)]
#[event_cpi]
pub struct CreateBondingCurve {
    pub mint: :decimals = global.mint_decimals,
    pub mint: :authority = bonding_curve,
    pub mint: :freeze_authority = bonding_curve,
    #[account(mut)]
    pub creator: Signer<'info>,
    pub associated_token: :mint = mint,
    pub associated_token: :authority = bonding_curve,
    pub bonding_curve_sol_escrow: AccountInfo<'info>,
    #[account(mut)]
    pub metadata: UncheckedAccount<'info>,
    pub system_program: UncheckedAccount<'info>,
    pub associated_token_program: UncheckedAccount<'info>,
    pub token_metadata_program: UncheckedAccount<'info>,
    pub rent: UncheckedAccount<'info>,
    pub bonding_curve_bump: u8,
    pub mint: self.mint.clone(),
    pub bonding_curve: self.bonding_curve.clone(),
    pub bonding_curve_token_account: self.bonding_curve_token_account.clone(),
    pub bonding_curve_sol_escrow: self.bonding_curve_sol_escrow.clone(),
    pub token_program: self.token_program.clone(),
    pub global: self.global.clone(),
}

// ../2025-01-pump-science/programs/pump-science/src/instructions/migration/create_pool.rs:12
#[derive(Accounts)]
#[derive(Accounts)]
pub struct InitializePoolWithConfig {
    #[account(mut)]
    pub fee_receiver: UncheckedAccount<'info>,
    #[account(mut)]
    pub pool: UncheckedAccount<'info>,
    pub config: UncheckedAccount<'info>,
    #[account(mut)]
    pub lp_mint: UncheckedAccount<'info>,
    #[account(mut)]
    pub a_vault_lp: UncheckedAccount<'info>,
    #[account(mut)]
    pub b_vault_lp: UncheckedAccount<'info>,
    pub token_a_mint: UncheckedAccount<'info>,
    #[account(mut)]
    #[account(mut)]
    pub a_vault: UncheckedAccount<'info>,
    #[account(mut)]
    pub b_vault: UncheckedAccount<'info>,
    pub seeds: :program = vault_program.key(),
    pub seeds: :program = vault_program.key(),
    #[account(mut)]
    pub a_vault_lp_mint: UncheckedAccount<'info>,
    #[account(mut)]
    pub b_vault_lp_mint: UncheckedAccount<'info>,
    pub associated_token: :mint = token_b_mint,
    pub associated_token: :authority = bonding_curve,
    pub associated_token: :mint = token_b_mint,
    pub associated_token: :authority = fee_receiver,
    #[account(mut, seeds = [BondingCurve::SOL_ESCROW_SEED_PREFIX.as_bytes(), token_b_mint.to_account_info().key.as_ref()]
    pub bonding_curve_sol_escrow: AccountInfo<'info>,
    pub associated_token: :mint = token_a_mint,
    pub associated_token: :authority = bonding_curve_sol_escrow,
    pub associated_token: :mint = token_b_mint,
    pub associated_token: :authority = bonding_curve_sol_escrow,
    #[account(mut)]
    pub payer_pool_lp: UncheckedAccount<'info>,
    #[account(mut)]
    pub protocol_token_a_fee: UncheckedAccount<'info>,
    #[account(mut)]
    pub protocol_token_b_fee: UncheckedAccount<'info>,
    #[account(mut)]
    pub payer: Signer<'info>,
    #[account(mut)]
    pub mint_metadata: UncheckedAccount<'info>,
    pub rent: UncheckedAccount<'info>,
    pub metadata_program: UncheckedAccount<'info>,
    pub vault_program: UncheckedAccount<'info>,
    pub associated_token_program: UncheckedAccount<'info>,
    #[account(mut)]
    pub meteora_program: AccountInfo<'info>,
    pub ContractError: :ConfigOutdated,
    pub ContractError: :NotBondingCurveMint,
    pub ContractError: :NotSOL,
    pub ContractError: :InvalidFeeReceiver,
    pub ContractError: :InvalidConfig,
    pub ContractError: :InvalidMigrationAuthority,
    pub ContractError: :NotCompleted,
    pub ContractError: :InvalidMeteoraProgram,
    pub from: ctx.accounts.bonding_curve_token_account.to_account_info(),
    pub to: ctx.accounts.payer_token_b.to_account_info(),
    pub authority: ctx.accounts.bonding_curve.to_account_info(),
    pub token: :transfer(,
    pub CpiContext: :new_with_signer(,
    pub account: ctx.accounts.payer_token_a.to_account_info(),
    pub token: :sync_native(cpi_ctx)?;,
    pub pubkey: *acc.key,
    pub is_signer: false,
    pub is_writable: true,
    pub program_id: ctx.accounts.meteora_program.key(),
    pub from: ctx.accounts.bonding_curve_token_account.to_account_info(),
    pub to: ctx.accounts.fee_receiver_token_account.to_account_info(),
    pub authority: ctx.accounts.bonding_curve.to_account_info(),
    pub token: :transfer(,
    pub CpiContext: :new_with_signer(,
}

// ../2025-01-pump-science/programs/pump-science/src/state/whitelist.rs:5
#[derive(InitSpace, Debug, Default)]
#[derive(InitSpace, Debug, Default)]
#[account]
pub struct Whitelist {
    pub creator: Pubkey,
}

// ../2025-01-pump-science/programs/pump-science/src/state/global.rs:8
#[derive(AnchorSerialize, AnchorDeserialize)]
#[derive(AnchorSerialize, AnchorDeserialize)]
pub struct GlobalAuthorityInput {
    pub global_authority: Option<Pubkey>,
    pub migration_authority: Option<Pubkey>,
}

// ../2025-01-pump-science/programs/pump-science/src/state/global.rs:15
#[derive(InitSpace, Debug)]
#[derive(InitSpace, Debug)]
#[account]
pub struct Global {
    pub initialized: bool,
    pub global_authority: Pubkey,
    pub migration_authority: Pubkey,
    pub migrate_fee_amount: u64,
    pub migration_token_allocation: u64,
    pub fee_receiver: Pubkey,
    pub initial_virtual_token_reserves: u64,
    pub initial_virtual_sol_reserves: u64,
    pub initial_real_token_reserves: u64,
    pub token_total_supply: u64,
    pub mint_decimals: u8,
    pub meteora_config: Pubkey,
    pub whitelist_enabled: bool,
    pub last_updated_slot: u64,
}

// ../2025-01-pump-science/programs/pump-science/src/state/global.rs:59
#[derive(AnchorSerialize, AnchorDeserialize, Debug, Clone)]
#[derive(AnchorSerialize, AnchorDeserialize, Debug, Clone)]
pub struct GlobalSettingsInput {
    pub initial_virtual_token_reserves: u64,
    pub initial_virtual_sol_reserves: u64,
    pub initial_real_token_reserves: u64,
    pub token_total_supply: u64,
    pub mint_decimals: u8,
    pub migrate_fee_amount: u64,
    pub migration_token_allocation: u64,
    pub fee_receiver: Pubkey,
    pub whitelist_enabled: bool,
    pub meteora_config: Pubkey,
}

// ../2025-01-pump-science/programs/pump-science/src/state/bonding_curve/structs.rs:4
#[derive(Debug, Clone)]
#[derive(Debug, Clone)]
pub struct BuyResult {
    pub token_amount: u64,
    pub sol_amount: u64,
}

// ../2025-01-pump-science/programs/pump-science/src/state/bonding_curve/structs.rs:10
#[derive(Debug, Clone)]
#[derive(Debug, Clone)]
pub struct SellResult {
    pub token_amount: u64,
    pub sol_amount: u64,
}

// ../2025-01-pump-science/programs/pump-science/src/state/bonding_curve/structs.rs:17
#[derive(InitSpace, Debug, Default)]
#[derive(InitSpace, Debug, Default)]
#[account]
pub struct BondingCurve {
    pub mint: Pubkey,
    pub creator: Pubkey,
    pub initial_real_token_reserves: u64,
    pub virtual_sol_reserves: u64,
    pub virtual_token_reserves: u64,
    pub real_sol_reserves: u64,
    pub real_token_reserves: u64,
    pub token_total_supply: u64,
    pub start_slot: u64,
    pub complete: bool,
    pub bump: u8,
}

// ../2025-01-pump-science/programs/pump-science/src/state/bonding_curve/structs.rs:36
#[derive(AnchorSerialize, AnchorDeserialize, Clone)]
#[derive(AnchorSerialize, AnchorDeserialize, Clone)]
pub struct CreateBondingCurveParams {
    pub name: String,
    pub symbol: String,
    pub uri: String,
    pub start_slot: Option<u64>,
}

// ===== GOVERNANCE =====

// ../2025-01-pump-science/programs/pump-science/src/events.rs:5
// Governance Type: admin

// ../2025-01-pump-science/programs/pump-science/src/events.rs:6
// Governance Type: migration

// ../2025-01-pump-science/programs/pump-science/src/state/global.rs:9
// Governance Type: admin

// ../2025-01-pump-science/programs/pump-science/src/state/global.rs:10
// Governance Type: migration

// ../2025-01-pump-science/programs/pump-science/src/state/global.rs:17
// Governance Type: admin

// ../2025-01-pump-science/programs/pump-science/src/state/global.rs:18
// Governance Type: migration

