type BoardType = [i8; 9];

pub struct TicTacToe {
    pub elapsed_turn: u8,
    pub board: BoardType,
}

impl TicTacToe {
    const LINES: [[u8; 3]; 8] = [
        [0, 1, 2],
        [3, 4, 5],
        [6, 7, 8],
        [0, 3, 6],
        [1, 4, 7],
        [2, 5, 8],
        [0, 4, 8],
        [2, 4, 6],
    ];

    const HITS: [[i8; 3]; 2] = [[0, 0, 0], [1, 1, 1]];

    pub fn new() -> TicTacToe {
        TicTacToe {
            elapsed_turn: 0,
            board: [-1; 9],
        }
    }
    pub fn is_ended(&self) -> bool {
        for target_line in TicTacToe::LINES.iter() {
            let mut line = [0; 3];
            for (i, target) in target_line.iter().enumerate() {
                line[i] = self.board[*target as usize];
            }
            if line == TicTacToe::HITS[0] || line == TicTacToe::HITS[1] {
                return true;
            };
        }

        if self.elapsed_turn == 9 {
            return true;
        }

        false
    }

    pub fn get_result(&self) -> i8 {
        if !self.is_ended() {
            return -1;
        }

        for target_line in TicTacToe::LINES.iter() {
            let mut line = [0; 3];
            for (i, target) in target_line.iter().enumerate() {
                line[i] = self.board[*target as usize];
            }
            if line == TicTacToe::HITS[0] {
                return 0;
            } else if line == TicTacToe::HITS[1] {
                return 1;
            };
        }
        2
    }

    pub fn put(&mut self, pos: usize) -> bool {
        if self.is_ended() {
            return false;
        }

        if self.board[pos] != -1 {
            return false;
        }

        if pos > 8 {
            return false;
        }

        self.board[pos] = (self.elapsed_turn as i8) % 2;
        self.elapsed_turn += 1;

        true
    }

    pub fn reset(&mut self) {
        self.elapsed_turn = 0;
        self.board = [-1; 9];
    }
}
