use crate::messages::{ClientMessage, Connect, Disconnect, WebsocketMessage};
use crate::websocket_actor::WebsocketActor;
use actix::{
    fut, Actor, ActorContext, ActorFutureExt, Addr, AsyncContext, ContextFutureSpawner, Handler,
    Running, StreamHandler, WrapFuture,
};
use actix_web_actors::ws;
use std::time::{Duration, Instant};
use uuid::Uuid;

const HEARTBEAT_INTERVAL: Duration = Duration::from_secs(5);
const CLIENT_TIMEOUT: Duration = Duration::from_secs(10);

#[derive(Debug)]
enum SessionStatus {
    Searching,
    Waiting,
    Playing,
}

pub struct WebsocketSession {
    id: Uuid,
    addr: Addr<WebsocketActor>,
    hb: Instant,
    status: SessionStatus,
    room_name: Option<String>,
}

impl WebsocketSession {
    pub fn new(addr: Addr<WebsocketActor>) -> WebsocketSession {
        WebsocketSession {
            id: Uuid::new_v4(),
            addr,
            hb: Instant::now(),
            status: SessionStatus::Searching,
            room_name: None,
        }
    }

    fn hb(&self, ctx: &mut ws::WebsocketContext<Self>) {
        ctx.run_interval(HEARTBEAT_INTERVAL, |act, ctx| {
            if Instant::now().duration_since(act.hb) > CLIENT_TIMEOUT {
                ctx.stop();
                return;
            }
            ctx.ping(b"");
        });
    }
}

impl Actor for WebsocketSession {
    type Context = ws::WebsocketContext<Self>;

    fn started(&mut self, ctx: &mut Self::Context) {
        self.hb(ctx);

        let addr = ctx.address();
        self.addr
            .send(Connect {
                id: self.id,
                addr: addr.recipient(),
            })
            .into_actor(self)
            .then(|res, _, ctx| {
                match res {
                    Ok(_) => (),
                    _ => ctx.stop(),
                }
                fut::ready(())
            })
            .wait(ctx);
    }

    fn stopping(&mut self, _: &mut Self::Context) -> Running {
        self.addr.do_send(Disconnect {
            id: self.id,
            room_name: self.room_name.clone(),
        });
        Running::Stop
    }
}

impl StreamHandler<Result<ws::Message, ws::ProtocolError>> for WebsocketSession {
    fn handle(&mut self, msg: Result<ws::Message, ws::ProtocolError>, ctx: &mut Self::Context) {
        let msg = match msg {
            Err(_) => {
                ctx.stop();
                return;
            }
            Ok(msg) => msg,
        };

        match msg {
            ws::Message::Ping(msg) => {
                self.hb = Instant::now();
                ctx.pong(&msg);
            }
            ws::Message::Pong(_) => {
                self.hb = Instant::now();
            }
            ws::Message::Binary(bin) => ctx.binary(bin),
            ws::Message::Close(_) => {
                ctx.stop();
            }
            ws::Message::Continuation(_) => {
                ctx.stop();
            }
            ws::Message::Nop => (),
            ws::Message::Text(s) => {
                let query = s.split(' ').collect::<Vec<&str>>();

                match self.status {
                    SessionStatus::Searching => {
                        if !(query[0] == "create" || query[0] == "join") {
                            return;
                        }
                    }
                    SessionStatus::Waiting => {
                        if query[0] != "leave" {
                            return;
                        }
                    }
                    SessionStatus::Playing => {
                        if !(query[0] == "put" || query[0] == "restart" || query[0] == "exit") {
                            return;
                        }
                    }
                }

                self.addr.do_send(ClientMessage {
                    id: self.id,
                    room_name: if self.room_name.is_none() {
                        None
                    } else {
                        Some(self.room_name.clone().unwrap())
                    },
                    query: query[0].to_string(),
                    body: query[1..].join(" "),
                })
            }
        }
    }
}

impl Handler<WebsocketMessage> for WebsocketSession {
    type Result = ();

    fn handle(&mut self, msg: WebsocketMessage, ctx: &mut Self::Context) {
        if let Some(ref status_message) = msg.status_message {
            match status_message.status.as_str() {
                "Searching" => {
                    self.status = SessionStatus::Searching;
                }
                "Waiting" => {
                    self.status = SessionStatus::Waiting;
                }
                "Playing" => {
                    self.status = SessionStatus::Playing;
                }
                _ => (),
            }
            if let Some(room_name) = status_message.room_name.to_owned() {
                self.room_name = Some(room_name);
            }
        }
        ctx.text(serde_json::to_string(&msg).unwrap());
    }
}
