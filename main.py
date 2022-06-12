from classes import *
import io_classes as io_


def main():
    playing = True
    io = io_.IoHandler()
    players = ["Clay", "Lauren"] # , "Scott", "Malinda"]
    player = ""
    state = "starting"
    events = []
    while playing:
        event = io.CheckEvents(state)
        if event[0] == "QUIT":
            playing = False
        if state == "starting":
            game = Game(io, players)
            state = "dealing"
        elif state == "dealing":
            game.Deal()
            state = "playing"
        elif state == "playing":
            state = game.Play(event)
        elif state == "scoring round":
            state = game.ScoreRound(event)
        elif state == "scoring game":
            game.ScoreGame(event)
            state = "complete"
        elif state == "complete":
            pass
        else:
            pass
        io.Display()


main()