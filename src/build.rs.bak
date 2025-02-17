fn main() {
    println!("cargo:rerun-if-changed=docs");
    if std::process::Command::new("mdbook")
        .arg("build")
        // .arg("../src")
        // .arg("--dest-dir")
        // .arg("../target/website")
        .status()
        .expect("Failed to execute mdbook")
        .success()
    {
        println!("cargo:warning=Documentation built successfully");
    } else {
        println!("cargo:warning=Documentation build failed");
    }
}
