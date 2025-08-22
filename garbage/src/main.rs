mod utils;
mod calculator;

use utils::helper_function;
use calculator::Calculator;

fn main() {
    println!("Testing call hierarchy");
    
    // 调用本地函数
    let result = add_numbers(5, 3);
    println!("Addition result: {}", result);
    
    // 调用模块函数
    helper_function();
    
    // 调用结构体方法
    let calc = Calculator::new();
    let multiply_result = calc.multiply(4, 6);
    println!("Multiplication result: {}", multiply_result);
    
    // 调用嵌套函数
    complex_operation();
}

fn add_numbers(a: i32, b: i32) -> i32 {
    a + b
}

fn complex_operation() {
    let x = calculate_square(10);
    let y = calculate_cube(3);
    println!("Square: {}, Cube: {}", x, y);
}

fn calculate_square(n: i32) -> i32 {
    n * n
}

fn calculate_cube(n: i32) -> i32 {
    n * n * n
}