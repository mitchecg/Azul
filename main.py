from classes import *
import io_classes as io_


state = "controls"
prev_state = ""


def main():
    global state
    global prev_state
    playing = True
    io = io_.IoHandler()
    players = ["Clay", "Lauren"] # , "Scott", "Malinda"]
    player = ""
    begun = False
    events = []
    while playing:
        event = io.CheckEvents(state)
        if event[0] == "QUIT":
            playing = False
        if state == "controls":
            controls = Controls(io, begun)
            change_state("starting")
        elif state == "starting":
            begun = True
            game = Game(io, players)
            change_state("dealing")
        elif state == "dealing":
            game.Deal()
            change_state("playing")
        elif state == "playing":
            change_state(game.Play(event))
            # state = game.Play(event)
        elif state == "scoring round":
            change_state(game.ScoreRound(event))
            # state = game.ScoreRound(event)
        elif state == "scoring game":
            game.ScoreGame(event)
            change_state("complete")
        elif state == "complete":
            pass
        else:
            pass
        io.Display()


def change_state(new_state):
    global state
    global prev_state
    prev_state = state
    state = new_state


main()
