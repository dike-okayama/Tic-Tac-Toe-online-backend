mod game;
mod messages;
mod websocket_actor;
mod websocket_session;
use actix::{Actor, Addr};
use actix_web::{get, web::Data, web::Payload, App, Error, HttpRequest, HttpResponse, HttpServer};
use actix_web_actors::ws;
use dotenvy::dotenv;
use openssl::ssl::{SslAcceptor, SslFiletype, SslMethod};
use websocket_actor::WebsocketActor;
use websocket_session::WebsocketSession;

#[get("/")]
pub async fn handle_connection(
    req: HttpRequest,
    stream: Payload,
    srv: Data<Addr<WebsocketActor>>,
) -> Result<HttpResponse, Error> {
    let session = WebsocketSession::new(srv.get_ref().clone());
    let response = ws::start(session, &req, stream)?;
    Ok(response)
}

#[get("/health")]
pub async fn health() -> HttpResponse {
    HttpResponse::Ok().finish()
}

#[actix_web::main]
async fn main() -> std::io::Result<()> {
    dotenv().ok();

    let host = std::env::var("HOST").unwrap_or("0.0.0.0".to_string());
    let port = std::env::var("PORT").unwrap_or("8000".to_string());

    let websocket_server = WebsocketActor::default().start();

    if std::env::var("PRIVATE_KEY_FILE").is_err()
        || std::env::var("CERTIFICATE_CHAIN_FILE").is_err()
    {
        HttpServer::new(move || {
            App::new()
                .service(handle_connection)
                .service(health)
                .app_data(Data::new(websocket_server.clone()))
        })
        .bind(format!("{}:{}", host, port))?
        .run()
        .await
    } else {
        let private_key = std::env::var("PRIVATE_KEY_FILE").unwrap();
        let certificate_chain = std::env::var("CERTIFICATE_CHAIN_FILE").unwrap();

        let mut builder = SslAcceptor::mozilla_intermediate(SslMethod::tls()).unwrap();
        builder
            .set_private_key_file(private_key, SslFiletype::PEM)
            .unwrap();
        builder
            .set_certificate_chain_file(certificate_chain)
            .unwrap();

        HttpServer::new(move || {
            App::new()
                .service(handle_connection)
                .service(health)
                .app_data(Data::new(websocket_server.clone()))
        })
        .bind_openssl(format!("{}:{}", host, port), builder)?
        .run()
        .await
    }
}
