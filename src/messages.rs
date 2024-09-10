use actix::{Message, Recipient};
use serde::Serialize;
use uuid::Uuid;

#[derive(Message, Serialize)]
#[serde(rename_all = "camelCase")]
#[rtype(result = "()")]
pub struct WebsocketMessage {
    pub type_: String,
    pub error: Option<String>,
    pub message: MessageType,
}

#[derive(Serialize)]
pub enum MessageType {
    Status(StatusMessage),
    Game(GameMessage),
}

#[derive(Serialize)]
#[serde(rename_all = "camelCase")]
pub struct StatusMessage {
    pub status: String,
    pub room_name: Option<String>,
}

#[derive(Serialize)]
#[serde(rename_all = "camelCase")]
pub struct GameMessage {
    pub board: [i8; 9],
    pub elapsed_turn: u8,
    pub is_my_turn: bool,
    pub result: Option<String>,
}

#[derive(Message)]
#[rtype(result = "()")]
pub struct Connect {
    pub id: Uuid,
    pub addr: Recipient<WebsocketMessage>,
}

#[derive(Message)]
#[rtype(result = "()")]
pub struct Disconnect {
    pub id: Uuid,
    pub room_name: Option<String>,
}

#[derive(Message)]
#[rtype(result = "()")]
pub struct ClientMessage {
    pub id: Uuid,
    pub room_name: Option<String>,
    pub query: String,
    pub body: String,
}
