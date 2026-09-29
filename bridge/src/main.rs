use std::{
    env,
    net::{IpAddr, Ipv4Addr, SocketAddr},
};

#[tokio::main]
async fn main() -> Result<(), Box<dyn std::error::Error>> {
    match env::args().nth(1).as_deref() {
        Some("stdio") => devloop_bridge::server::run_stdio()?,
        Some("serve") => {
            let port: u16 = env::var("DEVLOOP_BRIDGE_PORT")
                .unwrap_or_else(|_| "8765".into())
                .parse()?;
            let listener = tokio::net::TcpListener::bind(SocketAddr::new(
                IpAddr::V4(Ipv4Addr::LOCALHOST),
                port,
            ))
            .await?;
            axum::serve(listener, devloop_bridge::server::router()).await?;
        }
        _ => {
            eprintln!("usage: devloop-bridge [stdio|serve]");
            std::process::exit(2);
        }
    }
    Ok(())
}
