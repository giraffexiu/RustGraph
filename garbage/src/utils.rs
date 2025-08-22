pub fn helper_function() {
    println!("Helper function called");
    internal_helper();
}

fn internal_helper() {
    println!("Internal helper called");
    another_internal_function();
}

fn another_internal_function() {
    println!("Another internal function called");
}

pub fn utility_function(value: i32) -> i32 {
    value * 2
}