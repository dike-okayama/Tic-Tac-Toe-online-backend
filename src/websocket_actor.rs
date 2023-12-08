use crate::game::TicTacToe;
use crate::messages::{
    ClientMessage, Connect, Disconnect, GameMessage, StatusMessage, WebsocketMessage,
};
use actix::{Actor, Context, Handler, Recipient};
use std::collections::HashMap;
use uuid::Uuid;

#[derive(Default)]
pub struct WebsocketActor {
    sessions: HashMap<Uuid, Recipient<WebsocketMessage>>,
    rooms: HashMap<String, (Vec<Uuid>, TicTacToe)>,
}

impl WebsocketActor {
    fn send_status_message(
        &self,
        id_to: &Uuid,
        room_name: Option<String>,
        status: &str,
        error: Option<String>,
    ) {
        if let Some(socket_recipient) = self.sessions.get(id_to) {
            socket_recipient.do_send(WebsocketMessage {
                type_: "Status".to_string(),
                error,
                status_message: Some(StatusMessage {
                    status: status.to_owned(),
                    room_name: room_name.to_owned(),
                }),
                game_message: None,
            });
        }
    }

    fn send_game_message(&self, id_to: &Uuid, room_name: &str, to_cross: bool) {
        let (_, game) = self.rooms.get(room_name).unwrap();
        let result = match game.get_result() {
            0 => Some(if to_cross { "You win!" } else { "You lose." }.to_string()),
            1 => Some(if to_cross { "You lose." } else { "You win!" }.to_string()),
            2 => Some("Draw".to_string()),
            _ => None,
        };
        if let Some(socket_recipient) = self.sessions.get(id_to) {
            socket_recipient.do_send(WebsocketMessage {
                type_: "Game".to_string(),
                error: None, // for the future implementation
                status_message: None,
                game_message: Some(GameMessage {
                    board: game.board,
                    elapsed_turn: game.elapsed_turn,
                    is_my_turn: to_cross == (game.elapsed_turn % 2 == 0),
                    result,
                }),
            });
        }
    }
}

impl Actor for WebsocketActor {
    type Context = Context<Self>;
}

impl Handler<Connect> for WebsocketActor {
    type Result = ();

    fn handle(&mut self, msg: Connect, _: &mut Context<Self>) -> Self::Result {
        self.sessions.insert(msg.id, msg.addr);
    }
}

impl Handler<Disconnect> for WebsocketActor {
    type Result = ();

    fn handle(&mut self, msg: Disconnect, _: &mut Context<Self>) {
        let client_id = msg.id;
        if let Some(room_name) = msg.room_name {
            let (members, _) = self.rooms.get_mut(&room_name).unwrap();
            for id in members.clone().iter() {
                if id != &client_id {
                    self.send_status_message(id, None, "Searching", None);
                }
            }
            self.rooms.remove(&room_name);
        }
        self.sessions.remove(&client_id);
    }
}

impl Handler<ClientMessage> for WebsocketActor {
    type Result = ();

    fn handle(&mut self, msg: ClientMessage, _: &mut Context<Self>) {
        match msg.query.as_str() {
            "create" => {
                let room_name = &msg.body;
                if self.rooms.contains_key(room_name) {
                    self.send_status_message(
                        &msg.id,
                        None,
                        "Searching",
                        Some("The room already exists.".to_string()),
                    );
                } else {
                    self.rooms
                        .insert(room_name.to_owned(), (vec![msg.id], TicTacToe::new()));
                    self.send_status_message(&msg.id, Some(room_name.to_owned()), "Waiting", None);
                }
            }
            "join" => {
                let room_name = &msg.body;
                if let Some((members, _)) = self.rooms.get_mut(room_name) {
                    if members.len() >= 2 {
                        self.send_status_message(
                            &msg.id,
                            None,
                            "Searching",
                            Some("The room is already full.".to_string()),
                        );
                    } else {
                        let cross_id = members[0];
                        members.push(msg.id);
                        for id in members.clone().iter() {
                            self.send_status_message(
                                id,
                                Some(room_name.to_owned()),
                                "Playing",
                                None,
                            );
                            self.send_game_message(id, room_name, cross_id == *id);
                        }
                    }
                } else {
                    self.send_status_message(
                        &msg.id,
                        None,
                        "Searching",
                        Some("The room does not exist.".to_string()),
                    );
                }
            }
            "leave" => {
                let room_name = &msg.room_name.unwrap();
                if let Some((members, _)) = self.rooms.get_mut(room_name) {
                    for id in members.clone().iter() {
                        self.send_status_message(id, None, "Searching", None);
                    }
                    self.rooms.remove(room_name);
                }
            }
            "put" => {
                let room_name = &msg.room_name.unwrap();
                if let Some((members, game)) = self.rooms.get_mut(room_name) {
                    if let Ok(pos) = msg.body.parse::<usize>() {
                        let cross_id = members[0];
                        if game.put(pos) {
                            for id in members.clone().iter() {
                                self.send_game_message(id, room_name, cross_id == *id);
                            }
                        }
                    }
                }
            }
            "restart" => {
                let room_name = &msg.room_name.unwrap();
                if let Some((members, game)) = self.rooms.get_mut(room_name) {
                    members.reverse();
                    let cross_id = members[0];
                    game.reset();
                    for id in members.clone().iter() {
                        self.send_game_message(id, room_name, cross_id == *id);
                    }
                }
            }
            "exit" => {
                let room_name = &msg.room_name.unwrap();
                if let Some((members, _)) = self.rooms.get_mut(room_name) {
                    for id in members.clone().iter() {
                        self.send_status_message(id, None, "Searching", None);
                    }
                    self.rooms.remove(room_name);
                }
            }
            _ => (),
        }
    }
}
