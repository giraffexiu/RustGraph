pub mod utils;
pub mod calculator;

pub use utils::*;
pub use calculator::*;

pub fn library_function() {
    println!("Library function called");
    utils::helper_function();
}

pub fn advanced_calculation(x: i32, y: i32) -> i32 {
    let calc = Calculator::new();
    let result = calc.multiply(x, y);
    utils::utility_function(result)
}