pub struct Calculator {
    name: String,
}

impl Calculator {
    pub fn new() -> Self {
        Calculator {
            name: "Basic Calculator".to_string(),
        }
    }
    
    pub fn multiply(&self, a: i32, b: i32) -> i32 {
        self.internal_multiply(a, b)
    }
    
    fn internal_multiply(&self, a: i32, b: i32) -> i32 {
        a * b
    }
    
    pub fn divide(&self, a: f64, b: f64) -> Option<f64> {
        if b != 0.0 {
            Some(a / b)
        } else {
            None
        }
    }
}

pub fn standalone_function() {
    println!("Standalone function in calculator module");
}