class(animal).
class(mammal).
class(polar_bear).
class(seal).
class(reindeer).
class(fish).
class(sardine).
class(bird).
class(penguin).
class(herbivore).
class(carnivore).
class(prey).
class(predator).

subclass(mammal, animal).
subclass(bird, animal).
subclass(fish, animal).
subclass(polar_bear, mammal).
subclass(seal, mammal).
subclass(reindeer, mammal).
subclass(sardine, fish).
subclass(penguin, bird).
subclass(reindeer, herbivore).


subClass(C1, C2) :-
    subclass(C1, C2).
subClass(C1, C2) :-
    subclass(C1, C3),
    subClass(C3, C2).

disjointClasses(carnivore, herbivore).

isa(beary, polar_bear).
isa(sealy, seal).
isa(reiny, reindeer).
isa(reiny_b, reindeer).
isa(reiny_c, reindeer).
isa(sardy, sardine).
isa(penguy, penguin).

hasproperty(beary, hunt, sealy).
hasproperty(beary, hunt, penguy).
hasproperty(sealy, hunt, penguy).
hasproperty(penguy, hunt, sardy).
hasproperty(reiny, hunt, sardy).
hasproperty(reiny_b, sonOf, reiny).
hasproperty(reiny_c, sonOf, reiny_b).

hasproperty(I1, ancestor, I2) :-
    hasproperty(I2, sonOf, I1).
hasproperty(I1, ancestor, I2) :-
    hasproperty(I2, sonOf, I3),
    hasproperty(I1, ancestor, I3).


isA(I, C) :-
    isa(I, C).
isA(I, C) :-
    isa(I, C2),
    subClass(C2, C).

isA(I, carnivore) :-
    hasproperty(I, hunt, _).
isA(I, predator) :-
    hasproperty(I, hunt, _).
isA(I, prey) :-
    hasproperty(_, hunt, I).


not(isA(I, C)) :-
    disjointClasses(C, C2),
    isA(I, C2).

error(['A term cannot be both true and false.', P]) :- not(P), P.